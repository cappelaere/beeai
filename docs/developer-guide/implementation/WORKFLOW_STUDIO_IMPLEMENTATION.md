# Workflow Studio Implementation

Successfully implemented Workflow Studio - an admin-only interface for creating AI-generated workflows in RealtyIQ.

**Status**: Enabled and functional  
**Date**: February 21, 2026

---

## Overview

Workflow Studio allows administrators to create new workflows by providing a description and requirements. The system uses Claude to generate:
- Complete workflow implementation (`workflow.py`)
- Metadata configuration (`metadata.yaml`)
- Documentation (`README.md`, `USER_STORY.md`, `documentation.md`)
- BPMN 2.0 diagram (`currentVersion/workflow.bpmn`) and handler bindings (`currentVersion/bpmn-bindings.yaml`)

---

## What Was Implemented

### 1. Navigation Link

**File**: `agent_ui/templates/base.html`

Enabled the Workflow Studio link in the Workflows section:
- Admin-only visibility (`{% if user_role == 'admin' %}`)
- Active link to `{% url 'workflow_studio' %}`
- Positioned after "Previous Runs" in Workflows section

### 2. Studio Page

**File**: `agent_ui/templates/workflows/studio.html`

Created complete workflow creation interface with:

**Form Fields:**
- Workflow Name (text input)
- Workflow ID (auto-generated from name, lowercase with underscores)
- Icon Emoji (single emoji)
- Category (dropdown: Compliance, Verification, Analysis, Approval, etc.)
- Description (textarea)
- Workflow Generation Prompt (large textarea with detailed requirements)

**Features:**
- Auto-generation of workflow ID from name
- Pattern validation for workflow ID
- Real-time status messages (info, success, error)
- Loading state during generation
- Responsive grid layout (form + info panel)
- Bootstrap 5 styling consistent with Agent Studio

**Info Panel:**
- What gets created (file structure)
- After creation (where workflow appears)
- Tips for effective prompt writing
- Example workflows for reference
- Link to context guidelines

### 3. Backend Views

**Files**: `agent_ui/agent_app/views/api_workflows.py` (API), `agent_ui/agent_app/views/workflows.py` (studio page), `agent_ui/agent_app/services/workflow_service.py` (business logic)

The workflow studio page and create API are implemented as follows:

#### `workflow_studio(request)` (in `workflows.py`)
- Admin-only access check
- Redirects non-admin users to workflows list
- Renders `workflows/studio.html` template

#### `workflow_create(request)` (in `api_workflows.py`)
- POST endpoint at `/api/workflows/create/` (or equivalent from `urls.py`)
- Admin-only authorization
- Parses and validates input, then delegates to `workflow_service.create_workflow()`

**AI Generation Process (in `workflow_service.py`):**
1. Loads context from `context/CONTEXT.md` and `context/WORKFLOW_GUIDELINES.md` (first 3000 chars each)
2. Generates `workflow.py` with comprehensive prompt (RealtyIQ context, guidelines, user requirements)
3. Generates `README.md` with usage documentation
4. Generates BPMN 2.0 XML via BPMN tools (e.g. `tools.bpmn_tools.create_new_bpmn_impl`)
5. Generates `USER_STORY.md` (business value first template)
6. Creates `metadata.yaml`, `documentation.md`, and all workflow files
7. Creates `currentVersion/workflow.bpmn` and `currentVersion/bpmn-bindings.yaml` with serviceTask IDs from the generated workflow
8. Reloads the workflow registry so the new workflow appears immediately

**Generated Files:**
```
workflows/<workflow_id>/
├── __init__.py              # Python package marker
├── workflow.py              # AI-generated implementation
├── metadata.yaml            # Workflow configuration
├── README.md                # AI-generated documentation
├── USER_STORY.md            # AI-generated user story
├── documentation.md         # Technical documentation
└── currentVersion/
    ├── workflow.bpmn        # BPMN 2.0 diagram (used by UI and runner)
    └── bpmn-bindings.yaml   # BPMN element → handler bindings
```
The UI and execution engine use `workflow.bpmn` and `bpmn-bindings.yaml` from `currentVersion/` (or version folders). Mermaid (`diagram.mmd`) is not generated; BPMN 2.0 is the single source of truth.

**Fallback Handling:**
- If LLM generation fails, creates basic template files
- Ensures workflow structure is always created
- Logs errors for debugging

### 4. URL Configuration

**File**: `agent_ui/agent_app/urls.py`

Added two new routes:
- `workflows/studio/` → `workflow_studio` view (page)
- `api/workflows/create/` → `workflow_create` view (API)

### 5. Workflows List Enhancement

**File**: `agent_ui/templates/workflows/list.html`

