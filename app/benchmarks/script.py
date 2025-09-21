#!/usr/bin/env python3
"""
monkeSearch Benchmark Suite
Comprehensive benchmarking for Spotlight metadata extraction and LEANN vector database
Outputs JSON metrics only with timing, throughput, and file sizes
"""

import json
import time
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import re
import numpy as np
import io
import contextlib
import logging

# Import required modules
from Foundation import NSMetadataQuery, NSPredicate, NSRunLoop, NSDate
from leann import LeannBuilder, LeannSearcher

# Configuration
SEARCH_FOLDERS = [
    "Desktop",
    "Downloads", 
    "Documents",
    "Music",
    "Pictures",
    "Movies",
]

# Test queries for benchmarking
TEST_QUERIES = [
    "python scripts",
    "find my resume from 1 week ago",
    "image files",
    "latest version of my edited resume",
    "downloads folder photos",
    "movies folder files",
    "music files in downloads folder",
    "mp3 files or any music file",
    "configuration files",
    "project documentation"
]

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types"""
    def default(self, obj):
        if isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        if isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

class SpotlightDumper:
    """Handles Spotlight metadata extraction"""
    
    @staticmethod
    def convert_to_serializable(obj):
        """Convert NS objects to Python serializable types"""
        if obj is None:
            return None
        
        if hasattr(obj, 'timeIntervalSince1970'):
            return datetime.fromtimestamp(obj.timeIntervalSince1970()).isoformat()
        
        if hasattr(obj, 'count') and hasattr(obj, 'objectAtIndex_'):
            return [SpotlightDumper.convert_to_serializable(obj.objectAtIndex_(i)) 
                    for i in range(obj.count())]
        
        try:
            return str(obj)
        except:
            return repr(obj)
    
    @staticmethod
    def dump_spotlight_data(max_items=None, output_file="spotlight_dump.json"):
        """Dump Spotlight metadata for specified number of items"""
        home_dir = os.path.expanduser("~")
        search_paths = []
        
        print("Setting up search locations...")
        for folder in SEARCH_FOLDERS:
            if folder.startswith('/'):
                full_path = folder
            else:
                full_path = os.path.join(home_dir, folder)
            
            if os.path.exists(full_path):
                search_paths.append(full_path)
                print(f"  ✓ {full_path}")
            else:
                print(f"  ✗ {full_path} (not found)")
        
        if not search_paths:
            print("No valid search paths found!")
            return []
        
        print(f"\nStarting Spotlight query...")
        
        query = NSMetadataQuery.alloc().init()
        predicate = NSPredicate.predicateWithFormat_(
            "kMDItemContentTypeTree CONTAINS 'public.item'"
        )
        query.setPredicate_(predicate)
        query.setSearchScopes_(search_paths)
        
        query.startQuery()
        
        run_loop = NSRunLoop.currentRunLoop()
        print("Gathering results...")
        
        # Let it gather for up to 10 seconds
        for i in range(100):
            run_loop.runMode_beforeDate_(
                "NSDefaultRunLoopMode",
                NSDate.dateWithTimeIntervalSinceNow_(0.1)
            )
            if i % 20 == 0:
                current_count = query.resultCount()
                if current_count > 0:
                    print(f"  Found {current_count} items so far...")
        
        timeout = NSDate.dateWithTimeIntervalSinceNow_(2.0)
        while query.isGathering() and timeout.timeIntervalSinceNow() > 0:
            run_loop.runMode_beforeDate_(
                "NSDefaultRunLoopMode",
                NSDate.dateWithTimeIntervalSinceNow_(0.1)
            )
        
        query.stopQuery()
        
        total_results = query.resultCount()
        print(f"Found {total_results} total items in Spotlight")
        
        if total_results == 0:
            print("No results found")
            return []
        
        items_to_process = min(total_results, max_items) if max_items else total_results
        results = []
        
        attributes = [
            "kMDItemPath",
            "kMDItemFSName",
            "kMDItemFSSize",
            "kMDItemContentType",
            "kMDItemKind",
            "kMDItemFSCreationDate",
            "kMDItemFSContentChangeDate",
        ]
        
        print(f"Processing {items_to_process} items...")
        
        for i in range(items_to_process):
            try:
                item = query.resultAtIndex_(i)
                metadata = {}
                
                for attr in attributes:
                    try:
                        value = item.valueForAttribute_(attr)
                        if value is not None:
                            clean_key = attr.replace("kMDItem", "").replace("FS", "")
                            metadata[clean_key] = SpotlightDumper.convert_to_serializable(value)
                    except:
                        continue
                
                if metadata.get('Path'):
                    results.append(metadata)
                
                if (i + 1) % 1000 == 0:
                    print(f"  Processed {i + 1}/{items_to_process} items...")
            
            except Exception as e:
                print(f"Error processing item {i}: {e}")
                continue
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {len(results)} items to {output_file}")
        return results

class LeannIndexBuilder:
    """Handles LEANN index building"""
    
    @staticmethod
    def build_index(json_items, index_path):
        """Build LEANN index from JSON items"""
        builder = LeannBuilder(backend_name="hnsw", is_recompute=False)
        
        total_items = len(json_items)
        print(f"Building index with {total_items} items...")
        
        for idx, item in enumerate(json_items):
            # Create embedding text
            embedding_text = (f"{item.get('Name', 'unknown')} located at "
                            f"{item.get('Path', 'unknown')} and size "
                            f"{item.get('Size', 'unknown')} bytes with content type "
                            f"{item.get('ContentType', 'unknown')} and kind "
                            f"{item.get('Kind', 'unknown')}")
            
            # Prepare metadata
            metadata = {}
            if 'CreationDate' in item:
                metadata['creation_date'] = item['CreationDate']
            if 'ContentChangeDate' in item:
                metadata['modification_date'] = item['ContentChangeDate']
            
            builder.add_text(embedding_text, metadata=metadata)
            
            if (idx + 1) % 100 == 0:
                progress = (idx + 1) / total_items * 100
                sys.stdout.write(f"\r  Progress: {idx + 1}/{total_items} ({progress:.1f}%)")
                sys.stdout.flush()
        
        print("\n  Finalizing index...")
        builder.build_index(index_path)
        print(f"  ✓ Index saved to {index_path}")

class TimeParser:
    """Parse temporal expressions from queries"""
    
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
    """Run the complete benchmark suite"""
    benchmark_results = {
        'timestamp': datetime.now().isoformat(),
        'spotlight_dump': {},
        'index_building': {},
        'search_performance': {}
    }
    
    # Create output directory
    output_dir = Path("benchmark_results")
    output_dir.mkdir(exist_ok=True)
    
    try:
        print("=" * 80)
        print("LEANN SPOTLIGHT BENCHMARK SUITE")
        print(f"Started: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Step 1: Dump ALL files from Spotlight
        print("\n[PHASE 1] Dumping ALL files from Spotlight...")
        print("-" * 40)
        
        start_time = time.time()
        all_items = SpotlightDumper.dump_spotlight_data(
            max_items=None, 
            output_file=output_dir / "spotlight_all.json"
        )
        dump_time = time.time() - start_time
        
        total_files = len(all_items)
        benchmark_results['spotlight_dump']['total_files'] = total_files
        benchmark_results['spotlight_dump']['dump_time'] = dump_time
        benchmark_results['spotlight_dump']['files_per_second'] = total_files / dump_time if dump_time > 0 else 0
        
        print(f"\nDump completed: {total_files} files in {dump_time:.2f} seconds")
        print(f"Rate: {total_files/dump_time:.0f} files/second")
        
        # Determine test sizes based on available data
        test_sizes = []
        if total_files >= 1000:
            test_sizes.append(1000)
        if total_files >= 10000:
            test_sizes.append(10000)
        if total_files >= 50000:
            test_sizes.append(50000)
        test_sizes.append(total_files)  # Always test with all files
        
        # Remove duplicates and sort
        test_sizes = sorted(list(set(test_sizes)))
        
        print(f"\nTest sizes determined: {test_sizes}")
        benchmark_results['test_sizes'] = test_sizes
        
        # Step 2: Create subsets and build indexes
        print("\n[PHASE 2] Building LEANN indexes...")
        print("-" * 40)
        
        for size in test_sizes:
            print(f"\n## Building index for {size} files ##")
            
            # Create subset
            subset = all_items[:size]
            subset_file = output_dir / f"subset_{size}.json"
            with open(subset_file, 'w', encoding='utf-8') as f:
                json.dump(subset, f, indent=2, cls=NumpyEncoder)
            
            # Build index
            index_path = str(output_dir / f"index_{size}.leann")
            
            start_time = time.time()
            LeannIndexBuilder.build_index(subset, index_path)
            build_time = time.time() - start_time
            
            # Measure LEANN file sizes
            leann_files = {}
            index_base = Path(index_path)
            
            # Extract base name without .leann extension for .index file
            base_name = str(index_base).replace('.leann', '')
            
            # Check for common LEANN file patterns
            possible_files = [
                f"{base_name}.index",  # Main index file (e.g., index_1000.index)
                index_path,  # The path itself
                f"{index_path}.meta.json",
                f"{index_path}.passages.idx",
                f"{index_path}.passages.jsonl",
                f"{index_path}.graph",
                f"{index_path}.embeddings",
                # Check without extension too
                str(index_base.with_suffix('')),
                str(index_base.with_suffix('')) + ".meta.json",
                str(index_base.with_suffix('')) + ".passages.idx",
                str(index_base.with_suffix('')) + ".passages.jsonl",
                str(index_base.with_suffix('')) + ".index",
            ]
            
            total_size = 0
            for file_path in possible_files:
                if Path(file_path).exists():
                    file_size = Path(file_path).stat().st_size
                    relative_name = Path(file_path).name
                    leann_files[relative_name] = {
                        'size_bytes': file_size,
                        'size_mb': file_size / (1024 * 1024)
                    }
                    total_size += file_size
            
            # Also check if it's a directory
            if Path(index_path).is_dir():
                for file in Path(index_path).iterdir():
                    if file.is_file():
                        file_size = file.stat().st_size
                        leann_files[file.name] = {
                            'size_bytes': file_size,
                            'size_mb': file_size / (1024 * 1024)
                        }
                        total_size += file_size
            
            benchmark_results['index_building'][f'size_{size}'] = {
                'files': size,
                'build_time': build_time,
                'files_per_second': size / build_time if build_time > 0 else 0,
                'index_path': index_path,
                'leann_files': leann_files,
                'total_index_size_bytes': total_size,
                'total_index_size_mb': total_size / (1024 * 1024),
                'bytes_per_document': total_size / size if size > 0 else 0
            }
            
            print(f"Index built in {build_time:.2f} seconds ({size/build_time:.0f} files/sec)")
            print(f"Total index size: {total_size / (1024 * 1024):.2f} MB")
        
        # Step 3: Run search benchmarks
        print("\n[PHASE 3] Running search benchmarks...")
        print("-" * 40)
        
        # Set up terminal and logging capture for LEANN API logs
        search_log_buffer = []
        
        # Get LEANN loggers
        leann_logger = logging.getLogger('leann')
        leann_backend_logger = logging.getLogger('leann_backend_hnsw')
        leann_logger.setLevel(logging.INFO)
        leann_backend_logger.setLevel(logging.INFO)
        
        for size in test_sizes:
            print(f"\n## Testing searches on {size}-file index ##")
            index_path = str(output_dir / f"index_{size}.leann")
            
            # Initialize searcher ONCE and wait for RAM caching
            print("Initializing searcher and waiting for RAM cache...")
            init_start = time.time()
            searcher = LeannSearcher(index_path)
            init_time = time.time() - init_start
            time.sleep(1)  # Wait for RAM caching
            print(f"Searcher initialized in {init_time:.3f}s, cached in RAM")
            
            search_results = []
            
            for query_idx, query in enumerate(TEST_QUERIES):
                # Set up fresh log capture for this query
                log_stream = io.StringIO()
                log_handler = logging.StreamHandler(log_stream)
                log_handler.setLevel(logging.INFO)
                
                # Add handler to LEANN loggers
                leann_logger.addHandler(log_handler)
                leann_backend_logger.addHandler(log_handler)
                
                # Capture stdout/stderr as well
                stdout_capture = io.StringIO()
                
                with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stdout_capture):
                    # Parse time expressions from query
                    parser = TimeParser()
                    time_matches = parser.parse(query)
                    
                    clean_query = query
                    if time_matches:
                        for match in time_matches:
                            clean_query = clean_query.replace(match['full_match'], '').strip()
                    
                    # Run search
                    start_time = time.time()
                    results = searcher.search(
                        clean_query if clean_query else query,
                        top_k=10,
                        recompute_embeddings=False
                    )
                    search_time = time.time() - start_time
                    
                    # Apply time filter if needed
                    if time_matches:
                        time_range = time_matches[0]['range']
                        start_time_filter, end_time_filter = time_range
                        
                        filtered_results = []
                        for result in results:
                            metadata = result.metadata if hasattr(result, 'metadata') else {}
                            if metadata:
                                date_str = metadata.get('modification_date') or metadata.get('creation_date')
                                if date_str and start_time_filter <= date_str <= end_time_filter:
                                    filtered_results.append(result)
                        results = filtered_results
                
                # Remove handler after query
                leann_logger.removeHandler(log_handler)
                leann_backend_logger.removeHandler(log_handler)
                
                # Combine captured output
                captured_log = log_stream.getvalue() + stdout_capture.getvalue()
                if captured_log:
                    search_log_buffer.append(f"\n{'='*60}")
                    search_log_buffer.append(f"Index Size: {size} files | Query: '{query}'")
                    search_log_buffer.append(f"{'='*60}")
                    search_log_buffer.append(captured_log)
                
                # Convert numpy float32 to regular float
                top_score = float(results[0].score) if results else 0.0
                
                search_results.append({
                    'query': query,
                    'search_time': search_time,
                    'result_count': len(results),
                    'top_score': top_score
                })
                
                print(f"  Query: '{query[:50]}...' - {search_time:.4f}s ({len(results)} results)")
            
            # Add results to benchmark
            benchmark_results['search_performance'][f'size_{size}'] = {
                'files': size,
                'searcher_init_time': init_time,
                'queries_tested': len(TEST_QUERIES),
                'avg_search_time': sum(r['search_time'] for r in search_results) / len(search_results),
                'min_search_time': min(r['search_time'] for r in search_results),
                'max_search_time': max(r['search_time'] for r in search_results),
                'individual_results': search_results
            }
        
        # Save captured LEANN search logs
        search_log_file = output_dir / "leann_search_logs.txt"
        with open(search_log_file, 'w', encoding='utf-8') as f:
            f.write("LEANN Search API Logs\n")
            f.write(f"Captured at: {datetime.now().isoformat()}\n")
            f.write("="*80 + "\n")
            f.write("\n".join(search_log_buffer))
        print(f"✓ LEANN search logs saved to {search_log_file}")
        
        # Step 4: Save benchmark results
        print("\n[PHASE 4] Saving results...")
        print("-" * 40)
        
        results_file = output_dir / "benchmark_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(benchmark_results, f, indent=2, cls=NumpyEncoder)
        
        print(f"✓ Results saved to {results_file}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        
        print(f"\nTotal files found: {total_files:,}")
        print(f"Spotlight dump time: {benchmark_results['spotlight_dump']['dump_time']:.2f}s")
        
        print("\nIndex Building Performance:")
        for size_key, data in benchmark_results['index_building'].items():
            print(f"  {data['files']:,} files: {data['build_time']:.2f}s ({data['files_per_second']:.0f} files/sec)")
            print(f"    Index size: {data['total_index_size_mb']:.2f} MB ({data['bytes_per_document']:.0f} bytes/doc)")
        
        print("\nSearch Performance (average times):")
        for size_key, data in benchmark_results['search_performance'].items():
            print(f"  {data['files']:,} files:")
            print(f"    Searcher init: {data['searcher_init_time']:.4f}s")
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
    print("  - leann_search_logs.txt: LEANN API debug logs for all queries")
    print("  - spotlight_all.json: Full Spotlight metadata dump")
    print("  - subset_*.json: Test data subsets")
    print("  - index_*.leann: Built LEANN indexes")

if __name__ == "__main__":
    run_full_benchmark()