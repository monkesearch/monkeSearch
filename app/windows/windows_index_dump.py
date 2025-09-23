import os
import json
import sys
from datetime import datetime
import mimetypes 


# define the folders to index
HOME_DIR = os.path.expanduser("~")
SEARCH_FOLDERS = [
    os.path.join(HOME_DIR, "Desktop"),
    os.path.join(HOME_DIR, "Downloads"),
    os.path.join(HOME_DIR, "Documents"),
    os.path.join(HOME_DIR, "Pictures"),
]


# os.walk is literally slow of large index 
# we're supposed to use win32 api using 'pywin32' / 'pypiwin32' for sub-second indexing, but couldn't get the stable build 
def dump_file_metadata(max_items=1000, output_file="os_walk_dump.json"):
    results = []
    print("Starting file scan with os.walk. This may take a while...")

    for folder in SEARCH_FOLDERS:
        if not os.path.exists(folder):
            print(f"Warning: Folder not found, skipping: {folder}")
            continue

        print(f"Scanning: {folder}")
        for root, _, files in os.walk(folder):
            for filename in files:
                if len(results) >= max_items:
                    break 

                file_path = os.path.join(root, filename)
                try:
                    stats = os.stat(file_path)

                    content_type, _ = mimetypes.guess_type(file_path)
                    
                    item = {
                        'Path': file_path,
                        'Name': filename,
                        'Size': stats.st_size,
                        'ContentType': content_type if content_type else 'unknown',
                        'Kind': os.path.splitext(filename)[1],
                        'CreationDate': datetime.fromtimestamp(stats.st_birthtime).isoformat(),
                        'ContentChangeDate': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    }
                    results.append(item)
                    
                    if len(results) % 100 == 0:
                        sys.stdout.write(f"\rFound {len(results)} files...")
                        sys.stdout.flush()

                except (FileNotFoundError, PermissionError) as e:
                    continue
            
            if len(results) >= max_items:
                break
        
        if len(results) >= max_items:
            break

    print(f"\nScan complete. Saving {len(results)} items to {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✓ Successfully saved metadata to {output_file}")


if __name__ == "__main__":
    max_items_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    dump_file_metadata(max_items=max_items_arg)