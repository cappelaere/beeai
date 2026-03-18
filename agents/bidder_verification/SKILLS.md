# Bidder Verification Agent Documentation

## Overview

**Agent Name:** Bidder Verification ✅  
**Purpose:** Orchestrate SAM.gov and OFAC compliance checks for comprehensive bidder eligibility screening  
**Type:** Multi-agent orchestration agent (coordinates specialized compliance agents)

The Bidder Verification Agent demonstrates **agent orchestration** by coordinating multiple specialized agents to provide comprehensive bidder eligibility screening. Instead of requiring users to manually check both SAM.gov and OFAC separately, this agent automatically runs both checks and combines the results into a single, unified eligibility determination.

## What is Agent Orchestration?

**Agent Orchestration** is the coordination of multiple specialized agents to accomplish a complex task:

- **Single Interface**: User interacts with one agent
- **Multiple Agents**: That agent calls tools from other specialized agents
- **Combined Results**: Merges outputs using business logic
- **Unified Response**: Provides one comprehensive answer

This agent orchestrates:
1. **SAM Agent** - Federal contract exclusions database
2. **OFAC Agent** - Sanctions and SDN list screening

## When to Use This Agent

Use the Bidder Verification Agent when you need to:
- Perform comprehensive compliance screening for bidders
- Check if someone can participate in federal auctions
- Verify both SAM.gov and OFAC status in one request
- Get a unified eligibility determination with all compliance checks

## Quick Start

### Selecting the Agent
1. Open the RealtyIQ interface
2. Use the agent selector dropdown in the top bar
3. Select "✅ Bidder Verification"

### Basic Usage Examples

**Simple eligibility check:**
```
Can John Smith bid?
Is Jane Doe eligible to participate?
Check if ABC Corporation can bid on property #12345
Verify eligibility for Mohammed Ahmed
```

**Company verification:**
```
Can XYZ Construction Company bid?
Check eligibility for Acme Holdings LLC
Verify that Smith & Associates can participate
```

**Multiple names:**
```
Check John Smith and ABC Corporation
Verify both Jane Doe (individual) and Doe Enterprises (company)
```

## Available Tool

### verify_bidder_eligibility

**Purpose:** Comprehensive bidder screening that orchestrates both SAM.gov and OFAC compliance checks

**Key Parameters:**
- `bidder_name` (str, required): Full name of the bidder (individual or company) to verify
- `strict_mode` (bool, optional): If True, use stricter matching thresholds. Default False.

**Example:**
```
verify_bidder_eligibility(bidder_name="John Smith")
verify_bidder_eligibility(bidder_name="ABC Corporation", strict_mode=True)
```

**What This Tool Does:**
1. **Calls SAM Agent**: Checks federal contract exclusions via `check_entity_status()`
2. **Calls OFAC Agent**: Screens against SDN list via `check_bidder_eligibility()`
3. **Applies Business Rules**: Bidder must PASS BOTH checks to be eligible
4. **Returns Unified Report**: Combined eligibility determination with all details

**Returns:**
- `eligible` (bool): Overall eligibility - must pass BOTH checks
- `compliance_status` (str): "APPROVED" or "DENIED"
- `overall_recommendation` (str): Clear guidance on eligibility
- `requires_review` (bool): Whether manual review is needed
- `risk_summary` (list): List of all compliance risks identified
- `checks_performed` (dict): Detailed results from both SAM and OFAC checks
  - `sam_gov.passed` (bool): Whether SAM check passed
  - `sam_gov.details` (dict): Full SAM.gov check results
  - `ofac.passed` (bool): Whether OFAC check passed
  - `ofac.details` (dict): Full OFAC check results

**Response Format:**
```json
{
  "bidder_name": "John Smith",
  "eligible": true/false,
  "compliance_status": "APPROVED" or "DENIED",
  "overall_recommendation": "Clear YES/NO with reasoning",
  "requires_review": true/false,
  "risk_summary": ["List of issues found or 'No compliance risks identified'"],
  "checks_performed": {
    "sam_gov": {
      "passed": true/false,
      "is_excluded": true/false,
      "details": {...}
    },
    "ofac": {
      "passed": true/false,
      "flagged": true/false,
      "details": {...}
    }
  }
}
```

