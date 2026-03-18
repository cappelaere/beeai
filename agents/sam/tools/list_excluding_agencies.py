"""List all excluding agencies"""

import sys
from pathlib import Path

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from beeai_framework.tools import StringToolOutput, tool

from agents.sam.database import get_db_connection


@tool
def list_excluding_agencies() -> StringToolOutput:
    """
    Get list of all federal agencies that have issued exclusions.

    Returns:
        List of agency codes and exclusion counts, sorted by count descending
    """
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT excluding_agency, COUNT(*) as count
            FROM exclusions
            WHERE excluding_agency IS NOT NULL AND excluding_agency != ''
            GROUP BY excluding_agency
            ORDER BY count DESC
        """)

        rows = cursor.fetchall()
        agencies = [
            {"agency": row["excluding_agency"], "exclusion_count": row["count"]} for row in rows
        ]

    return StringToolOutput(str({"total_agencies": len(agencies), "agencies": agencies}))
