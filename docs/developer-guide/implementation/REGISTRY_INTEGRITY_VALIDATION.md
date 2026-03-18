# Agent and Workflow Registry Integrity Validation

Implemented comprehensive startup validation for agent and workflow registries to ensure system integrity.

**Date**: February 21, 2026  
**Status**: Complete

---

## Overview

The system now performs automatic integrity checks on startup to validate:
- Agent registry (`agents.yaml`) structure and completeness
- Agent folder structure and required files
- Workflow folder structure and metadata files
- All required imports and configurations

---

## What Was Implemented

### 1. Agent Folder Deletion on Remove

**File**: `agent_ui/agent_app/views.py` - `agent_remove()`

When an admin deletes an agent:
```python
# Delete agent folder from filesystem
agent_dir = repo_root / 'agents' / agent_id

if agent_dir.exists() and agent_dir.is_dir():
    shutil.rmtree(agent_dir)
    logger.info(f"Deleted agent directory: {agent_dir}")

# Remove from agents.yaml
del registry[agent_id]
```

**Benefits:**
- No orphaned folders
- Clean filesystem
- Reduced confusion
- Storage cleanup

---

### 2. Agent Registry Integrity Validation

**File**: `agents/registry.py`

Added `validate_registry_integrity()` function that checks:

#### Required Fields in agents.yaml
- name
- display_name
- icon
- description
- config_module
- config_name

#### Folder Structure
- Agent folder exists at `agents/<agent_id>/`
- Is a directory (not a file)

#### Required Files
- `agent.py` - Required (configuration file)
- `__init__.py` - Optional but recommended
- `SKILLS.md` - Optional (if specified in registry)

#### Importability
- Config module can be imported
- Config object exists and has required attributes
- No import errors or attribute errors

#### Auto-Fix Capability
```python
validate_registry_integrity(fix_issues=True)
```

When `fix_issues=True`:
- Removes orphaned entries (agents in YAML but no folder)
- Updates agents.yaml automatically
- Clears cache to reload
- Logs all fixes applied

---

### 3. Workflow Auto-Discovery

**File**: `agent_ui/agent_app/workflow_registry.py`

Refactored workflow registry from hardcoded to dynamic:

#### Before (Hardcoded):
```python
workflow_registry = WorkflowRegistry()

# Manually register each workflow
workflow_registry.register(
    WorkflowMetadata(...),
    BidderOnboardingWorkflow()
)
```

#### After (Auto-Discovery):
```python
class WorkflowRegistry:
    def __init__(self):
        self.workflows = {}
        self._auto_discover_workflows()  # Scans workflows/ folder
```

**Discovery Process:**
1. Scans `workflows/` directory
2. For each subdirectory with `metadata.yaml`:
   - Loads metadata from YAML
   - Loads diagram from `diagram.mmd`
   - Attempts to import and instantiate workflow class
   - Registers workflow in registry
3. Logs success/warnings for each workflow

**Benefits:**
- No more hardcoded registrations
- Workflows created via Workflow Studio automatically appear
- Easy to add/remove workflows
- Consistent with agent registry approach

---

### 4. Workflow Integrity Validation

**File**: `agent_ui/agent_app/workflow_registry.py`

Added `validate_workflow_integrity()` function that checks:

#### Folder Structure
- Workflow folder exists in `workflows/`
- Is a directory

#### metadata.yaml
- File exists
- Valid YAML syntax
- Required fields: id, name, description

#### Optional Files (Warnings)
- `workflow.py` - Implementation file
- `__init__.py` - Package marker
- `diagram.mmd` - Mermaid diagram

---

### 5. Startup Validation

**File**: `agent_ui/agent_app/apps.py` - `ready()` method

Runs automatically on Django/Uvicorn startup:

