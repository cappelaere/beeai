# Quick Reference Card

**One-page reference for workflow and task commands**

---

## Workflows

```bash
# List available workflows
/workflow list

# View workflow details
/workflow 1

# Execute workflow (via Flo agent)
run workflow 1 for Jane Doe on property 99999

# View your workflow runs
/workflow runs

# View all users' runs (admin only)
/workflow runs all

# View specific user's runs (admin only)
/workflow runs user 5
```

---

## Tasks

```bash
# List active tasks
/task list

# List all tasks (including completed)
/task list all

# View task details
/task <task_id>

# Claim a task
/task claim <task_id>

# Submit with approval
/task submit <task_id> approve

# Submit with denial
/task submit <task_id> deny

# Delete completed task
/task delete <task_id>
```

---

## Schedules

```bash
# List your scheduled workflows
/schedule list

# Schedule workflow once at a specific time
/schedule add 1 "Monthly report" at 2025-03-10 09:00

# Schedule workflow every N minutes
/schedule add 1 every 60

# Show schedule details
/schedule show <id>

# Delete a schedule
/schedule delete <id>
```

**Web UI:** `http://localhost:8002/workflows/schedules/` — view, create, edit, delete schedules and run now.

---

## Chat with Flo

Switch to **Flo** in chat to do the following in natural language (no slash commands):

- **What do I need to do?** — Summary of pending tasks, recent runs, next schedules, unread notifications.
- **Schedule workflow X** — Create, update, pause, or delete schedules (e.g. "schedule workflow 1 every 60 minutes", "pause schedule 3").
- **What happened with run X?** — One-line run summary (status, outcome).
- **Run that again** / **Re-run run abc123** — Clone a run with the same inputs; then start it from chat or the run page.
- **Find runs/tasks** — Search runs by workflow, status, date range; search tasks by text or status.
- **Run workflow for these 5 bidders** — Bulk run: one run per input (e.g. list of companies).
- **Notification settings** — Get or set "notify when workflow completes" and "daily digest".
- **Is everything okay?** / **Why isn't my schedule running?** — System status (run counts, scheduler note).
- **Help me run workflow 1** — Guided: Flo asks for each required input, then confirms and runs.

---

## User Tracking

### Workflows
- `user_id` - Who started the workflow

### Tasks
- `assigned_to_user_id` - Who claimed the task
- `completed_by_user_id` - Who completed the task

---

## Web UI

```
http://localhost:8002/workflows/runs/       # Your workflow runs
http://localhost:8002/workflows/schedules/  # Scheduled workflows
http://localhost:8002/workflows/tasks/      # Active tasks
http://localhost:8002/workflows/tasks/?status=all  # All tasks
```

---

## Common Flows

### Execute and Complete Workflow:
```bash
1. /workflow list
2. Switch to Flo: "run workflow 1 for ABC Corp on property 12345"
3. Wait 5-10 seconds
4. /task list
5. /task claim <task_id>
6. /task submit <task_id> approve
```

### Monitor Your Activity:
```bash
/workflow runs        # See your workflow executions
/task list all        # See all your tasks
```

### Admin Oversight:
```bash
/workflow runs all    # See all users' workflows
/workflow runs user 5 # See User 5's workflows
```

---

**Full Guide**: See `WORKFLOW_AND_TASK_GUIDE.md` for complete documentation.
