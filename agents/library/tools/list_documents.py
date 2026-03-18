"""
List documents tool - List all PDF documents in the library
"""

import json
from datetime import datetime

from beeai_framework.tools import StringToolOutput, tool

from agents.library.tools.document_utils import DOCUMENTS_PATH


@tool
def list_documents(
    filename_pattern: str = "",
) -> StringToolOutput:
    """
    List all PDF documents in the library.

    Args:
        filename_pattern: Optional substring to filter filenames (case-insensitive)

    Returns:
        List of documents with filename, path, size, and modification date.
    """
    if not DOCUMENTS_PATH.exists():
        return StringToolOutput(
            json.dumps(
                {"status": "error", "message": f"Documents directory not found: {DOCUMENTS_PATH}"},
                indent=2,
            )
        )

    # Find all PDF files
    pdf_files = list(DOCUMENTS_PATH.rglob("*.pdf"))

    # Apply filename filter if provided
    if filename_pattern:
        pattern_lower = filename_pattern.lower()
        pdf_files = [f for f in pdf_files if pattern_lower in f.name.lower()]

    # Collect document information
    documents = []
    for pdf_path in sorted(pdf_files):
        try:
            stat = pdf_path.stat()
            rel_path = pdf_path.relative_to(DOCUMENTS_PATH)

            documents.append(
                {
                    "filename": pdf_path.name,
                    "relative_path": str(rel_path),
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "created_date": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                }
            )
        except Exception as e:
            documents.append({"filename": pdf_path.name, "error": str(e)})

    result = {
        "total_documents": len(documents),
        "filter_applied": filename_pattern if filename_pattern else None,
        "documents": documents,
    }

    return StringToolOutput(json.dumps(result, indent=2))
