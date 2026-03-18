# Workflow Creation Guidelines

Guidelines for designing and implementing workflows in RealtyIQ.

---

## Workflow Design Principles

### 1. Clear Objective

Every workflow should have **one clear goal**:

**Good Examples:**
- "Verify bidder eligibility for federal contracts"
- "Onboard new property listing with compliance checks"
- "Complete post-auction transfer process"

**Bad Examples:**
- "Handle everything related to bidders"
- "Manage properties and auctions"
- "General administrative workflow"

**Why:** Clear objectives make workflows easier to understand, test, and maintain.

---

### 2. Logical Steps

Break processes into discrete, sequential steps:

**Example: Bidder Onboarding**
```
Step 1: Collect bidder information
Step 2: SAM.gov exclusions check
Step 3: OFAC sanctions screening
Step 4: Identity document verification
Step 5: Human review (if flags raised)
Step 6: Final approval/rejection
```

**Each step should:**
- Have a clear input and output
- Be independently testable
- Have defined success/failure criteria
- Be resumable if interrupted

---

### 3. Human-in-the-Loop

Identify where human judgment is required:

**Automated Steps** (no human needed):
- Database lookups
- API calls
- Data validation
- Simple calculations
- Status checks

**Human Review Steps** (requires task):
- Ambiguous compliance matches
- Final approval decisions
- Document quality review
- Exception handling
- Policy interpretations

**Rule of thumb:** If decision requires judgment, create a task.

---

## Workflow Structure

### Directory Layout

```
workflows/
└── workflow_name/
    ├── __init__.py           # Python package marker
    ├── metadata.yaml         # Workflow description
    ├── workflow.py          # Main workflow implementation
    ├── tasks/               # Task templates (optional)
    │   └── review_task.md
    └── README.md            # Documentation (optional)
```

---

### metadata.yaml Format

```yaml
id: workflow_name
name: "Workflow Display Name"
description: "Clear description of what this workflow accomplishes"
version: "1.0"
author: "Team/Person"
category: "verification"  # or: onboarding, analysis, approval, etc.

parameters:
  - name: param1
    type: string
    description: "Parameter description"
    required: true
    
  - name: param2
    type: string
    description: "Optional parameter"
    required: false
    default: "default_value"

steps:
  - step: 1
    name: "Step Name"
    description: "What this step does"
    agent: agent_id  # Which agent handles this step
    
  - step: 2
    name: "Another Step"
    description: "What this step does"
    requires_human: true  # Indicates human task

outputs:
  - success_result: "What happens on success"
  - failure_result: "What happens on failure"

estimated_duration: "5-10 minutes"
requires_admin: false
```

---

### workflow.py Structure

```python
"""
Workflow Name - Description
"""

from beeai_framework.workflows import Workflow, WorkflowStep
from agents.registry import load_agents_registry
import logging

logger = logging.getLogger(__name__)


class WorkflowNameWorkflow(Workflow):
    """Workflow description."""
    
    def __init__(self):
        super().__init__(
            name="workflow_name",
            description="What this workflow does"
        )
    
    async def execute(self, context: dict) -> dict:
        """
        Execute the workflow.
        
        Args:
            context: Workflow execution context with parameters
            
        Returns:
            dict: Results with status and data
        """
        # Extract parameters
        param1 = context.get('param1')
        param2 = context.get('param2', 'default')
        
        # Validate inputs
        if not param1:
            return {
                'status': 'error',
                'message': 'param1 is required'
            }
        
        # Step 1: Do something
        result1 = await self._step_one(param1)
        if not result1['success']:
            return self._error_response('Step 1 failed', result1)
        
        # Step 2: Do something else
        result2 = await self._step_two(result1['data'])
        if not result2['success']:
            return self._error_response('Step 2 failed', result2)
        
        # Step 3: Create human task if needed
        if result2.get('needs_review'):
            task_id = await self._create_review_task(result2['data'])
            return {
                'status': 'pending',
                'message': 'Human review required',
                'task_id': task_id
            }
        
        # Success
        return {
            'status': 'success',
            'message': 'Workflow completed',
            'data': result2['data']
        }
    
    async def _step_one(self, param1: str) -> dict:
        """First workflow step."""
        try:
            # Step logic
            result = do_something(param1)
            return {'success': True, 'data': result}
        except Exception as e:
            logger.error(f"Step 1 failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _step_two(self, data: dict) -> dict:
        """Second workflow step."""
        # Step logic
        pass
    
    async def _create_review_task(self, data: dict) -> str:
        """Create a human review task."""
        # Task creation logic
        pass
    
    def _error_response(self, message: str, details: dict) -> dict:
        """Standardized error response."""
        return {
            'status': 'error',
            'message': message,
            'details': details
        }
```

