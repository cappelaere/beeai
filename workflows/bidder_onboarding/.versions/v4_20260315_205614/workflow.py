"""
Bidder Onboarding & Verification Workflow

Execution is BPMN-only; see currentVersion/bpmn-bindings.yaml and the BPMN engine.

Automates the complete bidder registration and verification process by:
1. Validating registration data
2. Screening against SAM.gov exclusions
3. Screening against OFAC SDN list  
4. Applying business rules for approval/denial
5. Checking auto-approval settings
6. Creating registration record
7. Maintaining comprehensive audit trail

This workflow orchestrates the SAM, OFAC, and GRES agents to implement
consistent compliance screening and approval logic.

## Workflow Diagram

```mermaid
graph TB
    start[Start: Bidder Registration] --> validate[Validate Registration Data]
    validate --> checkSam[Check SAM.gov Exclusions]
    checkSam --> checkOfac[Check OFAC SDN List]
    checkOfac --> combine[Combine Compliance Results]
    combine --> eligible{Pass All Checks?}
    eligible -->|FAIL| deny[DENIED - Notify Bidder]
    eligible -->|FLAGGED| manualReview[Manual Review Required]
    eligible -->|PASS| autoApproval{Auto-Approval Enabled?}
    autoApproval -->|YES| setBidLimit[Set Bid Limit]
    autoApproval -->|NO| pendingApproval[Pending Manual Approval]
    setBidLimit --> approved[APPROVED - Create Registration]
    approved --> notify[Send Approval Notification]
    deny --> auditLog[Log to Audit Trail]
    manualReview --> auditLog
    notify --> auditLog
    pendingApproval --> auditLog
    auditLog --> end[End]
```

## Business Rules

**DENIED if:**
- Found on SAM.gov exclusions list (active exclusion)
- Match on OFAC SDN list (>85% similarity in strict mode, >60% default)
- Property is not active or approved

**MANUAL REVIEW if:**
- Potential OFAC match (60-85% similarity)
- Recently terminated SAM exclusion
- Risk factors identified

**AUTO-APPROVED if:**
- Passes both SAM and OFAC checks
- Property has auto-approval enabled
- Within bid limit parameters

**PENDING APPROVAL if:**
- Passes compliance checks
- Auto-approval not enabled

## Usage

```python
from workflows.bidder_onboarding_workflow import BidderOnboardingWorkflow

workflow = BidderOnboardingWorkflow()

result = await workflow.run(
    bidder_name="John Smith",
    property_id=12345,
    registration_data={
        "email": "john.smith@example.com",
        "phone": "555-123-4567",
        "user_type": "Investor",
        "address": "123 Main St, City, ST 12345",
        "terms_accepted": True,
        "age_accepted": True
    }
)

if result.state.is_eligible and result.state.approval_status == "approved":
    print("Bidder approved and ready to bid!")
    print(f"Bid limit: ${result.state.bid_limit:,.2f}")
elif result.state.requires_manual_review:
    print("Flagged for manual review")
    print(f"Risk factors: {result.state.risk_factors}")
else:
    print("Registration denied")
```

## Integration

This workflow can be integrated into Django views:

```python
from workflows.bidder_onboarding_workflow import BidderOnboardingWorkflow

async def register_bidder_view(request):
    workflow = BidderOnboardingWorkflow()
    
    result = await workflow.run(
        bidder_name=request.POST['name'],
        property_id=request.POST['property_id'],
        registration_data=request.POST.dict()
    )
    
    # Create Django model record
    registration = BidRegistration.objects.create(
        property_id=result.state.property_id,
        user_id=request.user.id,
        is_approved=2 if result.state.approval_status == "approved" else 1,
        is_reviewed=result.state.approval_status != "pending"
    )
    
    return JsonResponse({
        "status": result.state.approval_status,
        "eligible": result.state.is_eligible,
        "registration_id": registration.id
    })
```
"""

import asyncio
import ast
from datetime import datetime, UTC
from typing import Literal, Optional
from pydantic import BaseModel, Field

# Import SAM and OFAC database functions
# We'll implement the checks directly to avoid tool decorator issues
from agents.sam.database import get_db_connection as get_sam_db
from agents.ofac.database import get_db_connection as get_ofac_db, dict_from_row
import re
from difflib import SequenceMatcher


