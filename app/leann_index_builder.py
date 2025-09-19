#!/usr/bin/env python3
import json
from pathlib import Path
from leann import LeannBuilder
import sys

def process_json_items(json_file_path):
    """Load and process JSON file with metadata items"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    INDEX_PATH = str(Path("./").resolve() / "demo.leann")
    builder = LeannBuilder(backend_name="hnsw", is_recompute=False)
    
    total_items = len(items)
    print(f"Processing {total_items} items...")
    
    for idx, item in enumerate(items):
        # Create embedding text sentence
        embedding_text = f"{item.get('Name', 'unknown')} located at {item.get('Path', 'unknown')} and size {item.get('Size', 'unknown')} bytes with content type {item.get('ContentType', 'unknown')} and kind {item.get('Kind', 'unknown')}"
        
        # Prepare metadata with dates
        metadata = {}
        if 'CreationDate' in item:
            metadata['creation_date'] = item['CreationDate']
        if 'ContentChangeDate' in item:
            metadata['modification_date'] = item['ContentChangeDate']
        
        # Add to builder
        builder.add_text(embedding_text, metadata=metadata)
        
        # Show progress
        progress = (idx + 1) / total_items * 100
        sys.stdout.write(f"\rProgress: {idx + 1}/{total_items} ({progress:.1f}%)")
        sys.stdout.flush()
    
    print("\n\nBuilding index...")
    builder.build_index(INDEX_PATH)
    print(f"✓ Index saved to {INDEX_PATH}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python build_index.py <json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    if not Path(json_file).exists():
        print(f"Error: File {json_file} not found")
        sys.exit(1)
    
    process_json_items(json_file)