#!/usr/bin/env python3
"""
Windows ChromaDB Benchmark Suite
"""

import json
import time
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import re
import chromadb
import mimetypes
import shutil

# Configuration
HOME_DIR = os.path.expanduser("~")
SEARCH_FOLDERS = [
    os.path.join(HOME_DIR, "Desktop"),
    os.path.join(HOME_DIR, "Downloads"),
    os.path.join(HOME_DIR, "Documents"),
    os.path.join(HOME_DIR, "Music"),
    os.path.join(HOME_DIR, "Pictures"),
    os.path.join(HOME_DIR, "Videos"),
]

TEST_QUERIES = [
    "python scripts",
    "find my resume from 1 week ago",
    "image files",
    "latest version of my edited resume",
    "downloads folder photos",
    "videos folder files",
    "music files in downloads folder",
    "mp3 files or any music file",
    "configuration files",
    "project documentation"
]

class FileSystemDumper:
    @staticmethod
    def dump_file_metadata(max_items=None, output_file="filesystem_dump.json"):
        results = []
        print("Setting up search locations...")
        valid_folders = []
        
        for folder in SEARCH_FOLDERS:
            if os.path.exists(folder):
                valid_folders.append(folder)
                print(f"  ✓ {folder}")
            else:
                print(f"  ✗ {folder} (not found)")
        
        if not valid_folders:
            print("No valid search paths found!")
            return []
        
        print(f"\nStarting file system scan...")
        
        for folder in valid_folders:
            for root, _, files in os.walk(folder):
                for filename in files:
                    if max_items and len(results) >= max_items:
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
                            'CreationDate': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                            'ContentChangeDate': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                        }
                        results.append(item)
                        
                        if len(results) % 1000 == 0:
                            print(f"  Found {len(results)} files so far...")
                    except:
                        continue
                
                if max_items and len(results) >= max_items:
                    break
            
            if max_items and len(results) >= max_items:
                break
        
        print(f"Found {len(results)} total items")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {len(results)} items to {output_file}")
        return results

class ChromaIndexBuilder:
    @staticmethod
    def build_index(json_items, index_path):
        # Clean up existing index if present
        if os.path.exists(index_path):
            shutil.rmtree(index_path)
        
        client = chromadb.PersistentClient(path=index_path)
        collection = client.get_or_create_collection(name="files")
        
        total_items = len(json_items)
        print(f"Building index with {total_items} items...")
        
        batch_size = 100
        for i in range(0, total_items, batch_size):
            batch_items = json_items[i:i + batch_size]
            documents = []
            metadatas = []
            ids = []
            
            for idx, item in enumerate(batch_items):
                embedding_text = (f"{item.get('Name', 'unknown')} located at "
                                f"{item.get('Path', 'unknown')} and size "
                                f"{item.get('Size', 'unknown')} bytes with content type "
                                f"{item.get('ContentType', 'unknown')} and kind "
                                f"{item.get('Kind', 'unknown')}")
                
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
                ids.append(str(i + idx))
            
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            progress = (i + len(batch_items)) / total_items * 100
            sys.stdout.write(f"\r  Progress: {i + len(batch_items)}/{total_items} ({progress:.1f}%)")
            sys.stdout.flush()
        
        print(f"\n  ✓ Index saved to {index_path}")

class TimeParser:
    def __init__(self):
        self.pattern = r'(?:(around|about|roughly|approximately)\s+)?(\d+)\s+(hour|day|week|month|year)s?(?:\s+ago)?'
        self.regex = re.compile(self.pattern, re.IGNORECASE)
        self.stop_words = {
            'in', 'at', 'of', 'by', 'as', 'me',
            'the', 'a', 'an', 'and', 'any',
            'find', 'search', 'list',
            'ago', 'back', 'past', 'earlier',
        }
    
    def clean_text(self, text):
        words = text.split()
        cleaned = ' '.join(word for word in words if word.lower() not in self.stop_words)
        return cleaned
    
    def parse(self, text):
        cleaned_text = self.clean_text(text)
        matches = []
        
        for match in self.regex.finditer(cleaned_text):
            fuzzy = match.group(1)
            number = int(match.group(2))
            unit = match.group(3).lower()
            
            matches.append({
                'full_match': match.group(0),
                'fuzzy': bool(fuzzy),
                'number': number,
                'unit': unit,
                'range': self.calculate_range(number, unit, bool(fuzzy))
            })
        
        return matches
    
    def calculate_range(self, number, unit, is_fuzzy):
        units = {
            'hour': timedelta(hours=number),
            'day': timedelta(days=number),
            'week': timedelta(weeks=number),
            'month': timedelta(days=number * 30),
            'year': timedelta(days=number * 365)
        }
        
        delta = units[unit]
        now = datetime.now()
        target = now - delta
        
        if is_fuzzy:
            buffer = delta * 0.2
            start = (target - buffer).isoformat()
            end = (target + buffer).isoformat()
        else:
            start = target.isoformat()
            end = now.isoformat()
        
        return (start, end)

