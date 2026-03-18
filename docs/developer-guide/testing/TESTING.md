# RealtyIQ Testing Documentation

## Overview

Comprehensive test suite covering all UI features and functionality of the RealtyIQ Agent application.

## Test Structure

```
beeai/
├── agent_ui/agent_app/tests/     # Backend Django tests (141 tests)
│   ├── test_api.py               # API endpoint tests
│   ├── test_commands.py          # Command handler tests
│   ├── test_tts_integration.py   # TTS integration tests
│   ├── test_workflow_commands.py # Workflow command tests
│   └── test_models.py            # Database model tests
├── tests/                        # Frontend and E2E tests
│   ├── frontend/                 # JavaScript unit tests
│   │   ├── test_chat.spec.js
│   │   ├── test_autocomplete.spec.js
│   │   ├── test_prompt_history.spec.js
│   │   └── test_theme.spec.js
│   ├── e2e/                      # End-to-end tests
│   │   └── test_user_flows.spec.js
│   ├── package.json
│   ├── playwright.config.js
│   ├── README.md
│   └── QUICK_START.md
```

## Running Tests

### Makefile Commands

**Backend Tests** (Recommended):
```bash
make test-backend       # Django tests (~25s, 141 tests)
```

**All Tests**:
```bash
make test-all           # Backend + Frontend + E2E
```

**Individual Test Suites**:
```bash
make test-frontend      # Jest tests
make test-e2e           # Playwright tests (requires server)
```

**Direct Django Commands**:
```bash
# Run all backend tests
cd agent_ui && ../venv/bin/python manage.py test

# Run specific test file
cd agent_ui && ../venv/bin/python manage.py test agent_app.tests.test_api

# Run specific test class
cd agent_ui && ../venv/bin/python manage.py test agent_app.tests.test_api.ChatAPITests

# Run with verbosity
cd agent_ui && ../venv/bin/python manage.py test --verbosity=2

# Keep test database (faster reruns)
cd agent_ui && ../venv/bin/python manage.py test --keepdb
```

**See**: [MAKEFILE_COMMANDS.md](../MAKEFILE_COMMANDS.md) for complete reference.

## Test Coverage by Feature

### ✅ Chat Functionality
- **Backend Tests**:
  - `ChatAPITests.test_create_chat_session` - New session creation
  - `ChatAPITests.test_chat_with_existing_session` - Continue conversation
  - `ChatAPITests.test_chat_history` - Retrieve message history
  - `ChatAPITests.test_chat_empty_message` - Input validation
  
- **Frontend Tests**:
  - `test_chat.spec.js` - Message rendering, bubbles, markdown
  
- **E2E Tests**:
  - `test_user_flows.spec.js:Chat Flow` - Full chat interaction

### ✅ Session Management
- **Backend Tests**:
  - `SessionAPITests.test_create_session` - Create named session
  - `SessionAPITests.test_list_sessions` - List all sessions
  - `SessionAPITests.test_rename_session` - Rename existing session
  - `SessionAPITests.test_delete_session` - Delete session
  
- **E2E Tests**:
  - Create new session with custom name
  - Switch between sessions
  - Delete sessions with confirmation

### ✅ Feedback System (Thumbs Up/Down)
- **Backend Tests**:
  - `MessageFeedbackTests.test_positive_feedback` - Submit positive feedback
  - `MessageFeedbackTests.test_negative_feedback` - Submit negative with comment
  - `MessageFeedbackTests.test_change_feedback` - Change from positive to negative
  
- **Frontend Tests**:
  - `test_chat.spec.js:Feedback Buttons` - Button rendering and state
  
- **E2E Tests**:
  - Click thumbs up, verify active state
  - Click thumbs down, verify active state

### ✅ Autocomplete Suggestions
- **Backend Tests**:
  - `PromptSuggestionTests.test_autocomplete_suggestions` - Query suggestions
  - `PromptSuggestionTests.test_autocomplete_ordering` - Sort by usage count
  
- **Frontend Tests**:
  - `test_autocomplete.spec.js` - Dropdown, selection, keyboard navigation
  
- **E2E Tests**:
  - Type to show suggestions
  - Click suggestion to fill input

### ✅ Prompts Management Page
- **Backend Tests**:
  - `PromptsManagementTests.test_list_prompts` - List with pagination
  - `PromptsManagementTests.test_search_prompts` - Search functionality
  - `PromptsManagementTests.test_filter_predefined` - Filter by type
  - `PromptsManagementTests.test_filter_user_prompts` - Filter user prompts
  - `PromptsManagementTests.test_create_prompt` - Create new prompt
  - `PromptsManagementTests.test_update_prompt` - Edit existing prompt
  - `PromptsManagementTests.test_delete_prompt` - Delete prompt
  
- **E2E Tests**:
  - View all prompts
  - Search prompts by text
  - Filter by predefined/user/popular/feedback
  - Run prompt from prompts page
  - Delete prompt with confirmation

### ✅ Dashboard Metrics
- **Backend Tests**:
  - `DashboardAPITests.test_dashboard_view` - Page renders
  - `DashboardAPITests.test_dashboard_stats_calculation` - Correct metrics
    - Total sessions
    - Total queries
    - Total documents uploaded (count + size)
    - Positive/negative feedback counts
    - Satisfaction rate percentage
  
- **E2E Tests**:
  - Dashboard displays all metric cards
  - Session count visible
  - Documents uploaded visible

### ✅ Favorite Cards
- **Backend Tests**:
  - `AssistantCardTests.test_list_favorite_cards` - List favorites
  - `AssistantCardTests.test_update_card` - Edit card details
  - `AssistantCardModelTests.test_create_card` - Create card
  - `AssistantCardModelTests.test_favorite_cards_filter` - Filter favorites
  