## How Orchestration Works

### Traditional Approach (Manual)
User would need to:
1. Switch to SAM agent → ask about bidder → get result
2. Switch to OFAC agent → ask about same bidder → get result  
3. Manually combine both results
4. Determine eligibility themselves

### Orchestration Approach (Automated)
User simply:
1. Use Bidder Verification agent
2. Ask one question: "Can John Smith bid?"
3. Agent automatically:
   - Calls SAM agent's tool internally
   - Calls OFAC agent's tool internally
   - Combines results using business logic
   - Returns unified eligibility determination

**Result:** One question, one comprehensive answer!

## Eligibility Decision Rules

The agent applies these business rules to combine SAM and OFAC results:

### APPROVED (Eligible)
✅ SAM.gov: No active exclusions  
✅ OFAC: No matches found on SDN list  
**→ Bidder is ELIGIBLE to participate**

### DENIED (Ineligible)
Bidder fails if ANY of these conditions:
- ❌ SAM.gov: Active federal contract exclusion found
- ❌ OFAC: Name matches (>60% similarity) entries on SDN list
- ❌ Either check requires manual review

**→ Bidder is NOT ELIGIBLE - Manual review required**

## Understanding the Compliance Checks

### SAM.gov Check (via SAM Agent)
- **What it checks**: Federal contract exclusions database
- **Who gets excluded**: Entities barred from federal contracts due to fraud, performance issues, legal violations
- **Active exclusions**: Only flags currently active exclusions (not expired)
- **Result format**: `is_excluded: true/false` with exclusion details

### OFAC Check (via OFAC Agent)
- **What it checks**: Office of Foreign Assets Control SDN list
- **Who gets sanctioned**: Terrorists, drug traffickers, sanctioned countries, cybercriminals, human rights violators
- **Fuzzy matching**: Uses similarity scoring to catch name variations
- **Threshold**: Flags matches >60% similarity (>85% in strict mode)
- **Result format**: `eligible: true/false` with match details and risk level

## Typical Workflows

### Workflow 1: Clean Bidder (Passes Both Checks)
```
User: "Can Sarah Johnson bid?"

Agent runs verify_bidder_eligibility:
→ SAM check: No exclusions found ✅
→ OFAC check: No SDN matches ✅
→ Combined: APPROVED

Response: "✅ APPROVED: Sarah Johnson passed both SAM.gov and OFAC compliance 
checks. Bidder is eligible to participate in auctions."
```

### Workflow 2: SAM.gov Exclusion Found
```
User: "Check eligibility for John Doe Construction"

Agent runs verify_bidder_eligibility:
→ SAM check: Active exclusion found ❌
→ OFAC check: No matches ✅
→ Combined: DENIED (SAM failure)

Response: "❌ DENIED: John Doe Construction failed compliance screening. 
Issues: SAM.gov: 1 active federal contract exclusion(s). 
MANUAL REVIEW REQUIRED before allowing participation."
```

### Workflow 3: OFAC SDN Match Found
```
User: "Is Mohammed Al-Farsi eligible?"

Agent runs verify_bidder_eligibility:
→ SAM check: No exclusions ✅
→ OFAC check: 2 potential SDN matches (82% similarity) ❌
→ Combined: DENIED (OFAC failure)

Response: "❌ DENIED: Mohammed Al-Farsi failed compliance screening. 
Issues: OFAC: 2 SDN match(es) - HIGH. 
MANUAL REVIEW REQUIRED before allowing participation."
```

### Workflow 4: Multiple Issues
```
User: "Can Narco Trading LLC bid?"

Agent runs verify_bidder_eligibility:
→ SAM check: Active exclusion ❌
→ OFAC check: SDN matches ❌
→ Combined: DENIED (Both failed)

Response: "❌ DENIED: Narco Trading LLC failed compliance screening. 
Issues: SAM.gov: 1 active federal contract exclusion(s); OFAC: 3 SDN match(es) - VERY HIGH. 
MANUAL REVIEW REQUIRED before allowing participation."
```

