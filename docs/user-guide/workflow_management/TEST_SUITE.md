# Workflow Command Tests

Comprehensive test suite for workflow and task management via `/cmds` commands.

## Overview

This test suite validates the complete workflow lifecycle using command-line style commands through the chat interface:

1. **List workflows** - `/workflow list`
2. **Execute workflow** - Via Flo agent: `run workflow 1 for [params]`
3. **List tasks** - `/task list`
4. **Claim task** - `/task claim <task_id>`
5. **Submit task** - `/task submit <task_id> approve`

## Test Classes

### `WorkflowCommandsTest`

Automated unit tests for each command:

- `test_workflow_command_list()` - Test listing available workflows
- `test_workflow_execute_via_flo()` - Test workflow execution via Flo agent
- `test_task_claim_command()` - Test claiming a task via command
- `test_task_submit_command()` - Test submitting a task via command
- `test_full_workflow_lifecycle()` - End-to-end test of complete lifecycle

### `WorkflowCommandsIntegrationTest`

Manual test guide for browser-based testing:

- `test_manual_workflow_flow()` - Prints step-by-step instructions for manual testing in browser

### `WorkflowCommandsAPITest`

Documentation for direct API testing (future implementation).

## Running Tests

### Run all workflow command tests:
```bash
python manage.py test agent_app.tests.test_workflow_commands
```

### Run specific test class:
```bash
python manage.py test agent_app.tests.test_workflow_commands.WorkflowCommandsTest
```

### Run specific test:
```bash
python manage.py test agent_app.tests.test_workflow_commands.WorkflowCommandsTest.test_full_workflow_lifecycle --verbosity=2
```

### View manual test guide:
```bash
python manage.py test agent_app.tests.test_workflow_commands.WorkflowCommandsIntegrationTest.test_manual_workflow_flow --verbosity=2
```

## Manual Testing in Browser

Run the manual test guide to get step-by-step instructions:

```bash
python manage.py test agent_app.tests.test_workflow_commands.WorkflowCommandsIntegrationTest.test_manual_workflow_flow --verbosity=2
```

Then follow the printed instructions in your browser chat interface.

## What Gets Tested

### Commands Fixed:
- `/workflow list` - Lists all available workflows
- `/workflow <number>` - Shows workflow details
- `/workflow execute <number>` - Initiates workflow execution
- `/task list` - Lists active (open/in-progress) tasks only
- `/task list all` - Lists ALL tasks including completed/cancelled
- `/task claim <task_id>` - Claims a task for the current user
- `/task submit <task_id> <approve|deny>` - Submits task decision
- `/task delete <task_id>` - Deletes a completed/cancelled task

### Fixed Issues:
- ✅ `HumanTask.STATUS_PENDING` → `HumanTask.STATUS_OPEN` (correct status constant)
- ✅ `task.claimed_by_user_id` → `task.assigned_to_user_id` (correct field name)
- ✅ `task.response_data` → `task.output_data` (correct field name for task results)
- ✅ Removed unused imports in task submit handler
- ✅ Task claim now properly sets `status` to `STATUS_IN_PROGRESS`

## Test Output Example

```
================================================================================
FULL TEST: Complete Workflow Lifecycle
================================================================================

🚀 STEP 1: Execute Bidder Onboarding Workflow
------------------------------------------------------------
✓ Workflow execution request sent

🤝 STEP 3: Claim Task a1b2c3d4
------------------------------------------------------------
✓ Task a1b2c3d4 claimed successfully!

✅ STEP 4: Submit Task with Approval
------------------------------------------------------------
✅ Task a1b2c3d4 submitted successfully!
✓ Task status: completed
✓ Decision: approved

================================================================================
🎉 FULL LIFECYCLE TEST PASSED!
================================================================================
```

## Architecture

### Test Flow:
```
Browser Chat Interface
    ↓
/api/chat/ endpoint
    ↓
Command Dispatcher
    ↓
Command Handlers (workflow.py, task.py)
    ↓
Django Models (WorkflowRun, HumanTask)
    ↓
Workflow Registry & Tools
```

### Command Handler Files:
- `agent_ui/agent_app/commands/workflow.py` - Workflow command handler
- `agent_ui/agent_app/commands/task.py` - Task command handler

### Test File:
- `agent_ui/agent_app/tests/test_workflow_commands.py` - All test implementations

## Notes

- Tests use in-memory SQLite database for speed
- Database locks during concurrent tests are expected and handled gracefully
- Tests mock the chat API interface to simulate user commands
- Each test is independent and creates its own test data
- Tests automatically clean up after completion
