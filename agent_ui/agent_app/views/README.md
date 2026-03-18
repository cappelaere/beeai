# Views Module - Refactored Structure

This directory contains the refactored views from the monolithic `views.py` file.

## Quick Reference

### Import Examples
```python
# All imports work as before (backward compatible)
from agent_app.views import chat_api, dashboard_view, agents_list

# Or import from specific modules
from agent_app.views.api_chat import chat_api
from agent_app.views.admin import dashboard_view
from agent_app.views.agents import agents_list
```

## Module Guide

| Module | What It Contains |
|--------|------------------|
| `chat.py` | Main chat interface view |
| `api_chat.py` | Chat API with message processing |
| `api_sessions.py` | Session create/read/update/delete |
| `agents.py` | Agent browsing and detail views |
| `api_agents.py` | Agent management endpoints |
| `api_cards.py` | Assistant cards API |
| `prompts.py` | Prompt library management |
| `messages.py` | Message feedback and TTS |
| `documents.py` | Document upload/library |
| `workflows.py` | Workflow execution views |
| `api_workflows.py` | Workflow creation API |
| `tasks.py` | Human task interface |
| `admin.py` | Dashboard, settings, logs |
| `api_system.py` | System APIs (cache, 508, etc) |

## Complexity Improvements

- `chat_api`: 32 → 11 (66% reduction)
- `dashboard_view`: 19 → 7 (63% reduction)
- `workflow_create`: 12 → 7 (42% reduction)
- `docs_view`: 11 → 6 (45% reduction)

## File Sizes

All modules are under 1000 lines:
- Largest: `workflows.py` (907 lines)
- Smallest: `chat.py` (47 lines)
- Average: ~424 lines per module

See `REFACTORING_SUMMARY.md` for complete details.
