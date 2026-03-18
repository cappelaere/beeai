"""Search SAM.gov exclusions database"""

import sys
from pathlib import Path

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from beeai_framework.tools import StringToolOutput, tool

from agents.sam.database import dict_from_row, get_db_connection


@tool
def search_exclusions(
    name: str = "",
    classification: str = "",
    excluding_agency: str = "",
    exclusion_type: str = "",
    country: str = "",
    limit: int = 20,
) -> StringToolOutput:
    """
    Search SAM.gov exclusions database.

    Args:
        name: Individual or entity name (partial match)
        classification: Individual, Firm, Vessel, or Special Entity Designation
        excluding_agency: Agency code (e.g., TREAS-OFAC, DOJ, HHS, OPM)
        exclusion_type: Prohibition/Restriction, Ineligible, Voluntary Exclusion
        country: Country code (USA, CAN, etc.)
        limit: Maximum results to return (default 20, max 100)

    Returns:
        List of matching exclusion records with key fields
    """
    limit = min(int(limit), 100)

    query = """
        SELECT name, classification, excluding_agency, exclusion_type,
               active_date, termination_date, sam_number, unique_entity_id,
               city, state_province, country
        FROM exclusions WHERE 1=1
    """
    params = []

    if name:
        term = f"%{(name or '').strip()}%"
        query += " AND (name LIKE ? OR first LIKE ? OR middle LIKE ? OR last LIKE ? OR (cross_reference IS NOT NULL AND cross_reference LIKE ?))"
        params.extend([term, term, term, term, term])

    if classification:
        query += " AND classification = ?"
        params.append(classification)

    if excluding_agency:
        query += " AND excluding_agency LIKE ?"
        params.append(f"%{excluding_agency}%")

    if exclusion_type:
        query += " AND exclusion_type LIKE ?"
        params.append(f"%{exclusion_type}%")

    if country:
        query += " AND country = ?"
        params.append(country)

    query += f" LIMIT {limit}"

    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        results = [dict_from_row(row) for row in rows]

    return StringToolOutput(str({"total_found": len(results), "limit": limit, "results": results}))
