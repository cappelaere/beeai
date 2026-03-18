"""Get statistics about the OFAC SDN database"""

import sys
from pathlib import Path

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from beeai_framework.tools import StringToolOutput, tool

from agents.ofac.database import get_db_connection


@tool
def sdn_statistics() -> StringToolOutput:
    """
    Get statistics about the OFAC SDN database.

    No parameters required.

    Returns:
        Database statistics including:
        - total_entries: Total number of SDN records
        - individuals: Count of individual entries
        - entities: Count of entity entries
        - top_programs: Most common OFAC programs
        - database_info: Database file information
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total entries
        cursor.execute("SELECT COUNT(*) FROM sdn_list")
        total_entries = cursor.fetchone()[0]

        # Individuals
        cursor.execute("SELECT COUNT(*) FROM sdn_list WHERE entity_type = 'individual'")
        individuals = cursor.fetchone()[0]

        # Entities
        cursor.execute("SELECT COUNT(*) FROM sdn_list WHERE entity_type = 'entity'")
        entities = cursor.fetchone()[0]

        # Top programs
        cursor.execute("""
            SELECT program, COUNT(*) as count
            FROM sdn_list
            WHERE program != ''
            GROUP BY program
            ORDER BY count DESC
            LIMIT 15
        """)
        top_programs = [{"program": row[0], "count": row[1]} for row in cursor.fetchall()]

        # Database file info
        from agents.ofac.database import DB_PATH

        db_exists = DB_PATH.exists()
        db_size_mb = round(DB_PATH.stat().st_size / (1024 * 1024), 2) if db_exists else 0

    return StringToolOutput(
        str(
            {
                "total_entries": total_entries,
                "individuals": individuals,
                "entities": entities,
                "top_programs": top_programs,
                "database_info": {"path": str(DB_PATH), "exists": db_exists, "size_mb": db_size_mb},
            }
        )
    )
