# monkeSearch

![logo](src/fin.jpg)

---
Read the technical report at: [monkesearch.github.io](https://monkesearch.github.io)
---

A prototype system that brings semantic search capabilities to your file system, allowing you to search for files using natural language queries with temporal awareness like "documents from last week" or "photos from 3 days ago". Nothing leaves your PC, fully offline with local vector embeddings.

<!-- This is a bare bones prototype, just commenting the note out because it doesn't look nice. -->

<!-- #### watch an intro video i made on this project [here](https://youtu.be/J2O5yv1h6cs) -->

## Table of Contents
- [The Idea](#the-idea)
- [The Original Implementation (LLM → Spotlight)](#the-original-implementation-llm--spotlight)
- [Current Implementation (Vector DB-based)](#current-implementation-vector-db-based)
- [Example Queries](#example-queries)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage by Platform](#usage-by-platform)
- [Customization](#customization)
- [Project Structure](#project-structure)
- [Limitations](#limitations)
- [License](#license)

## The Idea

The core idea behind monkeSearch is simple: you should be able to search your own file system using natural language. Not exact filenames, not regex, not folder browsing — just describe what you're looking for and when, and the system finds it. Fully offline, nothing leaves your machine.

Any natural language file search query can be broken down into 3 constituents:
1. **File type** — what kind of file (pdf, image, code, etc.)
2. **Temporal context** — when (3 days ago, last week, etc.)
3. **Misc keywords** — any remaining context (project name, topic, etc.)

The original implementation used a local LLM to extract these constituents and convert them directly into macOS Spotlight query arguments. The current `main` branch achieves the same thing using vector databases instead. Both approaches are fully offline.

## The Original Implementation (LLM → Spotlight)

This was the first version of monkeSearch and the original vision behind the project. The idea: use a local LLM to convert a natural language query directly into arguments for macOS's built-in Spotlight search — no vector database, no embeddings index, no metadata dump. Just natural language in, structured OS-level query out, instant results back.

### How it works

1. **User writes a natural language query** like `"python scripts from 3 days ago"`

2. **Stop words are stripped** (`find`, `search`, `files`, `ago`, `back`, etc.) to clean up the query before it hits the LLM

3. **A local LLM (Qwen3-0.6B running via llama.cpp) parses the cleaned query** and extracts structured components:
   ```json
   {
     "file_types": ["py"],
     "time_unit": "days",
     "time_unit_value": "3",
     "is_specific": true,
     "source_text": {
       "file_types": "python scripts",
       "time_unit": "3 days ago"
     }
   }
   ```
   The LLM understands that "python scripts" means `.py`, "images" means `jpg,png`, "yesterday" means `days,1`, "last week" means `weeks,1`, etc. It uses constrained JSON output via llama.cpp's `response_format` to guarantee valid structured output.

4. **The extracted components are converted into `NSMetadataQuery` predicates** — the same API that powers Spotlight and `mdfind` under the hood:
   - File types → mapped to UTIs via `utitools`, then used as `kMDItemContentTypeTree` predicates. For broad categories (`is_specific: false`), the UTI hierarchy is climbed to match parent types (e.g., "images" matches all image formats, not just jpg)
   - Temporal data → converted to `kMDItemFSContentChangeDate` date predicates using `timedelta`
   - Remaining misc keywords → matched against `kMDItemTextContent` and `kMDItemFSName`
   - All predicates are combined with `NSCompoundPredicate`

5. **The compound query runs against Spotlight's existing index** — results come back instantly since macOS already maintains the index. No separate database to build or maintain.

### The two LLM-based branches

- [**LangExtract implementation**](https://github.com/monkesearch/monkeSearch/tree/langextract-llama-server) — uses [LangExtract](https://github.com/langextract/langextract) with a local Llama server (`llama_cpp.server` on `localhost:8000`) for structured extraction. Defines `file_type_indicator` and `temporal_indicator` extraction classes with few-shot examples.
- **llama.cpp direct implementation** (`legacy-main-llm-implementation` branch) — uses `llama_cpp.Llama` directly with constrained JSON output via Pydantic schema. More examples in the system prompt, tighter structured output.

Both use the same `parser.py` that converts the LLM's structured output into `NSMetadataQuery` predicates and runs the query against Spotlight.

> **Why this matters:** There's no index to build, no metadata to dump, no embeddings to generate. The LLM is the only "intelligence" layer — it converts human language to Spotlight's query language, and Spotlight does the actual searching using its pre-existing system index. This makes it safe by design (read-only, scoped through Spotlight's own access controls).

> **For Agentic Use:** These LLM-based implementations are particularly suitable for integration into larger AI pipelines and agentic systems. They provide a direct LLM-to-filesystem bridge through natural language without modifying any files, leveraging OS-level scoped safety through Spotlight. If you're building autonomous agents or LLM orchestration systems that need file discovery capabilities, these branches give you that without the overhead of maintaining a separate index.

## Current Implementation (Vector DB-based)

The current `main` branch achieves the same functionality using vector databases instead of a live LLM at query time. This was built to make monkeSearch cross-platform (the LLM → Spotlight approach is macOS-only) and to make search faster since it doesn't need an LLM running.

The tradeoff: you need to build and maintain an index, but search is sub-second and doesn't require a running LLM.

### How it works

1. **Metadata extraction** (platform-specific):
   - **macOS**: Spotlight metadata extraction via Foundation framework
   - **Linux/Windows**: `os.walk`-based file system traversal with configurable search folders

2. **Embedding generation**: File metadata is converted to a text representation and embedded using sentence transformers (default: `facebook/contriever`)

3. **Vector database indexing**:
   - **Mac/Linux → LEANN**: Graph-based vector index with 97% storage savings
   - **Windows → ChromaDB**: Persistent collection-based semantic search

4. **Temporal expression parsing**: Regex-based extraction of time expressions (`"3 days ago"`, `"last week"`, `"around 2 months ago"`) → ISO timestamp ranges. Stop words removed during parsing.

5. **Search & filter**: Clean query is embedded and matched via semantic similarity against the vector index. Results are filtered by date range if a temporal expression was found.

### Metadata fields indexed (all platforms)
- `Path`: Full file path
- `Name`: File name
- `Size`: File size in bytes
- `ContentType`: MIME type (e.g., `text/plain`, `image/jpeg`)
- `Kind`: File extension or type
- `CreationDate`: File creation timestamp (ISO format)
- `ContentChangeDate`: Last modification timestamp (ISO format)

> ### Developer note:
> I've been working on this project since long and this idea had many versions. The LLM → Spotlight approach was the original vision — letting a language model convert your natural language directly into OS-level search commands, no database needed. The vector DB approach on main right now is faster and cross-platform, but the LLM branches are still very relevant, especially for agentic pipelines where you want zero setup overhead. Rigorous evals and testing will be done before finalizing on a single approach for the main release. This is under active development and any new suggestions + PRs are welcome. My goal for this tool is to be open source, safe and cross platform.
>
> please star the repo too, if you've read it till here :P

## Example Queries

The system performs semantic search on file metadata with temporal filtering, understanding context without exact keyword matching:

| Natural Language Query | What It Finds |
|------------------------|---------------|
| `"photos from wedding"` | Image files with name/path semantically matching "wedding" |
| `"documents from 3 weeks ago"` | Any document-like files from 3 weeks ago |
| `"old music files"` | Audio files with temporal context |
| `"invoices from last month"` | Files semantically similar to "invoices" from last month |
| `"presentations about 2 months ago"` | Files matching "presentations" context from ~2 months ago |
| `"downloads from last week"` | Files in downloads folder from last week |

## Requirements

- **Python 3.12**
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

### 2. Install Dependencies

#### Mac/Linux (LEANN-based):
```bash
pip install leann
pip install numpy
```

#### Windows (ChromaDB-based):
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

### Temporal Search Examples (all platforms)
```bash
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
    print(f"Created: {result.metadata.get('CreationDate')}")
```

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

## Limitations

- **Indexed Files Only**: Only searches files that have been indexed (vector DB approach)
- **Metadata-based**: Searches file metadata, not file contents (can be added as a feature later)
- **Basic Temporal Parsing**: Currently supports simple time expressions
- **Windows Performance**: Currently uses os.walk which may be slow for large file counts (win32 API integration planned)
- **LLM branches are macOS-only**: The Spotlight-based approach requires macOS and a running local LLM

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