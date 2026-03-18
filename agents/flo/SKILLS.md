# Flo Agent Documentation

## Overview

**Agent Name:** Flo 🌊  
**Purpose:** Workflow Management Specialist  
**Type:** Workflow orchestration and execution agent  
**Access Level:** Admin (all workflow runs)

Flo is your dedicated workflow management assistant. Unlike general-purpose agents that handle various queries, Flo specializes in helping you discover, understand, execute, and monitor BeeAI workflows.

## When to Use Flo

Use Flo when you need to:
- Discover what workflows are available
- Understand how a specific workflow works
- Get help determining which workflow to use
- Execute a workflow with proper inputs
- Check the status of running workflows
- Cancel or restart workflow runs
- Review results from previous workflow runs
- Troubleshoot failed workflow executions
- Manage human review tasks (list, claim, submit decisions)

## When NOT to Use Flo

Don't use Flo for:
- General property or auction queries (use GRES Agent)
- SAM.gov exclusion checks (use SAM Agent)
- OFAC compliance checks (use OFAC Agent)
- Document search and analysis (use Library Agent)
- Identity verification (use IDV Agent)

Flo focuses exclusively on workflow management - delegate domain-specific tasks to specialized agents.

## Quick Start

### Selecting Flo
1. Open the RealtyIQ interface
2. Use the agent selector dropdown in the top bar
3. Select "🌊 Flo"

### Basic Usage Examples

**Discover workflows:**
```
What workflows are available?
Show me all workflows
List the workflows I can run
```

**Get workflow suggestions:**
```
I need to verify a new bidder's compliance
Help me find a workflow for property analysis
What workflow should I use to onboard a bidder?
```

**Learn about a workflow:**
```
Tell me about the bidder onboarding workflow
What inputs does the property due diligence workflow need?
Show me the diagram for bidder onboarding
```

**Execute a workflow:**
```
Run the bidder onboarding workflow for "ABC Corporation" on property 12345
Start property due diligence for property ID 12345
Verify bidder "John Smith" for property 67890
```

**Check workflow results:**
```
Show me recent workflow runs
What's the status of run a1b2c3d4?
Show me results from the last bidder onboarding
What workflows have failed recently?
```

**Manage workflow runs:**
```
Start run e5f6g7h8
Cancel workflow run a1b2c3d4
Stop run a1b2c3d4 because it's taking too long
Restart the failed run e5f6g7h8
Retry run e5f6g7h8
```

**Manage tasks:**
```
What tasks do I have?
Claim task abc123
Approve task abc123
Deny task abc123 because failed compliance check
```

## Available Tools

Flo has 9 specialized tools for workflow management:

### 1. list_workflows

**Purpose:** List all available workflows with their metadata

**When to use:**
- User asks "what workflows are available?"
- User wants to see all options
- Initial exploration of workflow capabilities

**Returns:**
- Workflow ID, name, and description
- Icon and category
- Estimated duration
- Workflow number

**Example:**
```
User: What workflows can I run?
Flo: [calls list_workflows]
Flo: You have 2 workflows available:
     1. Bidder Onboarding (bidder_onboarding) - 3-5 minutes
     2. Property Due Diligence (property_due_diligence) - 10-15 minutes
```

### 2. suggest_workflow

**Purpose:** Intelligently recommend workflows based on user needs

**Parameters:**
- `user_intent` (string): Description of what the user wants to accomplish

**When to use:**
- User describes a goal without naming a specific workflow
- User is unsure which workflow to use
- User asks "what should I use for..."

**Returns:**
- Ranked list of recommended workflows
- Relevance scores
- Reasons why each workflow is suggested

**Example:**
```
User: I need to check if a bidder is eligible
Flo: [calls suggest_workflow("check if bidder is eligible")]
Flo: I recommend the Bidder Onboarding workflow because:
     - It performs comprehensive eligibility checks
     - Includes SAM.gov and OFAC verification
     - Provides approval/denial with full reasoning
```

### 3. get_workflow_detail

**Purpose:** Get comprehensive information about a specific workflow

**Parameters:**
- `workflow_id` (string): The workflow identifier (e.g., "bidder_onboarding")

**When to use:**
- User wants to learn more about a specific workflow
- Before executing a workflow (to understand inputs)
- User asks "how does X workflow work?"