class BidderOnboardingState(BaseModel):
    """
    State model for Bidder Onboarding Workflow.
    
    Tracks all data through the registration and verification process,
    maintaining a complete audit trail of all compliance checks and decisions.
    """
    
    # ===== Input Fields (Required) =====
    bidder_name: str = Field(description="Full name of bidder to screen")
    property_id: int = Field(description="Property ID for registration")
    registration_data: dict = Field(
        default_factory=dict,
        description="Complete registration form data (email, phone, address, etc.)"
    )
    
    # ===== Property Context =====
    property_details: dict | None = Field(
        default=None,
        description="Property details including approval status, settings"
    )
    property_active: bool = Field(
        default=False,
        description="Whether property is active and accepting registrations"
    )
    
    # ===== Compliance Check Results =====
    sam_check_result: dict | None = Field(
        default=None,
        description="SAM.gov exclusions check result"
    )
    sam_passed: bool = Field(
        default=False,
        description="Whether bidder passed SAM.gov screening"
    )
    
    ofac_check_result: dict | None = Field(
        default=None,
        description="OFAC SDN list check result"
    )
    ofac_passed: bool = Field(
        default=False,
        description="Whether bidder passed OFAC screening"
    )
    
    # ===== Eligibility Determination =====
    is_eligible: bool = Field(
        default=False,
        description="Overall eligibility to participate in auction"
    )
    requires_manual_review: bool = Field(
        default=False,
        description="Whether manual review is required"
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="List of identified risk factors"
    )
    compliance_summary: str = Field(
        default="",
        description="Human-readable summary of compliance checks"
    )
    
    # ===== Approval Logic =====
    auto_approval_enabled: bool = Field(
        default=False,
        description="Whether auto-approval is enabled for this property"
    )
    approval_status: Literal["pending", "approved", "denied", "review_required"] = Field(
        default="pending",
        description="Current approval status"
    )
    bid_limit: float | None = Field(
        default=None,
        description="Approved bid limit amount (if auto-approved)"
    )
    
    # ===== Human Review =====
    human_review_result: dict | None = Field(
        default=None,
        description="Results from human review task (decision, comments, confidence)"
    )
    
    # ===== Audit Trail =====
    checks_performed: list[dict] = Field(
        default_factory=list,
        description="Complete list of all compliance checks performed"
    )
    workflow_steps: list[str] = Field(
        default_factory=list,
        description="List of workflow steps executed"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Workflow execution timestamp"
    )
    
    # ===== Notifications =====
    notifications_sent: list[dict] = Field(
        default_factory=list,
        description="List of notifications sent to bidder/admin"
    )


