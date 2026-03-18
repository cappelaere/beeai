# Workflow Templates

Use these templates when creating new workflows.

## Available Templates

### 1. User Story Template
**File**: `USER_STORY_TEMPLATE.md`

Start here when creating a new workflow. Define:
- User story (As a... I want... so that...)
- Business value (quantifiable benefits)
- Acceptance criteria (testable requirements)
- Current vs automated process
- Success metrics

### 2. Workflow Documentation Template
**File**: `WORKFLOW_DOCUMENTATION_TEMPLATE.md`

Use for complete technical documentation. Includes:
- Overview & purpose
- Process flow with Mermaid diagrams
- Input/output specifications
- State management details
- Error handling strategy
- Testing approach
- Usage examples

### 3. Run result template (optional)
**File**: `workflows/<workflow_id>/run_result.html`

Optional Django HTML fragment to customize how a completed run’s output is shown on the run detail page. If present, it is included instead of the generic key/value table. Example: `workflows/bi_weekly_report/run_result.html`. Context: `run` (WorkflowRun with `output_data`). Use `{% load markdown_filters %}` for markdown fields.

## Usage

```bash
# Copy templates to your new workflow directory
cp templates/USER_STORY_TEMPLATE.md my_workflow/USER_STORY.md
cp templates/WORKFLOW_DOCUMENTATION_TEMPLATE.md my_workflow/documentation.md

# Edit and customize
```

See `../docs/DEVELOPER_GUIDE.md` for complete workflow development guide.