---

## Agent Integration

### Calling Agents from Workflows

**Method 1: Direct Tool Usage**
```python
from tools.gres_tools import list_properties

async def _check_properties(self, criteria: dict):
    """Use tools directly."""
    properties = list_properties(**criteria)
    return properties
```

**Method 2: Agent Invocation**
```python
from agents.registry import get_agent_by_id

async def _run_sam_check(self, entity_name: str):
    """Invoke specialized agent."""
    sam_agent = get_agent_by_id('sam')
    result = await sam_agent.execute(
        prompt=f"Check if {entity_name} is excluded"
    )
    return result
```

**When to use each:**
- Direct tools: Simple, single tool call
- Agent invocation: Complex queries requiring agent reasoning

---

## Task Management

### Creating Tasks

```python
from tools.workflow_tools import create_task

task_id = create_task(
    workflow_run_id=run_id,
    task_type="review",
    title="Review Bidder Verification Results",
    description="Manual review required for flagged bidder",
    data={
        'bidder_name': 'ABC Corp',
        'sam_result': 'PASS',
        'ofac_result': 'FLAGGED',
        'match_score': 0.85,
        'details': ofac_details
    },
    assigned_role="compliance_officer"
)
```

---

### Task Data Structure

**Include in task data:**
- **Context**: What is being reviewed
- **Findings**: Results from automated checks
- **Options**: Available decisions (approve/reject/escalate)
- **Criteria**: What to look for
- **References**: Links to source data

**Example:**
```python
task_data = {
    'entity_name': 'XYZ Corporation',
    'verification_type': 'bidder_onboarding',
    'automated_checks': {
        'sam': {'status': 'PASS', 'checked_at': '2026-02-21T10:30:00Z'},
        'ofac': {'status': 'FLAGGED', 'match_score': 0.78, 'reason': 'Name similarity'}
    },
    'documents': [
        {'name': 'business_license.pdf', 'url': '/media/docs/123.pdf'},
        {'name': 'id_verification.pdf', 'url': '/media/docs/124.pdf'}
    ],
    'decision_options': ['approve', 'reject', 'escalate'],
    'review_criteria': 'Verify OFAC match is false positive',
    'notes_required': True
}
```

---

## State Management

### Workflow State

Track workflow progress:

```python
class WorkflowRun:
    """Workflow execution instance."""
    
    run_id: str           # Unique run identifier
    workflow_id: str      # Which workflow
    status: str           # pending, in_progress, completed, failed
    started_at: datetime
    completed_at: datetime
    parameters: dict      # Input parameters
    results: dict         # Output results
    current_step: int     # Progress tracking
    error_message: str    # If failed
```

---

### Step State

Track individual step outcomes:

```python
step_results = {
    'step_1': {
        'status': 'completed',
        'result': 'PASS',
        'executed_at': '2026-02-21T10:30:00Z',
        'duration_ms': 1234
    },
    'step_2': {
        'status': 'completed',
        'result': 'FLAGGED',
        'executed_at': '2026-02-21T10:30:05Z',
        'duration_ms': 5678,
        'details': {...}
    },
    'step_3': {
        'status': 'pending',
        'waiting_for': 'TASK_123'
    }
}
```

---

## Error Handling

### Graceful Degradation

```python
async def execute(self, context: dict):
    """Execute workflow with error handling."""
    
    try:
        # Step 1: Critical step
        result1 = await self._critical_step()
        if not result1['success']:
            return self._fail_workflow('Critical step failed', result1)
        
        # Step 2: Non-critical step
        try:
            result2 = await self._optional_step()
        except Exception as e:
            logger.warning(f"Optional step failed: {e}")
            result2 = self._default_result()
        
        # Continue with results
        return self._complete_workflow(result1, result2)
        
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        return {
            'status': 'error',
            'message': 'Workflow encountered an error',
            'error': str(e),
            'recoverable': True  # Can retry
        }
```

---

### Retry Logic

