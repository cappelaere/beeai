"""Check if entity is currently excluded"""

import sys
from pathlib import Path

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from beeai_framework.tools import StringToolOutput, tool

from agents.sam.database import get_db_connection


@tool
def check_entity_status(entity_name: str) -> StringToolOutput:
    """
    Check if an individual or company is currently excluded from federal contracts.

    Args:
        entity_name: Full or partial name to check

    Returns:
        Exclusion status and active exclusion details if found
    """
    search_name = (entity_name or "").strip()
    search_term = f"%{search_name}%" if search_name else "%"
    params = (search_term,) * 5
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT name, classification, excluding_agency, exclusion_type,
                   active_date, termination_date, record_status, sam_number
            FROM exclusions
            WHERE (name LIKE ? OR first LIKE ? OR middle LIKE ? OR last LIKE ?
                   OR (cross_reference IS NOT NULL AND cross_reference LIKE ?))
            AND (termination_date = 'Indefinite' OR termination_date >= date('now'))
            ORDER BY active_date DESC
            """,
            params,
        )

        rows = cursor.fetchall()

        if not rows:
            return StringToolOutput(
                str(
                    {
                        "entity_name": entity_name,
                        "is_excluded": False,
                        "message": f"No active exclusions found for '{entity_name}'",
                    }
                )
            )

        results = []
        for row in rows:
            results.append(
                {
                    "name": row["name"],
                    "classification": row["classification"],
                    "excluding_agency": row["excluding_agency"],
                    "exclusion_type": row["exclusion_type"],
                    "active_since": row["active_date"],
                    "termination_date": row["termination_date"],
                    "status": row["record_status"],
                    "sam_number": row["sam_number"],
                }
            )

        return StringToolOutput(
            str(
                {
                    "entity_name": entity_name,
                    "is_excluded": True,
                    "active_exclusions": len(results),
                    "details": results,
                }
            )
        )