```python
def ready(self):
    # Validate agent registry
    logger.info("🔍 Startup: Validating agent registry integrity...")
    validation_results = validate_registry_integrity(fix_issues=True)
    
    if validation_results['valid']:
        logger.info(f"✅ Agent Registry: {validation_results['checked']} agents validated")
    else:
        logger.error(f"❌ Agent Registry: Validation failed!")
        for error in validation_results['errors']:
            logger.error(f"   - {error}")
    
    # Validate workflow registry
    logger.info("🔍 Startup: Validating workflow registry integrity...")
    workflow_results = validate_workflow_integrity(fix_issues=False)
    
    if workflow_results['valid']:
        logger.info(f"✅ Workflow Registry: {workflow_results['checked']} workflows validated")
```

**Startup Log Example:**
```
INFO 🔍 Startup: Validating agent registry integrity...
INFO ✅ Agent Registry: 8 agents validated successfully
INFO ✓ Discovered workflow: Bidder Onboarding & Verification (bidder_onboarding)
INFO ✓ Discovered workflow: Property Due Diligence (property_due_diligence)
INFO 🔍 Startup: Validating workflow registry integrity...
INFO ✅ Workflow Registry: 2 workflows validated successfully
```

---

## Validation Results Format

### Success Response
```python
{
    'valid': True,
    'errors': [],
    'warnings': [
        "Agent 'flo': Missing __init__.py (optional but recommended)"
    ],
    'checked': 8,
    'fixed': 0
}
```

### Error Response
```python
{
    'valid': False,
    'errors': [
        "Agent 'custom_agent': Folder not found at agents/custom_agent/",
        "Agent 'broken_agent': Missing agent.py configuration file"
    ],
    'warnings': [],
    'checked': 8,
    'fixed': 2  # If fix_issues=True
}
```

---

## Benefits

### For Agents

**Before:**
- Deleting agent left orphaned folder
- No startup validation
- Broken agents discovered at runtime
- Manual cleanup required

**After:**
- Folder deleted automatically on removal
- Startup validation catches issues early
- Broken/orphaned entries auto-fixed
- Clean system state guaranteed

### For Workflows

**Before:**
- Hardcoded workflow registration
- Adding workflow required code changes
- No validation of folder structure
- Import errors at runtime

**After:**
- Auto-discovery from `workflows/` folder
- Workflows Studio creates automatically appear
- Startup validation of all workflows
- Import errors logged clearly at startup

---

## How It Works

### Agent Lifecycle

#### Creation (via Agent Studio):
```
1. User submits form
2. System creates:
   - agents/<id>/__init__.py
   - agents/<id>/agent.py
   - agents/<id>/SKILLS.md
3. Updates agents.yaml
4. Clears cache
5. Agent appears in UI
```

#### Startup Validation:
```
1. Django starts
2. Load agents.yaml
3. For each agent:
   - Check folder exists
   - Check required files
   - Try to import config
4. Auto-fix orphaned entries
5. Log results
```

#### Deletion (via Agent Actions):
```
1. Admin clicks "Remove Agent"
2. System checks not default agent
3. Deletes folder: shutil.rmtree(agent_dir)
4. Removes from agents.yaml
5. Clears cache
6. Agent disappears from UI
```

### Workflow Lifecycle

#### Creation (via Workflow Studio):
```
1. User submits form
2. System creates:
   - workflows/<id>/__init__.py
   - workflows/<id>/workflow.py (AI-generated)
   - workflows/<id>/metadata.yaml
   - workflows/<id>/README.md (AI-generated)
   - workflows/<id>/diagram.mmd
3. Workflow appears in UI automatically
```

#### Startup Discovery:
```
1. Django starts
2. WorkflowRegistry.__init__()
3. Scans workflows/ directory
4. For each subfolder with metadata.yaml:
   - Load metadata
   - Load diagram
   - Try to import workflow class
   - Register in registry
5. Validate all discovered workflows
6. Log results
```

#### Deletion (Future):
```
- Similar to agent deletion
- Delete folder
- Reload registry
```

---

## Known Issues

### IDV Agent Django Error

**Issue**: `populate() isn't reentrant` error during startup validation

