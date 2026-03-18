"""Get exclusions database statistics"""

import sys
from pathlib import Path

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from beeai_framework.tools import StringToolOutput, tool

from agents.sam.database import get_db_connection


@tool
def exclusion_statistics() -> StringToolOutput:
    """
    Get statistical summary of exclusions database.

    Returns:
        Overall statistics including totals, breakdowns by classification,
        exclusion type, and termination status
    """
    with get_db_connection() as conn:
        # Total count
        cursor = conn.execute("SELECT COUNT(*) as total FROM exclusions")
        total = cursor.fetchone()["total"]

        # By classification
        cursor = conn.execute("""
            SELECT classification, COUNT(*) as count
            FROM exclusions
            GROUP BY classification
            ORDER BY count DESC
        """)
        by_classification = [dict(row) for row in cursor.fetchall()]

        # By exclusion type
        cursor = conn.execute("""
            SELECT exclusion_type, COUNT(*) as count
            FROM exclusions
            WHERE exclusion_type IS NOT NULL
            GROUP BY exclusion_type
            ORDER BY count DESC
        """)
        by_type = [dict(row) for row in cursor.fetchall()]

        # Top excluding agencies
        cursor = conn.execute("""
            SELECT excluding_agency, COUNT(*) as count
            FROM exclusions
            WHERE excluding_agency IS NOT NULL AND excluding_agency != ''
            GROUP BY excluding_agency
            ORDER BY count DESC
            LIMIT 10
        """)
        top_agencies = [dict(row) for row in cursor.fetchall()]

        # Active vs terminated
        cursor = conn.execute("""
            SELECT
                SUM(CASE WHEN termination_date = 'Indefinite' THEN 1 ELSE 0 END) as indefinite,
                SUM(CASE WHEN termination_date != 'Indefinite' AND termination_date != '' THEN 1 ELSE 0 END) as definite,
                SUM(CASE WHEN termination_date = '' OR termination_date IS NULL THEN 1 ELSE 0 END) as no_term_date
            FROM exclusions
        """)
        term_stats = dict(cursor.fetchone())

    return StringToolOutput(
        str(
            {
                "total_exclusions": total,
                "by_classification": by_classification,
                "by_exclusion_type": by_type,
                "top_excluding_agencies": top_agencies,
                "termination_status": term_stats,
            }
        )
    )