Added "Create New Workflow" button:
- Admin-only visibility
- Positioned in page header next to title
- Links to Workflow Studio
- Consistent styling with Agent Collection

**Updated CSS:**
- Page header now uses flexbox layout
- Button positioned on the right
- Responsive design maintained

**File**: `agent_ui/agent_app/views/workflows.py` (or equivalent) - `workflows_list` view

Added `user_role` to template context for admin check.

---

## User Flow

### Creating a Workflow

1. **Navigate**: Admin user clicks "Workflow Studio" in left navigation
2. **Fill Form**: Enter workflow details:
   - Name (e.g., "Property Due Diligence")
   - ID auto-generates (e.g., "property_due_diligence")
   - Select icon emoji (e.g., 🔍)
   - Choose category (e.g., "Analysis")
   - Write description
   - Write detailed generation prompt with steps, agents, logic
3. **Submit**: Click "Create Workflow" button
4. **Generation**: System shows "Creating workflow... This may take 1-2 minutes"
5. **AI Processing**:
   - Reads context documentation
   - Generates workflow.py implementation
   - Generates README.md, USER_STORY.md, and documentation
   - Generates BPMN 2.0 diagram and bindings; creates metadata.yaml and all files in currentVersion/
6. **Completion**: Success message and redirect to workflows list
7. **Result**: New workflow appears in workflow list, ready to use

### Example Prompt

```
This workflow handles property due diligence before auction listing:

Steps:
1. Validate property data (agent: gres) - Check all required fields
2. Title search (external API call) - Verify clean title
3. Environmental screening - Check EPA database
4. Market analysis (agent: gres) - Pull comparable sales
5. Human review task - Specialist approves findings
6. Generate final report

If any automated step fails, create a task for manual review.
Use parallel execution for independent checks (title, environmental, market).
Include proper error handling and retry logic.
```

---

## Technical Details

### LLM Configuration

**Model**: `claude-sonnet-4-20250514`

**Max Tokens:**
- workflow.py generation: 8000 tokens
- README.md generation: 3000 tokens

**Context Included:**
- Application context (3000 chars from CONTEXT.md)
- Workflow guidelines (3000 chars from WORKFLOW_GUIDELINES.md)
- User requirements (full prompt)
- Workflow specifications (name, ID, category, description)

### Validation

**Workflow ID:**
- Must start with lowercase letter
- Can contain lowercase letters, numbers, underscores
- Regex pattern: `^[a-z][a-z0-9_]*$`

**Directory Check:**
- Verifies workflow directory doesn't already exist
- Creates directory with proper permissions

**Authentication:**
- Admin role required for both page and API
- Returns 403 for unauthorized users

### File Generation

**__init__.py:**
```python
"""Workflow: <Workflow Name>"""
```

**metadata.yaml:**
```yaml
id: workflow_id
name: Workflow Name
description: Description text
icon: 🔄
category: Category
version: "1.0"
estimated_duration: "To be determined"

input_schema:
  # TODO: Define input parameters

output_schema:
  status:
    type: string
    description: Workflow execution status
  message:
    type: string
    description: Human-readable result message
  data:
    type: object
    description: Workflow output data
```

**BPMN and bindings:** The UI and runner load `currentVersion/workflow.bpmn` (BPMN 2.0 XML) and `currentVersion/bpmn-bindings.yaml` (serviceTask id → handler method). The registry resolves the version folder (`currentVersion/` or `v1/`, `v2/`, etc.) when loading workflows.

---

## Integration with Context System

The workflow generation leverages the `/context` folder:

**Used During Generation:**
1. `context/CONTEXT.md` - Application overview and architecture
2. `context/WORKFLOW_GUIDELINES.md` - Design patterns and best practices

**Benefits:**
- Generated code follows RealtyIQ conventions
- Uses appropriate agents for steps
- Implements proper error handling
- Includes comprehensive logging
- Production-ready code structure

---

## Security

### Admin-Only Access

- Both UI page and API require `user_role == 'admin'`
- Non-admin users redirected to workflows list
- 403 Forbidden for unauthorized API calls

### Input Validation

- All fields required (name, ID, icon, category, description, prompt)
- Workflow ID format validated with regex
- Directory existence checked before creation
- Proper error messages for validation failures

---

## Testing

### Manual Testing Checklist

- [ ] Workflow Studio link visible only to admin users
- [ ] Non-admin users cannot access studio page
- [ ] Form validation works (required fields, ID format)
- [ ] Workflow ID auto-generates from name
- [ ] Submit button shows loading state
- [ ] Status messages display correctly
- [ ] Workflow files created in correct location
- [ ] Generated workflow.py is valid Python
- [ ] Generated README.md is properly formatted
- [ ] New workflow appears in workflows list
- [ ] Workflow is executable via Flo agent

