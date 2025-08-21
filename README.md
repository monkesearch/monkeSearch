# monkeSearch

A prototype system that brings natural language search capabilities to macOS Spotlight, allowing you to search for files using everyday language like "python scripts from last week" or "photos from yesterday". Nothing leaves your pc, offline inference and can even run on potato PCs. You don't need a massive GPU rig to run the small model backing the intelligence.


> ⚠️ **Prototype**: This is an initial proof-of-concept implementation. Expect rough edges and limited functionality.
> Currently aimed at macOS but the logic is independent for cross platform adaptations. (In the works!)

> ### Developer note:
> I've been working on this project since long and this idea had many versions. Currently the system supports a few file types because I am "rebuilding" the macOS filetype hierarchy > to connect filetypes directly with their UTI hierarchy. Future plans include finetuning Gemma 3 270M and getting community insights for a more efficient way of doing this. The
> current turnaround time for this tool to recieve a query and give out files is around 1 second and doesn't exceed it, the largest bottleneck is model inference. This is under active
> development and any new suggestions + PRs are welcome. My goal for this tool is to be open source, safe and cross platform. So developers experienced in Windows/Linux Indexing are
> very welcome to collaborate and develop their versions together.
>
> 
> please star the repo too, if you've read it till here :P

## Overview

![usage gif](inference.gif)

> shows zero results because i don't have any videos related to "wedding"
This system combines:
- **AI-powered query parsing** using a local LLM (Qwen 0.6B) to understand natural language
- **Native macOS Spotlight integration** for fast, efficient file searching. (cross platform support is very welcome for development!)
- **Intelligent file type recognition** that understands context (e.g., "resume" → PDF/DOCX files)
- **Temporal expression parsing** for time-based searches. (3 weeks ago, 10 months ago, etc.)

## Example Queries
#### You can convert any natural language query to 3 major constituents: File type, temporal data (time related), and miscellaneous (file name, path etc.) I used this idea as base to build the whole project, and yes it is that simple.



| Natural Language Query | What It Finds |
|------------------------|---------------|
| `"photos from yesterday"` | Image files modified in the last day |
| `"python scripts from three days ago"` | .py and .ipynb files from 3 days ago |
| `"old music files"` | Audio files with "old" in name or content |
| `"pdf invoices from 2023"` | PDF files from 2023 with "invoices" keyword |
| `"resume from last week"` | Recent DOC/DOCX/PDF files with "resume" |
| `"code files"` | Source code files of any language |


## Features

- **Natural Language Queries**: Search with phrases like "old music files" or "python scripts three days ago"
- **Smart File Type Detection**: Automatically maps concepts to file extensions (e.g., "photos" → jpg, png, heic) (limited support due to manual hierarchy building.)
- **Temporal Understanding**: Recognizes time expressions like "yesterday", "last week", "3 days ago"
- **Full Spotlight Integration**: Leverages macOS's indexed metadata for instant results
- **Local Processing**: Everything runs on your machine - nothing leaves your pc.
- **Can run on Potato PCs** : You don't need a hefty GPU rig to do simple semantic search.

## Requirements

- **macOS** (required for Spotlight integration)
- **Python 3.8+**
- **Ollama running qwen0.6b** (local LLM server)

> Currently planning to fine tune Gemma 3 270M for a smaller and faster model for this use case. Also aiming at using llama.cpp 

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

### 3. Install and Setup Ollama

**Using Homebrew:**
```bash
# Install Ollama
brew install ollama

# Start the Ollama server (keep this running in a separate terminal)
ollama serve

# In another terminal, pull the Qwen model
ollama pull qwen3:0.6b
```

**Alternative installation** (if not using Homebrew):
- Download Ollama from [ollama.com](https://ollama.com)
- Follow the installation instructions for macOS

### 4. Verify Setup
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test the parser
python parser.py "python files from yesterday"
```

## Usage

### Command Line
```bash
# Basic search
python parser.py "photos from last week"

# More examples
python parser.py "python scripts modified yesterday"
python parser.py "pdf invoices from 2023"
python parser.py "music files"
python parser.py "old presentations"
```

### As a Module
```python
from parser import FileSearchParser

# Initialize the parser
searcher = FileSearchParser()

# Perform a search
results, parsed_data = searcher.search("python files from last week")

# results contains file paths
for path in results:
    print(path)
```


## How It Works

1. **Query Parsing**: Your natural language query is analyzed by Qwen running locally to extract:
   - File type indicators (e.g., "photos" → jpg, png, heic)
   - Temporal expressions (e.g., "last week" → 7 days)
   - Additional keywords

2. **Predicate Building**: Extracted information is converted to Spotlight search predicates:
   - File types map to Uniform Type Identifiers (UTIs)
   - Time expressions become date comparisons
   - Keywords search both filenames and content

3. **Spotlight Search**: macOS's native search engine queries the indexed metadata:
   - Searches complete in milliseconds
   - No need to scan directories
   - Respects system indexing preferences

## Supported File Types

The system recognizes these categories:
- **Images**: jpg, png, gif, heic, svg, etc.
- **Videos**: mp4, mov, avi, mkv, etc.
- **Audio**: mp3, wav, flac, m4a, etc.
- **Code**: py, js, java, cpp, go, rs, etc.
- **Documents**: pdf, doc, docx, txt, md
- **Spreadsheets**: xls, xlsx, csv
- **Presentations**: ppt, pptx
- **Archives**: zip, tar, gz, rar
  > More can be added with ongoing community support.

## Limitations

- **Indexed Files Only**: Only searches files indexed by Spotlight
- **Local Model Limitations**: The small AI model may misunderstand very complex queries
- **Basic Temporal Parsing**: Currently supports simple time expressions (More features to be added soon!)

## Troubleshooting

### "Connection refused" error
- Ensure Ollama is running: `ollama serve`
- Check if it's accessible: `curl http://localhost:11434`

### No results returned
- Verify Spotlight is enabled: System Settings → Siri & Spotlight → Search Results
- Check if the location is indexed: Spotlight preferences
- Try a simpler query first

### Model not found
- Pull the model: `ollama pull qwen3:0.6b`
- List available models: `ollama list`

### PyObjC import errors
- Ensure you're using Python 3, not Python 2
- Try: `pip install --upgrade pyobjc`
- On Apple Silicon Macs, you might need: `pip install --no-cache-dir pyobjc`

## Future Improvements

This is an early prototype. Potential enhancements include:
- [ ] GUI interface
- [ ] Adding temporal expressions for more semantic flexibility (in the works!)
- [ ] Custom file type definitions
- [ ] More adaptable and easier usage (for example, terminal usage can be like: `where resume pdf 3 weeks ago`)
- [ ] Source identification, MacOS also contains data about the origin of the file (example: files from google drive)
- [ ] Performance optimizations
- [ ] More features!

## Architecture

```
User Query (Natural Language)
        ↓
QueryExtractor (LangExtract + Qwen 0.6b)
        ↓
Structured Data {file_types, temporal, keywords}
        ↓
FileSearchParser (PyObjC + Foundation)
        ↓
NSPredicate Objects
        ↓
NSMetadataQuery (Spotlight)
        ↓
File Paths Results
```

## Contributing

This is an experimental prototype. Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests
- Share interesting use cases

## License

Apache-2.0 license

## Acknowledgments

- Built with [LangExtract](https://github.com/google/langextract) for structured extraction
- Powered by [Ollama](https://ollama.com) for local LLM inference. 
- Uses Apple's Spotlight and Foundation frameworks.

---

**Note**: This is an experimental prototype created to explore natural language file searching on macOS. It's not production-ready and should be used for experimentation and learning purposes. 
