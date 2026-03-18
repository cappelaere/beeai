# Code Refactoring Plan - PEP 8 & Best Practices

**Date**: February 21, 2026  
**Goal**: Refactor codebase to follow PEP 8, reduce complexity, and improve maintainability

---

## Current Issues

### File Size Violations (>1000 lines)

| File | Lines | Target | Priority |
|------|-------|--------|----------|
| `agent_ui/agent_app/views.py` | 3,537 | <1000 | **HIGH** |
| `tools/workflow_tools.py` | 1,171 | <1000 | **HIGH** |

### Complexity Violations (C901 >10)

| File | Function | Complexity | Target | Priority |
|------|----------|------------|--------|----------|
| `views.py` | `chat_api` | 32 | ≤10 | **CRITICAL** |
| `views.py` | `dashboard_view` | 19 | ≤10 | **HIGH** |
| `views.py` | `workflow_create` | 12 | ≤10 | **MEDIUM** |
| `views.py` | `docs_view` | 11 | ≤10 | **MEDIUM** |
| `workflow_tools.py` | `manage_workflow_run` | 19 | ≤10 | **HIGH** |
| `workflow_tools.py` | `perform_action` | 16 | ≤10 | **HIGH** |

### Style Violations

- `views.py`: 116 line-too-long violations (E501)
- Various files: Missing type hints, inconsistent formatting

---

## Refactoring Strategy

### Phase 1: Setup & Configuration ✅

**Status**: Complete

- [x] Install Ruff
- [x] Create `pyproject.toml` with configuration
  - Max complexity: 10
  - Line length: 100
  - PEP 8 rules enabled
  - Security checks enabled

---

### Phase 2: Split Large Files

#### A. Split `views.py` (3,537 lines → 4-5 files)

**New Structure:**
```
agent_ui/agent_app/views/
├── __init__.py           # Import all views
├── chat_views.py         # Chat & messaging (~500 lines)
├── agent_views.py        # Agent management (~400 lines)
├── workflow_views.py     # Workflow management (~600 lines)
├── document_views.py     # Documents & library (~300 lines)
├── admin_views.py        # Dashboard, settings, metrics (~500 lines)
└── api_views.py          # API endpoints (~800 lines)
```

**Responsibilities:**

1. **chat_views.py**: Chat interface, sessions, messages
2. **agent_views.py**: Agent collection, studio, CRUD
3. **workflow_views.py**: Workflows, runs, execution
4. **document_views.py**: Document upload, library, RAG
5. **admin_views.py**: Dashboard, settings, metrics, health
6. **api_views.py**: All JSON API endpoints

#### B. Split `workflow_tools.py` (1,171 lines → 3 files)

**New Structure:**
```
tools/
├── workflow_tools.py     # Main workflow tools (<400 lines)
├── workflow_actions.py   # Action handlers (<400 lines)
└── workflow_helpers.py   # Helper functions (<400 lines) [EXISTS]
```

**Move:**
- `manage_workflow_run` → workflow_actions.py
- Helper functions → workflow_helpers.py (already exists)
- Keep core tools in workflow_tools.py

---

### Phase 3: Reduce Complexity

#### A. Refactor `chat_api` (Complexity: 32 → <10)

**Extract functions:**
```python
def _validate_chat_request(request) -> tuple[dict, str]:
    """Validate and parse chat request."""
    
def _get_or_create_session(user_id, session_id) -> ChatSession:
    """Get existing or create new chat session."""
    
def _check_cache_for_response(cache_key) -> dict | None:
    """Check Redis cache for existing response."""
    
def _execute_agent_and_cache(prompt, agent_type, context, cache_key):
    """Execute agent and cache the response."""
    
def _save_chat_messages(session, prompt, response, model_id):
    """Save user and assistant messages to database."""
```

**Refactored:**
```python
@require_http_methods(["POST"])
def chat_api(request):
    # Parse and validate
    data, error = _validate_chat_request(request)
    if error:
        return JsonResponse({"error": error}, status=400)
    
    # Get/create session
    session = _get_or_create_session(data['user_id'], data.get('session_id'))
    
    # Check cache
    cached_response = _check_cache_for_response(cache_key)
    if cached_response:
        return JsonResponse(cached_response)
    
    # Execute agent
    response = _execute_agent_and_cache(...)
    
    # Save messages
    _save_chat_messages(session, data['prompt'], response, model_id)
    
    return JsonResponse(response)
```

#### B. Refactor `dashboard_view` (Complexity: 19 → <10)

**Extract calculators:**
```python
def _calculate_message_stats(user_id) -> dict:
    """Calculate message and session statistics."""
    
def _calculate_feedback_stats(user_id) -> dict:
    """Calculate user feedback statistics."""
    
def _calculate_performance_stats(user_id) -> dict:
    """Calculate response time and token usage."""
    
def _get_recent_activity(user_id) -> list:
    """Get recent session activity."""
    
def _calculate_system_stats() -> dict:
    """Calculate document, card, and DB statistics."""
```

#### C. Refactor `manage_workflow_run` (Complexity: 19 → <10)

**Extract action handlers:**
```python
def _handle_workflow_pause(run_id, user_id) -> dict:
    """Handle pause action."""
    
def _handle_workflow_resume(run_id, user_id) -> dict:
    """Handle resume action."""
    
def _handle_workflow_cancel(run_id, user_id) -> dict:
    """Handle cancel action."""
    
def _handle_workflow_retry(run_id, user_id) -> dict:
    """Handle retry action."""
```

---

### Phase 4: Apply PEP 8 Formatting

```bash
# Format all Python files
ruff format .

# Fix auto-fixable issues
ruff check . --fix

# Check remaining issues
ruff check .
```

---

### Phase 5: Testing & Validation

```bash
# Run test suite
make test-backend

# Check specific modules
python -m pytest agent_ui/agent_app/tests/

# Validate no regressions
make test
```

---

## Implementation Order

1. ✅ Create `pyproject.toml` with Ruff config
2. ⏳ Extract complex function helpers (reduce complexity first)
3. ⏳ Split large files into modules (improve organization)
4. ⏳ Run Ruff format and auto-fix
5. ⏳ Run tests to ensure no breakage
6. ⏳ Document changes

---

## Metrics to Track

### Before Refactoring
- `views.py`: 3,537 lines
- `workflow_tools.py`: 1,171 lines
- Complexity violations: 6
- Line-too-long violations: 116

### Target After Refactoring
- All files: <1000 lines
- All functions: Complexity ≤10
- Line length: ≤100 chars
- PEP 8 compliant
- All tests passing

---

**Status**: In Progress  
**Next**: Start with complexity reduction, then file splitting
