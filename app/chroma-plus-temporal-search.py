import sys
from pathlib import Path
import chromadb
import re
from datetime import datetime, timedelta


CHROMA_PATH = str(Path("./").resolve() / "monke_index")
COLLECTION_NAME = "files"


class TimeParser:
    def __init__(self):
        self.pattern = r'(?:(around|about|roughly|approximately)\s+)?(\d+)\s+(hour|day|week|month|year)s?(?:\s+ago)?'
        self.regex = re.compile(self.pattern, re.IGNORECASE)
        self.stop_words = {'in', 'at', 'of', 'by', 'as', 'me', 'the', 'a', 'an', 'and', 'any', 'find', 'search', 'list', 'ago', 'back', 'past', 'earlier'}
    
    def clean_text(self, text):
        words = text.split()
        return ' '.join(word for word in words if word.lower() not in self.stop_words)
    
    def parse(self, text):
        cleaned_text = self.clean_text(text)
        matches = []
        for match in self.regex.finditer(cleaned_text):
            matches.append({
                'full_match': match.group(0), 'fuzzy': bool(match.group(1)),
                'number': int(match.group(2)), 'unit': match.group(3).lower(),
                'range': self.calculate_range(int(match.group(2)), match.group(3).lower(), bool(match.group(1)))
            })
        return matches
    
    def calculate_range(self, number, unit, is_fuzzy):
        units = {'hour': timedelta(hours=1), 'day': timedelta(days=1), 'week': timedelta(weeks=1), 'month': timedelta(days=30), 'year': timedelta(days=365)}
        base_delta = units[unit] * number
        now = datetime.now()
        target = now - base_delta
        if is_fuzzy:
            buffer = base_delta * 0.2
            start = (target - buffer).isoformat()
            end = (target + buffer).isoformat()
        else:
            start = target.isoformat()
            end = now.isoformat()
        return (start, end)


def search_files(query, top_k=15):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)

    parser = TimeParser()
    time_matches = parser.parse(query)
    
    clean_query = query
    if time_matches:
        for match in time_matches:
            clean_query = clean_query.replace(match['full_match'], '').strip()

   
    search_text = clean_query if clean_query else query
    results_chroma = collection.query(
        query_texts=[search_text],
        n_results=top_k
    )
    
    results = []
    for i in range(len(results_chroma['ids'][0])):
        results.append({
            'score': results_chroma['distances'][0][i],
            'text': results_chroma['documents'][0][i],
            'metadata': results_chroma['metadatas'][0][i]
        })

    if time_matches:
        time_range = time_matches[0]['range']
        start_time, end_time = time_range
        
        filtered_results = []
        for result in results:
            metadata = result['metadata']
            date_str = metadata.get('modification_date') or metadata.get('creation_date')
            if date_str and start_time <= date_str <= end_time:
                filtered_results.append(result)
        results = filtered_results

  
    print(f"\nSearch results for: '{query}'")
    if time_matches:
        print(f"Time filter: {time_matches[0]['number']} {time_matches[0]['unit']}(s) {'(fuzzy)' if time_matches[0]['fuzzy'] else ''}")
        print(f"Date range: {time_matches[0]['range'][0][:10]} to {time_matches[0]['range'][1][:10]}")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] Score: {result['score']:.4f} (Lower is better)")
        print(f"File Path: {result['metadata'].get('path', 'N/A')}")
        print(f"Content: {result['text']}")
        
        metadata = result['metadata']
        if 'creation_date' in metadata: print(f"Created: {metadata['creation_date']}")
        if 'modification_date' in metadata: print(f"Modified: {metadata['modification_date']}")
        print("-" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chroma-plus-temporal-search.py \"<search query>\" [top_k]")
        sys.exit(1)
    
    query_arg = sys.argv[1]
    top_k_arg = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    
    search_files(query_arg, top_k=top_k_arg)