"""
Library Agent Configuration
Document management and semantic search
"""

import sys
from pathlib import Path

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from beeai_framework.tools.think import ThinkTool

from agents.base import AgentConfig
from agents.library.tools import (
    get_document_info,
    library_statistics,
    list_documents,
    reindex_all_documents,
    search_documents,
)

LIBRARY_AGENT_CONFIG = AgentConfig(
    name="Library Agent",
    description="Document library management and semantic search assistant",
    instructions=(
        "You are the Library Agent, specialized in document management and semantic search. "
        "You help users search through indexed PDF documents using semantic similarity, "
        "manage the document library, reindex documents, and provide library statistics. "
        "\n\n"
        "Key capabilities:\n"
        "- Search documents semantically using natural language queries (search_documents)\n"
        "- List all documents in the library with metadata (list_documents)\n"
        "- Get detailed information about specific documents (get_document_info)\n"
        "- Rebuild the search index for all documents (reindex_all_documents)\n"
        "- View library statistics and index health (library_statistics)\n"
        "\n\n"
        "When users ask about documents, use search_documents for semantic queries "
        "('find information about X'), list_documents to browse available files, "
        "and get_document_info to inspect specific documents. "
        "If search returns no results, suggest reindexing or checking if documents are uploaded."
    ),
    tools=[
        ThinkTool(),
        search_documents,
        reindex_all_documents,
        list_documents,
        get_document_info,
        library_statistics,
    ],
    icon="📚",
)