```python
async def _step_with_retry(self, data: dict, max_retries: int = 3):
    """Execute step with retry on failure."""
    
    for attempt in range(max_retries):
        try:
            result = await self._execute_step(data)
            return {'success': True, 'result': result}
        
        except TemporaryError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Step failed (attempt {attempt+1}), retrying...")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Step failed after {max_retries} attempts")
                return {'success': False, 'error': str(e)}
        
        except PermanentError as e:
            # Don't retry permanent failures
            logger.error(f"Permanent failure: {e}")
            return {'success': False, 'error': str(e)}
```

---

## Real-Time Updates

### Server-Sent Events (SSE)

Provide progress updates to users:

```python
from django.http import StreamingHttpResponse

def workflow_progress_stream(request, run_id):
    """Stream workflow progress via SSE."""
    
    def event_stream():
        workflow_run = get_workflow_run(run_id)
        
        while workflow_run.status == 'in_progress':
            # Yield current status
            yield f"data: {json.dumps({
                'step': workflow_run.current_step,
                'message': workflow_run.status_message,
                'progress': workflow_run.progress_percent
            })}\n\n"
            
            # Wait before next update
            time.sleep(1)
            workflow_run = get_workflow_run(run_id)
        
        # Final status
        yield f"data: {json.dumps({
            'status': workflow_run.status,
            'results': workflow_run.results
        })}\n\n"
    
    return StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
```

---

### Frontend SSE Handler

```javascript
function subscribeToWorkflowUpdates(runId) {
    const eventSource = new EventSource(`/api/workflows/runs/${runId}/stream/`);
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.status === 'completed' || data.status === 'failed') {
            eventSource.close();
            displayFinalResults(data);
        } else {
            updateProgressUI(data);
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('SSE error:', error);
        eventSource.close();
    };
}
```

---

## Workflow Patterns

### Pattern 1: Linear Verification

Sequential checks with early exit:

```
START
  ↓
Check 1 → FAIL → END (Rejected)
  ↓ PASS
Check 2 → FAIL → END (Rejected)
  ↓ PASS
Check 3 → FAIL → END (Rejected)
  ↓ PASS
END (Approved)
```

**Example:** Bidder Onboarding
- SAM check → FAIL = reject immediately
- OFAC check → FAIL = reject immediately
- Identity check → FAIL = reject immediately
- All PASS = approve

---

### Pattern 2: Parallel Verification

Multiple checks run simultaneously:

```
       START
       ↓
   ┌───┼───┐
   ↓   ↓   ↓
Check1 Check2 Check3
   ↓   ↓   ↓
   └───┼───┘
       ↓
   Aggregate
       ↓
      END
```

**Example:** Property Analysis
- Title search (parallel)
- Environmental check (parallel)
- Market analysis (parallel)
→ Combine results → Final report

**Benefit:** Faster execution (3 steps in parallel vs. sequential)

---

### Pattern 3: Multi-Stage Approval

Progressive approval with escalation:

```
START
  ↓
Auto Checks
  ↓
Reviewer → Approve → END
  ↓ Reject
Escalate
  ↓
Supervisor → Approve → END
  ↓ Reject
END (Rejected)
```

**Example:** High-Value Property Listing
- Step 1: Auto-validation
- Step 2: Specialist review
- Step 3: If issues, manager approval
- Step 4: If major issues, director approval

---

### Pattern 4: Conditional Branching

Different paths based on conditions:

```
START
  ↓
Check Value
  ↓
< $100K ──→ Fast Track → END
  ↓
< $1M ────→ Standard Review → END
  ↓
≥ $1M ────→ Enhanced Review → END
```

**Example:** Contract Approval
- Small value: Auto-approve
- Medium value: Single reviewer
- High value: Multi-level approval

---

## Task Design

### Task Types

**1. Binary Decision:**
```yaml
type: approval
options: [approve, reject]
requires_notes: false
```

**2. Multi-Option:**
```yaml
type: selection
options: [approve, reject, escalate, request_more_info]
requires_notes: true
```

**3. Data Entry:**
```yaml
type: data_entry
fields:
  - name: verified_amount
    type: number
  - name: notes
    type: text
```

**4. Document Review:**
```yaml
type: document_review
documents: [url1, url2, url3]
checklist:
  - "Document is legible"
  - "Signature present"
  - "Date is current"
options: [approve, reject]
```

---

### Task Template Example

