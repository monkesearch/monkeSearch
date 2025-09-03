#!/usr/bin/env python3
from query_gen import QueryExtractor
from Foundation import NSMetadataQuery, NSPredicate, NSCompoundPredicate, NSRunLoop, NSDate
from datetime import datetime, timedelta
from utitools import uti_for_suffix, content_type_tree_for_uti
import json



class FileSearchParser:

    def __init__(self):
        self.extractor = QueryExtractor()

    def calculate_date_predicate(self, time_unit, time_unit_value):
        """Convert temporal data to date predicate - all time ranges are relative"""
        if not time_unit or not time_unit_value:
            return None

        try:
            value = int(time_unit_value)
        except (ValueError, TypeError):
            return None

        # Handle different time units - all relative from current date
        if time_unit == 'days':
            date = datetime.now() - timedelta(days=value)

        elif time_unit == 'weeks':
            date = datetime.now() - timedelta(weeks=value)

        elif time_unit == 'months':
            # Approximate months as 30 days each
            date = datetime.now() - timedelta(days=value * 30)

        elif time_unit == 'years':
            # Use 365 days per year approximation
            date = datetime.now() - timedelta(days=value * 365)
        else:
            return None

        return NSPredicate.predicateWithFormat_(
            "kMDItemFSContentChangeDate > %@", date
        )

    def extract_misc_keywords(self, cleaned_query, parsed_data):
        misc_keywords = cleaned_query.lower()
        
        # Remove text from file_type_indicators
        for indicator in parsed_data.get('file_type_indicators', []):
            if indicator.get('text'):
                misc_keywords = misc_keywords.replace(indicator['text'].lower(), "").strip()
        
        # Also remove temporal text if any
        if 'source_text' in parsed_data:
            if parsed_data['source_text'].get('time_unit'):
                misc_keywords = misc_keywords.replace(parsed_data['source_text']['time_unit'].lower(), "").strip()
            if parsed_data['source_text'].get('time_unit_value'):
                misc_keywords = misc_keywords.replace(parsed_data['source_text']['time_unit_value'].lower(), "").strip()
        
        misc_keywords = ' '.join(misc_keywords.split())
        
        # Filter out words with 2 or fewer characters
        if misc_keywords:
            words = misc_keywords.split()
            filtered_words = [word for word in words if len(word) > 2]
            misc_keywords = " ".join(filtered_words)
        
        return misc_keywords

    def search(self, query_text, max_results=20):
        """Parse query and execute search"""
        # stop words which will be removed right away, before LLM even gets it.
        STOP_WORDS = {
            'in', 'at', 'of', 'by', 'as', 'me',
            'the', 'a', 'an', 'and', 'any',
            'find', 'search', 'list', 'file', 'files',
            'ago', 'back',
            'past', 'earlier', 'folder'
        }
        words = query_text.split()
        filtered_words = [word for word in words if word.lower() not in STOP_WORDS]
        cleaned_query = " ".join(filtered_words)
        parsed = json.loads(self.extractor.llm_query_gen(cleaned_query))
        file_types = []
        is_specific = False
        for indicator in parsed.get('file_type_indicators', []):
            file_types.extend(indicator['extensions'])
            if indicator['is_specific']:
                is_specific = True
        parsed['file_types'] = file_types
        parsed['is_specific'] = is_specific

        predicates = []
        misc_keywords = []
        
        # Extract misc keywords from remaining text after LLM parsing
        misc_keywords = self.extract_misc_keywords(cleaned_query, parsed)
        
        # Convert file types to UTIs and add predicates
        utis = set()
        for ft in parsed['file_types']:
            uti = uti_for_suffix(ft.lower())
            if uti:
                if parsed['is_specific']:
                    # Don't climb hierarchy for specific requests
                    utis.add(uti)
                    print(f'{utis}-------source----------')
                else:
                    # Climb hierarchy for broad categories
                    hierarchy = content_type_tree_for_uti(uti)
                    if hierarchy:
                        parent_uti = hierarchy[1] if len(
                            hierarchy) > 1 else hierarchy[0]
                        utis.add(parent_uti)
                    print(f'{uti}------parent-----------')

        if utis:
            uti_predicates = [
                NSPredicate.predicateWithFormat_("kMDItemContentTypeTree CONTAINS %@", u)
                for u in utis
                ]
            if len(uti_predicates) > 1:
                predicates.append(
                    NSCompoundPredicate.orPredicateWithSubpredicates_(uti_predicates))
            else:
                predicates.append(uti_predicates[0])

        # Add misc keywords predicate
        if misc_keywords:
            keyword_pred = NSPredicate.predicateWithFormat_(
                "kMDItemTextContent CONTAINS[cd] %@ OR kMDItemFSName CONTAINS[cd] %@",
                misc_keywords,
                misc_keywords
            )
            predicates.append(keyword_pred)

        if parsed['time_unit'] and parsed['time_unit_value']:
            date_pred = self.calculate_date_predicate(parsed['time_unit'], parsed['time_unit_value'])
            if date_pred:
                predicates.append(date_pred)

        # Combine all predicates
        if not predicates:
            # Fallback to simple filename search
            final_predicate = NSPredicate.predicateWithFormat_(
                "kMDItemFSName CONTAINS[cd] %@",
                query_text
            )
        elif len(predicates) == 1:
            final_predicate = predicates[0]
        else:
            final_predicate = NSCompoundPredicate.andPredicateWithSubpredicates_(
                predicates)

        query = NSMetadataQuery.alloc().init()
        query.setPredicate_(final_predicate)
        query.setSearchScopes_(["/"])

        query.startQuery()

        # Wait for results (3 secs)
        run_loop = NSRunLoop.currentRunLoop()
        timeout = NSDate.dateWithTimeIntervalSinceNow_(3.0)

        while query.isGathering() and timeout.timeIntervalSinceNow() > 0:
            run_loop.runMode_beforeDate_(
                "NSDefaultRunLoopMode",
                NSDate.dateWithTimeIntervalSinceNow_(0.1)
            )

        query.stopQuery()

        # Collect results
        results = []
        for i in range(min(query.resultCount(), max_results)):
            item = query.resultAtIndex_(i)
            path = item.valueForAttribute_("kMDItemPath")
            if path:
                results.append(path)

        return results, parsed, misc_keywords


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        parser = FileSearchParser()
        query = " ".join(sys.argv[1:])

        print(f"Searching for: {query}")
        results, parsed_data, misc = parser.search(query)

        print(f"\nParsed data:")
        print(f"  File types: {parsed_data['file_types']}")
        print(f"  Time unit: {parsed_data['time_unit']}")
        print(f"  Time unit value: {parsed_data['time_unit_value']}")
        print(f"  Misc keywords: {misc}")
        print(f"  Is specific: {parsed_data['is_specific']}")
        print(parsed_data)
        print(f"\nFound {len(results)} results:")
        for path in results[:10]:  # Show first 10
            print(f"  {path}")