# Technical Documentation

Deep dive into MonkeSearch's architecture, implementation details, and the roadmap for making file search smarter.  

<br>
<img width="3985" height="2929" alt="image" src="https://github.com/user-attachments/assets/1393fc1d-52e0-4a3e-9825-0d9b924c8e19" />


## How It Works

### 1. Query Parsing
Your natural language query is analyzed by Qwen (0.6b) running locally via llama-cpp-python to extract:
- **File type indicators**: "photos" → jpg, jpeg, png, heic
  - **Specificity flag**: Determines if exact file type matching is required
- **Temporal expressions**: "last week" → 7 days, "3 weeks ago" → 21 days
- **Residual keywords**: Remaining meaningful terms after extraction

### 2. Intelligent Filtering
Before LLM processing, common stop words are removed:
```python
STOP_WORDS = {'in', 'at', 'of', 'by', 'as', 'me', 'the', 'a', 'an', 
              'and', 'any', 'find', 'search', 'list', 'file', 'files',
              'ago', 'back', 'past', 'earlier', 'folder'}
```

### 3. File Type Specificity Detection
The system intelligently determines whether you want exact file types or broader categories:
- **Specific type (`is_specific=true`)**: When you mention exact file types
  - "python files" → only .py files
  - "pdf documents" → only .pdf files
  - "excel sheets" → only .xlsx files
- **Broad type (`is_specific=false`)**: When you mention general categories
  - "images" → all image types (jpg, png, heic, etc.)
  - "documents" → all document types
  - "code" → all source code files

### 4. Predicate Building
Extracted information is converted to macOS Spotlight search predicates:
- File types map to Uniform Type Identifiers (UTIs) using `utitools`
  - **When `is_specific=true`**: Uses exact UTI without hierarchy climbing
  - **When `is_specific=false`**: Climbs UTI hierarchy to include related types
- Time expressions become `kMDItemFSContentChangeDate` comparisons
- Keywords search both `kMDItemTextContent` and `kMDItemFSName`

### 5. Spotlight Search
macOS's native search engine queries the indexed metadata:
- Searches complete in milliseconds
- No directory scanning required
- Respects system indexing preferences
- Results limited to top 20 by default



## Troubleshooting

### Model loading errors
- Ensure you have the correct GGUF model file in your project directory
- Check the model path in your code matches the actual file location
- See [llama-cpp-python documentation](https://github.com/abetlen/llama-cpp-python) for troubleshooting

### No results returned
- Verify Spotlight is enabled: System Settings → Siri & Spotlight → Search Results
- Check if the location is indexed: Spotlight preferences
- Try a simpler query first

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
- [x] ✅ Llama-cpp-python inference support

### Advanced Temporal Processing (major upgrade)
- [ ] Temporal approximators ("around 3 weeks", "about 2 months")
- [ ] Temporal operators ("before last month", "within 2 days", "since yesterday")
- [ ] Specific time values ("within 3 hours", "4 months ago")
- [ ] Date ranges ("between 2 and 3 weeks ago")
- [ ] Named time references ("this morning", "tonight", "today", "now")

### Enhanced Query Understanding (major upgrade)
- [ ] Fuzzy matching for keywords
- [ ] Semantic tag extraction and indexing
- [x] ✅ Implemented via is_specific flag: Prioritizing a specific filetype if it's included in the prompt. (If someone searches for python files, show only python files instead of stepping up in the UTI hierarchy and showing all the `public.shell-script` files.)

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
QueryExtractor (Qwen 0.6b via llama-cpp-python)
        ↓
Structured Data {file_types, temporal, keywords, is_specific}
        ↓
FileSearchParser (PyObjC + Foundation)
        ↓
NSPredicate Objects (with UTI hierarchy control)
        ↓
NSMetadataQuery (Spotlight)
        ↓
File Paths Results
```

## Current Capabilities

### File Type Specificity Control
The system now intelligently determines search scope based on query phrasing:

**Specific File Type Searches** (`is_specific=true`):
- Query: "python files from last week"
  - Returns: Only .py files, not other script types
- Query: "pdf invoices"
  - Returns: Only PDF files, not other document types

**Broad Category Searches** (`is_specific=false`):
- Query: "images from yesterday"
  - Returns: All image types (jpg, png, heic, etc.)
- Query: "documents about taxes"
  - Returns: PDFs, Word docs, spreadsheets, etc.

### Supported Time Units
- **Days**: "3 days ago"
- **Weeks**: "2 weeks ago"  
- **Months**: "4 months ago" (approximated as 30 days)
- **Years**: "1 year ago"(approximated as 365 days)

### File Type Recognition
The system recognizes common file type descriptions and maps them to extensions:
- "photos" → jpg, jpeg, png, heic (broad search)
- "python scripts" → py, ipynb (specific search)
- "music files" → mp3, flac, m4a, wav (broad search)
- "pdf", "invoices" → pdf, xlsx (context-dependent)
- "resume" → pdf, docx, doc (broad search)

### UTI Hierarchy Navigation
When `is_specific=false`, the system climbs the Uniform Type Identifier hierarchy:
- Searching for "images" includes all `public.image` subtypes
- Searching for "code" includes all `public.source-code` subtypes
- Searching for "documents" includes all `public.content` text types

When `is_specific=true`, the system uses exact UTI matching:
- "python files" searches only for `public.python-script`
- "mp4 files" searches only for `public.mpeg-4`


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
- **llama-cpp-python + Qwen 0.6b**: Local LLM for query understanding
- **PyObjC**: Bridge to macOS Foundation framework
- **NSMetadataQuery**: Spotlight search API
- **UTI Tools**: File type identification