```markdown
# Review Bidder Verification Results

## Task Information
- **Workflow**: Bidder Onboarding
- **Step**: Final Review
- **Created**: {{ created_at }}
- **Assigned Role**: Compliance Officer

## Bidder Details
- **Name**: {{ bidder_name }}
- **Entity Type**: {{ entity_type }}
- **Contact**: {{ contact_email }}

## Verification Results

### SAM.gov Check
- **Status**: {{ sam_status }}
- **Details**: {{ sam_details }}

### OFAC Screening
- **Status**: {{ ofac_status }}
- **Match Score**: {{ ofac_match_score }}
- **Details**: {{ ofac_details }}

### Identity Verification
- **Documents**: {{ id_documents }}
- **Status**: {{ id_status }}

## Decision Required

Please review the verification results and make a decision:
- **Approve**: All checks passed, bidder is eligible
- **Reject**: Failed checks, bidder is not eligible
- **Escalate**: Uncertain, needs supervisor review

## Notes
{{ task_notes }}
```

---

## Implementation Examples

### Example 1: Simple Linear Workflow

**Scenario:** Email notification workflow

```python
class EmailNotificationWorkflow(Workflow):
    """Send email notifications for auction events."""
    
    async def execute(self, context: dict):
        auction_id = context['auction_id']
        event_type = context['event_type']
        
        # Step 1: Get auction details
        auction = await self._get_auction(auction_id)
        
        # Step 2: Get recipient list
        recipients = await self._get_recipients(auction, event_type)
        
        # Step 3: Generate email content
        email_content = self._generate_email(auction, event_type)
        
        # Step 4: Send emails
        sent_count = await self._send_emails(recipients, email_content)
        
        return {
            'status': 'success',
            'sent': sent_count,
            'recipients': len(recipients)
        }
```

---

### Example 2: Workflow with Human Task

**Scenario:** Property listing approval

```python
class PropertyListingWorkflow(Workflow):
    """Multi-step property listing with approval."""
    
    async def execute(self, context: dict):
        property_id = context['property_id']
        
        # Step 1: Validate property data
        validation = await self._validate_property(property_id)
        if not validation['valid']:
            return {'status': 'rejected', 'reason': validation['errors']}
        
        # Step 2: Run automated checks
        checks = await self._run_automated_checks(property_id)
        
        # Step 3: Create approval task
        task_id = await self._create_approval_task(property_id, checks)
        
        return {
            'status': 'pending',
            'message': 'Awaiting review',
            'task_id': task_id
        }
    
    async def _create_approval_task(self, property_id: str, checks: dict):
        """Create task for specialist review."""
        return create_task(
            workflow_run_id=self.run_id,
            task_type="property_listing_approval",
            title=f"Approve Property Listing {property_id}",
            description="Review property details and approve for listing",
            data={
                'property_id': property_id,
                'validation_results': checks,
                'decision_options': ['approve', 'reject', 'request_changes']
            },
            assigned_role='real_estate_specialist'
        )
```

---

### Example 3: Parallel Execution

**Scenario:** Comprehensive property report

```python
import asyncio

class PropertyReportWorkflow(Workflow):
    """Generate comprehensive property report with parallel checks."""
    
    async def execute(self, context: dict):
        property_id = context['property_id']
        
        # Run multiple checks in parallel
        results = await asyncio.gather(
            self._title_search(property_id),
            self._environmental_check(property_id),
            self._market_analysis(property_id),
            self._comparable_sales(property_id),
            return_exceptions=True  # Don't fail all if one fails
        )
        
        title, environmental, market, comps = results
        
        # Check for errors
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            logger.warning(f"Some checks failed: {errors}")
        
        # Compile report
        report = self._compile_report(title, environmental, market, comps)
        
        return {
            'status': 'success',
            'report': report,
            'warnings': [str(e) for e in errors] if errors else []
        }
```

---

## Best Practices

### 1. Parameter Validation

Always validate inputs at the start:

```python
async def execute(self, context: dict):
    # Validate required parameters
    required = ['param1', 'param2']
    missing = [p for p in required if p not in context]
    if missing:
        return {
            'status': 'error',
            'message': f'Missing required parameters: {", ".join(missing)}'
        }
    
    # Validate parameter types and values
    if not isinstance(context['param1'], str):
        return {'status': 'error', 'message': 'param1 must be a string'}
    
    if context['param2'] not in ['option1', 'option2']:
        return {'status': 'error', 'message': 'param2 must be option1 or option2'}
    
    # Proceed with validated parameters
    ...
```