class BidderOnboardingWorkflow:
    """
    BeeAI Workflow for Bidder Onboarding and Verification.
    
    This workflow automates the complete bidder registration process by:
    1. Validating registration data and property status
    2. Screening bidder against SAM.gov exclusions
    3. Screening bidder against OFAC SDN list
    4. Combining compliance results with business logic
    5. Checking auto-approval settings
    6. Determining final approval status
    7. Creating comprehensive audit trail
    
    The workflow ensures consistent application of compliance rules
    across all registrations and maintains complete documentation
    for audit purposes.
    """
    
    def __init__(self, strict_mode: bool = False, run_id: str = None):
        """
        Initialize the Bidder Onboarding Workflow.
        
        Args:
            strict_mode: If True, uses stricter OFAC matching (85% vs 60%)
            run_id: Workflow run ID (required for creating human tasks)
        """
        self.strict_mode = strict_mode
        self.run_id = run_id

    # ===== Workflow Steps (BPMN handlers) =====

    async def validate_input(self, state: BidderOnboardingState) -> str:
        """
        Step 1: Validate input data.
        
        Ensures all required fields are present and valid before proceeding
        with compliance checks.
        """
        state.workflow_steps.append("validate_input")
        
        # Validate bidder name
        if not state.bidder_name or len(state.bidder_name.strip()) < 2:
            state.approval_status = "denied"
            state.risk_factors.append("Invalid bidder name")
            return "finalize_status"
        
        # Validate property ID
        if state.property_id <= 0:
            state.approval_status = "denied"
            state.risk_factors.append("Invalid property ID")
            return "finalize_status"
        
        # Validate registration data
        required_fields = ["email", "terms_accepted", "age_accepted"]
        missing_fields = [f for f in required_fields if f not in state.registration_data]
        
        if missing_fields:
            state.approval_status = "denied"
            state.risk_factors.append(f"Missing required fields: {', '.join(missing_fields)}")
            return "finalize_status"
        
        # Check terms acceptance
        if not state.registration_data.get("terms_accepted"):
            state.approval_status = "denied"
            state.risk_factors.append("Terms not accepted")
            return "finalize_status"
        
        if not state.registration_data.get("age_accepted"):
            state.approval_status = "denied"
            state.risk_factors.append("Age verification not accepted")
            return "finalize_status"
        
        print(f"✓ Input validation passed for {state.bidder_name}")
        return "check_property_status"
    
    async def check_property_status(self, state: BidderOnboardingState) -> str:
        """
        Step 2: Check property status and settings.
        
        Verifies the property is active and accepting registrations.
        Loads property settings for auto-approval logic.
        """
        state.workflow_steps.append("check_property_status")
        
        # TODO: Integrate with GRES agent to get property details
        # For now, simulate property check
        # In production: result = await gres_agent.get_property_detail(state.property_id)
        
        # Simulate property lookup
        state.property_details = {
            "property_id": state.property_id,
            "status_id": 1,  # 1 = active
            "is_approved": True,
            "name": f"Property {state.property_id}"
        }
        
        # Check if property is active
        if state.property_details.get("status_id") != 1:
            state.property_active = False
            state.approval_status = "denied"
            state.risk_factors.append("Property is not active")
            return "finalize_status"
        
        if not state.property_details.get("is_approved"):
            state.property_active = False
            state.approval_status = "denied"
            state.risk_factors.append("Property is not approved")
            return "finalize_status"
        
        state.property_active = True
        print(f"✓ Property {state.property_id} is active and accepting registrations")
        return "check_sam_compliance"
    
    async def check_sam_compliance(self, state: BidderOnboardingState) -> str:
        """
        Step 3: Check SAM.gov exclusions.
        
        Screens bidder against SAM.gov federal contract exclusions database.
        """
        state.workflow_steps.append("check_sam_compliance")
        
        print(f"→ Screening {state.bidder_name} against SAM.gov exclusions...")
        
        # Check SAM.gov directly against database
        with get_sam_db() as conn:
            cursor = conn.execute(
                """
                SELECT name, classification, excluding_agency, exclusion_type,
                       active_date, termination_date, record_status, sam_number
                FROM exclusions
                WHERE name LIKE ?
                AND (termination_date = 'Indefinite' OR termination_date >= date('now'))
                ORDER BY active_date DESC
                """,
                (f"%{state.bidder_name}%",)
            )
            
            rows = cursor.fetchall()
            
            if not rows:
                is_excluded = False
                exclusions = []
                message = f"No active exclusions found for '{state.bidder_name}'"
            else:
                is_excluded = True
                exclusions = []
                for row in rows:
                    exclusions.append({
                        "name": row["name"],
                        "classification": row["classification"],
                        "excluding_agency": row["excluding_agency"],
                        "exclusion_type": row["exclusion_type"],
                        "active_since": row["active_date"],
                        "termination_date": row["termination_date"],
                        "status": row["record_status"],
                        "sam_number": row["sam_number"]
                    })
                message = f"Found {len(exclusions)} active exclusion(s)"
        
        state.sam_check_result = {
            "bidder_name": state.bidder_name,
            "is_excluded": is_excluded,
            "active_exclusions": len(exclusions),
            "details": exclusions,
            "message": message,
            "check_timestamp": datetime.now(UTC).isoformat(),
            "database": "SAM.gov"
        }
        
        print(f"   SAM.gov search complete: {state.sam_check_result.get('active_exclusions', 0)} exclusions found")
        
        # Determine if passed
        if state.sam_check_result.get("is_excluded"):
            state.sam_passed = False
            state.risk_factors.append("Found on SAM.gov exclusions list")
            print("✗ SAM.gov check FAILED - bidder is excluded")
        else:
            state.sam_passed = True
            print("✓ SAM.gov check PASSED - no exclusions found")
        
        # Log check to audit trail
        state.checks_performed.append({
            "check_type": "SAM.gov Exclusions",
            "result": "PASS" if state.sam_passed else "FAIL",
            "timestamp": datetime.now(UTC).isoformat(),
            "details": state.sam_check_result
        })
        
        return "check_ofac_compliance"
    
    async def check_ofac_compliance(self, state: BidderOnboardingState) -> str:
        """
        Step 4: Check OFAC SDN list.
        
        Screens bidder against OFAC Specially Designated Nationals list
        with fuzzy matching.
        """
        state.workflow_steps.append("check_ofac_compliance")
        
        print(f"→ Screening {state.bidder_name} against OFAC SDN list...")
        
        # Helper functions for OFAC check
        def normalize_name(name: str) -> str:
            """Normalize name for fuzzy matching"""
            if not name:
                return ""
            name = name.lower()
            name = re.sub(r'[^\w\s]', ' ', name)
            name = re.sub(r'\s+', ' ', name)
            return name.strip()
        
        def calculate_similarity(str1: str, str2: str) -> float:
            """Calculate similarity ratio between two strings (0.0 to 1.0)"""
            return SequenceMatcher(None, str1, str2).ratio()
        
        # Set similarity threshold based on mode
        similarity_threshold = 0.85 if self.strict_mode else 0.60
        
        # Normalize the bidder name
        search_normalized = normalize_name(state.bidder_name)
        
        # Search OFAC database
        with get_ofac_db() as conn:
            cursor = conn.execute(
                """
                SELECT entity_id, name, entity_type, program, remarks, name_normalized
                FROM sdn_list 
                WHERE name_normalized LIKE ?
                LIMIT 100
                """,
                (f"%{search_normalized}%",)
            )
            rows = cursor.fetchall()
        
        # Calculate similarity scores
        potential_matches = []
        for row in rows:
            row_dict = dict_from_row(row)
            
            # Calculate similarity with both normalized and original names
            similarity_normalized = calculate_similarity(search_normalized, row_dict['name_normalized'])
            similarity_original = calculate_similarity(state.bidder_name.lower(), row_dict['name'].lower())
            
            # Use the higher similarity score
            similarity = max(similarity_normalized, similarity_original)
            
            if similarity >= similarity_threshold:
                row_dict['similarity_score'] = round(similarity, 3)
                row_dict.pop('name_normalized', None)
                potential_matches.append(row_dict)
        
        # Sort by similarity (highest first)
        potential_matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Determine eligibility
        if not potential_matches:
            # No matches found
            eligible = True
            confidence = 0.95
            risk_level = "LOW"
            requires_review = False
            recommendation = "No matches found in OFAC SDN list. Bidder appears eligible."
            highest_similarity = None
        else:
            # Matches found
            eligible = False
            highest_similarity = potential_matches[0]['similarity_score']
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
            
            requires_review = True
            recommendation = f"FLAGGED: Found {match_count} potential match(es) with {highest_similarity*100:.1f}% similarity. Risk Level: {risk_level}. MANUAL REVIEW REQUIRED."
        
        state.ofac_check_result = {
            "bidder_name": state.bidder_name,
            "eligible": eligible,
            "confidence": confidence,
            "matches": potential_matches[:10],
            "total_matches": len(potential_matches),
            "highest_similarity": highest_similarity,
            "risk_level": risk_level,
            "requires_review": requires_review,
            "recommendation": recommendation,
            "check_timestamp": datetime.now(UTC).isoformat(),
            "database": "OFAC SDN",
            "similarity_threshold": similarity_threshold
        }
        
        print(f"   OFAC search complete: {state.ofac_check_result.get('total_matches', 0)} potential matches")
        if state.ofac_check_result.get('matches'):
            print(f"   Highest similarity: {state.ofac_check_result.get('highest_similarity', 0)*100:.1f}%")
        
        # Determine if passed
        if not state.ofac_check_result.get("eligible"):
            state.ofac_passed = False
            state.risk_factors.append("Match found on OFAC SDN list")
            matches_count = state.ofac_check_result.get("total_matches", 0)
            print(f"✗ OFAC check FAILED - {matches_count} potential match(es) found")
        elif state.ofac_check_result.get("requires_review"):
            state.ofac_passed = True  # Technical pass, but needs review
            state.requires_manual_review = True
            state.risk_factors.append("Potential OFAC match requires manual review")
            print("⚠ OFAC check PASSED but requires manual review")
        else:
            state.ofac_passed = True
            print("✓ OFAC check PASSED - no matches found")
        
        # Log check to audit trail
        state.checks_performed.append({
            "check_type": "OFAC SDN List",
            "result": "PASS" if state.ofac_passed else "FAIL",
            "timestamp": datetime.now(UTC).isoformat(),
            "details": state.ofac_check_result
        })
        
        return "determine_eligibility"
    
    async def determine_eligibility(self, state: BidderOnboardingState) -> str:
        """
        Step 5: Determine overall eligibility.
        
        Applies business rules to combine compliance check results.
        Bidder must pass BOTH SAM and OFAC checks to be eligible.
        """
        state.workflow_steps.append("determine_eligibility")
        
        print("→ Determining overall eligibility...")
        
        # Business Rule: Must pass BOTH checks
        state.is_eligible = state.sam_passed and state.ofac_passed
        
        # Build compliance summary
        summary_parts = []
        if state.sam_passed:
            summary_parts.append("✓ SAM.gov: PASSED")
        else:
            summary_parts.append("✗ SAM.gov: FAILED")
        
        if state.ofac_passed:
            summary_parts.append("✓ OFAC: PASSED")
        else:
            summary_parts.append("✗ OFAC: FAILED")
        
        state.compliance_summary = " | ".join(summary_parts)
        
        # Always send to human review regardless of automated check results
        # This allows human override even if SAM/OFAC checks fail
        if not state.is_eligible:
            print(f"⚠ Automated checks FAILED: {state.compliance_summary}")
            print("  → Sending to human review for potential override")
        elif state.requires_manual_review:
            print(f"⚠ Bidder passes but REQUIRES MANUAL REVIEW: {state.compliance_summary}")
        else:
            print(f"✓ Bidder PASSED all automated checks: {state.compliance_summary}")
        
        # Always request human review - let humans make the final decision
        return "request_human_review"
    
    async def request_human_review(self, state: BidderOnboardingState) -> str:
        """
        Step 5.5: Request human review of eligibility results.
        
        Creates a human task for administrator review and pauses workflow execution.
        """
        state.workflow_steps.append("request_human_review")
        
        print("\n→ Requesting human review...")
        
        # Import create_human_task
        from agent_app.task_service import create_human_task
        
        # Create human task for review (this will raise TaskPendingException)
        # Human can approve even if automated checks fail
        await create_human_task(
            workflow_run_id=self.run_id,
            task_type='approval',
            title=f'Review Bidder: {state.bidder_name}',
            description=f'Review compliance checks for {state.bidder_name}. You can approve or deny this bidder regardless of automated check results. Your decision will override automated recommendations.',
            state=state,
            next_step='process_human_review',
            required_role='admin',
            input_data={
                'bidder_name': state.bidder_name,
                'property_id': state.property_id,
                'sam_check': 'PASSED' if state.sam_passed else 'FAILED',
                'ofac_check': 'PASSED' if state.ofac_passed else 'FAILED',
                'automated_eligible': state.is_eligible,
                'risk_factors': state.risk_factors,
                'compliance_summary': state.compliance_summary
            }
        )
        
        # Note: This function never returns normally - TaskPendingException is raised
        # When workflow resumes, it will start from process_human_review step
    
    async def process_human_review(self, state: BidderOnboardingState) -> str:
        """
        Step 5.6: Process human review results.
        
        Integrates the human reviewer's decision into the workflow.
        Human decision overrides automated check results.
        """
        state.workflow_steps.append("process_human_review")
        
        print("\n→ Processing human review...")
        
        if state.human_review_result:
            decision = state.human_review_result.get('decision')
            comments = state.human_review_result.get('comments', '')
            confidence = state.human_review_result.get('confidence', 'N/A')
            
            print(f"   Human Decision: {decision}")
            print(f"   Comments: {comments}")
            print(f"   Confidence: {confidence}")
            
            if decision == 'denied':
                # Human denied - final decision is NO
                state.is_eligible = False
                state.approval_status = "denied"
                state.compliance_summary += f"\n\n🚫 Human Review: DENIED (overrides automated checks)\nComments: {comments}"
                state.checks_performed.append({
                    'check_type': 'Human Review',
                    'result': 'DENIED',
                    'timestamp': datetime.now(UTC).isoformat(),
                    'details': {'comments': comments, 'confidence': confidence}
                })
                print("✗ Human reviewer DENIED the bidder")
            else:
                # Human approved - final decision is YES (overrides any failed automated checks)
                state.is_eligible = True
                state.approval_status = "approved"
                override_note = " (overriding automated checks)" if not state.sam_passed or not state.ofac_passed else ""
                state.compliance_summary += f"\n\n✓ Human Review: APPROVED{override_note}\nComments: {comments}"
                state.checks_performed.append({
                    'check_type': 'Human Review',
                    'result': 'APPROVED',
                    'timestamp': datetime.now(UTC).isoformat(),
                    'details': {'comments': comments, 'confidence': confidence, 'overridden': not (state.sam_passed and state.ofac_passed)}
                })
                print(f"✓ Human reviewer APPROVED the bidder{override_note}")
        else:
            print("⚠ No human review result found, continuing with original eligibility")
        
        # Skip auto-approval check - go directly to finalize since human has made the decision
        return "finalize_status"
    
    async def finalize_status(self, state: BidderOnboardingState) -> str:
        """
        Step 6: Finalize approval status.
        
        Prepares final status message, sets bid limits for approved bidders,
        and creates notification data.
        """
        state.workflow_steps.append("finalize_status")
        
        print("\n→ Finalizing bidder status...")
        
        # Set bid limit for approved bidders
        if state.approval_status == "approved" and not state.bid_limit:
            state.bid_limit = 1000000.0  # Default $1M limit for approved bidders
            print(f"   Set default bid limit: ${state.bid_limit:,.2f}")
        
        # Build final status message
        if state.approval_status == "approved":
            message = f"✅ APPROVED: {state.bidder_name} is approved to bid on Property {state.property_id}"
            if state.bid_limit:
                message += f" with a ${state.bid_limit:,.2f} bid limit"
            if state.risk_factors:
                message += f"\n⚠️ Note: Approved despite flags: {', '.join(state.risk_factors)}"
        elif state.approval_status == "denied":
            message = f"❌ DENIED: {state.bidder_name} registration denied for Property {state.property_id}"
            if state.risk_factors:
                message += f"\nReasons: {', '.join(state.risk_factors)}"
        else:  # pending or review_required (shouldn't reach here with new flow)
            message = f"⏳ PENDING: {state.bidder_name} registration pending for Property {state.property_id}"
        
        print(f"\n{message}")
        
        # Prepare notification
        state.notifications_sent.append({
            "recipient": state.registration_data.get("email", "unknown"),
            "message_type": state.approval_status,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat()
        })
        
        return "create_audit_log"
    
    async def create_audit_log(self, state: BidderOnboardingState) -> str:
        """
        Step 8: Create comprehensive audit log.
        
        Final step that documents all workflow execution details
        for compliance and audit purposes.
        """
        state.workflow_steps.append("create_audit_log")
        
        print("\n→ Creating audit trail...")
        
        audit_log = {
            "workflow": "Bidder Onboarding & Verification",
            "bidder_name": state.bidder_name,
            "property_id": state.property_id,
            "timestamp": state.timestamp,
            "execution_duration_ms": "N/A",  # Would calculate in production
            "steps_executed": state.workflow_steps,
            "checks_performed": state.checks_performed,
            "compliance_summary": state.compliance_summary,
            "risk_factors": state.risk_factors,
            "final_status": state.approval_status,
            "is_eligible": state.is_eligible,
            "requires_manual_review": state.requires_manual_review,
            "auto_approval_enabled": state.auto_approval_enabled,
            "bid_limit": state.bid_limit,
            "notifications_sent": state.notifications_sent
        }
        
        # TODO: In production, save to database or logging system
        print("✓ Audit log created")
        return None


# ===== Standalone =====

if __name__ == "__main__":
    print("Run this workflow via the API or UI (BPMN-driven execution).")