## Technical Implementation

### How the Orchestration Tool Works

```python
# agents/bidder_verification/tools/verify_bidder_eligibility.py

@tool
def verify_bidder_eligibility(bidder_name: str, strict_mode: bool = False):
    # Step 1: Call SAM agent's tool
    sam_result = check_entity_status(bidder_name)
    sam_data = parse_result(sam_result)
    
    # Step 2: Call OFAC agent's tool
    ofac_result = check_bidder_eligibility(bidder_name, strict_mode)
    ofac_data = parse_result(ofac_result)
    
    # Step 3: Apply business rules
    sam_excluded = sam_data.get("is_excluded", False)
    ofac_flagged = not ofac_data.get("eligible", True)
    overall_eligible = not sam_excluded and not ofac_flagged
    
    # Step 4: Combine results and return
    return unified_report
```

### Database Architecture

This agent doesn't maintain its own database - it leverages existing specialized databases:

- **SAM Database**: `data/sam_exclusions.db` (maintained by SAM agent)
  - Federal contract exclusions
  - ~70,000+ records
  
- **OFAC Database**: `data/ofac_sdn.db` (maintained by OFAC agent)
  - Specially Designated Nationals list
  - ~18,000+ records

### Tool Dependency Graph

```
Bidder Verification Agent
    └── verify_bidder_eligibility (orchestration tool)
        ├── SAM Agent Tools
        │   └── check_entity_status()
        └── OFAC Agent Tools
            └── check_bidder_eligibility()
```

## Benefits of Orchestration

### For Users
- **Simplicity**: One question instead of two separate checks
- **Completeness**: Automatic comprehensive screening
- **Consistency**: Business rules applied uniformly
- **Efficiency**: No need to manually combine results

### For Developers
- **Reusability**: Leverages existing SAM and OFAC tools
- **Maintainability**: Changes to SAM/OFAC tools automatically flow through
- **Modularity**: Each agent maintains its own expertise
- **Extensibility**: Easy to add more compliance checks (e.g., credit checks, bond verification)

## Comparison: Orchestration vs. Manual

### Manual Approach (Without Orchestration)
```
User to SAM Agent: "Check John Smith"
→ SAM Agent: "No exclusions found"

User to OFAC Agent: "Check John Smith"  
→ OFAC Agent: "2 potential matches found"

User: *manually decides* → "Not eligible"
```

### Orchestration Approach (With This Agent)
```
User to Bidder Verification Agent: "Can John Smith bid?"
→ Agent automatically runs both checks
→ Agent applies business rules
→ Agent responds: "❌ DENIED: Failed OFAC check (2 matches)"
```

**Benefit:** User asks once, gets comprehensive answer with all compliance factors considered.

## Important Notes

### Compliance Considerations
- **Conservative Approach**: When in doubt, requires manual review
- **False Positives**: Acceptable and expected in compliance screening
- **Legal Requirement**: OFAC compliance is required for U.S. government contracts
- **Documentation**: All checks are logged for audit purposes

### Limitations
- Does not perform identity verification beyond name matching
- Does not check state or local exclusion lists
- Requires manual review for all flagged matches
- Name variations may require multiple checks

### Best Practices
- Always verify bidder's full legal name
- Check both individual names and company names for corporate bidders
- Document all screening results for compliance records
- Escalate all flagged cases to compliance team for manual review

## Future Enhancements

Potential additions to demonstrate more orchestration:
- **Credit Check Integration**: Add financial verification
- **Bond Verification**: Check surety bond status
- **License Validation**: Verify contractor licenses
- **Multi-jurisdiction**: Coordinate state and local checks
- **Historical Analysis**: Track bidder behavior over time

## Support

For questions about:
- **SAM.gov checks**: See `agents/sam/SKILLS.md`
- **OFAC checks**: See `agents/ofac/SKILLS.md`
- **Agent orchestration**: This documentation
- **Tool errors**: Check `logs/` directory for detailed error messages
