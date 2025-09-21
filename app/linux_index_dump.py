#!/usr/bin/env python3
"""
Linux Metadata Dumper for Vector DB
Extracts only essential metadata for semantic search embeddings
Output is optimized for vector database storage with minimal fields
"""

import os
import json
import mimetypes
from datetime import datetime
import sys

# EDIT THIS LIST: Add or remove folders to search
SEARCH_FOLDERS = [
    "Desktop",
    "Downloads", 
    "Documents",
    "Music",
    "Pictures",
    "Videos",   # Linux usually uses Videos instead of Movies
    # "/usr/share",  # Absolute path example
    # "Code/Projects",  # Subfolder example
]

def get_metadata(file_path):
    """Extract essential metadata for a given file"""
    try:
        stat = os.stat(file_path)

        # Guess MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "unknown"

        return {
            "Path": file_path,
            "Name": os.path.basename(file_path),
            "Size": stat.st_size,
            "ContentType": mime_type,
            "Kind": mime_type.split("/")[-1] if "/" in mime_type else mime_type,
            "CreationDate": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "ContentChangeDate": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def dump_linux_data(max_items: int | None, output_file="linux_dump.json"):
    home_dir = os.path.expanduser("~")
    search_paths = []

    print("Search locations:")
    for folder in SEARCH_FOLDERS:
        full_path = folder if folder.startswith("/") else os.path.join(home_dir, folder)
        if os.path.exists(full_path):
            search_paths.append(full_path)
            print(f"  ✓ {full_path}")
        else:
            print(f"  ✗ {full_path} (not found)")

    if not search_paths:
        print("No valid search paths found!")
        return []

    print(f"\nScanning filesystem (up to {max_items} items)...")
    results = []
    for root_path in search_paths:
        for root, _, files in os.walk(root_path):
            for f in files:
                file_path = os.path.join(root, f)
                meta = get_metadata(file_path)
                if meta:
                    results.append(meta)

                if max_items and len(results) >= max_items:
                    break
            if max_items and len(results) >= max_items:
                break
        if max_items and len(results) >= max_items:
            break

    # Save to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved {len(results)} items to {output_file}")

    # Show summary
    print("\nSample items:")
    for i, item in enumerate(results[:3]):
        print(f"\n[Item {i+1}]")
        print(f"  Path: {item['Path']}")
        print(f"  Name: {item['Name']}")
        print(f"  Type: {item['ContentType']}")
        print(f"  Kind: {item['Kind']}")
        size = int(item["Size"])
        if size > 1024*1024:
            print(f"  Size: {size/(1024*1024):.2f} MB")
        elif size > 1024:
            print(f"  Size: {size/1024:.2f} KB")
        else:
            print(f"  Size: {size} bytes")
        print(f"  Created: {item['CreationDate']}")
        print(f"  Modified: {item['ContentChangeDate']}")

    return results

def main():
    if len(sys.argv) > 1:
        try:
            max_items = int(sys.argv[1])
        except ValueError:
            print("Usage: python linux_spot.py [number_of_items]")
            print("Default: 10 items")
            sys.exit(1)
    else:
        max_items = None

    output_file = sys.argv[2] if len(sys.argv) > 2 else "linux_dump.json"
    dump_linux_data(max_items=max_items, output_file=output_file)

if __name__ == "__main__":
    main()
