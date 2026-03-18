"""Check bidder eligibility against OFAC SDN list"""

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
    """Normalize name for fuzzy matching"""
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
def check_bidder_eligibility(bidder_name: str, strict_mode: bool = False) -> StringToolOutput:
    """
    Check if a bidder is eligible to participate in auctions by screening against OFAC SDN list.

    This is the primary screening tool for bidder validation. It flags ANY potential match
    for manual review, even with low confidence scores, to ensure compliance.

    Args:
        bidder_name: Name of the bidder to check (required)
        strict_mode: If True, only flag very close matches (>85% similarity).
                    If False (default), flag any potential match (>60% similarity)

    Returns:
        Eligibility determination with:
        - eligible: Boolean indicating if bidder can proceed (False if ANY match found)
        - confidence: How confident we are in the determination (0.0 to 1.0)
        - matches: List of potential SDN matches with similarity scores
        - recommendation: Clear guidance on next steps
        - requires_review: Whether manual review is needed
    """
    if not bidder_name or not bidder_name.strip():
        return StringToolOutput(
            str({"error": "Bidder name is required", "eligible": False, "requires_review": True})
        )

    # Set similarity threshold based on mode
    similarity_threshold = 0.85 if strict_mode else 0.60

    # Normalize the bidder name
    search_normalized = normalize_name(bidder_name)

    # Search with broad LIKE to catch variations
    query = """
        SELECT entity_id, name, entity_type, program, remarks, name_normalized
        FROM sdn_list
        WHERE name_normalized LIKE ?
        LIMIT 100
    """

    with get_db_connection() as conn:
        cursor = conn.execute(query, (f"%{search_normalized}%",))
        rows = cursor.fetchall()

    # Calculate similarity scores
    potential_matches = []
    for row in rows:
        row_dict = dict_from_row(row)

        # Calculate similarity with both normalized and original names
        similarity_normalized = calculate_similarity(search_normalized, row_dict["name_normalized"])
        similarity_original = calculate_similarity(bidder_name.lower(), row_dict["name"].lower())

        # Use the higher similarity score
        similarity = max(similarity_normalized, similarity_original)

        if similarity >= similarity_threshold:
            row_dict["similarity_score"] = round(similarity, 3)
            row_dict.pop("name_normalized", None)  # Remove internal field
            potential_matches.append(row_dict)

    # Sort by similarity (highest first)
    potential_matches.sort(key=lambda x: x["similarity_score"], reverse=True)

    # Determine eligibility
    if not potential_matches:
        # No matches found - bidder is eligible
        return StringToolOutput(
            str(
                {
                    "eligible": True,
                    "confidence": 0.95,
                    "bidder_name": bidder_name,
                    "matches": [],
                    "recommendation": "No matches found in OFAC SDN list. Bidder appears eligible.",
                    "requires_review": False,
                    "strict_mode": strict_mode,
                    "search_threshold": similarity_threshold,
                }
            )
        )

    # Matches found - flag for review
    highest_similarity = potential_matches[0]["similarity_score"]
    match_count = len(potential_matches)

    # Determine confidence level
    if highest_similarity >= 0.95:
        confidence = 0.99
        risk_level = "VERY HIGH - Likely exact match"
    elif highest_similarity >= 0.85:
        confidence = 0.90
        risk_level = "HIGH - Very similar name"
    elif highest_similarity >= 0.75:
        confidence = 0.75
        risk_level = "MODERATE - Similar name"
    else:
        confidence = 0.60
        risk_level = "LOW - Possible match"

    # Build recommendation
    if match_count == 1:
        recommendation = (
            f"FLAGGED: Found 1 potential match with {highest_similarity * 100:.1f}% similarity. "
            f"Risk Level: {risk_level}. MANUAL REVIEW REQUIRED before allowing bidder to participate."
        )
    else:
        recommendation = (
            f"FLAGGED: Found {match_count} potential matches (highest: {highest_similarity * 100:.1f}% similarity). "
            f"Risk Level: {risk_level}. MANUAL REVIEW REQUIRED before allowing bidder to participate."
        )

    return StringToolOutput(
        str(
            {
                "eligible": False,
                "confidence": confidence,
                "bidder_name": bidder_name,
                "matches": potential_matches[:10],  # Return top 10 matches
                "total_matches": match_count,
                "highest_similarity": highest_similarity,
                "risk_level": risk_level,
                "recommendation": recommendation,
                "requires_review": True,
                "strict_mode": strict_mode,
                "search_threshold": similarity_threshold,
            }
        )
    )
