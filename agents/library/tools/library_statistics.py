"""
Library statistics tool - Get overall library and index statistics
"""

import contextlib
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from beeai_framework.tools import StringToolOutput, tool

from agents.library.tools.document_utils import (
    DOCUMENTS_PATH,
    EMBEDDING_MODEL_NAME,
    FAISS_INDEX_FILE,
    load_faiss_index,
)


@tool
def library_statistics() -> StringToolOutput:
    """
    Get comprehensive statistics about the document library and search index.

    Returns:
        Total documents, indexed documents, chunks, index status, and storage info.
    """
    import agents.library.tools.document_utils as utils

    # Load index if not already loaded
    if utils._faiss_index is None:
        load_faiss_index()

    # Count documents in filesystem
    pdf_files = list(DOCUMENTS_PATH.rglob("*.pdf")) if DOCUMENTS_PATH.exists() else []
    total_docs = len(pdf_files)

    # Calculate directory size
    total_size_bytes = 0
    if DOCUMENTS_PATH.exists():
        for pdf_file in pdf_files:
            with contextlib.suppress(BaseException):
                total_size_bytes += pdf_file.stat().st_size

    # Get unique indexed documents
    indexed_doc_names = {m["document_name"] for m in utils._document_metadata}
    indexed_count = len(indexed_doc_names)

    # Index file stats
    index_exists = FAISS_INDEX_FILE.exists()
    index_size_mb = None
    index_last_modified = None

    if index_exists:
        try:
            index_stat = FAISS_INDEX_FILE.stat()
            index_size_mb = round(index_stat.st_size / (1024 * 1024), 2)
            index_last_modified = datetime.fromtimestamp(
                index_stat.st_mtime, tz=timezone.utc
            ).isoformat()
        except Exception as e:
            logger.debug("Could not get index file stats: %s", e)

    result = {
        "library": {
            "total_documents": total_docs,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "documents_path": str(DOCUMENTS_PATH),
        },
        "index": {
            "exists": index_exists,
            "indexed_documents": indexed_count,
            "total_chunks": len(utils._document_metadata),
            "index_size_mb": index_size_mb,
            "last_modified": index_last_modified,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "embedding_dimension": 384,
        },
        "status": {
            "documents_not_indexed": total_docs - indexed_count,
            "index_coverage_percent": round((indexed_count / total_docs * 100), 1)
            if total_docs > 0
            else 0,
        },
    }

    return StringToolOutput(json.dumps(result, indent=2))
