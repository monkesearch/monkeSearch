# Technical Documentation

Deep dive into MonkeSearch's architecture using LEANN vector database for semantic file search with temporal awareness.

<br>
<img width="3985" height="2929" alt="image" src="https://github.com/user-attachments/assets/1393fc1d-52e0-4a3e-9825-0d9b924c8e19" />
The core idea revolves around the fact that we can convert any semantic file search related query into 3 constituents as stated above.

## How It Works

### 1. Metadata Extraction
Spotlight metadata is extracted for each file:
- **Path**: Full file location
- **Name**: Filename for display & embedding
- **Size**: File size in bytes
- **ContentType**: UTI content type (e.g., public.jpeg)
- **Kind**: Human-readable type (e.g., "JPEG image")
- **CreationDate**: File creation timestamp
- **ContentChangeDate**: Last modification timestamp

### 2. Embedding Generation
File metadata is converted to semantic embeddings:
```python
embedding_text = f"{name} located at {path} and size {size} bytes with content type {content_type} and kind {kind}"
```
This text is then embedded using:
- Sentence transformers (default: `facebook/contriever`)
- OpenAI embeddings (optional: `text-embedding-3-small`)
- Ollama embeddings (optional: `nomic-embed-text`)

### 3. LEANN Index Building
The embeddings can be stored in a LEANN index with two modes:
- **Recompute mode** : Stores only graph structure, recomputes embeddings during search (97% storage savings)
- **No-recompute mode**: Stores full embeddings for faster search (more storage, default for monkeSearch)

### 4. Query Processing

#### Temporal Expression Parsing
Regex-based temporal parser extracts time expressions:
```python
pattern = r'(?:(around|about|roughly|approximately)\s+)?(\d+)\s+(hour|day|week|month|year)s?(?:\s+ago)?'
```
- Supports fuzzy modifiers ("around", "about")
- Converts to ISO timestamp ranges
- Removes stop words before parsing

#### Query Cleaning
Stop words are removed from temporal parsing:
```python
STOP_WORDS = {'in', 'at', 'of', 'by', 'as', 'me', 'the', 'a', 'an', 
              'and', 'any', 'find', 'search', 'list', 'ago', 'back',
              'past', 'earlier'}
```

### 5. Semantic Search
LEANN performs graph-based semantic search:
- Query is embedded using the same model as indexing
- Graph traversal finds semantically similar files
- Recomputes embeddings on-the-fly (if in recompute mode)
- Returns top-k most similar results

### 6. Temporal Filtering
If temporal expression found, results are filtered:
- Compares file dates against extracted time range
- Supports both creation and modification dates
- Returns only files within the specified timeframe

## Architecture

```
User Query (Natural Language)
        ↓
Temporal Parser (Regex-based)
        ↓
Query Cleaning (Remove time expressions)
        ↓
Embedding Generation (Sentence Transformers)
        ↓
LEANN Search (Graph-based similarity)
        ↓
Temporal Filtering (Date metadata)
        ↓
Filtered Results
```

## LEANN Configuration

### Build Parameters
```python
LeannBuilder(
    backend_name="hnsw",           # or "diskann" for large datasets
    is_recompute=False,             # True for relatively slower search (less storage - high compute)
    is_compact=False,               # Must be False when is_recompute=False
)
```

### Search Parameters
```python
LeannSearcher.search(
    query,
    top_k=15,                     # Number of results
    recompute_embeddings=False,    # Must match build setting
)
```

## Performance Characteristics

### Storage Comparison
Will be updated after testing
<!-- - **With recomputation**: ~30Kb for 5k files
- **Without recomputation**: ~18MB for 5k files
- **Storage savings**: 93-97% -->

### Search Speed
Will be updated after testing
<!-- - **With recomputation**: ~0.8s for semantic search
- **Without recomputation**: ~0.01s for semantic search
- **Temporal filtering**: Adds minimal overhead -->

### Memory Usage
Will be updated after testing

<!-- - Index loading: Minimal (graph structure only)
- Search time: Proportional to search complexity
- Embedding cache: Configurable based on available RAM -->

## Troubleshooting

### No results returned
- Verify Spotlight is enabled: System Settings → Siri & Spotlight → Search Results
- Check if files are indexed by Spotlight
- Try broader queries without temporal expressions first

### Slow search performance
- Use smaller embedding models

### Index build errors
- Ensure sufficient disk space
- Check file permissions for index directory
- Verify embedding model is downloaded/accessible

## Future Improvements

### Core Features
- [ ] GUI interface for easier usage
- [ ] Windows/Linux support via alternative indexing
- [ ] Content-based search (not just metadata)
- [ ] Smarter algorithms.
- [ ] Multi Model system with indexing for video/ audio/ images using generated context.

## Current Capabilities

### Temporal Expressions Supported
- **Days**: "3 days ago", "yesterday"
- **Weeks**: "2 weeks ago", "last week"
- **Months**: "4 months ago" (approximated as 30 days)
- **Years**: "1 year ago" (approximated as 365 days)
- **Fuzzy**: "around 3 weeks", "about 2 months" (±20% buffer)

### Semantic Understanding
The system understands context without exact matches:
- "documents" matches PDFs, Word files, spreadsheets
- "photos" matches various image formats
- "presentations" matches PowerPoint, Keynote files
- "code" matches source code files

### Metadata Fields Searched
- File name and path
- File type and kind
- Creation and modification dates
- File size (part of embedding)

## Limitations
- **Metadata only**: Doesn't search file contents
- **Spotlight dependency**: Requires macOS Spotlight indexing (for now)
- **Static index**: Requires manual rebuild for new files
- **Language**: English-focused temporal expressions

## Contributing

This project explores the intersection of vector databases and system search. Contributions are very appreciated!

Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests
- Share interesting use cases

### Areas needing help:
- GUI development (SwiftUI/PyQt/Electron)
- Cross-platform file indexing (Windows/Linux)
- Advanced temporal expression parsing
- Performance optimizations

## Technical Stack

- **Python 3.x**: Core implementation
- **LEANN**: Graph-based vector database with 97% storage savings
- **Sentence Transformers**: Embedding generation
- **PyObjC**: Bridge to macOS Foundation framework
- **NSMetadataQuery**: Spotlight search API
- **Regex**: Temporal expression parsing