# Workflow & Task Management Complete Guide

**Complete reference for workflow execution, task management, and user tracking in BeeAI.**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Command Reference](#command-reference)
3. [User Tracking & Audit Trail](#user-tracking--audit-trail)
4. [Web UI](#web-ui)
5. [Database Queries](#database-queries)
6. [Testing](#testing)

---

## Quick Start

### Execute a Workflow
```bash
# 1. List available workflows
/workflow list

# 2. View workflow details
/workflow 1

# 3. Switch to Flo agent, then execute
run workflow 1 for Jane Doe on property 99999

# 4. Monitor workflow run
/workflow runs
```

### Manage Tasks
```bash
# 1. List your pending tasks
/task list

# 2. Claim a task
/task claim <task_id>

# 3. Submit task decision
/task submit <task_id> approve

# 4. View all tasks (including completed)
/task list all

# 5. Delete completed task
/task delete <task_id>
```

---

## Command Reference

### Workflow Commands

| Command | Description | Access |
|---------|-------------|--------|
| `/workflow list` | List all available workflows | All users |
| `/workflow <number>` | Show workflow details | All users |
| `/workflow execute <number>` | Execute workflow (shows instructions) | All users |
| `/workflow runs` | View YOUR workflow runs | All users |
| `/workflow runs all` | View ALL users' runs | Admin only |
| `/workflow runs user <id>` | View specific user's runs | Admin only |

### Task Commands

| Command | Description | Access |
|---------|-------------|--------|
| `/task list` | List YOUR active tasks | All users |
| `/task list all` | List ALL your tasks (active + completed) | All users |
| `/task <task_id>` | Show task details | All users |
| `/task claim <task_id>` | Claim an open task | All users |
| `/task submit <task_id> approve` | Approve task | Task owner |
| `/task submit <task_id> deny` | Deny task | Task owner |
| `/task delete <task_id>` | Delete completed/cancelled task | All users |

### Schedule Commands

| Command | Description | Access |
|---------|-------------|--------|
| `/schedule list` | List your scheduled workflows | All users |
| `/schedule add <workflow> ["name"] at <datetime>` | Schedule workflow once at a specific time | All users |
| `/schedule add <workflow> every <N> [minutes]` | Schedule workflow on a repeating interval | All users |
| `/schedule show <id>` | Show schedule details | All users |
| `/schedule edit <id>` | Link to edit in UI | All users |
| `/schedule delete <id>` | Delete a schedule | All users |

**Examples:** `/schedule add 1 "Monthly report" at 2025-03-10 09:00` | `/schedule add 1 every 60`

**Web UI:** **Workflows → Schedules** (or `/workflows/schedules/`) to create, edit, delete schedules and run a schedule immediately.

---

## Flo from chat

When you use the **Flo** agent in chat, you can do the following in plain language (no slash commands):

| What you want | Example |
|---------------|--------|
| Summary of your work | "What do I need to do?", "What's running?" |
| Schedule a workflow | "Schedule workflow 1 every Monday at 9am", "Schedule bi_weekly_report once at 2025-03-15 10:00" |
| Change or pause a schedule | "Update schedule 3 to run at 10am", "Pause schedule 5" |
| Run outcome | "What happened with run abc12345?" |
| Re-run a workflow | "Run that again", "Re-run run abc12345" (creates new run with same inputs) |
| Search runs | "Find my completed runs from last week", "Runs for bidder_onboarding" |
| Search tasks | "Find tasks about approval", "My completed tasks" |
| Bulk run | "Run bidder onboarding for these 5 companies" (provide list of inputs) |
| Notification settings | "What are my notification settings?", "Notify me when workflows complete" |
| System health | "Is everything okay?", "Why isn't my schedule running?" |
| Guided run | "Help me run workflow 1", "Walk me through running the report" — Flo asks for each required input, then runs |

Run detail page in the UI also has a **Run again** button to clone that run (same inputs, new run).

---

## User Tracking & Audit Trail

### Workflow Run Tracking

**Field**: `WorkflowRun.user_id`

Automatically tracks who started each workflow execution.

**Example**:
```python
run = WorkflowRun.objects.get(run_id='abc12345')
print(f"Started by: User {run.user_id}")
print(f"Started at: {run.started_at}")
print(f"Status: {run.status}")
```

### Task Tracking

**Fields**:
- `assigned_to_user_id` - User who claimed the task
- `claimed_at` - When task was claimed
- `completed_by_user_id` - User who completed the task
- `completed_at` - When task was completed

**Example**:
```python
task = HumanTask.objects.get(task_id='xyz98765')
print(f"Claimed by: User {task.assigned_to_user_id}")
print(f"Completed by: User {task.completed_by_user_id}")
```

### Complete Audit Trail

```
Workflow Run abc12345:
  ├─ Started by: User 3 at 2026-03-02 14:30:00
  ├─ Status: completed
  └─ Completed at: 2026-03-02 14:45:00
  
  Task xyz98765:
    ├─ Claimed by: User 5 at 2026-03-02 14:35:00
    ├─ Completed by: User 7 at 2026-03-02 14:44:00
    └─ Decision: approved
```

**Note**: `assigned_to_user_id` and `completed_by_user_id` can differ (task reassignment, supervisor override, etc.)

---

## Web UI

### Workflow Runs
```
http://localhost:8002/workflows/runs/
```
- Auto-filters to current user's runs
- Shows status, duration, timestamps
- Pagination (10 per page)
- Filter by status: `?status=completed`
- Filter by workflow type: `?workflow=bidder_onboarding`

### Tasks
```
http://localhost:8002/workflows/tasks/
```
- Shows active tasks by default
- View all: `?status=all`
- Role-based filtering (admin sees more)
- Claim, submit, and cancel actions

### Schedules
```
http://localhost:8002/workflows/schedules/
```
- List your scheduled workflows (once or recurring)
- Create: **Schedule Workflow** or `/workflows/schedules/new/?workflow_id=<id>` from a workflow detail page
- Edit / delete / **Run now** per schedule
- Scheduler runs due jobs via `python manage.py run_scheduled_workflows` (run every 1–5 minutes via cron)

### Individual Workflow Run
```
http://localhost:8002/workflows/runs/<run_id>/
```
- Real-time status updates
- Progress tracking
- Associated tasks
- Export results

---

## Database Queries

### Find All Workflows by User
```python
from agent_app.models import WorkflowRun

user_workflows = WorkflowRun.objects.filter(user_id=5).order_by('-created_at')

for run in user_workflows:
    print(f"{run.run_id}: {run.workflow_name} ({run.status})")
```

### Find Tasks by Completer
```python
from agent_app.models import HumanTask

user_completions = HumanTask.objects.filter(
    completed_by_user_id=7,
    status=HumanTask.STATUS_COMPLETED
).order_by('-completed_at')

for task in user_completions:
    print(f"{task.task_id}: {task.title} - {task.output_data.get('decision')}")
```

### Find Task Reassignments
```python
from django.db.models import F

reassigned_tasks = HumanTask.objects.filter(
    status=HumanTask.STATUS_COMPLETED,
    assigned_to_user_id__isnull=False,
    completed_by_user_id__isnull=False
).exclude(
    assigned_to_user_id=F('completed_by_user_id')
)

for task in reassigned_tasks:
    print(f"Task {task.task_id}: "
          f"Claimed by {task.assigned_to_user_id}, "
          f"Completed by {task.completed_by_user_id}")
```

### User Activity Statistics
```python
from django.db.models import Count, Q

# Workflows per user
workflow_stats = WorkflowRun.objects.values('user_id').annotate(
    total=Count('run_id'),
    completed=Count('run_id', filter=Q(status=WorkflowRun.STATUS_COMPLETED)),
    failed=Count('run_id', filter=Q(status=WorkflowRun.STATUS_FAILED))
).order_by('-total')

# Tasks per user
task_stats = HumanTask.objects.filter(
    completed_by_user_id__isnull=False
).values('completed_by_user_id').annotate(
    completed_count=Count('task_id')
).order_by('-completed_count')
```

---

## Database Schema

### WorkflowRun Model
```python
run_id                  # 8-char unique ID (primary key)
workflow_id             # Workflow type identifier
workflow_name           # Human-readable name
status                  # pending/running/completed/failed/cancelled/waiting_for_task
user_id                 # 🎯 User who started workflow (indexed)
input_data              # Workflow input parameters (JSON)
output_data             # Workflow results (JSON)
progress_data           # Real-time progress updates (JSON)
error_message           # Error details if failed
created_at              # When workflow run created
started_at              # When execution began
completed_at            # When execution finished
```

### HumanTask Model
```python
task_id                 # 8-char unique ID (primary key)
workflow_run            # Foreign key to WorkflowRun
task_type               # approval/review/data_collection/verification
status                  # open/in_progress/completed/cancelled/expired
required_role           # user/manager/admin
assigned_to_user_id     # 🎯 User who claimed task (indexed)
claimed_at              # When claimed
completed_by_user_id    # 🎯 User who completed task (indexed)
completed_at            # When completed
title                   # Task title
description             # Task description
input_data              # Task context data (JSON)
output_data             # Task submission data (JSON)
expires_at              # Task expiration timestamp
```

---

## Testing

### Run Complete Test Suite
```bash
cd agent_ui
python manage.py test agent_app.tests.test_workflow_commands
```

**Result**: `Ran 8 tests in 33.826s - OK` ✅

### Tests Include:
1. ✅ Workflow list command
2. ✅ Workflow execution via Flo agent
3. ✅ Workflow runs filtering by user
4. ✅ Task claim with user tracking
5. ✅ Task submit with user tracking
6. ✅ Task delete command
7. ✅ Task list all command
8. ✅ Complete end-to-end lifecycle

### Test Specific Features
```bash
# Test workflow runs filtering
python manage.py test agent_app.tests.test_workflow_commands.WorkflowCommandsTest.test_workflow_runs_command

# Test task user tracking
python manage.py test agent_app.tests.test_workflow_commands.WorkflowCommandsTest.test_task_submit_command
```

---

## Security & Permissions

### Regular Users Can:
- ✅ View their own workflow runs
- ✅ View their own tasks
- ✅ Execute workflows
- ✅ Claim and submit tasks

### Regular Users Cannot:
- ❌ View other users' workflow runs
- ❌ Use `/workflow runs all`
- ❌ Use `/workflow runs user <id>`

### Admin Users Can:
- ✅ All regular user capabilities
- ✅ View all users' workflow runs
- ✅ Filter by specific user
- ✅ See all tasks based on role hierarchy

---

## Common Use Cases

### 1. Execute Workflow and Complete Task
```bash
# Execute (via Flo)
run workflow 1 for ABC Corp on property 12345

# Wait 5-10 seconds, then list tasks
/task list

# Claim the task (note the task_id)
/task claim a1b2c3d4

# Submit decision
/task submit a1b2c3d4 approve
```

### 2. Review Your Activity
```bash
# View your workflow runs
/workflow runs

# View all your tasks
/task list all
```

### 3. Admin Oversight
```bash
# View all users' workflows
/workflow runs all

# Filter by specific user
/workflow runs user 5
```

### 4. Clean Up Completed Tasks
```bash
# View completed tasks
/task list all

# Delete completed task
/task delete <task_id>
```

---

## Troubleshooting

### Task Not Showing
**Problem**: Task exists but not visible in `/task list`

**Solution**: Task might be completed. Try:
```bash
/task list all
```

### Cannot View Other Users' Runs
**Problem**: `/workflow runs all` returns permission denied

**Solution**: This command is admin-only. Regular users can only view their own runs.

### Task Cannot Be Deleted
**Problem**: `/task delete <task_id>` fails with error

**Solution**: Can only delete completed, cancelled, or expired tasks. Active tasks cannot be deleted.

---

## Implementation Details

### Migration History
- `0020_workflowrun.py` - Added WorkflowRun model with user_id
- `0021_alter_workflowrun_status_humantask.py` - Added HumanTask model
- `0022_chatsession_user_id_userpreference_user_id_and_more.py` - User ID updates
- `0023_add_completed_by_user_id.py` - Added completed_by_user_id to HumanTask

### Files Modified
1. `agent_app/models.py` - Added completed_by_user_id field
2. `agent_app/commands/workflow.py` - Added /workflow runs commands
3. `agent_app/commands/task.py` - Enhanced commands, delete support
4. `agent_app/views.py` - User tracking in web submission
5. `tools/workflow_tools.py` - User tracking in Flo agent tools
6. `agent_app/tests/test_workflow_commands.py` - Complete test suite

### Performance Optimizations
**Indexes added for fast queries:**
- `(user_id, -started_at)` on WorkflowRun
- `(assigned_to_user_id, status)` on HumanTask
- `completed_by_user_id` on HumanTask

---

## API Reference

### List Workflow Runs (Web)
```
GET /workflows/runs/
```
Query parameters:
- `status=all|pending|running|completed|failed` - Filter by status
- `workflow=<workflow_id>` - Filter by workflow type
- `page=<number>` - Pagination

### List Tasks (Web)
```
GET /workflows/tasks/
```
Query parameters:
- `status=active|all` - Filter by status
- `page=<number>` - Pagination

### Task Actions (Web)
```
POST /workflows/tasks/<task_id>/claim/
POST /workflows/tasks/<task_id>/submit/
POST /workflows/tasks/<task_id>/cancel/
```

---

## Best Practices

### For Regular Users
1. Use `/workflow runs` to monitor your workflows
2. Use `/task list` to see pending work
3. Claim tasks before working on them
4. Clean up completed tasks periodically with `/task delete`

### For Admins
1. Use `/workflow runs all` to monitor system activity
2. Use `/workflow runs user <id>` to investigate specific users
3. Review task completion patterns for process optimization
4. Use audit trail for compliance reporting

### For Developers
1. Always test with full test suite after changes
2. Use user_id consistently across all operations
3. Add indexes when querying by user fields
4. Document any new tracking fields

---

## Summary

### Workflow Tracking:
- ✅ `user_id` - Who started the workflow
- ✅ Command-line viewing and filtering
- ✅ Admin cross-user visibility

### Task Tracking:
- ✅ `assigned_to_user_id` - Who claimed the task
- ✅ `completed_by_user_id` - Who completed the task
- ✅ Complete audit trail with timestamps
- ✅ Full command-line interface

**Result**: Complete accountability and audit trail for compliance! 🎯