- **E2E Tests**:
  - Click card to run prompt
  - Verify prompt appears in chat

### ✅ Document Management
- **Backend Tests**:
  - `DocumentAPITests.test_list_documents` - List uploaded documents
  - `DocumentAPITests.test_delete_document` - Delete document
  - `DocumentModelTests.test_create_document` - Create document record
  
- **E2E Tests**:
  - Navigate to documents page
  - View document list

### ✅ Theme Switching
- **Frontend Tests**:
  - `test_theme.spec.js` - Light/dark/system themes
  - Theme persistence in localStorage
  
- **E2E Tests**:
  - Click theme toggle
  - Verify theme class on body

### ✅ Copy to Clipboard
- **Frontend Tests**:
  - `test_chat.spec.js:Copy to Clipboard` - Button exists
  
- **E2E Tests**:
  - Click copy button on response
  - Verify button text changes to "Copied!"

### ✅ Prompt History (Readline)
- **Frontend Tests**:
  - `test_prompt_history.spec.js` - Add to history
  - Navigate up/down with arrow keys
  - Don't add empty prompts
  
- **E2E Tests**:
  - Implicit test through chat usage

### ✅ Voice Input
- **E2E Tests**:
  - Voice input button exists on page

### ✅ Navbar Resize
- **E2E Tests**:
  - Navbar width is resizable

### ✅ Panel Resize
- **E2E Tests**:
  - Favorite cards panel height is resizable

### ✅ Navigation
- **Backend Tests**:
  - `ViewTests.test_home_page` - Home page loads
  - `ViewTests.test_chat_page` - Chat page loads
  - `ViewTests.test_prompts_page` - Prompts page loads
  - `ViewTests.test_dashboard_page` - Dashboard page loads
  - `ViewTests.test_documents_page` - Documents page loads
  - `ViewTests.test_examples_page` - Examples page loads
  
- **E2E Tests**:
  - Navigate to dashboard
  - Navigate to prompts
  - Navigate to documents
  - Navigate to examples

## Quick Test Execution

### Run ALL Tests
```bash
# Backend tests (from agent_ui directory)
cd agent_ui && python manage.py test agent_app.tests

# Frontend tests (from tests directory)
cd tests && npm test

# E2E tests (from tests directory)
cd tests && npm run test:e2e
```

### Run Specific Test Categories
```bash
# API tests only
python manage.py test agent_app.tests.test_api

# Model tests only
python manage.py test agent_app.tests.test_models

# Chat tests only
python manage.py test agent_app.tests.test_api.ChatAPITests

# Session tests only
python manage.py test agent_app.tests.test_api.SessionAPITests

# Feedback tests only
python manage.py test agent_app.tests.test_api.MessageFeedbackTests
```

## Test Statistics

### Backend Tests
- **Total Test Files**: 2
- **Total Test Classes**: 12
- **Total Test Methods**: 45+
- **Lines of Code**: 800+

### Frontend Tests
- **Total Test Files**: 4
- **Total Test Suites**: 15+
- **Total Test Cases**: 40+
- **Lines of Code**: 400+

### E2E Tests
- **Total Test Files**: 1
- **Total Test Suites**: 12
- **Total Test Cases**: 30+
- **Lines of Code**: 450+

### Grand Total
- **Total Tests**: 115+
- **Total Coverage**: All major features

## Continuous Integration

### Recommended CI Pipeline

```yaml
name: RealtyIQ Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: cd agent_ui && python manage.py test
      
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd tests && npm install && npm test
      
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: cd tests && npm install
      - run: npx playwright install --with-deps
      - run: cd tests && npm run test:e2e
```

## Test Maintenance

### Adding New Tests

1. **For new API endpoints**: Add to `test_api.py`
2. **For new models**: Add to `test_models.py`
3. **For new JS features**: Add to appropriate `frontend/*.spec.js`
4. **For new user flows**: Add to `e2e/test_user_flows.spec.js`

### Updating Existing Tests

When modifying features:
1. Run related tests first
2. Update test expectations
3. Run full test suite
4. Update this documentation

## Test Data

### Seed Data Command
```bash
python manage.py seed_prompts
```

This creates:
- 100+ predefined prompt suggestions
- Based on business-intelligence.md
- With varying usage counts

## Troubleshooting

### Common Issues

**Issue**: `ImportError: cannot import name 'X' from 'agent_app.models'`
- **Solution**: Check model names match exactly (e.g., `AssistantCard` not `Card`)

**Issue**: `Connection refused localhost:8002`
- **Solution**: Start dev server: `uvicorn agent_ui.asgi:application --port 8002`

**Issue**: `playwright: command not found`
- **Solution**: Run `npx playwright install` in tests directory

**Issue**: Tests pass locally but fail in CI
- **Solution**: Check database migrations, environment variables, static files

## Performance Benchmarks

Target test execution times:
- **Backend Tests**: < 5 seconds
- **Frontend Tests**: < 2 seconds
- **E2E Tests**: < 60 seconds

Total suite: **< 70 seconds**

## Next Steps

Future testing enhancements:
1. ✅ Visual regression testing (Percy/Chromatic)
2. ✅ Load testing (Locust)
3. ✅ Security testing (OWASP ZAP)
4. ✅ Accessibility testing (axe-core)
5. ✅ Code coverage reporting (Codecov)

## Contact

For questions about tests:
- See `tests/README.md` for detailed documentation
- Check `tests/QUICK_START.md` for quick reference
