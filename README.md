# monkeSearch

![logo](src/fin.jpg)

---
Read the technical report at: [monkesearch.github.io](https://monkesearch.github.io)
---

A prototype system that brings semantic search capabilities to your file system using lightweight vector databases, allowing you to search for files using natural language queries with temporal awareness like "documents from last week" or "photos from 3 days ago". Nothing leaves your PC, fully offline with local vector embeddings.

> ⚠️ **Prototype**: This is an initial proof-of-concept implementation. Expect rough edges and limited functionality.
> **Multi-platform support**: Now available for macOS, Linux, and Windows!

#### watch an intro video i made on this project [here](https://youtu.be/J2O5yv1h6cs)

> ### Developer note:
> I've been working on this project since long and this idea had many versions. The current implementation uses platform-specific approaches:
> - **Mac**: Spotlight metadata extraction for fast, comprehensive indexing
> - **Linux/Windows**: os.walk-based file traversal with configurable search folders
> - **Mac/Linux**: LEANN vector database with 97% storage savings
> - **Windows**: ChromaDB for robust semantic search
> 
> The system builds a semantic index of your files' metadata and enables temporal-aware search through regex parsing. The current turnaround time is sub-second thanks to efficient indexing. This is under active development and any new suggestions + PRs are welcome. My goal for this tool is to be open source, safe and cross platform.
>
> please star the repo too, if you've read it till here :P

## Overview
Read the technical details at [technical.md](src/technical.md)

This system combines:
- **Platform-optimized metadata extraction**
  - macOS: Native Spotlight integration
  - Linux/Windows: os.walk file system traversal
- **Efficient vector databases** for semantic search
  - LEANN (Mac/Linux) - 97% storage savings
  - ChromaDB (Windows) - robust semantic search
- **Temporal expression parsing** for time-based searches (3 weeks ago, 10 months ago, etc.)
- **Semantic similarity matching** using embeddings instead of exact keyword matching

## Implementation versions
There are multiple implementations in different branches written in achieving the same task, for testing purposes. Rigorous evals and testing will be done before finalizing on a single one for the main release.

> **For Agentic Use:** The legacy LLM-based implementations (branches below) are particularly suitable for integration into larger AI pipelines and agentic systems. These versions allow direct filesystem access through natural language without modifying any files, leveraging OS-level scoped safety through Spotlight. If you're building autonomous agents or LLM orchestration systems that need file discovery capabilities, these branches provide a direct LLM-to-filesystem bridge without the overhead of maintaining a separate index.

- [Initial implementation using LangExtract](https://github.com/monkesearch/monkeSearch/tree/feature/llama-cpp-support) (Legacy - LLM based, ideal for agentic pipelines)
- **Current main branch**: LEANN-based (except windows: windows uses ChromaDB) semantic search with temporal awareness via regex parsing 
- llama.cpp rewrite (legacy-main-llm-implementation) - deprecated but useful for direct LLM integration
- llama.cpp [feature branch](https://github.com/monkesearch/monkeSearch/tree/feature/chunking) - another variation of the llama.cpp rewrite, with a detailed response model.

## Example Queries
#### The system performs semantic search on file metadata with temporal filtering, understanding context without exact keyword matching

| Natural Language Query | What It Finds |
|------------------------|---------------|
| `"photos from wedding"` | Image files with name/path including the keyword wedding (semantic match on "wedding") |
| `"documents from 3 weeks ago"` | Any document-like files from 3 weeks ago |
| `"old music files"` | Audio files with temporal context |
| `"invoices from last month"` | Files semantically similar to "invoices" from last month |
| `"presentations about 2 months ago"` | Files matching "presentations" context from ~2 months ago |
| `"downloads from last week"` | Files in downloads folder from last week |

## Requirements

- **Python 3.8+**
- **Platform-specific notes:**
  - **macOS**: Spotlight indexing enabled (uses Foundation framework)
  - **Linux**: Standard file system access via os.walk
  - **Windows**: Standard file system access via os.walk (future: pywin32 for performance)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/monkesearch/monkesearch
cd monkeSearch
```

### 2. Install dependencies

#### For Mac/Linux (LEANN-based):
```bash
pip install leann
pip install numpy
```

#### For Windows (ChromaDB-based):
```bash
pip install sentence-transformers
pip install chromadb
pip install numpy
```

## Usage by Platform

### macOS

```bash
cd app/

# 1. Dump Spotlight metadata
python spotlight_index_dump.py 1000  # Dump 1000 files

# 2. Build LEANN index
python leann_index_builder.py spotlight_dump.json

# 3. Search
python leann-plus-temporal-search.py "pdf documents 2 weeks ago"
python leann-plus-temporal-search.py "presentations" 10  # Top 10 results
```

### Linux

```bash
cd app/

# 1. Dump file metadata using os.walk
python linux_index_dump.py 1000  # Dump 1000 files
# Or dump all files (no limit)
python linux_index_dump.py

# 2. Build LEANN index
python leann_index_builder.py linux_dump.json

# 3. Search
python leann-plus-temporal-search.py "documents from last week"
python leann-plus-temporal-search.py "photos" 15  # Top 15 results
```

**Note**: Linux indexer scans Desktop, Downloads, Documents, Music, Pictures, and Videos folders by default. Edit `SEARCH_FOLDERS` in `linux_index_dump.py` to customize.

### Windows

```bash
cd app/windows/

# 1. Dump file metadata using os.walk
python windows_index_dump.py 1000  # Index 1000 files

# 2. Build ChromaDB index
python chroma_index_builder.py os_walk_dump.json

# 3. Search
python chroma-plus-temporal-search.py "presentations from last month"
python chroma-plus-temporal-search.py "downloads from 3 days ago" 20  # Top 20 results
```

**Note**: Windows indexer scans Desktop, Downloads, Documents, and Pictures folders by default. Currently uses `os.walk` which may be slow for large indexes (pywin32 API support planned for performance improvement).

## Command Line Examples

### Basic semantic search (all platforms)
```bash
# Mac/Linux from app/
python leann-plus-temporal-search.py "photos"

# Windows from app/windows/
python chroma-plus-temporal-search.py "photos"
```

### Temporal search examples
```bash
# Find documents from specific time periods
"documents from 3 days ago"
"downloads from last week"
"files from around 2 months ago"
"presentations from yesterday"
"invoices from last month"
```

### As a Module
```python
# Import based on your platform
from leann_search import search_files  # Mac/Linux
# OR
from chroma_search import search_files  # Windows

# Perform a semantic search with temporal filtering
results = search_files("documents from last week", top_k=15)

# Results are SearchResult objects with score, text, and metadata
for result in results:
    print(f"Score: {result.score}")
    print(f"File: {result.text}")
    print(f"Created: {result.metadata.get('CreationDate')}")  # Note: field names match platform
```

## How It Works

1. **Metadata Extraction**: 
   - **Mac**: Spotlight metadata extraction via Foundation framework
   - **Linux/Windows**: os.walk-based file system traversal
     - Scans common folders: Desktop, Downloads, Documents, Pictures, etc.
     - Extracts: file path, name, size, MIME type, creation/modification dates
     - Note: Windows implementation currently uses os.walk (pywin32 API support planned for faster indexing)
2. **Embedding Generation**: File metadata is converted to embeddings using sentence transformers
3. **Vector Database Indexing**: 
   - Mac/Linux: LEANN graph-based index with storage optimization
   - Windows: ChromaDB persistent collection
4. **Query Processing**: 
   - Temporal expressions are extracted via regex ("3 days ago" → ISO timestamp range)
   - Stop words are removed from temporal parsing
   - Clean query is embedded for semantic search
5. **Search & Filter**: Vector database performs semantic search, then results are filtered by date if temporal expression found

### Metadata Fields Indexed
All platforms extract similar metadata for each file:
- `Path`: Full file path
- `Name`: File name
- `Size`: File size in bytes
- `ContentType`: MIME type (e.g., "text/plain", "image/jpeg")
- `Kind`: File extension or type
- `CreationDate`: File creation timestamp (ISO format)
- `ContentChangeDate`: Last modification timestamp (ISO format)

## Project Structure
```
app/
├── benchmarks/              # Performance testing scripts
├── windows/                 # Windows-specific implementation
│   ├── chroma_index_builder.py
│   ├── chroma-plus-temporal-search.py
│   └── windows_index_dump.py
├── spotlight_index_dump.py  # macOS metadata extraction
├── linux_index_dump.py      # Linux metadata extraction
├── leann_index_builder.py   # LEANN index builder (Mac/Linux)
└── leann-plus-temporal-search.py  # LEANN search (Mac/Linux)
```

Note that the LEANN project has windows implementation in the works, so it will be added here when it's complete.

## Customization

### Configuring Search Folders

Both Linux and Windows implementations allow you to customize which folders are indexed:

**Linux** (`app/linux_index_dump.py`):
```python
SEARCH_FOLDERS = [
    "Desktop",
    "Downloads", 
    "Documents",
    "Music",
    "Pictures",
    "Videos",
    # Add custom paths:
    # "Code/Projects",
    # "/usr/share",  # Absolute paths also supported
]
```

**Windows** (`app/windows/windows_index_dump.py`):
```python
SEARCH_FOLDERS = [
    os.path.join(HOME_DIR, "Desktop"),
    os.path.join(HOME_DIR, "Downloads"),
    os.path.join(HOME_DIR, "Documents"),
    os.path.join(HOME_DIR, "Pictures"),
    # Add more folders as needed
]
```

## Limitations

- **Indexed Files Only**: Only searches files that have been indexed
- **Metadata-based**: Searches file metadata, not file contents (can be added as a feature later)
- **Basic Temporal Parsing**: Currently supports simple time expressions
- **Windows Performance**: Currently uses os.walk which may be slow for large file counts (win32 API integration planned)

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
- [LEANN](https://github.com/yichuan-w/LEANN) team for collaborating and communication, and the tool of course
- [ChromaDB](https://github.com/chroma-core/chroma) for Windows implementation
- Apple's Spotlight and Foundation frameworks for macOS support

---

**Note**: This is an experimental prototype created to explore semantic file searching across multiple platforms. It's not production-ready and should be used for experimentation and learning purposes.