def run_full_benchmark():
    benchmark_results = {
        'timestamp': datetime.now().isoformat(),
        'filesystem_dump': {},
        'index_building': {},
        'search_performance': {}
    }
    
    output_dir = Path("benchmark_results")
    output_dir.mkdir(exist_ok=True)
    
    try:
        print("=" * 80)
        print("CHROMADB WINDOWS BENCHMARK SUITE")
        print(f"Started: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Phase 1: Dump ALL files
        print("\n[PHASE 1] Dumping ALL files from file system...")
        print("-" * 40)
        
        start_time = time.time()
        all_items = FileSystemDumper.dump_file_metadata(
            max_items=None, 
            output_file=output_dir / "filesystem_all.json"
        )
        dump_time = time.time() - start_time
        
        total_files = len(all_items)
        benchmark_results['filesystem_dump']['total_files'] = total_files
        benchmark_results['filesystem_dump']['dump_time'] = dump_time
        benchmark_results['filesystem_dump']['files_per_second'] = total_files / dump_time if dump_time > 0 else 0
        
        print(f"\nDump completed: {total_files} files in {dump_time:.2f} seconds")
        print(f"Rate: {total_files/dump_time:.0f} files/second")
        
        # Determine test sizes
        test_sizes = []
        if total_files >= 1000:
            test_sizes.append(1000)
        if total_files >= 10000:
            test_sizes.append(10000)
        if total_files >= 50000:
            test_sizes.append(50000)
        test_sizes.append(total_files)
        test_sizes = sorted(list(set(test_sizes)))
        
        print(f"\nTest sizes determined: {test_sizes}")
        benchmark_results['test_sizes'] = test_sizes
        
        # Phase 2: Build indexes
        print("\n[PHASE 2] Building ChromaDB indexes...")
        print("-" * 40)
        
        for size in test_sizes:
            print(f"\n## Building index for {size} files ##")
            
            subset = all_items[:size]
            subset_file = output_dir / f"subset_{size}.json"
            with open(subset_file, 'w', encoding='utf-8') as f:
                json.dump(subset, f, indent=2)
            
            index_path = str(output_dir / f"index_{size}_chroma")
            
            start_time = time.time()
            ChromaIndexBuilder.build_index(subset, index_path)
            build_time = time.time() - start_time
            
            # Measure ChromaDB file sizes
            chroma_files = {}
            total_size = 0
            
            if Path(index_path).exists():
                for root, _, files in os.walk(index_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        relative_path = os.path.relpath(file_path, index_path)
                        chroma_files[relative_path] = {
                            'size_bytes': file_size,
                            'size_mb': file_size / (1024 * 1024)
                        }
                        total_size += file_size
            
            benchmark_results['index_building'][f'size_{size}'] = {
                'files': size,
                'build_time': build_time,
                'files_per_second': size / build_time if build_time > 0 else 0,
                'index_path': index_path,
                'chroma_files': chroma_files,
                'total_index_size_bytes': total_size,
                'total_index_size_mb': total_size / (1024 * 1024),
                'bytes_per_document': total_size / size if size > 0 else 0
            }
            
            print(f"Index built in {build_time:.2f} seconds ({size/build_time:.0f} files/sec)")
            print(f"Total index size: {total_size / (1024 * 1024):.2f} MB")
        
        # Phase 3: Run search benchmarks
        print("\n[PHASE 3] Running search benchmarks...")
        print("-" * 40)
        
        for size in test_sizes:
            print(f"\n## Testing searches on {size}-file index ##")
            index_path = str(output_dir / f"index_{size}_chroma")
            
            print("Initializing ChromaDB client and waiting for cache...")
            init_start = time.time()
            client = chromadb.PersistentClient(path=index_path)
            collection = client.get_collection(name="files")
            init_time = time.time() - init_start
            time.sleep(1)
            print(f"Client initialized in {init_time:.3f}s, cached in RAM")
            
            search_results = []
            
            for query_idx, query in enumerate(TEST_QUERIES):
                parser = TimeParser()
                time_matches = parser.parse(query)
                
                clean_query = query
                if time_matches:
                    for match in time_matches:
                        clean_query = clean_query.replace(match['full_match'], '').strip()
                
                start_time = time.time()
                results_chroma = collection.query(
                    query_texts=[clean_query if clean_query else query],
                    n_results=10
                )
                search_time = time.time() - start_time
                
                results = []
                if results_chroma['ids'][0]:
                    for i in range(len(results_chroma['ids'][0])):
                        results.append({
                            'score': results_chroma['distances'][0][i],
                            'metadata': results_chroma['metadatas'][0][i]
                        })
                
                if time_matches:
                    time_range = time_matches[0]['range']
                    start_time_filter, end_time_filter = time_range
                    
                    filtered_results = []
                    for result in results:
                        metadata = result['metadata']
                        date_str = metadata.get('modification_date') or metadata.get('creation_date')
                        if date_str and start_time_filter <= date_str <= end_time_filter:
                            filtered_results.append(result)
                    results = filtered_results
                
                top_score = float(results[0]['score']) if results else 0.0
                
                search_results.append({
                    'query': query,
                    'search_time': search_time,
                    'result_count': len(results),
                    'top_score': top_score
                })
                
                print(f"  Query: '{query[:50]}...' - {search_time:.4f}s ({len(results)} results)")
            
            benchmark_results['search_performance'][f'size_{size}'] = {
                'files': size,
                'client_init_time': init_time,
                'queries_tested': len(TEST_QUERIES),
                'avg_search_time': sum(r['search_time'] for r in search_results) / len(search_results),
                'min_search_time': min(r['search_time'] for r in search_results),
                'max_search_time': max(r['search_time'] for r in search_results),
                'individual_results': search_results
            }
        
        # Phase 4: Save results
        print("\n[PHASE 4] Saving results...")
        print("-" * 40)
        
        results_file = output_dir / "benchmark_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(benchmark_results, f, indent=2)
        
        print(f"✓ Results saved to {results_file}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        
        print(f"\nTotal files found: {total_files:,}")
        print(f"File system dump time: {benchmark_results['filesystem_dump']['dump_time']:.2f}s")
        
        print("\nIndex Building Performance:")
        for size_key, data in benchmark_results['index_building'].items():
            print(f"  {data['files']:,} files: {data['build_time']:.2f}s ({data['files_per_second']:.0f} files/sec)")
            print(f"    Index size: {data['total_index_size_mb']:.2f} MB ({data['bytes_per_document']:.0f} bytes/doc)")
        
        print("\nSearch Performance (average times):")
        for size_key, data in benchmark_results['search_performance'].items():
            print(f"  {data['files']:,} files:")
            print(f"    Client init: {data['client_init_time']:.4f}s")
            print(f"    Avg search: {data['avg_search_time']:.4f}s (min: {data['min_search_time']:.4f}s, max: {data['max_search_time']:.4f}s)")
        
        print("\n" + "=" * 80)
        print(f"Benchmark completed: {datetime.now().isoformat()}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n✓ All results saved to {output_dir}/")
    print("\n📁 Output Files:")
    print("  - benchmark_results.json: Complete benchmark metrics")
    print("  - filesystem_all.json: Full file system metadata dump")
    print("  - subset_*.json: Test data subsets")
    print("  - index_*_chroma/: Built ChromaDB indexes")

if __name__ == "__main__":
    run_full_benchmark()