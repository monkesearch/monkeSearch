import json
import sys
from pathlib import Path
import chromadb


CHROMA_PATH = str(Path("./").resolve() / "monke_index")
COLLECTION_NAME = "files"

def process_json_items(json_file_path):
    """Load JSON file and add items to a persistent ChromaDB collection."""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        items = json.load(f)

    # change-path to build persistent monkey index 
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    total_items = len(items)
    print(f"Processing {total_items} items...")

    batch_size = 100
    for i in range(0, total_items, batch_size):
        batch_items = items[i:i + batch_size]
        
        documents = []
        metadatas = []
        ids = []

        for idx, item in enumerate(batch_items):
            embedding_text = f"{item.get('Name', 'unknown')} located at {item.get('Path', 'unknown')} of type {item.get('Kind', 'unknown')}"
            
            metadata = {
                'path': item.get('Path', ''), 
                'name': item.get('Name', '')
            }
            if 'CreationDate' in item:
                metadata['creation_date'] = item['CreationDate']
            if 'ContentChangeDate' in item:
                metadata['modification_date'] = item['ContentChangeDate']
            
            documents.append(embedding_text)
            metadatas.append(metadata)
            ids.append(str(i + idx)) # unique id for each item 

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        progress = (i + len(batch_items)) / total_items * 100
        sys.stdout.write(f"\rProgress: {i + len(batch_items)}/{total_items} ({progress:.1f}%)")
        sys.stdout.flush()

    print(f"\n\n✓ Index built and saved to {CHROMA_PATH}")
    print(f"Total items in collection: {collection.count()}")
    

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python chroma_index_builder.py <json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    if not Path(json_file).exists():
        print(f"Error: File {json_file} not found")
        sys.exit(1)
    
    process_json_items(json_file)