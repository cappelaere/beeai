"""
Shared utilities for document indexing and retrieval.
Used by Library agent tools.
"""

import pickle
from pathlib import Path

import faiss
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# Configuration
MEDIA_ROOT = Path(__file__).parent.parent.parent.parent / "media"
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
