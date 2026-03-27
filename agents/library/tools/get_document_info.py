"""
Get document info tool - Get detailed information about a specific document
"""

import json
from datetime import datetime, timezone

from beeai_framework.tools import StringToolOutput, tool
from pypdf import PdfReader

from agents.library.tools.document_utils import (
    DOCUMENTS_PATH,
    load_faiss_index,
)


@tool
def get_document_info(
    filename: str,
) -> StringToolOutput:
    """
    Get detailed information about a specific document.

    Args:
        filename: Name of the document (e.g., "document.pdf")

    Returns:
        Document metadata including size, dates, page count, and index status.
    """
    import agents.library.tools.document_utils as utils

    # Load index to check if document is indexed
    if utils._faiss_index is None:
        load_faiss_index()

    # Find the document file
    pdf_files = list(DOCUMENTS_PATH.rglob(filename))

    if not pdf_files:
        return StringToolOutput(
            json.dumps(
                {"status": "error", "message": f"Document '{filename}' not found in library"},
                indent=2,
            )
        )

    if len(pdf_files) > 1:
        return StringToolOutput(
            json.dumps(
                {
                    "status": "error",
                    "message": f"Multiple documents found with name '{filename}'. Please be more specific.",
                    "matches": [str(f.relative_to(DOCUMENTS_PATH)) for f in pdf_files],
                },
                indent=2,
            )
        )

    pdf_path = pdf_files[0]

    try:
        # Get file stats
        stat = pdf_path.stat()
        rel_path = pdf_path.relative_to(DOCUMENTS_PATH)

        # Get page count
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)

        # Check if indexed
        indexed_chunks = [
            m for m in utils._document_metadata if m["document_name"] == pdf_path.name
        ]

        result = {
            "filename": pdf_path.name,
            "relative_path": str(rel_path),
            "full_path": str(pdf_path),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_date": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
            "modified_date": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "page_count": page_count,
            "is_indexed": len(indexed_chunks) > 0,
            "indexed_chunks": len(indexed_chunks),
        }

        return StringToolOutput(json.dumps(result, indent=2))

    except Exception as e:
        return StringToolOutput(
            json.dumps(
                {
                    "status": "error",
                    "filename": filename,
                    "message": f"Error reading document: {str(e)}",
                },
                indent=2,
            )
        )
