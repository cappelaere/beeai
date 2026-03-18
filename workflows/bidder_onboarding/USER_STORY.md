# User Story: Bidder Onboarding & Verification Workflow

## Story ID
**US-001** - Automated Bidder Onboarding with Compliance Screening

## As a...
**Real Estate Platform Administrator**

## I want to...
Automatically verify and approve bidder registrations by screening against government exclusion lists and sanctions databases in real-time

## So that...
We ensure only compliant bidders participate in auctions while reducing manual verification time from hours to seconds and maintaining regulatory compliance

---

## Business Value

### Primary Benefits
- **Time Savings**: Reduces compliance screening from 2-4 hours to < 5 seconds, with human review for all final approvals
- **Risk Mitigation**: Eliminates human error in compliance screening while requiring human oversight for all final decisions
- **Regulatory Compliance**: Ensures 100% screening against SAM.gov (138K exclusions) and OFAC SDN list (18K records)
- **Scalability**: Handles unlimited concurrent registrations with automated screening, human review required for all bidders
- **Audit Trail**: Complete logging of all automated checks and human decisions for compliance reporting
- **Human Override**: Allows administrators to approve bidders even if automated checks fail, with full documentation of override rationale

### ROI Impact
- **Staff Time**: Automate compliance screening (~1.5 hours per registration) + streamlined human review (~15 minutes) × 100 registrations/month = 165 hours/month saved
- **Risk Avoidance**: Prevent potential fines ($10K-$500K per violation) for accepting sanctioned bidders with 100% screening coverage
- **Customer Experience**: Near-instant screening with human review for approvals balances speed and security
- **Compliance Quality**: Human oversight ensures nuanced decisions while automation handles tedious data checks

### Success Metrics
- Automated processing time < 5 seconds (target: 3 seconds)
- Human review response time < 24 hours (target: 4 hours)
- 100% coverage of SAM.gov and OFAC checks
- Zero false negatives (missing sanctioned entities)
- < 2% false positives (legitimate bidders flagged for review)
- 100% audit trail completeness including human decisions
- Task completion rate > 95% (< 5% expired)

---

## Acceptance Criteria

### Functional Requirements

#### 1. Input Validation
- **Given** a bidder registration request
- **When** the system receives bidder information
- **Then** it must validate:
  - ✅ Bidder name is provided and non-empty
  - ✅ Property ID exists and is active
  - ✅ Email format is valid (if provided)
  - ✅ Phone number format is acceptable (if provided)
  - ✅ Required terms are accepted

#### 2. Property Verification
- **Given** a valid bidder registration
- **When** checking the associated property
- **Then** the system must:
  - ✅ Verify property exists in the system
  - ✅ Confirm property is active and accepting bids
  - ✅ Deny registration if property is inactive or closed

#### 3. SAM.gov Exclusion Check
- **Given** a validated bidder with active property
- **When** screening against SAM.gov exclusion list
- **Then** the system must:
  - ✅ Search all 138K+ SAM.gov exclusion records
  - ✅ Match on exact and fuzzy name matches
  - ✅ Check both individual and business names
  - ✅ Flag any matches for immediate denial
  - ✅ Complete search in < 2 seconds

#### 4. OFAC SDN Sanctions Check
- **Given** a bidder who passed SAM.gov check
- **When** screening against OFAC SDN list
- **Then** the system must:
  - ✅ Search all 18K+ OFAC SDN records
  - ✅ Match on name, aliases, and variations
  - ✅ Check both Specially Designated Nationals and blocked entities
  - ✅ Flag any matches for immediate denial
  - ✅ Complete search in < 2 seconds

#### 5. Human Review Task (Always Required)
- **Given** a bidder who completed automated compliance checks (regardless of pass/fail)
- **When** eligibility is determined
- **Then** the system must:
  - ✅ Create a human review task with approval form for ALL bidders
  - ✅ Pause workflow execution and save state
  - ✅ Display task in administrator's task queue
  - ✅ Show all compliance check results (SAM, OFAC) with pass/fail status
  - ✅ Display risk factors and flags if any exist
  - ✅ Allow administrator to approve or deny with comments
  - ✅ Support human override: can approve even if automated checks failed
  - ✅ Automatically resume workflow when task is completed
  - ✅ Integrate human decision into workflow results
  - ✅ Document override rationale if automated checks were failed

#### 6. Final Status Logic
- **Given** a human reviewer has made their decision
- **When** finalizing bidder status
- **Then** the system must:
  - ✅ Apply human decision (approve/deny) as final outcome
  - ✅ Assign default bid limit ($1M) if approved
  - ✅ Include risk factors in approval message if any were flagged
  - ✅ Document override if human approved despite failed automated checks
  - ✅ Log final decision to audit trail with override notation