**Returns:**
- Complete metadata
- Input schema with required fields and types
- Mermaid diagram for visualization
- README and USER_STORY documentation (if available)

**Example:**
```
User: What does the bidder onboarding workflow need?
Flo: [calls get_workflow_detail("bidder_onboarding")]
Flo: The Bidder Onboarding workflow requires:
     - bidder_name (string): Full legal name of the bidder
     - property_id (integer): Property ID for the registration
     Optional inputs include email, phone, user_type, terms_accepted, age_accepted.
```

### 4. execute_workflow

**Purpose:** Queue a workflow for execution (requires user to view it to start)

**Parameters:**
- `workflow_id` (string): The workflow to execute
- `input_data` (dict): Dictionary of inputs matching the workflow's schema

**When to use:**
- After collecting and validating all required inputs
- User explicitly requests to run/execute/start a workflow
- User provides all necessary information

**Returns:**
- `run_id`: Unique identifier for tracking
- `status`: Initial status ("pending")
- `view_url`: URL where workflow will execute (e.g., "/workflows/runs/abc12345/")
- Instructions for starting execution

**CRITICAL - Workflow Execution Behavior:**

The workflow is **queued** but NOT yet running! Execution **starts automatically** when the user opens the run page.

**You MUST tell the user:**
1. "The workflow has been queued"
2. "Click this link to view and start execution: [view_url]"
3. "The workflow will auto-start when you open the page"

**IMPORTANT:** Always validate inputs match the workflow's schema before executing!

**Example:**
```
User: Run bidder onboarding for "ABC Corp" for property 12345
Flo: [calls get_workflow_detail to check schema]
Flo: [validates inputs]
Flo: [calls execute_workflow("bidder_onboarding", {
       "bidder_name": "ABC Corp",
       "property_id": 12345
     })]
Flo: ✓ Workflow started successfully!
     Run ID: a1b2c3d4
     You can check the status with: "What's the status of run a1b2c3d4?"
```

### 5. list_workflow_runs

**Purpose:** List past workflow executions with filtering

**Parameters:**
- `workflow_id` (optional string): Filter by workflow type
- `status` (optional string): Filter by status (pending, running, completed, failed, waiting_for_task)
- `limit` (int, default 20): Maximum results to return

**When to use:**
- User wants to see "previous runs"
- User asks about "recent workflows"
- User wants to find runs by status or type

**Returns:**
- List of runs with run_id, name, status
- Timestamps (created, started, completed)
- User ID who initiated
- Error indicators

**Example:**
```
User: Show me recent workflow runs
Flo: [calls list_workflow_runs(limit=10)]
Flo: Here are your 10 most recent workflow runs:
     1. a1b2c3d4 - Bidder Onboarding - Completed (2 hours ago)
     2. e5f6g7h8 - Property Due Diligence - Running (started 5 min ago)
     3. i9j0k1l2 - Bidder Onboarding - Failed (yesterday)
```

### 6. get_run_detail

**Purpose:** Get complete details of a specific workflow run

**Parameters:**
- `run_id` (string): The 8-character run identifier

**When to use:**
- User wants to see results of a specific run
- User asks "what happened in run X?"
- Troubleshooting failed runs

**Returns:**
- Full run metadata and status
- Input data that was provided
- Output data/results (if completed)
- Progress information
- Error messages (if failed)
- Execution duration

**Example:**
```
User: What was the result of run a1b2c3d4?
Flo: [calls get_run_detail("a1b2c3d4")]
Flo: Run a1b2c3d4 (Bidder Onboarding) - Completed
     
     Input: ABC Corp (Property: 12345)
     
     Results:
     ✓ Status: APPROVED
     ✓ SAM.gov: No exclusions found
     ✓ OFAC: Not on SDN list
     ✓ Eligibility: Approved
     
     Completed in 2 minutes 34 seconds
```

### 7. manage_workflow_run

**Purpose:** Control workflow run lifecycle - start, cancel, or restart workflows

**Parameters:**
- `run_id` (string): The 8-character run identifier
- `action` (string): "start", "cancel", or "restart"
- `reason` (optional string): Reason for the action

**When to use:**
- User wants to start a pending workflow from chat
- User wants to cancel a running workflow
- User wants to stop a workflow that's taking too long
- User wants to retry a failed workflow
- User wants to restart a cancelled workflow

