"""Search OFAC SDN list with fuzzy matching"""

import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from beeai_framework.tools import StringToolOutput, tool

from agents.ofac.database import dict_from_row, get_db_connection


def normalize_name(name: str) -> str:
    """
    Normalize name for fuzzy matching.
    - Convert to lowercase
    - Remove punctuation except spaces
    - Collapse multiple spaces
    """
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings (0.0 to 1.0)"""
    return SequenceMatcher(None, str1, str2).ratio()


@tool
def search_sdn_list(
    name: str,
    program: str = "",
    entity_type: str = "",
    min_similarity: float = 0.7,
    limit: int = 20,
) -> StringToolOutput:
    """
    Search OFAC SDN list with fuzzy name matching.

    Args:
        name: Name to search for (required). Supports fuzzy matching.
        program: Filter by program (e.g., CUBA, SDGT, FTO, SDNTK). Optional.
        entity_type: Filter by type: 'individual' or 'entity'. Optional.
        min_similarity: Minimum similarity score (0.0 to 1.0). Default 0.7 (70%)
        limit: Maximum results to return (default 20, max 100)

    Returns:
        List of matching SDN records with similarity scores, sorted by relevance
    """
    if not name or not name.strip():
        return StringToolOutput("Error: Name parameter is required")

    limit = min(int(limit), 100)
    min_similarity = max(0.0, min(1.0, float(min_similarity)))

    # Normalize the search name
    search_normalized = normalize_name(name)

    # Build query
    query = """
        SELECT entity_id, name, entity_type, program, remarks, name_normalized
        FROM sdn_list WHERE 1=1
    """
    params = []

    # Use LIKE for initial filtering (more permissive)
    query += " AND name_normalized LIKE ?"
    params.append(f"%{search_normalized}%")

    if program:
        query += " AND program LIKE ?"
        params.append(f"%{program}%")

    if entity_type:
        query += " AND entity_type = ?"
        params.append(entity_type.lower())

    # Get more results than limit for fuzzy matching
    query += f" LIMIT {limit * 3}"

    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

    # Calculate similarity scores and filter
    results = []
    for row in rows:
        row_dict = dict_from_row(row)

        # Calculate similarity with both original and normalized names
        similarity_normalized = calculate_similarity(search_normalized, row_dict["name_normalized"])
        similarity_original = calculate_similarity(name.lower(), row_dict["name"].lower())

        # Use the higher similarity score
        similarity = max(similarity_normalized, similarity_original)

        if similarity >= min_similarity:
            row_dict["similarity_score"] = round(similarity, 3)
            results.append(row_dict)

    # Sort by similarity (highest first) and limit
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    results = results[:limit]

    # Remove name_normalized from output (internal use only)
    for result in results:
        result.pop("name_normalized", None)

    if not results:
        return StringToolOutput(
            str(
                {
                    "total_found": 0,
                    "search_term": name,
                    "min_similarity": min_similarity,
                    "message": "No matches found above the similarity threshold",
                    "results": [],
                }
            )
        )

    return StringToolOutput(
        str(
            {
                "total_found": len(results),
                "search_term": name,
                "min_similarity": min_similarity,
                "results": results,
            }
        )
    )
