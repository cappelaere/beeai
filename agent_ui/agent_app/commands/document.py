"""
/document command handler - Document library operations
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _handle_document_list(args):
    """List documents with optional pattern filter."""
    import json

    from agents.library.tools import list_documents

    pattern = args[1] if len(args) > 1 else ""
    result = list_documents.run(filename_pattern=pattern)

    try:
        data = json.loads(result.data)
        if data.get("status") == "error":
            return {
                "content": data.get("message", "Error listing documents"),
                "metadata": {"error": True, "command": "document list"},
            }

        lines = [f"📁 Document Library ({data['total_documents']} documents)"]
        if pattern:
            lines.append(f"Filter: '{pattern}'")
        lines.append("")

        for doc in data.get("documents", []):
            if "error" in doc:
                lines.append(f"  ❌ {doc['filename']}: {doc['error']}")
            else:
                lines.append(
                    f"  📄 {doc['filename']}\n"
                    f"     Size: {doc['size_mb']}MB | Modified: {doc['modified_date'][:10]}"
                )

        return {
            "content": "\n".join(lines),
            "metadata": {"command": "document list", "count": data["total_documents"]},
        }
    except Exception as e:
        return {"content": f"Error parsing document list: {e}", "metadata": {"error": True}}


def _handle_document_search(args):
    """Search documents semantically."""
    import json

    from agents.library.tools import search_documents

    if len(args) < 2:
        return {"content": "Usage: /document search <query> [top_k]", "metadata": {"error": True}}

    query = " ".join(args[1:])
    top_k = 5

    try:
        if args[-1].isdigit():
            top_k = int(args[-1])
            query = " ".join(args[1:-1])
    except (ValueError, IndexError):
        pass

    result = search_documents.run(query=query, top_k=top_k)

    try:
        data = json.loads(result.data)

        if "No documents have been indexed" in result.data:
            return {
                "content": result.data,
                "metadata": {"command": "document search", "query": query},
            }

        lines = [f"🔍 Search Results for: '{data['query']}'"]
        lines.append(
            f"Found {data['results_returned']} results from {data['total_indexed_documents']} documents\n"
        )

        for r in data.get("results", []):
            lines.append(
                f"{r['rank']}. {r['document_name']} (score: {r['relevance_score']:.2f})\n"
                f"   {r['text'][:150]}...\n"
            )

        return {
            "content": "\n".join(lines),
            "metadata": {
                "command": "document search",
                "query": query,
                "results": len(data.get("results", [])),
            },
        }
    except Exception as e:
        return {
            "content": f"Error parsing search results: {e}\n\nRaw: {result.data}",
            "metadata": {"error": True},
        }


def _handle_document_info(args):
    """Get information about a specific document."""
    import json

    from agents.library.tools import get_document_info

    if len(args) < 2:
        return {"content": "Usage: /document info <filename>", "metadata": {"error": True}}

    filename = " ".join(args[1:])
    result = get_document_info.run(filename=filename)

    try:
        data = json.loads(result.data)

        if data.get("status") == "error":
            return {
                "content": data.get("message", "Error getting document info"),
                "metadata": {"error": True},
            }

        lines = [
            f"📄 Document Information: {data['filename']}",
            "",
            f"Path: {data['relative_path']}",
            f"Size: {data['size_mb']}MB ({data['size_bytes']:,} bytes)",
            f"Pages: {data['page_count']}",
            f"Created: {data['created_date'][:10]}",
            f"Modified: {data['modified_date'][:10]}",
            "",
            f"Index Status: {'✓ Indexed' if data['is_indexed'] else '✗ Not indexed'}",
        ]

        if data["is_indexed"]:
            lines.append(f"Indexed Chunks: {data['indexed_chunks']}")

        return {
            "content": "\n".join(lines),
            "metadata": {"command": "document info", "filename": filename},
        }
    except Exception as e:
        return {"content": f"Error parsing document info: {e}", "metadata": {"error": True}}


def _handle_document_reindex():
    """Reindex all documents in the library."""
    import json

    from agents.library.tools import reindex_all_documents

    result = reindex_all_documents.run()

    try:
        data = json.loads(result.data)

        if "No PDF documents found" in result.data:
            return {
                "content": "No PDF documents found in /media/documents",
                "metadata": {"command": "document reindex"},
            }

        lines = [
            "🔄 Reindex Complete",
            "",
            f"Documents Found: {data['total_documents_found']}",
            f"Documents Indexed: {data['documents_indexed']}",
            f"Total Chunks Created: {data['total_chunks_created']}",
        ]

        if data.get("failed_documents"):
            lines.append("\nFailed Documents:")
            for fail in data["failed_documents"]:
                lines.append(f"  ❌ {fail}")

        return {
            "content": "\n".join(lines),
            "metadata": {
                "command": "document reindex",
                "indexed": data["documents_indexed"],
                "chunks": data["total_chunks_created"],
            },
        }
    except Exception as e:
        return {"content": f"Error parsing reindex results: {e}", "metadata": {"error": True}}


def _handle_document_stats():
    """Show library statistics."""
    import json

    from agents.library.tools import library_statistics

    result = library_statistics.run()

    try:
        data = json.loads(result.data)

        lib = data.get("library", {})
        idx = data.get("index", {})
        status = data.get("status", {})

        lines = [
            "📊 Library Statistics",
            "",
            "Library:",
            f"  Total Documents: {lib.get('total_documents', 0)}",
            f"  Total Size: {lib.get('total_size_mb', 0)}MB",
            f"  Path: {lib.get('documents_path', 'N/A')}",
            "",
            "Search Index:",
            f"  Status: {'✓ Exists' if idx.get('exists') else '✗ Not created'}",
            f"  Indexed Documents: {idx.get('indexed_documents', 0)}",
            f"  Total Chunks: {idx.get('total_chunks', 0)}",
            f"  Index Size: {idx.get('index_size_mb', 0)}MB",
            f"  Model: {idx.get('embedding_model', 'N/A')}",
            "",
            "Coverage:",
            f"  Documents Not Indexed: {status.get('documents_not_indexed', 0)}",
            f"  Index Coverage: {status.get('index_coverage_percent', 0)}%",
        ]

        return {"content": "\n".join(lines), "metadata": {"command": "document stats"}}
    except Exception as e:
        return {"content": f"Error parsing library stats: {e}", "metadata": {"error": True}}


def handle_document(request, args, session_key):
    """
    Handle document-related commands.

    Commands:
        /document list [pattern] - List all documents
        /document search <query> [top_k] - Search documents
        /document info <filename> - Get document info
        /document reindex - Reindex all documents
        /document stats - Library statistics

    Args:
        request: Django HTTP request
        args: Command arguments
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    if not args:
        return {
            "content": (
                "Usage: /document <command>\n\n"
                "Commands:\n"
                "  list [pattern] - List all documents\n"
                "  search <query> [top_k] - Search documents semantically\n"
                "  info <filename> - Get document information\n"
                "  reindex - Rebuild search index\n"
                "  stats - Show library statistics"
            ),
            "metadata": {"error": True, "command": "document"},
        }

    subcommand = args[0].lower()

    if subcommand == "list":
        return _handle_document_list(args)

    if subcommand == "search":
        return _handle_document_search(args)

    if subcommand == "info":
        return _handle_document_info(args)

    if subcommand == "reindex":
        return _handle_document_reindex()

    if subcommand == "stats":
        return _handle_document_stats()

    return {
        "content": f"Unknown document command: {subcommand}\n\nType '/document' for usage",
        "metadata": {"error": True},
    }