#### 7. Audit Logging
- **Given** any bidder registration attempt
- **When** the workflow completes (approved, denied, or flagged)
- **Then** the system must:
  - ✅ Log all input parameters
  - ✅ Log all screening results (SAM.gov and OFAC)
  - ✅ Log final decision and reason
  - ✅ Include timestamp and workflow execution ID
  - ✅ Store in immutable audit log

### Non-Functional Requirements

#### Performance
- ✅ Total processing time < 5 seconds (target: 3 seconds)
- ✅ Support 100+ concurrent registrations
- ✅ 99.9% uptime SLA
- ✅ Graceful degradation if external APIs are slow

#### Security
- ✅ Encrypt all PII (names, emails, phone numbers)
- ✅ Secure API calls to SAM.gov and OFAC databases
- ✅ No storage of raw compliance data
- ✅ Role-based access for manual review queue

#### Compliance
- ✅ 100% screening coverage (no skipped checks)
- ✅ Complete audit trail for all decisions
- ✅ Daily sync with SAM.gov and OFAC lists
- ✅ Compliance report generation capability

#### User Experience
- ✅ Clear status messages for all outcomes
- ✅ Explanation of denial reasons
- ✅ Immediate feedback (< 5 seconds)
- ✅ Retry capability for transient failures

---

## User Flow

### Happy Path (All Checks Pass, Human Approves)
1. Bidder submits registration form with name, property ID, and contact info
2. System validates input fields → ✅ Valid
3. System checks property status → ✅ Active
4. System screens against SAM.gov → ✅ Not found (clear)
5. System screens against OFAC SDN → ✅ Not found (clear)
6. **System creates human review task** → ⏸️ Workflow pauses
7. **Administrator reviews compliance results** → ✅ Approves
8. **System automatically resumes workflow**
9. System finalizes approval status with $1M bid limit
10. System logs audit trail
11. Bidder receives approval notification

**Expected Time**: 3-5 seconds (automated) + human review time

### Human Override Path (Automated Checks Fail, Human Approves)
1. Bidder submits registration form
2. System validates input → ✅ Valid
3. System checks property → ✅ Active
4. System screens against SAM.gov → ❌ Match found OR ⚠️ Flagged
5. System screens against OFAC SDN → ❌ Match found OR ⚠️ Flagged
6. **System still creates human review task** → ⏸️ Workflow pauses
7. **Administrator reviews failed checks and risk factors** → ✅ Approves with override rationale
8. **System automatically resumes workflow**
9. System finalizes as APPROVED (with override notation and risk factors documented)
10. System logs audit trail including override rationale
11. Bidder receives approval notification

**Expected Time**: 3-5 seconds (automated) + human review time

**Note**: This allows human judgment to override false positives or approve bidders with acceptable risk factors.

### Human Denial Path (Any Check Result, Human Denies)
1. Bidder submits registration form
2. System validates input → ✅ Valid
3. System checks property → ✅ Active
4. System screens against SAM.gov → (any result)
5. System screens against OFAC SDN → (any result)
6. **System creates human review task** → ⏸️ Workflow pauses
7. **Administrator reviews compliance results** → ❌ Denies with comments
8. **System automatically resumes workflow**
9. System marks bidder as DENIED
10. System logs audit trail with human review notes
11. Bidder receives denial notification

**Expected Time**: 3-5 seconds (automated) + human review time

### Invalid Input Path (Immediate Rejection)
1. Bidder submits registration form with invalid/missing data
2. System validates input → ❌ Invalid
3. System immediately rejects (no compliance checks needed)
4. System logs audit trail
5. Bidder receives error message

**Expected Time**: < 1 second

---

## Human Task System

### Task Lifecycle
1. **Created (Open)**: Task is created by workflow and appears in task queue
2. **Claimed (In Progress)**: Administrator claims task and begins review
3. **Completed**: Administrator submits approval/denial decision
4. **Workflow Resumes**: System automatically restarts workflow with task results
5. **Audit**: Task completion and decision logged to database

### Task Properties
- **Task ID**: 8-character unique identifier (e.g., "a1b2c3d4")
- **Task Type**: Approval form with decision, comments, and confidence rating
- **Required Role**: Admin (only administrators can review bidder approvals)
- **Expiration**: Tasks expire after 7 days if not completed
- **Assignment**: Tasks can be claimed by any user with sufficient role permissions
- **Context**: Full compliance check results displayed in task form

### Task Management UI
- **My Tasks**: Navigation item showing all tasks assigned to or accessible by current user
- **Badge Counter**: Real-time count of open/in-progress tasks
- **Task List**: Filterable table of all tasks with status, type, and workflow links
- **Task Detail**: Form showing workflow context and decision inputs
- **Workflow Integration**: Links between tasks and workflow runs for full traceability

---

## Technical Implementation Notes

