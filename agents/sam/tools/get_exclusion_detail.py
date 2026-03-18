"""Get detailed exclusion information"""

import sys
from pathlib import Path

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from beeai_framework.tools import StringToolOutput, tool

from agents.sam.database import dict_from_row, get_db_connection


@tool
def get_exclusion_detail(sam_number: str = "", unique_entity_id: str = "") -> StringToolOutput:
    """
    Get detailed information about a specific exclusion.

    Args:
        sam_number: SAM Number (e.g., S4MR3R7D6)
        unique_entity_id: Unique Entity Identifier

    Returns:
        Full exclusion record with all fields including addresses, dates, and cross-references
    """
    if not sam_number and not unique_entity_id:
        return StringToolOutput("Error: Must provide either sam_number or unique_entity_id")

    with get_db_connection() as conn:
        if sam_number:
            cursor = conn.execute("SELECT * FROM exclusions WHERE sam_number = ?", (sam_number,))
        else:
            cursor = conn.execute(
                "SELECT * FROM exclusions WHERE unique_entity_id = ?", (unique_entity_id,)
            )

        row = cursor.fetchone()

        if row:
            result = dict_from_row(row)
            return StringToolOutput(str(result))
        return StringToolOutput("No exclusion found with provided identifier")