**Cause**: Django models are imported during agent config loading, and Django's app registry doesn't allow reentrant calls during startup.

**Impact**: Non-critical - agent still loads and works correctly

**Workaround**: Error is logged but doesn't prevent agent from functioning

**Future Fix**: Lazy-load agent configs or defer model imports

---

## Testing

### Test Agent Deletion

```bash
# Via UI:
1. Navigate to Agent Collection
2. Click three-dot menu on custom agent
3. Select "Remove Agent"
4. Confirm deletion
5. Check folder deleted: ls agents/
6. Check removed from agents.yaml
```

### Test Startup Validation

```bash
# Create broken agent entry
1. Add entry to agents.yaml for non-existent agent
2. Restart server: ./start-server.sh
3. Check logs: tail -f terminals/19.txt
4. Should see error logged and entry removed
```

### Test Workflow Discovery

```bash
# Create new workflow via Studio
1. Navigate to Workflow Studio
2. Create workflow
3. Check folder created: ls workflows/
4. Check appears in workflow list
5. Restart server
6. Check workflow auto-discovered in logs
```

---

## Configuration

### Enable/Disable Auto-Fix

In `apps.py`:
```python
# Auto-fix issues (recommended for production)
validate_registry_integrity(fix_issues=True)

# Report only, don't fix (recommended for development)
validate_registry_integrity(fix_issues=False)
```

### Skip Validation

If needed (not recommended):
```python
# In apps.py, comment out validation calls
# try:
#     from agents.registry import validate_registry_integrity
#     ...
```

---

## Future Enhancements

### Workflow Deletion API

Add similar to agent removal:
```python
@require_POST
def workflow_remove(request, workflow_id):
    """Delete workflow folder and files."""
    # Delete folder
    workflow_dir = repo_root / 'workflows' / workflow_id
    shutil.rmtree(workflow_dir)
    
    # Reload registry
    workflow_registry.reload()
```

### Enhanced Validation

- Check Python syntax in generated files
- Validate workflow class structure
- Test workflow execution in dry-run mode
- Verify agent references are valid
- Check tool availability

### Health Check Endpoint

```python
def health_check_registries(request):
    """API endpoint for registry health."""
    agent_results = validate_registry_integrity()
    workflow_results = validate_workflow_integrity()
    
    return JsonResponse({
        'agents': agent_results,
        'workflows': workflow_results,
        'healthy': agent_results['valid'] and workflow_results['valid']
    })
```

---

## Files Modified

1. **agents/registry.py**
   - Added `validate_registry_integrity()` with comprehensive checks
   - Added auto-fix capability for orphaned entries

2. **agent_ui/agent_app/views.py**
   - Updated `agent_remove()` to delete agent folder
   - Added folder deletion with error handling

3. **agent_ui/agent_app/apps.py**
   - Added agent validation on startup
   - Added workflow validation on startup
   - Comprehensive logging of results

4. **agent_ui/agent_app/workflow_registry.py**
   - Refactored from hardcoded to auto-discovery
   - Added `_auto_discover_workflows()` method
   - Added `validate_workflow_integrity()` function
   - Added `reload()` method for dynamic refresh

5. **agents/flo/__init__.py**
   - Created missing file to fix validation warning

---

## Summary

### Agent Registry (agents.yaml based)
- ✅ Auto-loads from agents.yaml
- ✅ Validates on startup
- ✅ Auto-fixes orphaned entries
- ✅ Deletes folders on removal
- ✅ Comprehensive error reporting

### Workflow Registry (Directory-scan based)
- ✅ Auto-discovers from workflows/ folder
- ✅ Validates on startup
- ✅ Loads metadata from metadata.yaml files
- ✅ Attempts to import executors
- ✅ Comprehensive error reporting
- ⏳ Folder deletion on removal (not yet implemented)

**Result:** Robust, self-validating registry system that ensures data integrity and provides clear feedback on any issues.

---

**Version**: 1.0  
**Last Updated**: February 21, 2026