### API Testing

```bash
# Test workflow creation (as admin)
curl -X POST http://localhost:8002/api/workflows/create/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -d '{
    "name": "Test Workflow",
    "workflow_id": "test_workflow",
    "icon": "🧪",
    "category": "Testing",
    "description": "Test workflow for validation",
    "prompt": "Simple test workflow with one step"
  }'
```

---

## Files Modified

1. `agent_ui/templates/base.html`
   - Enabled Workflow Studio link (admin-only)

2. `agent_ui/templates/workflows/studio.html`
   - Created complete studio page with form

3. `agent_ui/templates/workflows/list.html`
   - Added "Create New Workflow" button (admin-only)
   - Updated CSS for header layout

4. `agent_ui/agent_app/views/workflows.py`
   - Added `workflow_studio()` view (studio page)

5. `agent_ui/agent_app/views/api_workflows.py`
   - Added `workflow_create()` API endpoint; delegates to workflow_service

6. `agent_ui/agent_app/services/workflow_service.py`
   - Business logic: `create_workflow()`, validation, LLM generation, file creation, registry reload

7. `agent_ui/agent_app/urls.py`
   - Added `workflows/studio/` route
   - Added `api/workflows/create/` route

---

## Future Enhancements

### Visual Workflow Builder
- Drag-and-drop step designer
- Visual connection lines
- Step configuration modals
- Live validation
- Preview mode

### Enhanced Generation
- Tool selection UI
- Agent assignment per step
- Task template selection
- Input/output schema builder
- Conditional logic builder

### Workflow Management
- Edit existing workflows
- Version control
- Clone/duplicate workflows
- Import/export workflows
- Workflow analytics

---

## Usage Examples

### Example 1: Compliance Workflow

**Input:**
- Name: "Environmental Compliance Check"
- ID: "environmental_compliance_check"
- Category: "Compliance"
- Prompt: "Create a workflow that checks properties for environmental compliance. Steps: 1) Query EPA database, 2) Check for contamination records, 3) Human review if issues found, 4) Generate compliance report."

**Output:**
- Complete workflow implementation with EPA tool integration
- Human task creation for flagged properties
- Structured compliance report output

### Example 2: Multi-Stage Approval

**Input:**
- Name: "High-Value Property Approval"
- ID: "high_value_approval"
- Category: "Approval"
- Prompt: "Multi-level approval for properties over $1M. Steps: 1) Validate property data, 2) Specialist review (task), 3) If approved, manager review (task), 4) Final status update."

**Output:**
- Workflow with conditional branching based on value
- Multiple human review tasks
- Proper state management between steps

---

## Troubleshooting

### Workflow Generation Fails

**Symptom**: Error message after submitting form

**Possible Causes:**
- LLM API key not configured
- Network connectivity issues
- Invalid prompt (too short or unclear)

**Solutions:**
1. Check `ANTHROPIC_API_KEY` in `.env`
2. Review logs: `docker logs agent_ui` or check `/logs/`
3. Ensure prompt is detailed with clear step descriptions

### Generated Code Invalid

**Symptom**: Workflow created but has syntax errors

**Solutions:**
1. Review generated `workflow.py` for syntax issues
2. Manually fix or regenerate with clearer prompt
3. Reference `context/WORKFLOW_GUIDELINES.md` for patterns
4. Check existing workflows for examples

### Workflow Not Appearing in List

**Symptom**: Workflow created but not visible

**Possible Causes:**
- Workflow registry not refreshed
- metadata.yaml missing or invalid
- Workflow directory permissions
- Registry loads BPMN from `currentVersion/` (or version folders) and requires valid `metadata.yaml` and a loadable executor class

**Solutions:**
1. Restart server to reload workflows
2. Verify `metadata.yaml` is valid YAML and contains required fields (id, name, description)
3. Check directory exists: `workflows/<workflow_id>/` and `workflows/<workflow_id>/currentVersion/` with `workflow.bpmn` and `bpmn-bindings.yaml`
4. Check workflow registry loading logic and executor import (workflow module must define the executor class referenced in bindings)

---

## Related Documentation

- [Workflow Guidelines](../../context/WORKFLOW_GUIDELINES.md) - Design patterns
- [Context Documentation](../../context/CONTEXT.md) - Application context
- [Workflow Developer Guide](../../../workflows/docs/DEVELOPER_GUIDE.md) - Development guide
- [Agent Studio Implementation](AGENT_STUDIO_IMPLEMENTATION.md) - Similar feature (if exists)

---

**Version**: 1.0  
**Implemented**: February 21, 2026  
**Status**: Production-ready
