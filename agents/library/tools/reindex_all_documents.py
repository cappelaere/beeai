"""
Reindex all documents tool - Rebuild FAISS index from all PDFs
"""

import faiss
from beeai_framework.tools import StringToolOutput, tool

from agents.library.tools.document_utils import (
    DOCUMENTS_PATH,
    index_document,
)


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
    import agents.library.tools.document_utils as utils

    # Reset index
    embedding_dim = 384
    utils._faiss_index = faiss.IndexFlatL2(embedding_dim)
    utils._document_metadata = []

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

    import json

    return StringToolOutput(json.dumps(result, indent=2))
