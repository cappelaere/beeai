"""Get detailed information about a specific SDN entry"""

import sys
from pathlib import Path

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from beeai_framework.tools import StringToolOutput, tool

from agents.ofac.database import dict_from_row, get_db_connection


@tool
def get_sdn_detail(entity_id: int) -> StringToolOutput:
    """
    Get full details for a specific SDN list entry.

    Args:
        entity_id: The unique entity ID from the SDN list (required)

    Returns:
        Complete SDN record with all available information including:
        - entity_id: Unique identifier
        - name: Full name of the individual or entity
        - entity_type: 'individual' or 'entity'
        - program: OFAC program (CUBA, SDGT, FTO, etc.)
        - remarks: Additional information (a.k.a. names, DOB, POB, passport numbers, etc.)
        - created_at: When the record was added to the database
    """
    if not entity_id:
        return StringToolOutput(str({"error": "Entity ID is required"}))

    query = """
        SELECT entity_id, name, entity_type, program, remarks, created_at
        FROM sdn_list
        WHERE entity_id = ?
    """

    with get_db_connection() as conn:
        cursor = conn.execute(query, (int(entity_id),))
        row = cursor.fetchone()

    if not row:
        return StringToolOutput(
            str({"error": f"No SDN entry found with entity_id {entity_id}", "entity_id": entity_id})
        )

    result = dict_from_row(row)

    return StringToolOutput(str({"found": True, "entity": result}))
