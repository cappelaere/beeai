"""Orchestration tool that combines SAM.gov and OFAC compliance checks"""

import ast
import sys
from pathlib import Path

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from beeai_framework.tools import StringToolOutput, tool

from agents.ofac.tools.check_bidder_eligibility import check_bidder_eligibility
from agents.sam.tools.check_entity_status import check_entity_status


@tool
def verify_bidder_eligibility(bidder_name: str, strict_mode: bool = False) -> StringToolOutput:
    """
    Comprehensive bidder verification that orchestrates both SAM.gov and OFAC compliance checks.

    This tool demonstrates agent orchestration by:
    1. Checking SAM.gov federal contract exclusions
    2. Checking OFAC Specially Designated Nationals (SDN) list
    3. Combining results into a single eligibility determination

    A bidder must pass BOTH checks to be eligible.

    Args:
        bidder_name: Full name of the bidder (individual or company) to verify
        strict_mode: If True, use stricter matching thresholds (default: False)

    Returns:
        Comprehensive eligibility report with:
        - eligible: Boolean - bidder can participate (must pass BOTH checks)
        - sam_check: Results from SAM.gov exclusions database
        - ofac_check: Results from OFAC SDN list screening
        - overall_recommendation: Clear guidance on bidder eligibility
        - requires_review: Whether manual compliance review is needed
        - risk_summary: Summary of all compliance risks identified
    """
    if not bidder_name or not bidder_name.strip():
        return StringToolOutput(
            str({"error": "Bidder name is required", "eligible": False, "requires_review": True})
        )

    # Call SAM.gov exclusions check
    sam_result = check_entity_status(bidder_name)
    sam_data = ast.literal_eval(sam_result.output)

    # Call OFAC SDN list check
    ofac_result = check_bidder_eligibility(bidder_name, strict_mode=strict_mode)
    ofac_data = ast.literal_eval(ofac_result.output)

    # Determine overall eligibility (must pass BOTH checks)
    sam_excluded = sam_data.get("is_excluded", False)
    ofac_flagged = not ofac_data.get("eligible", True)

    overall_eligible = not sam_excluded and not ofac_flagged
    requires_review = sam_excluded or ofac_data.get("requires_review", False)

    # Build risk summary
    risks = []
    if sam_excluded:
        count = sam_data.get("active_exclusions", 0)
        risks.append(f"SAM.gov: {count} active federal contract exclusion(s)")

    if ofac_flagged:
        matches = ofac_data.get("total_matches", ofac_data.get("matches", []))
        match_count = matches if isinstance(matches, int) else len(matches)
        risk_level = ofac_data.get("risk_level", "UNKNOWN")
        risks.append(f"OFAC: {match_count} SDN match(es) - {risk_level}")

    # Build overall recommendation
    if overall_eligible:
        recommendation = (
            f"✅ APPROVED: '{bidder_name}' passed both SAM.gov and OFAC compliance checks. "
            "Bidder is eligible to participate in auctions."
        )
    else:
        recommendation = (
            f"❌ DENIED: '{bidder_name}' failed compliance screening. "
            f"Issues: {'; '.join(risks)}. "
            "MANUAL REVIEW REQUIRED before allowing participation."
        )

    # Combine all results
    result = {
        "bidder_name": bidder_name,
        "eligible": overall_eligible,
        "requires_review": requires_review,
        "overall_recommendation": recommendation,
        "risk_summary": risks if risks else ["No compliance risks identified"],
        "checks_performed": {
            "sam_gov": {
                "passed": not sam_excluded,
                "is_excluded": sam_excluded,
                "details": sam_data,
            },
            "ofac": {"passed": not ofac_flagged, "flagged": ofac_flagged, "details": ofac_data},
        },
        "compliance_status": "APPROVED" if overall_eligible else "DENIED",
        "strict_mode": strict_mode,
    }

    return StringToolOutput(str(result))