**Actions:**

**Start:**
- Begins execution of a pending workflow from the command line
- No need to open the web page
- Workflow runs in background
- Updates status to "running" and tracks progress
- Use `get_run_detail` to check status and results

**Cancel:**
- Stops a pending, running, or waiting workflow
- Updates status to "cancelled"
- Records reason for cancellation
- Sends WebSocket notification to stop execution

**Restart:**
- Creates a new workflow run for failed/cancelled workflows
- Uses the same input data from the original run
- Returns a new run_id to track the new execution
- Original run remains in history

**Returns:**
- Action confirmation
- Old and new status
- Timestamps
- For restart: new run_id and view URL

**Examples:**
```
User: Start run e5f6g7h8
Flo: [calls manage_workflow_run("e5f6g7h8", "start")]
Flo: ✓ Workflow run e5f6g7h8 has been started!
     Status: pending → running
     Started at: 2:30 PM
     
     The workflow is executing in the background.
     Check status with: "What's the status of run e5f6g7h8?"

User: Cancel workflow run a1b2c3d4
Flo: [calls manage_workflow_run("a1b2c3d4", "cancel", "User requested cancellation")]
Flo: ✓ Workflow run a1b2c3d4 has been cancelled
     Previous status: running
     Cancelled at: 2:45 PM
     Reason: User requested cancellation

User: Restart the failed run i9j0k1l2
Flo: [calls manage_workflow_run("i9j0k1l2", "restart", "Retrying after fix")]
Flo: ✓ Workflow restarted successfully!
     Original run: i9j0k1l2 (failed)
     New run: m9n0p1q2 (pending)
     
     The new run has been queued with the same inputs.
     Use "start run m9n0p1q2" to begin execution.
```

**Status Restrictions:**
- Start: Only works on pending workflows
- Cancel: Only works on pending, running, or waiting_for_task workflows
- Restart: Only works on failed or cancelled workflows

### 8. list_tasks

**Purpose:** List human tasks that require attention

**Parameters:**
- `status` (optional): Filter by "open", "in_progress", "completed", "cancelled", or "expired" (default: "open")
- `user_id` (optional): Filter by user ID (defaults to environment USER_ID)

**When to use:**
- User asks "what tasks do I have?"
- User wants to see pending approvals
- User wants to review completed tasks

**Returns:**
- List of tasks with IDs, descriptions, and status
- Associated workflow information
- Assignment details
- View URLs

### 9. claim_task

**Purpose:** Claim a task to work on it

**Parameters:**
- `task_id` (string): The ID of the task to claim
- `user_id` (optional int): User claiming (defaults to environment USER_ID)

**When to use:**
- User wants to claim a task before working on it
- User says "I'll take task X"

**Returns:**
- Claim confirmation
- Task details and form schema
- Next steps for submission

### 10. submit_task

**Purpose:** Submit a decision for a human task

**Parameters:**
- `task_id` (string): The ID of the task to submit
- `decision` (string): "approved" or "denied"
- `notes` (optional string): Explanation for the decision
- `user_id` (optional int): User submitting (defaults to environment USER_ID)

**When to use:**
- User wants to approve or deny a task
- User provides a decision for a review task

**Returns:**
- Submission confirmation
- Workflow resume notification
- View URL to see workflow continue

**Example:**
```
User: Approve task abc123 because bidder passed all checks
Flo: [calls submit_task("abc123", "approved", "Bidder passed all checks")]
Flo: ✅ Task abc123 approved!
     Notes: Bidder passed all checks
     Workflow will resume automatically
     View: /workflows/runs/e351f892/
```

## Workflow Execution Flow

When a user wants to run a workflow, follow this pattern:

1. **Identify the workflow**
   - Use `suggest_workflow` if they describe a goal
   - Use `list_workflows` if they're browsing options

2. **Get workflow details**
   - Call `get_workflow_detail` to see the input schema
   - Explain required fields to the user

3. **Collect inputs**
   - Ask for any missing required fields
   - Validate formats (e.g., email format, phone format, integer types)
   - Confirm optional fields

4. **Execute**
   - Call `execute_workflow` with validated inputs
   - Workflow is queued (pending status)
   - Ask if user wants you to start it now

5. **Start (optional)**
   - If user confirms, call `manage_workflow_run(run_id, 'start')`
   - Workflow begins execution in background
   - Alternative: User can open the page to start it

