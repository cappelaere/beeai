# Library Agent Documentation

## Overview

**Agent Name:** Library Agent 📚  
**Purpose:** Document library management and semantic search assistant  
**Type:** PDF document search and management using AI embeddings

The Library Agent provides intelligent semantic search through PDF documents using FAISS (Facebook AI Similarity Search) and sentence transformers. It enables natural language queries to find relevant information across your document library.

## When to Use This Agent

Use the Library Agent when you need to:
- Search for information across multiple PDF documents
- Find relevant passages using natural language questions
- Browse and manage your document library
- Get detailed information about specific documents
- Rebuild the search index for documents
- View library statistics and index health

## Quick Start

### Selecting the Agent
1. Open the RealtyIQ interface
2. Use the agent selector dropdown in the top bar
3. Select "📚 Library"

### Basic Usage Examples

**Search documents:**
```
Find information about contract requirements
What does the policy say about data retention?
Search for sections about compliance procedures
```

**Manage library:**
```
List all documents in the library
Show me information about contract_template.pdf
Rebuild the search index
```

**Get statistics:**
```
How many documents are indexed?
Show library statistics
What's the status of the document index?
```

## Available Tools

### Semantic Search

#### search_documents
**Purpose:** Search indexed PDF documents using semantic similarity and natural language

**Key Parameters:**
- `query` (str, required): The search query or question in natural language
- `top_k` (int): Number of most relevant chunks to return (default: 5, max: 20)

**Example:**
```
search_documents(query="What are the security requirements?", top_k=10)
search_documents(query="contract termination clause")
```

**How It Works:**
1. Query is converted to an embedding vector
2. FAISS searches for most similar document chunks
3. Results ranked by semantic relevance
4. Returns top matches with context

**Returns:**
- Query used
- Total indexed documents
- Total indexed chunks
- Results returned
- List of results with:
  - Rank
  - Relevance score (0-1, higher is better)
  - Document name
  - Document path
  - Chunk index and total chunks
  - Text excerpt (up to 500 characters)

**Use Cases:**
- "Find contract clauses about liability"
- "What documents mention GDPR compliance?"
- "Search for pricing information"

### Document Management

#### list_documents
**Purpose:** List all PDF documents in the library with metadata

**Example:**
```
list_documents()
```

**Returns:**
- Total documents
- List of documents with:
  - Filename
  - Full path
  - File size (human-readable)
  - Last modified date
  - Index status (indexed/not indexed)

**Use Cases:**
- Browse available documents
- Check which documents are indexed
- Find recently added documents
- Review library contents

#### get_document_info
**Purpose:** Get detailed information about a specific document

**Key Parameters:**
- `document_name` (str, required): Name or partial name of the document

**Example:**
```
get_document_info(document_name="contract_template.pdf")
get_document_info(document_name="policy")
```

**Returns:**
- Document name and path
- File size
- Last modified date
- Index status
- If indexed:
  - Number of chunks
  - Total characters indexed
  - Average chunk size
  - Index date

**Use Cases:**
- Check if a document is indexed
- View document metadata
- Verify document upload
- Check indexing status

### Index Management

#### reindex_all_documents
**Purpose:** Rebuild the FAISS search index from all PDF documents in the library

**Example:**
```
reindex_all_documents()
```

**When to Use:**
- After uploading new documents
- If search results seem stale
- After updating existing documents
- To rebuild corrupted index

**What It Does:**
1. Scans document library for PDFs
2. Extracts text from each PDF
3. Splits text into semantic chunks
4. Generates embeddings for each chunk
5. Builds FAISS index for fast search
6. Saves metadata for results

**Returns:**
- Success/failure status
- Documents processed
- Total chunks indexed
- Processing time
- Any errors encountered

**Note:** Reindexing can take several minutes for large libraries.

### Analytics

#### library_statistics
**Purpose:** Get comprehensive statistics about the library and search index

**Example:**
```
library_statistics()
```

**Returns:**
- **Document Counts:**
  - Total PDFs in library
  - Indexed documents
  - Not indexed documents
- **Index Statistics:**
  - Total chunks indexed
  - Average chunks per document
  - Index size (if available)
  - Last index update
- **Library Health:**
  - Index status
  - Coverage percentage
  - Potential issues

**Use Cases:**
- Monitor library health
- Check indexing coverage
- Troubleshoot search issues
- Plan reindexing

## Common Workflows

### Finding Information

1. **Search with natural language:**
   ```
   search_documents(query="What are the payment terms?", top_k=5)
   ```

2. **Review results:**
   - Check relevance scores
   - Read text excerpts
   - Note document names and locations

3. **Refine if needed:**
   ```
   search_documents(query="net 30 payment terms contract", top_k=10)
   ```

### Adding New Documents

1. **Upload PDFs** to the document library directory

2. **Reindex the library:**
   ```
   reindex_all_documents()
   ```

3. **Verify indexing:**
   ```
   get_document_info(document_name="new_document.pdf")
   ```

4. **Test search:**
   ```
   search_documents(query="content from new document")
   ```

### Library Maintenance

