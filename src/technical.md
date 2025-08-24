# Technical Documentation

Deep dive into MonkeSearch's architecture, implementation details, and the roadmap for making file search smarter.

## How It Works

### 1. Query Parsing
Your natural language query is analyzed by Qwen (0.6b) running locally via Ollama to extract:
- **File type indicators**: "photos" → jpg, jpeg, png, heic
- **Temporal expressions**: "last week" → 7 days, "3 weeks ago" → 21 days
- **Residual keywords**: Remaining meaningful terms after extraction

### 2. Intelligent Filtering
Before LLM processing, common stop words are removed:
```python
STOP_WORDS = {'in', 'at', 'of', 'by', 'as', 'me', 'the', 'a', 'an', 
              'and', 'any', 'find', 'search', 'list', 'file', 'files',
              'ago', 'back', 'past', 'earlier', 'folder'}
```

### 3. Predicate Building
Extracted information is converted to macOS Spotlight search predicates:
- File types map to Uniform Type Identifiers (UTIs) using `utitools`
- Time expressions become `kMDItemFSContentChangeDate` comparisons
- Keywords search both `kMDItemTextContent` and `kMDItemFSName`

### 4. Spotlight Search
macOS's native search engine queries the indexed metadata:
- Searches complete in milliseconds
- No directory scanning required
- Respects system indexing preferences
- Results limited to top 20 by default



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

Based on the roadmap, these features are planned ( contributions are very welcome - I cannot do this all by myself!):

### Core Features
- [ ] GUI interface
- [ ] Performance optimizations
- [ ] Configurable result limits

### Advanced Temporal Processing (major upgrade)
- [ ] Temporal approximators ("around 3 weeks", "about 2 months")
- [ ] Temporal operators ("before last month", "within 2 days", "since yesterday")
- [ ] Specific time values ("within 3 hours", "4 months ago")
- [ ] Date ranges ("between 2 and 3 weeks ago")
- [ ] Named time references ("this morning", "tonight", "today", "now")

### Enhanced Query Understanding (major upgrade)
- [ ] Fuzzy matching for keywords
- [ ] Semantic tag extraction and indexing
- [ ] Prioritizing a specific filetype if it's included in the prompt. (If someone searches for python files, show only python files instead of stepping up in the UTI hierarchy and showing all the `public.shell-script` files.)

### Additional Metadata
- [ ] Source identification (files from Google Drive, downloads, etc.)
- [ ] Author/creator metadata search
- [ ] Application-specific metadata (which app created the file)
- [ ] Content-based deep search

### Model Improvements
- [ ] Model fine-tuning on file search queries (in the process! let's chat and finetune the model together!)

### System Integration
- [ ] Integration with other search backends beyond Spotlight (cross platform support can be achieved through utitools)


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

## Current Capabilities

### Supported Time Units
- **Days**: "3 days ago"
- **Weeks**: "2 weeks ago"  
- **Months**: "4 months ago" (approximated as 30 days)
- **Years**: "1 year ago"(approximated as 365 days)

### File Type Recognition
The system recognizes common file type descriptions and maps them to extensions:
- "photos" → jpg, jpeg, png, heic
- "python scripts" → py, ipynb
- "music files" → mp3, flac, m4a, wav
- "pdf", "invoices" → pdf, xlsx
- "resume" → pdf, docx, doc


## Limitations
- **Local Model Limitations**: The 0.6b model may struggle with very complex queries
- **No Fuzzy Matching**: Exact keyword matching only


## Contributing

This is a domain where I'm exploring the intersection of local LLMs and system search. Contributions are very appreciated!  

 Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests
- Share interesting use cases

### Areas needing help:
- GUI development (SwiftUI/PyQt/Electron)
- Temporal expression parsing improvements
- Performance optimization
- Cross-platform support (Linux/Windows)
- Documentation and examples

## Technical Stack

- **Python 3.x**: Core implementation
- **LangExtract**: Structured data extraction from natural language
- **Ollama + Qwen 0.6b**: Local LLM for query understanding
- **PyObjC**: Bridge to macOS Foundation framework
- **NSMetadataQuery**: Spotlight search API
- **UTI Tools**: File type identification