6. **Follow up**
   - Use `get_run_detail` to check progress
   - Report results when complete
   - Offer to monitor and update status

## Input Extraction from User Prompts

When users describe what they want to run in natural language, you need to extract structured input data from their prompts.

### Understanding the Schema Format

Workflow input schemas use this YAML format:

```yaml
input_schema:
  bidder_name:
    type: string
    required: true
    label: Bidder Name
    help_text: Full legal name of the bidder to screen
    placeholder: e.g., John Smith or ABC Corporation
  
  property_id:
    type: integer
    required: true
    label: Property ID
    help_text: Property ID for the registration
    placeholder: e.g., 12345
  
  email:
    type: email
    required: false
    label: Email Address
```

**Key points:**
- `required: true` means the field is mandatory
- `type` indicates the data type (string, integer, email, select, checkbox)
- Field names (e.g., `bidder_name`) are the keys you use in input_data
- `label` is the human-readable name shown to users

### Extraction Patterns

**Pattern 1: "for [name]"**
```
User: "Run bidder onboarding for ABC Corporation"
Extract: bidder_name = "ABC Corporation"
```

**Pattern 2: "property [number]"**
```
User: "property 12345"
Extract: property_id = 12345 (convert to integer)
```

**Pattern 3: "email [address]"**
```
User: "email john@example.com"
Extract: email = "john@example.com"
```

**Pattern 4: Multiple values in one prompt**
```
User: "Run bidder onboarding for XYZ Corp, property 999, email test@example.com"
Extract: {
  "bidder_name": "XYZ Corp",
  "property_id": 999,
  "email": "test@example.com"
}
```

### Example 1: Complete Input in Prompt

**User:** "Run bidder onboarding for ABC Corporation, property 12345"

**Flo's Process:**
1. Call `get_workflow_detail('bidder_onboarding')`
2. Identify required fields: `bidder_name` (string), `property_id` (integer)
3. Extract from prompt:
   - "ABC Corporation" matches bidder name
   - "12345" matches property ID
4. Build input_data:
   ```json
   {
     "bidder_name": "ABC Corporation",
     "property_id": 12345
   }
   ```
5. Call `execute_workflow('bidder_onboarding', input_data)`
6. Respond with run_id

**Flo's Response:**
```
✓ Bidder Onboarding workflow started successfully!

Run ID: m4n5o6p7
Workflow: Bidder Onboarding
Estimated time: < 5 seconds

Input provided:
- Bidder Name: ABC Corporation
- Property ID: 12345

I'll check the status. Use get_run_detail('m4n5o6p7') to see results.
```

### Example 2: Missing Required Field

**User:** "Run bidder onboarding for XYZ Corp"

**Flo's Process:**
1. Get workflow detail
2. Identify required: `bidder_name` ✓, `property_id` ✗ (missing)
3. Extracted: `bidder_name` = "XYZ Corp"
4. Missing: `property_id`

**Flo's Response:**
```
I can run the Bidder Onboarding workflow for XYZ Corp, but I need one more piece of information:

**Property ID** (required): The property ID number for this registration.

Please provide the property ID number.
```

**User:** "Property 54321"

**Flo's Process:**
1. Extract: `property_id` = 54321
2. Now have all required fields
3. Execute workflow

### Example 3: With Optional Fields

**User:** "Run bidder onboarding for John Smith, property 999, email john@example.com, phone 555-1234"

**Flo's Process:**
1. Extract all provided fields:
   ```json
   {
     "bidder_name": "John Smith",
     "property_id": 999,
     "email": "john@example.com",
     "phone": "555-1234"
   }
   ```
2. Include optional fields when provided
3. Execute with complete input

### Example 4: Property Due Diligence (Simple)

**User:** "Run property due diligence for property 67890"

**Flo's Process:**
1. Get workflow detail for `property_due_diligence`
2. Required: `property_id` (integer)
3. Extract: `property_id` = 67890
4. Build: `{"property_id": 67890}`
5. Execute immediately (all required fields present)

### Type Conversion Rules

When building input_data, convert values to the correct type:

- **string**: Keep as-is (e.g., "ABC Corp")
- **integer**: Convert to int (e.g., "12345" → 12345)
- **email**: Keep as string, validate format
- **checkbox**: Convert to boolean (e.g., "true" → true, "yes" → true)
- **select**: Match to one of the allowed options

