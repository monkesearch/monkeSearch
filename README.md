# monkeSearch

![logo](src/fin.jpg)

---

Read the technical report and look at model performance benchmarks at: [monkesearch.github.io](https://monkesearch.github.io)

---

A prototype for searching your files with natural language — **fully offline, aimed to run on potato PCs**. No GPU required, no cloud API calls, nothing leaves your machine. Currently macOS-only (uses Spotlight) with cross-platform support in the works.

**Perfect for agentic use:** monkeSearch provides a direct LLM-to-filesystem bridge — natural language in, native Spotlight search out — without any file modifications, index maintenance, or cloud dependencies. It's a read-only, scoped-safe discovery layer purpose-built for AI agents and LLM orchestration pipelines that need to find files autonomously.
## How It Works

Any natural language file search query can be broken into 3 constituents:

1. **File type** — what kind of file (pdf, image, python script, etc.)
2. **Temporal context** — when (3 days ago, last week, 7 months ago)
3. **Misc keywords** — any remaining context (project name, topic, content)

monkeSearch uses a small local LLM (like LFM 1.2B) to parse queries and convert them into native macOS Spotlight search predicates.

## Quick Start

```bash
# Terminal 1: Start llama-server (keep running) (or point to any openai compatible endpoint)
llama-server --hf-repo LiquidAI/LFM2.5-1.2B-Instruct-GGUF --hf-file LFM2.5-1.2B-Instruct-Q8_0.gguf --port 8080

# Terminal 2: Search your files
cd app/
python parser.py "photos from yesterday"
```

### As a Module

```python
from parser import FileSearchParser

searcher = FileSearchParser()
results, parsed_data, misc = searcher.search("python files from last week")
for path in results:
    print(path)
```

## Requirements

- **macOS** (for Spotlight integration)
- **Python 3.8+**
- **llama-server** from [llama.cpp](https://github.com/ggml-org/llama.cpp) (install via `brew install llama.cpp`)
- A GGUF model (default: LFM 2.5 1.2B, ~700MB)

## Configuration

Set `MONKE_SERVER_URL` to point to your llama-server (default: `http://localhost:8080/v1`):

```bash
export MONKE_SERVER_URL="http://192.168.1.42:8080/v1"
python parser.py "photos from last week"
```

## Branches

| Branch | Approach | Platform |
|--------|----------|----------|
| **main / dev** | LLM → Spotlight NSPredicate (this branch) | macOS |
| **vectordb** | Vector DB (LEANN/ChromaDB) + semantic embeddings | macOS / Linux / Windows |

## Example Queries

| Query | What It Finds |
|-------|---------------|
| `"photos from yesterday"` | Image files modified in the last day |
| `"python scripts from 3 days ago"` | .py files from 3 days ago |
| `"pdf invoices from last month"` | PDFs with "invoices" modified in the last month |
| `"code files"` | Source code files of any language |
| `"videos from 2 years ago"` | Video files modified ~2 years ago |

## Limitations

- **Spotlight-indexed files only** (more like a feature, you can scope your search)
- **Metadata-only** — file content search planned
- **Small LLM tradeoff** — tiny models can misunderstand complex queries
- **Basic temporal** — simple time expressions only
- **macOS-only** — see the `vectordb` branch for cross-platform

## License

Apache-2.0