1. **Check library status:**
   ```
   library_statistics()
   ```

2. **List all documents:**
   ```
   list_documents()
   ```

3. **Identify unindexed documents:**
   - Review documents with "not indexed" status

4. **Rebuild index:**
   ```
   reindex_all_documents()
   ```

### Troubleshooting No Results

1. **Check if documents are indexed:**
   ```
   library_statistics()
   ```

2. **Verify document exists:**
   ```
   list_documents()
   ```

3. **Check specific document:**
   ```
   get_document_info(document_name="filename.pdf")
   ```

4. **Reindex if needed:**
   ```
   reindex_all_documents()
   ```

## Technical Details

### Search Technology

**FAISS (Facebook AI Similarity Search):**
- Vector similarity search engine
- Fast approximate nearest neighbor search
- Optimized for large-scale embeddings
- Sub-millisecond search times

**Sentence Transformers:**
- Embedding model: `all-MiniLM-L6-v2`
- 384-dimensional embeddings
- Trained on semantic similarity
- Supports natural language queries

**Text Processing:**
- PDFs extracted using PyPDF2 or pdfplumber
- Text split into semantic chunks (approx. 500-1000 characters)
- Chunks overlap slightly for context preservation
- Embeddings generated for each chunk

### Index Storage

**FAISS Index:**
- Stored in: `agent_ui/faiss_index/`
- File: `documents.index`
- Metadata: `documents_metadata.pkl`

**Metadata Schema:**
```python
{
    "document_name": str,
    "document_path": str,
    "chunk_index": int,
    "total_chunks": int,
    "chunk_text": str
}
```

### Document Processing

**Supported Formats:**
- PDF files (.pdf)
- Text extraction from:
  - Text-based PDFs
  - OCR'd PDFs
  - Scanned documents (with OCR)

**Chunking Strategy:**
- Target chunk size: 500-1000 characters
- Preserves sentence boundaries
- Maintains semantic coherence
- Overlaps for context

### Performance

**Search Speed:**
- Typical query: < 100ms
- Index size impact: Minimal up to 10,000 documents
- Concurrent queries: Supported

**Indexing Speed:**
- ~5-10 documents per minute
- Depends on document size
- GPU acceleration possible (if available)

**Memory Usage:**
- Index loaded in memory for fast search
- Scales with number of documents
- Typical: 100-500MB for 1000 documents

## Example Use Cases

### For Researchers
- "Find all mentions of climate change in policy documents"
- "Search for studies about machine learning applications"
- "What documents discuss renewable energy?"

### For Legal Teams
- "Find contract clauses about intellectual property"
- "Search for force majeure provisions"
- "What agreements mention confidentiality?"

### For Compliance Officers
- "Find sections about data privacy requirements"
- "Search for GDPR compliance procedures"
- "What policies mention audit requirements?"

### For Technical Writers
- "Find API documentation for authentication"
- "Search for code examples in technical docs"
- "What manuals describe installation procedures?"

## Search Tips

### Effective Queries

**Good Queries:**
- "What are the security requirements for data handling?"
- "Find information about contract termination procedures"
- "Search for sections about employee benefits"

**Less Effective:**
- "security" (too vague)
- "the" (stop words)
- "abc123" (non-semantic)

### Query Optimization

1. **Use natural language:**
   - Write questions as you would ask a person
   - Include context words

2. **Be specific:**
   - Include key terms
   - Specify document type if known

3. **Adjust top_k:**
   - Start with 5 results
   - Increase to 10-20 if needed
   - Higher values for broad searches

4. **Refine searches:**
   - Use results to inform better queries
   - Combine multiple terms

## Limitations

### Current Limitations

1. **PDF Only:**
   - Only PDF documents supported
   - No Word, Excel, or text files

2. **English Language:**
   - Optimized for English text
   - Other languages may have reduced accuracy

3. **Index Updates:**
   - Manual reindexing required
   - No automatic document monitoring

4. **Chunk Boundaries:**
   - Information may span chunks
   - Context might be truncated

### Future Enhancements

- Support for additional document formats
- Automatic reindexing on upload
- Multi-language support
- Page number extraction
- Document highlighting

## Related Agents

- **GRES Agent** - For property and auction data
- **SAM.gov Agent** - For federal exclusions
- **Identity Verification Agent** - For compliance verification
- **Section 508 Agent** - For document accessibility

## Support

### Troubleshooting

**No search results:**
1. Check if index exists: `library_statistics()`
2. Verify documents uploaded: `list_documents()`
3. Reindex: `reindex_all_documents()`

**Slow searches:**
1. Check index size
2. Reduce top_k parameter
3. Verify system resources

**Indexing fails:**
1. Check PDF file integrity
2. Verify disk space
3. Review error messages
4. Try reindexing individual documents

**Incorrect results:**
1. Refine query with more context
2. Try different phrasing
3. Increase top_k to see more results
4. Check document content quality

### Requirements

- Python packages: FAISS, sentence-transformers, PyPDF2
- Disk space for index storage
- Memory for loaded index
- PDF documents in library directory