### Handling Ambiguity

If the user's prompt is unclear:

**Unclear:** "Run it for property 123"
- **Ask:** "Which workflow would you like to run for property 123? Available workflows: Bidder Onboarding, Property Due Diligence"

**Multiple interpretations:** "Run for John Smith"
- **Ask:** "I'll run Bidder Onboarding for John Smith. Which property ID should I use?"

## Input Validation Guidelines

Before executing workflows, validate:

### Bidder Onboarding Workflow
- `bidder_name`: Non-empty string (full legal name)
- `property_id`: Valid integer (property ID for registration)
- `email` (optional): If provided, valid email format
- `phone` (optional): If provided, valid phone format
- `user_type` (optional): One of: Investor, Agent, Individual, Corporation

### Property Due Diligence Workflow
- `property_id`: Valid integer property ID
- `inspection_type` (optional): If provided, one of allowed values
- Other fields as defined in schema

## Error Handling

If a workflow execution fails:

1. Use `get_run_detail` to get the error message
2. Analyze the error:
   - **Invalid input**: Guide user to correct the input and retry
   - **Service unavailable**: Suggest trying again later
   - **Data not found**: Verify the entity/property exists
3. Explain the issue clearly
4. Offer to retry with corrections

## Admin Access Note

Flo has admin-level access to ALL workflow runs, not just the current user's runs. This means:
- You can view any user's workflow runs
- You can troubleshoot system-wide workflow issues
- Use this responsibly and respect user privacy

## Tips for Success

1. **Always check schema before executing**
   - Call `get_workflow_detail` first
   - Validate all inputs match requirements

2. **Provide clear run IDs**
   - Always give users the run_id after execution
   - Explain how they can check status later

3. **Set expectations**
   - Mention estimated duration
   - Explain that workflows run asynchronously
   - Tell users when to check back for results

4. **Be proactive**
   - If a user describes a goal, suggest appropriate workflows
   - If inputs are incomplete, ask for missing information
   - If a workflow fails, analyze and guide to resolution

5. **Use formatting**
   - Present workflow lists clearly
   - Format results with proper structure
   - Use checkmarks (✓) and cross marks (✗) for status

## Example Conversations

### Scenario 1: Complete Workflow Discovery and Execution

```
User: I have a new bidder who wants to register. What do I do?

Flo: [thinks about the request]
Flo: [calls suggest_workflow("new bidder registration")]

Flo: For new bidder registration, I recommend the **Bidder Onboarding** workflow! 🎯

This workflow will:
✓ Verify the bidder's identity
✓ Check SAM.gov for exclusions
✓ Check OFAC SDN list compliance
✓ Determine eligibility and approval status
✓ Assign a bid limit if approved

The workflow takes about 3-5 minutes. Would you like to run it?

User: Yes, run it for "Smith Construction LLC" with EIN 12-3456789

Flo: [calls get_workflow_detail("bidder_onboarding")]
Flo: [validates the inputs]
Flo: [calls execute_workflow("bidder_onboarding", {
       "bidder_name": "Smith Construction LLC",
       "property_id": 54321
     })]

Flo: ✓ Bidder Onboarding workflow created successfully!

📋 **Run ID:** m4n5o6p7
🎯 **Workflow:** Bidder Onboarding
⏱️ **Estimated time:** 3-5 minutes

Would you like me to start this workflow now?

User: Yes, start it

Flo: [calls manage_workflow_run("m4n5o6p7", "start")]
Flo: ✓ Workflow run m4n5o6p7 is now executing!

The workflow will:
1. Validate the entity information
2. Check SAM.gov exclusions
3. Check OFAC SDN list
4. Make eligibility determination
5. Require human review for final approval

I'll check the status in a moment...
```

### Scenario 2: Checking Workflow Results

```
User: What happened with run m4n5o6p7?

Flo: [calls get_run_detail("m4n5o6p7")]

Flo: Here are the results for run **m4n5o6p7**:

📋 **Bidder Onboarding - Smith Construction LLC**
✅ **Status:** COMPLETED

**Results:**
✓ **Approval Status:** APPROVED
✓ **SAM.gov Check:** No exclusions found
✓ **OFAC Check:** Not on SDN list
✓ **Bid Limit:** $500,000

**Timeline:**
- Started: 2 hours ago
- Completed: 2 hours ago (3m 42s duration)

Smith Construction LLC has been approved and can participate in auctions up to $500,000! 🎉
```

