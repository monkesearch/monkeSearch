#!/usr/bin/env python3
from pathlib import Path
from leann import LeannSearcher
import sys

INDEX_PATH = str(Path("./").resolve() / "demo.leann")

def search_files(query, top_k=5):
    """Search the index and return results"""
    searcher = LeannSearcher(INDEX_PATH)
    results = searcher.search(query, top_k=top_k)
    
    print(f"\nSearch results for: '{query}'\n")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] Score: {result['score']:.4f}")
        print(f"Content: {result['text']}")
        
        # Show metadata if present
        if result.get('metadata'):
            metadata = result['metadata']
            if 'creation_date' in metadata:
                print(f"Created: {metadata['creation_date']}")
            if 'modification_date' in metadata:
                print(f"Modified: {metadata['modification_date']}")
    
    print("-" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python search_index.py \"<search query>\" [top_k]")
        sys.exit(1)
    
    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    search_files(query, top_k)