### Input Schema
```yaml
bidder_name: string (required) - Full legal name
property_id: integer (required) - Property to bid on
email: email (optional) - Contact email
phone: string (optional) - Contact phone
user_type: enum (optional) - Investor|Agent|Individual|Corporation
terms_accepted: boolean (optional, default: true)
age_accepted: boolean (optional, default: true)
```

### Output States
- **APPROVED**: Human approved bidder (may override failed automated checks)
- **DENIED**: Human denied bidder (based on automated checks or independent judgment)
- **ERROR**: System error, retry needed

**Note**: All valid bidders go through human review. Automated checks inform but do not determine the final decision.

### Integration Points
- SAM.gov Exclusion API
- OFAC SDN List API
- Property Management System
- Audit Logging Service
- Notification Service

### Workflow Diagram Required
- Flowchart showing all decision points
- Visual representation of validation, screening, and approval paths
- Color coding: Green (approved), Red (denied), Yellow (review)

---

## Testing Scenarios

### Test Case 1: Clean Bidder, Human Approves
- Input: Clean bidder name + active property
- Expected: Automated checks pass → Human review task created → Admin approves → APPROVED with $1M limit
- Time: 3-5 seconds (automated) + human review time

### Test Case 2: SAM.gov Match, Human Overrides
- Input: Name matching SAM.gov exclusion list + active property
- Expected: SAM check fails → Human review task created with failure warning → Admin reviews and approves with override rationale → APPROVED with override documented
- Time: 3-5 seconds (automated) + human review time

### Test Case 3: OFAC Match, Human Overrides
- Input: Name matching OFAC SDN list + active property
- Expected: OFAC check fails → Human review task created with failure warning → Admin reviews and approves with override rationale → APPROVED with override documented
- Time: 3-5 seconds (automated) + human review time

### Test Case 4: Clean Bidder, Human Denies
- Input: Clean bidder passing all automated checks
- Expected: All checks pass → Human review task created → Admin denies with rationale → DENIED
- Time: 3-5 seconds (automated) + human review time

### Test Case 5: Inactive Property (No Human Review)
- Input: Valid bidder + inactive property
- Expected: DENIED immediately at property check (no compliance checks or human review)
- Time: < 1 second

### Test Case 6: Invalid Input (No Human Review)
- Input: Missing bidder name
- Expected: DENIED immediately at validation (no compliance checks or human review)
- Time: < 1 second

### Test Case 7: Multiple Risk Factors, Human Approves
- Input: Bidder with partial SAM match + flagged OFAC similarity
- Expected: Both checks flag concerns → Human review task created with all flags → Admin reviews risk factors and approves with explanation → APPROVED with documented override
- Time: 3-5 seconds (automated) + human review time

### Test Case 8: Human Review - Task Expiration
- Input: Valid bidder with uncompleted task past 7 days
- Expected: Task expires → Workflow marked as failed with expiration reason
- Time: N/A (time-based test)

### Test Case 9: Both Checks Fail, Human Still Approves (Override Test)
- Input: Bidder name matching both SAM exclusion and OFAC SDN lists
- Expected: Both checks fail → Human review task created showing all failures → Admin investigates, determines false positive, approves with detailed explanation → APPROVED with full override documentation in audit trail
- Time: 3-5 seconds (automated) + human review time

**Note**: This tests the critical human override capability to handle false positives in automated screening.

---

## Documentation Requirements

### User-Facing Documentation
- How to register as a bidder
- What compliance checks are performed
- Why registrations may be denied
- How to appeal a denial
- How long approval takes

### Technical Documentation
- API integration details (SAM.gov, OFAC)
- Workflow state machine diagram
- Error handling procedures
- Monitoring and alerting setup
- Audit log schema and retention

### Compliance Documentation
- Regulatory requirements met
- Screening methodology
- Audit trail capabilities
- Compliance reporting procedures
- Data retention policies

---

## Dependencies

### External Systems
- SAM.gov API access and credentials
- OFAC SDN list access
- Property management database

### Internal Systems
- BeeAI workflow engine with human task support
- Human task management system (Django Channels + WebSockets)
- Audit logging infrastructure
- Notification service
- Admin review dashboard with task queue

---

## Definition of Done

- ✅ All acceptance criteria met and tested
- ✅ Workflow completes in < 5 seconds
- ✅ Unit tests achieve 90%+ coverage
- ✅ Integration tests with SAM.gov and OFAC pass
- ✅ Audit logging fully implemented
- ✅ Mermaid workflow diagram created
- ✅ User documentation written
- ✅ Technical documentation complete
- ✅ Code reviewed and approved
- ✅ Deployed to production
- ✅ Monitoring and alerting configured

---

## Future Enhancements (Out of Scope)

- International sanctions list screening (EU, UN)
- Real-time watch list updates
- Machine learning for fuzzy matching
- Batch registration processing
- White-label partner integration
- Mobile app registration support
