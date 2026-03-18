import pickle
from pathlib import Path

import faiss
from beeai_framework.tools import StringToolOutput, tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# Configuration
MEDIA_ROOT = Path(__file__).parent.parent / "media"
DOCUMENTS_PATH = MEDIA_ROOT / "documents"
FAISS_INDEX_DIR = MEDIA_ROOT / "faiss_index"
FAISS_INDEX_FILE = FAISS_INDEX_DIR / "documents.index"
METADATA_FILE = FAISS_INDEX_DIR / "metadata.pkl"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Global state (lazy loaded)
_embedding_model = None
_faiss_index = None
_document_metadata = []


def get_embedding_model():
    """Lazy load embedding model (80MB download on first use)"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def load_faiss_index():
    """Load FAISS index and metadata from disk"""
    global _faiss_index, _document_metadata

    if not FAISS_INDEX_FILE.exists():
        # Create empty index if none exists
        embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        _faiss_index = faiss.IndexFlatL2(embedding_dim)
        _document_metadata = []
        return

    _faiss_index = faiss.read_index(str(FAISS_INDEX_FILE))

    if METADATA_FILE.exists():
        with open(METADATA_FILE, "rb") as f:
            _document_metadata = pickle.load(f)
    else:
        _document_metadata = []


def save_faiss_index():
    """Save FAISS index and metadata to disk"""
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(_faiss_index, str(FAISS_INDEX_FILE))

    with open(METADATA_FILE, "wb") as f:
        pickle.dump(_document_metadata, f)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file"""
    reader = PdfReader(pdf_path)
    text = ""
    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()
        if page_text:
            text += f"\n--- Page {page_num} ---\n{page_text}"
    return text


def chunk_text_semantically(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Split text into semantic chunks using LangChain's splitter"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    return splitter.split_text(text)


def index_document(pdf_path: Path) -> int:
    """
    Index a single PDF document into FAISS.
    Returns the number of chunks indexed.
    """
    global _faiss_index, _document_metadata

    # Ensure index is loaded
    if _faiss_index is None:
        load_faiss_index()

    # Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        return 0

    # Chunk text
    chunks = chunk_text_semantically(text)
    if not chunks:
        return 0

    # Generate embeddings
    model = get_embedding_model()
    embeddings = model.encode(chunks, convert_to_numpy=True)

    # Add to FAISS index
    _faiss_index.add(embeddings.astype("float32"))

    # Store metadata for each chunk
    for i, chunk in enumerate(chunks):
        _document_metadata.append(
            {
                "document_name": pdf_path.name,
                "document_path": str(pdf_path.relative_to(MEDIA_ROOT)),
                "chunk_index": i,
                "chunk_text": chunk,
                "total_chunks": len(chunks),
            }
        )

    # Save index
    save_faiss_index()

    return len(chunks)


@tool
def search_documents(
    query: str,
    top_k: int = 5,
) -> StringToolOutput:
    """
    Search indexed PDF documents using semantic similarity.

    Args:
        query: The search query or question
        top_k: Number of most relevant chunks to return (default: 5, max: 20)

    Returns:
        Top-K relevant text chunks with document metadata and page information.
    """
    global _faiss_index, _document_metadata

    # Load index if not already loaded
    if _faiss_index is None:
        load_faiss_index()

    # Check if index is empty
    if _faiss_index.ntotal == 0:
        return StringToolOutput(
            "No documents have been indexed yet. "
            "Use reindex_all_documents to index existing documents, "
            "or upload new documents which will be indexed automatically."
        )

    # Validate and cap top_k
    top_k = max(1, min(int(top_k), 20))

    # Generate query embedding
    model = get_embedding_model()
    query_embedding = model.encode([query], convert_to_numpy=True).astype("float32")

    # Search FAISS index
    distances, indices = _faiss_index.search(query_embedding, top_k)

    # Collect results
    results = []
    for i, (distance, idx) in enumerate(zip(distances[0], indices[0], strict=False)):
        if idx >= len(_document_metadata):
            continue

        metadata = _document_metadata[idx]
        results.append(
            {
                "rank": i + 1,
                "relevance_score": float(1 / (1 + distance)),  # Convert L2 distance to similarity
                "document_name": metadata["document_name"],
                "document_path": metadata["document_path"],
                "chunk_index": metadata["chunk_index"],
                "total_chunks": metadata["total_chunks"],
                "text": metadata["chunk_text"][:500],  # Truncate very long chunks
            }
        )

    output = {
        "query": query,
        "total_indexed_documents": len({m["document_name"] for m in _document_metadata}),
        "total_indexed_chunks": len(_document_metadata),
        "results_returned": len(results),
        "results": results,
    }

    return StringToolOutput(str(output))


@tool
def reindex_all_documents() -> StringToolOutput:
    """
    Reindex all PDF documents in /media/documents.
    This will clear the existing index and rebuild it from scratch.

    Use this when:
    - First setting up the RAG tool
    - After bulk document uploads
    - If the index becomes corrupted
    """
    global _faiss_index, _document_metadata

    # Reset index
    embedding_dim = 384
    _faiss_index = faiss.IndexFlatL2(embedding_dim)
    _document_metadata = []

    # Find all PDF files
    pdf_files = list(DOCUMENTS_PATH.rglob("*.pdf"))

    if not pdf_files:
        return StringToolOutput("No PDF documents found in /media/documents")

    # Index each document
    total_chunks = 0
    indexed_docs = 0
    failed_docs = []

    for pdf_path in pdf_files:
        try:
            chunks = index_document(pdf_path)
            if chunks > 0:
                total_chunks += chunks
                indexed_docs += 1
        except Exception as e:
            failed_docs.append(f"{pdf_path.name}: {str(e)}")

    # Build result
    result = {
        "status": "success",
        "total_documents_found": len(pdf_files),
        "documents_indexed": indexed_docs,
        "total_chunks_created": total_chunks,
        "failed_documents": failed_docs if failed_docs else None,
    }

    return StringToolOutput(str(result))
