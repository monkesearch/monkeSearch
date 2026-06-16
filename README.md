# monkeSearch — Vector DB Implementation

This is the **vectordb** branch — one of two parallel approaches to natural language file search.  
It pre-indexes file metadata into a vector database and searches via semantic similarity.  
For the **LLM → Spotlight** approach (no index needed), see the **main / dev** branches.

![logo](src/fin.jpg)

---

Read the technical report at: [monkesearch.github.io](https://monkesearch.github.io)

---

A prototype for searching your files with natural language using **vector embeddings** — **fully offline, aimed to run on potato PCs**. No GPU required, no cloud API calls, nothing leaves your machine. Cross-platform (macOS / Linux / Windows).

## How It Works

```
File metadata → text sentence → embedding → vector index
                                          ↓
User query → temporal parse → embed query → similarity search → temporal filter → results
```

**Phase 1 — Indexing (one-time)**
1. **Metadata dump** — Extracts file metadata (path, name, size, type, dates) using platform APIs
2. **Embedding** — Each metadata record is embedded via `facebook/contriever` (sentence-transformers)
3. **Vector index** — Embeddings stored in LEANN (macOS/Linux) or ChromaDB (Windows)

**Phase 2 — Search**
1. **Temporal parsing** — Regex extracts time expressions ("3 days ago", "last week") into ISO date ranges
2. **Semantic search** — Cleaned query is embedded and searched against the vector index
3. **Temporal post-filter** — Results filtered by stored creation/modification dates

## Quick Start

### macOS / Linux (LEANN)

```bash
cd app/
python spotlight_index_dump.py 1000        # macOS, or:
python linux_index_dump.py 1000            # Linux
python leann_index_builder.py spotlight_dump.json
python leann-plus-temporal-search.py "pdfs from last week"
```

### Windows (ChromaDB)

```bash
cd app/windows/
python windows_index_dump.py 1000
python chroma_index_builder.py os_walk_dump.json
python chroma-plus-temporal-search.py "presentations from last month"
```

### As a Module

```python
from leann_search import search_files
results = search_files("documents from last week", top_k=15)
for r in results:
    print(f"Score: {r.score} | File: {r.text}")
```

## Example Queries

| Query | What It Finds |
|-------|---------------|
| `"photos from wedding"` | Images with path/name matching "wedding" semantically |
| `"documents from 3 weeks ago"` | Document-like files modified ~3 weeks ago |
| `"invoices from last month"` | Files semantically similar to "invoices" from ~last month |
| `"presentations"` | Files matching "presentations" context |
| `"old music files"` | Audio files with temporal context |

## The Two Approaches

monkeSearch explores two fundamentally different approaches to the same problem. This branch (vectordb) uses the **pre-indexed vector database** approach:

| Approach | This Branch | main / dev Branch |
|----------|-------------|-------------------|
| **Method** | Pre-index metadata → embed → semantic similarity search | LLM parses query → converts to native Spotlight predicates |
| **Index** | Requires one-time build (LEANN / ChromaDB) | No index — uses macOS Spotlight's existing system index |
| **LLM needed** | No (regex temporal parsing + embeddings) | Yes (local GGUF model via llama-server) |
| **Speed** | ~25ms search (sub-ms graph traversal + ~15ms embedding) | ~1s (LLM inference is the bottleneck) |
| **Platform** | macOS / Linux / Windows | macOS only |
| **Setup** | Build index first, then search | Start llama-server, search immediately |

## Requirements

- **Python 3.12**
- **macOS**: Spotlight enabled
- **Linux / Windows**: Standard filesystem access

## Performance

| Index Size | Build Time | Search Time | Index Size |
|-----------|-----------|-------------|------------|
| 1,000 files | ~11s | ~25ms | ~6.7 MB |
| 10,000 files | ~89s | ~20ms | ~67 MB |

Search time includes embedding generation (~15–60ms). HNSW graph traversal itself is ~0.2ms.

## Limitations

- **Indexed files only** — searches the metadata dump, not live filesystem
- **Metadata-based** — file content search planned
- **Basic temporal** — simple time expressions only
- **Windows performance** — os.walk is slow for large indexes (pywin32 planned)
- **One-time index** — adding files requires re-indexing

## License

Apache-2.0
