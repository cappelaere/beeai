# Workflow Development Documentation

This directory contains guides and references for developing BeeAI workflows.

## Quick Links

### Main Guides
- **[How to start a new workflow](DEVELOPER_GUIDE.md#how-to-start-a-new-workflow)** - Workflow Studio (recommended) or manual steps ⭐ START HERE
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Full workflow development guide
- **[Implementation History](IMPLEMENTATION_HISTORY.md)** - Historical implementation details

### Templates
- See `../templates/` for workflow templates (used when creating manually)

### Examples
- See `../EXAMPLES.md` for 7 detailed workflow examples
- See `../bidder_onboarding/` for production implementation

---

## What's in Developer Guide

The Developer Guide covers:
- **How to start a new workflow** – Workflow Studio (AI-generated BPMN + code) or manual creation
- User story driven development
- Documentation structure
- BPMN 2.0 and bindings (primary); Mermaid optional
- Implementation patterns
- Testing strategies
- Accessibility compliance
- Async execution
- Best practices

---

## Quick Reference

### Create new workflow (recommended: Workflow Studio)
- Log in as **admin** → **Workflows** → **Workflow Studio** (`/workflows/studio/`). Fill the form; the app generates BPMN, `workflow.py`, README, and metadata.

### Create new workflow (manual):
```bash
# 1. Create directory
mkdir workflows/my_workflow

# 2. Copy templates
cp templates/USER_STORY_TEMPLATE.md my_workflow/USER_STORY.md
cp templates/WORKFLOW_DOCUMENTATION_TEMPLATE.md my_workflow/documentation.md

# 3. Add currentVersion/workflow.bpmn and bpmn-bindings.yaml (see Developer Guide)
```

### Key files (Studio-generated or manual):
- `workflow.py` - Implementation
- `metadata.yaml` - Configuration
- `currentVersion/workflow.bpmn` - BPMN 2.0 diagram (primary)
- `currentVersion/bpmn-bindings.yaml` - BPMN task → handler bindings
- `README.md` - Quick reference
- `USER_STORY.md` / `documentation.md` - Optional; add for manual workflows

---

See [Developer Guide](DEVELOPER_GUIDE.md) for complete documentation.
