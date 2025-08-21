#!/usr/bin/env python3
from langextract_query_gen import QueryExtractor
from Foundation import NSMetadataQuery, NSPredicate, NSCompoundPredicate, NSRunLoop, NSDate
from datetime import datetime, timedelta

class FileSearchParser:
    HIERARCHIES = {
        'public.image': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif', 'svg', 'webp', 'ico', 'heic'],
        'public.movie': ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v', 'mpg', 'mpeg'],
        'public.audio': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus', 'aiff'],
        'public.source-code': ['py', 'js', 'ts', 'cpp', 'c', 'java', 'go', 'rs', 'rb', 'php', 'swift', 'ipynb'],
        'public.text': ['txt', 'md', 'markdown', 'rst', 'log', 'rtf'],
        'com.adobe.pdf': ['pdf'],
        'public.archive': ['zip', 'tar', 'gz', 'rar', '7z', 'bz2'],
        'public.html': ['html', 'htm', 'xhtml'],
        'public.spreadsheet': ['xls', 'xlsx', 'ods', 'csv'],
        'public.presentation': ['ppt', 'pptx', 'odp'],
        'com.microsoft.word.doc': ['doc', 'docx']
        # current prototype contains these filetypes only just for testing.
    }
    
    def __init__(self):
        self.extractor = QueryExtractor()
        self.ext_to_uti = {}
        for uti, extensions in self.HIERARCHIES.items():
            for ext in extensions:
                self.ext_to_uti[ext.lower()] = uti
    
    def calculate_date_predicate(self, temporal_data):
        """Convert temporal data to date predicate (placeholder for now)"""
        if not temporal_data:
            return None
            
        for temp in temporal_data:
            if temp['time_unit'] == 'days':
                days = int(temp['value'])
                date = datetime.now() - timedelta(days=days)
                return NSPredicate.predicateWithFormat_(
                    "kMDItemFSContentChangeDate > %@", 
                    date
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
            uti = self.ext_to_uti.get(ft.lower())
            if uti:
                utis.add(uti)
        
        # Add UTI predicates
        if utis:
            uti_predicates = []
            for uti in utis:
                uti_predicates.append(
                    NSPredicate.predicateWithFormat_("kMDItemContentTypeTree CONTAINS %@", uti)
                )
            if len(uti_predicates) > 1:
                predicates.append(NSCompoundPredicate.orPredicateWithSubpredicates_(uti_predicates))
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
        
        # Add temporal predicate (basic for now)
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
            final_predicate = NSCompoundPredicate.andPredicateWithSubpredicates_(predicates)
        
        # Execute query
        query = NSMetadataQuery.alloc().init()
        query.setPredicate_(final_predicate)
        query.setSearchScopes_(["/"])
        
        query.startQuery()
        
        # Wait for results
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
        
        print(f"\nFound {len(results)} results:")
        for path in results[:10]:  # Show first 10
            print(f"  {path}")
    else:
        print("Usage: python parser.py <search query>")