---

### 2. Comprehensive Logging

Log all important steps:

```python
async def execute(self, context: dict):
    logger.info(f"Starting workflow {self.name} with context: {context}")
    
    # Step 1
    logger.info("Executing step 1: SAM check")
    result1 = await self._step_one()
    logger.info(f"Step 1 result: {result1['status']}")
    
    # Step 2
    logger.info("Executing step 2: OFAC screen")
    result2 = await self._step_two()
    logger.info(f"Step 2 result: {result2['status']}")
    
    logger.info(f"Workflow {self.name} completed with status: {final_status}")
    return final_result
```

---

### 3. Idempotency

Workflows should be safely re-runnable:

```python
async def _step_one(self, context: dict):
    """Idempotent step - can run multiple times safely."""
    
    # Check if step already completed
    if context.get('step1_completed'):
        logger.info("Step 1 already completed, using cached result")
        return context['step1_result']
    
    # Execute step
    result = await self._do_work()
    
    # Store result for idempotency
    context['step1_completed'] = True
    context['step1_result'] = result
    
    return result
```

---

### 4. Progress Tracking

Provide visibility into workflow status:

```python
async def execute(self, context: dict):
    total_steps = 5
    
    for step_num in range(1, total_steps + 1):
        # Update progress
        self.update_progress(
            current_step=step_num,
            total_steps=total_steps,
            message=f"Executing step {step_num}"
        )
        
        # Execute step
        result = await self._execute_step(step_num, context)
        
        if not result['success']:
            break
    
    return final_result
```

---

## Testing Workflows

### Unit Tests

Test individual steps:

```python
import pytest

@pytest.mark.asyncio
async def test_sam_check_step():
    workflow = BidderOnboardingWorkflow()
    result = await workflow._sam_check('ABC Corp')
    
    assert result['success'] == True
    assert result['status'] in ['PASS', 'FAIL']
    assert 'details' in result
```

---

### Integration Tests

Test full workflow execution:

```python
@pytest.mark.asyncio
async def test_full_bidder_workflow():
    workflow = BidderOnboardingWorkflow()
    
    context = {
        'entity_name': 'Test Corporation',
        'contact_email': 'test@example.com'
    }
    
    result = await workflow.execute(context)
    
    assert result['status'] in ['success', 'pending', 'failed']
    if result['status'] == 'pending':
        assert 'task_id' in result
```

---

### E2E Tests

Test via user interface:

```python
def test_workflow_via_chat(chat_client):
    # User initiates workflow
    response = chat_client.send_message(
        agent='flo',
        message='Run workflow 1 for Test Corp'
    )
    
    assert 'Workflow started' in response
    run_id = extract_run_id(response)
    
    # Check workflow status
    status = chat_client.send_message(
        agent='flo',
        message=f'/workflow status {run_id}'
    )
    
    assert status['status'] in ['in_progress', 'completed']
```

---

## Performance Considerations

### Execution Time

**Target times:**
- Simple workflows: <5 seconds
- Medium workflows: <30 seconds
- Complex workflows: <2 minutes
- Long-running: >2 minutes (use background tasks)

**Optimization strategies:**
- Run steps in parallel when possible
- Cache intermediate results
- Use efficient database queries
- Minimize API calls
- Pre-compute when possible

---

### Resource Usage

**Memory:**
- Keep context data lean
- Stream large datasets
- Clean up after each step
- Avoid loading entire files

**Database:**
- Use connection pooling
- Index lookup fields
- Batch operations
- Close connections promptly

---

## Workflow Studio

### Design Guidelines

When creating workflows via Workflow Studio (future feature):

**1. Visual Design:**
- Drag-and-drop step builder
- Visual connector lines
- Color-coded step types (auto, manual, decision)
- Live validation

**2. Step Configuration:**
- Step name and description
- Agent selection dropdown
- Tool selection for auto steps
- Task template for manual steps
- Error handling options

**3. Testing:**
- "Dry run" simulation
- Step-by-step debugging
- Mock data input
- Trace visualization

**4. Deployment:**
- Save to workflows directory
- Generate metadata.yaml
- Create workflow.py from visual design
- Register with Flo agent

---

## Common Workflows

### Workflow 1: Bidder Onboarding

