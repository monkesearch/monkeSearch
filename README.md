# monkeSearch

![logo](src/fin.jpg)

---

A prototype system that brings semantic search capabilities to your file system using a very low profile vector database (size in a few KBs / MBs only), allowing you to search for files using natural language queries with temporal awareness like "documents from last week" or "photos from 3 days ago". Nothing leaves your PC, fully offline with local vector embeddings.

> ⚠️ **Prototype**: This is an initial proof-of-concept implementation. Expect rough edges and limited functionality.
> Currently aimed at macOS but the logic is independent for cross platform adaptations. (In the works!) visit [discussions](https://github.com/monkesearch/monkeSearch/discussions/8)

> ### Developer note:
> I've been working on this project since long and this idea had many versions. The current implementation uses LEANN, a vector database that saves 97% storage compared to traditional solutions. The system builds a semantic index of your files' metadata and enables temporal-aware search through regex parsing.
> The current turnaround time for this tool to receive a query and return files is sub-second thanks to LEANN's efficient code. This is under active
> development and any new suggestions + PRs are welcome. My goal for this tool is to be open source, safe and cross platform. So developers experienced in Windows/Linux Indexing are
> very welcome to collaborate and develop their versions together.
>
> 
> please star the repo too, if you've read it till here :P

## Overview


This system combines:
- **LEANN vector database** for semantic search with 97% storage savings
- **Native macOS Spotlight integration** for fast, efficient file metadata extraction
- **Temporal expression parsing** for time-based searches (3 weeks ago, 10 months ago, etc.)
- **Semantic similarity matching** using embeddings instead of exact keyword matching

## Implementation versions
There are multiple implementations in different branches written in achieving the same task, for testing purposes. Rigorous evals and testing will be done before finalizing on a single one for the main release.

- [Initial implementation using LangExtract](https://github.com/monkesearch/monkeSearch/tree/feature/llama-cpp-support) (Legacy - LLM based)
- **Current main branch**: LEANN-based semantic search with temporal awareness via regex parsing
- llama.cpp rewrite (legacy-main-llm-implementation) - deprecated
- llama.cpp [feature branch](https://github.com/monkesearch/monkeSearch/tree/feature/chunking) - deprecated but can be considered for testing.

## Example Queries
#### The system performs semantic search on file metadata with temporal filtering, understanding context without exact keyword matching

| Natural Language Query | What It Finds |
|------------------------|---------------|
| `"photos from wedding"` | Image files with name/ path including the keyword wedding (semantic match on "wedding") |
| `"documents from 3 weeks ago"` | Any document-like files from 3 weeks ago |
| `"old music files"` | Audio files with temporal context |
| `"invoices from last month"` | Files semantically similar to "invoices" from last month |
| `"presentations about 2 months ago"` | Files matching "presentations" context from ~2 months ago |
| `"downloads from last week"` | Files in downloads folder from last week |

## Requirements

- **macOS** (required for Spotlight integration, cross platform support in works.)
- **Python 3.8+**

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/monkesearch/monkesearch
cd monkeSearch
```

### 2. Install dependencies using the requirements file:
```bash
pip install -r requirements.txt
```


### 3. Build the Index
```bash
# First, dump Spotlight metadata
python spotlight_dump.py 1000  # Dump 1000 files

# Build LEANN index
python build_index.py spotlight_dump.json

# The default recompute settings for LEANN are set to false, so the index size might be comparatively large.
python build_index.py spotlight_dump.json
```

### 4. Verify Setup
```bash
# Test search
python leann-plus-temporal-search.py "pdf documents 2 weeks ago"
```

## Usage

### Command Line
```bash
cd app/

# Basic semantic search
python leann-plus-temporal-search.py "photos"

# Temporal search
python leann-plus-temporal-search.py "documents from 3 days ago"
python leann-plus-temporal-search.py "downloads from last week"
python leann-plus-temporal-search.py "files from around 2 months ago"

# Specify number of results (top-k)
python leann-plus-temporal-search.py "presentations" 10
```

### As a Module
```python
from search_index import search_files

# Perform a semantic search with temporal filtering
results = search_files("documents from last week", top_k=15)

# Results are SearchResult objects with score, text, and metadata
for result in results:
    print(f"Score: {result.score}")
    print(f"File: {result.text}")
    print(f"Created: {result.metadata.get('creation_date')}")
```

## How It Works

1. **Metadata Extraction**: Spotlight metadata is extracted for files (name, path, type, dates)
2. **Embedding Generation**: File metadata is converted to embeddings using sentence transformers
3. **LEANN Indexing**: Embeddings are stored in a graph-based index with 97% storage savings (not enabled by default for now)
4. **Query Processing**: 
   - Temporal expressions are extracted via regex ("3 days ago" → ISO timestamp range)
   - Stop words are removed from temporal parsing
   - Clean query is embedded for semantic search
5. **Search & Filter**: LEANN performs semantic search, then results are filtered by date if temporal expression found

## Limitations

- **Indexed Files Only**: Only searches files indexed by Spotlight
- **Metadata-based**: Searches file metadata, not file contents (can be added as a feature later)
- **Basic Temporal Parsing**: Currently supports simple time expressions

## License

Apache-2.0 license

## Star History

<a href="https://www.star-history.com/#monkesearch/monkeSearch&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=monkesearch/monkeSearch&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=monkesearch/monkeSearch&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=monkesearch/monkeSearch&type=Date" />
 </picture>
</a>

## Acknowledgments
- [LEANN](https://github.com/yichuan-w/LEANN) team for collaborating and communication, and the tool of course.
- Uses Apple's Spotlight and Foundation frameworks

---

**Note**: This is an experimental prototype created to explore semantic file searching on macOS. It's not production-ready and should be used for experimentation and learning purposes.