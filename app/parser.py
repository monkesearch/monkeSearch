#!/usr/bin/env python3
from langextract_query_gen import QueryExtractor
from Foundation import NSMetadataQuery, NSPredicate, NSCompoundPredicate, NSRunLoop, NSDate
from datetime import datetime, timedelta
from utitools import uti_for_suffix, content_type_tree_for_uti


class FileSearchParser:

    def __init__(self):
        self.extractor = QueryExtractor()

    def calculate_date_predicate(self, temporal_data):
        """Convert temporal data to date predicate - all time ranges are relative"""
        if not temporal_data:
            return None

        for temp in temporal_data:
            time_unit = temp['time_unit']
            value = int(temp['value'])

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
                continue

            return NSPredicate.predicateWithFormat_(
                "kMDItemFSContentChangeDate > %@", date
            )
        return None

    def search(self, query_text, max_results=20):
        """Parse query and execute search"""
        # Extract components using LangExtract
        parsed = self.extractor.parse_query(query_text)

        predicates = []

        # Convert file types to UTIs and add predicates
        utis = set()
        for ft in parsed['file_types']:
            uti = uti_for_suffix(ft.lower())
            if uti:
                if parsed['is_specific']:
                    # Don't climb hierarchy for specific requests
                    utis.add(uti)
                else:
                    # Climb hierarchy for broad categories
                    hierarchy = content_type_tree_for_uti(uti)
                    if hierarchy:
                        parent_uti = hierarchy[1] if len(
                            hierarchy) > 1 else hierarchy[0]
                        utis.add(parent_uti)

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
        if parsed['misc_keywords']:
            keyword_pred = NSPredicate.predicateWithFormat_(
                "kMDItemTextContent CONTAINS[cd] %@ OR kMDItemFSName CONTAINS[cd] %@",
                parsed['misc_keywords'],
                parsed['misc_keywords']
            )
            predicates.append(keyword_pred)

        if parsed['temporal']:
            date_pred = self.calculate_date_predicate(parsed['temporal'])
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

        return results, parsed


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        parser = FileSearchParser()
        query = " ".join(sys.argv[1:])

        print(f"Searching for: {query}")
        results, parsed_data = parser.search(query)

        print(f"\nParsed data:")
        print(f"  File types: {parsed_data['file_types']}")
        print(f"  Temporal: {parsed_data['temporal']}")
        print(f"  Misc keywords: {parsed_data['misc_keywords']}")
        print(f"  Is specific: {parsed_data['is_specific']}")

        print(f"\nFound {len(results)} results:")
        for path in results[:10]:  # Show first 10
            print(f"  {path}")
    else:
        print("Usage: python parser.py <search query>")