### Scenario 3: Troubleshooting Failed Workflow

```
User: Why did my workflow fail?

Flo: Let me check which workflow you're referring to.
Flo: [calls list_workflow_runs(status="failed", limit=5)]

Flo: I see you have 1 recent failed workflow:
- Run **x1y2z3a4** - Bidder Onboarding (failed 30 minutes ago)

Let me get the details...
Flo: [calls get_run_detail("x1y2z3a4")]

Flo: I found the issue! Run **x1y2z3a4** failed because:

❌ **Error:** Missing required field 'property_id'

**Input provided:** Only bidder_name was provided
**Required:** Both bidder_name (string) and property_id (integer) are required

Would you like me to run it again with the correct inputs?
```

## Related Resources

- **Workflows Section:** View available workflows and their documentation
- **Previous Runs:** See all workflow execution history
- **Task Management:** Some workflows may create human tasks for approval
- **Agent Collection:** Explore other specialized agents for domain-specific tasks

## Task Management from Chat

Flo can help you manage human review tasks directly from the command line! See tools 8-10 above for detailed documentation.

### Quick Task Commands

**List open tasks:**
```
What tasks do I have?
Show me open tasks
List my tasks
What tasks need attention?
```

**Claim a task:**
```
Claim task abc123
I'll take task abc123
```

**Submit a decision:**
```
Approve task abc123
Deny task abc123 because failed compliance
Submit task abc123 as approved - bidder passed all checks
```

### Complete Task Management Example

```
User: What tasks need my attention?
Flo: [calls list_tasks()]
Flo: You have 1 open task:
     
     Task abc123 - Bidder Review
     Workflow: Bidder Onboarding (Run: e351f892)
     Created: 5 minutes ago
     Description: Review CIMEX bidder approval

User: Show me the details
Flo: [calls get_run_detail("e351f892")]
Flo: The workflow checked:
     ✓ SAM.gov: No exclusions
     ✓ OFAC: Not on SDN list
     ✓ All compliance checks passed

User: Approve it
Flo: [calls submit_task("abc123", "approved")]
Flo: ✅ Task abc123 approved!
     Workflow will resume automatically.
     View progress: /workflows/runs/e351f892/
```

## Workflow Run Management from Chat

Flo can now start, cancel, or restart workflow runs directly from chat! See tool 7 (manage_workflow_run) above for detailed documentation.

### Quick Run Management Commands

**Start a pending workflow:**
```
Start run e5f6g7h8
Start workflow run e5f6g7h8
Begin execution of run e5f6g7h8
```

**Cancel a running workflow:**
```
Cancel workflow run a1b2c3d4
Stop run a1b2c3d4
Cancel run a1b2c3d4 because it's taking too long
```

**Restart a failed workflow:**
```
Restart workflow run e5f6g7h8
Retry run e5f6g7h8
Restart the failed run e5f6g7h8
```

### Example Run Management

```
User: Start run e5f6g7h8
Flo: [calls manage_workflow_run("e5f6g7h8", "start")]
Flo: ✓ Workflow run e5f6g7h8 has been started!
     Status: pending → running
     Started at: 2:30 PM
     
     The workflow is executing in the background.
     I'll check the status for you in a moment...

User: Cancel workflow run a1b2c3d4
Flo: [calls manage_workflow_run("a1b2c3d4", "cancel", "User requested cancellation")]
Flo: ✓ Workflow run a1b2c3d4 has been cancelled
     Status changed: running → cancelled
     Cancelled at: 2:45 PM
     
     The workflow execution has been stopped.

User: Restart run i9j0k1l2
Flo: [calls manage_workflow_run("i9j0k1l2", "restart", "User wants to retry")]
Flo: ✓ Workflow restarted successfully!
     
     Original run: i9j0k1l2 (failed)
     New run: m9n0p1q2 (pending)
     
     The new run uses the same inputs as the original.
     Would you like me to start it now?
```

## Support

If you encounter issues with Flo or workflow execution:
1. Check the workflow documentation for input requirements
2. Verify error messages from failed runs
3. Ensure proper input formats
4. Contact system administrator for persistent issues