**Purpose**: Verify bidder eligibility  
**Steps**: SAM → OFAC → Identity → Review  
**Duration**: 5-10 minutes  
**Human Tasks**: 0-1 (only if flagged)

---

### Workflow 2: Property Listing

**Purpose**: Prepare property for auction  
**Steps**: Data validation → Compliance → Photos → Approval  
**Duration**: 1-2 hours  
**Human Tasks**: 1 (final approval)

---

### Workflow 3: Post-Sale Transfer

**Purpose**: Complete property transfer after auction  
**Steps**: Verify payment → Title transfer → Documents → Notification  
**Duration**: 1-3 days  
**Human Tasks**: 2-3 (document verification, final sign-off)

---

### Workflow 4: Quarterly Audit

**Purpose**: Compliance audit of all transactions  
**Steps**: Data collection → Analysis → Flagged items → Review → Report  
**Duration**: 1-2 weeks  
**Human Tasks**: Multiple (reviewing flagged items)

---

## Troubleshooting

### Workflow Not Starting

**Check:**
1. Workflow registered in Flo agent
2. metadata.yaml is valid
3. Required parameters provided
4. User has permission

### Workflow Stuck

**Diagnose:**
1. Check current step in workflow state
2. Review logs for errors
3. Check if waiting for task
4. Verify external dependencies (API, database)

**Recovery:**
1. Resume from last successful step
2. Skip failed step if non-critical
3. Create manual task for intervention

### Tasks Not Appearing

**Check:**
1. Task created successfully (logs)
2. Task assigned to correct role
3. User has correct role
4. Task not already claimed
5. Task database record exists

---

## Workflow Checklist

### Planning Phase

- [ ] Define workflow objective
- [ ] Identify required steps
- [ ] Determine which agents to use
- [ ] Identify human decision points
- [ ] Map out error scenarios
- [ ] Estimate execution time

### Implementation Phase

- [ ] Create workflow directory
- [ ] Write metadata.yaml
- [ ] Implement workflow.py
- [ ] Create task templates
- [ ] Add logging throughout
- [ ] Implement error handling
- [ ] Add progress tracking

### Testing Phase

- [ ] Test with valid inputs
- [ ] Test with invalid inputs
- [ ] Test error scenarios
- [ ] Test human task flow
- [ ] Test workflow cancellation
- [ ] Test idempotency (re-run)
- [ ] Performance test with load

### Documentation Phase

- [ ] Write workflow README
- [ ] Document parameters
- [ ] Document expected outcomes
- [ ] Create example executions
- [ ] Add to user guide
- [ ] Update Flo agent SKILLS.md

---

## Examples from RealtyIQ

### Bidder Onboarding Workflow

**File**: `workflows/bidder_onboarding/workflow.py`

**Key Features:**
- Sequential verification steps
- Automatic agent invocation (SAM, OFAC)
- Conditional task creation
- Comprehensive logging
- State persistence

**Code Highlights:**
```python
# Step 1: SAM check
sam_result = await self._check_sam(entity_name)
if sam_result == 'EXCLUDED':
    return self._reject_immediately('SAM exclusion found')

# Step 2: OFAC screen
ofac_result = await self._check_ofac(entity_name)
if ofac_result['status'] == 'MATCH':
    # Create human review task
    task_id = await self._create_review_task(ofac_result)
    return {'status': 'pending', 'task_id': task_id}

# All passed
return {'status': 'approved'}
```

---

## Future Workflow Ideas

### Potential Workflows to Implement

1. **Property Inspection Workflow**
   - Schedule inspection
   - Upload inspection report
   - Review findings
   - Approve for listing

2. **Auction Setup Workflow**
   - Validate property ready
   - Set auction parameters
   - Create marketing materials
   - Schedule and publish

3. **Dispute Resolution Workflow**
   - File dispute
   - Gather evidence
   - Multiple reviewer opinions
   - Final arbitration

4. **Compliance Audit Workflow**
   - Define audit scope
   - Automated data collection
   - Flag anomalies
   - Human review
   - Generate audit report

5. **Agent Performance Review**
   - Collect agent metrics
   - Generate performance report
   - Manager review
   - Action plan creation

---

**Version**: 1.0  
**Last Updated**: February 21, 2026  
**Related**: [CONTEXT.md](CONTEXT.md), [USE_CASES.md](USE_CASES.md)
