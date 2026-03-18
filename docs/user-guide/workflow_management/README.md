# Workflow Management Documentation

This directory contains all documentation related to workflow execution, task management, and user tracking.

## Quick Links

### Main Guides
- **[Quick Reference Card](QUICK_REFERENCE.md)** - One-page command reference - START HERE
- **[Workflow & Task Management Guide](WORKFLOW_AND_TASK_GUIDE.md)** - Complete comprehensive reference
- **[Test Suite Documentation](TEST_SUITE.md)** - Test suite details and running tests

### Implementation Details
- **[Workflows UI Implementation](WORKFLOWS_UI_IMPLEMENTATION.md)** - Historical: Initial UI implementation (Feb 2026)

## Quick Command Reference

### Workflows:
```bash
/workflow list              # List available workflows
/workflow runs              # Your workflow runs
/workflow runs all          # All users' runs (admin)
```

### Tasks:
```bash
/task list                  # Your active tasks
/task list all              # All your tasks
/task claim <task_id>       # Claim a task
/task submit <task_id> approve  # Submit decision
/task delete <task_id>      # Delete completed task
```

## Testing

Run the complete test suite:
```bash
cd agent_ui
python manage.py test agent_app.tests.test_workflow_commands
```

See the main guide for complete documentation.
