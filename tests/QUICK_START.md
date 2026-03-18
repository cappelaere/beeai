# Quick Start - Running Tests

## 1. Backend Tests (5 minutes)

```bash
# Navigate to agent_ui directory
cd agent_ui

# Run all Django tests
python manage.py test agent_app.tests

# Expected output: Ran XX tests in X.XXs - OK
```

## 2. Frontend Unit Tests (2 minutes)

```bash
# Navigate to tests directory
cd tests

# Install dependencies (first time only)
npm install

# Run Jest tests
npm test

# Expected output: Test Suites: X passed, Tests: XX passed
```

## 3. End-to-End Tests (10 minutes)

```bash
# Navigate to tests directory
cd tests

# Install Playwright browsers (first time only)
npx playwright install

# Make sure Django server is running on port 8002
# In another terminal: cd agent_ui && uvicorn agent_ui.asgi:application --port 8002

# Run E2E tests
npm run test:e2e

# Expected output: XX passed (XXs)
```

## Quick Verification

Run this single command to verify Django tests work:

```bash
cd agent_ui && python manage.py test agent_app.tests.test_models.ChatSessionModelTests.test_create_session --keepdb
```

Expected output:
```
Creating test database for alias 'default'...
.
----------------------------------------------------------------------
Ran 1 test in 0.XXXs

OK
```

## Test Coverage Summary

- **Backend API Tests**: 100+ test cases covering all endpoints
- **Backend Model Tests**: 30+ test cases covering all models
- **Frontend Unit Tests**: 40+ test cases for JavaScript functionality
- **E2E Tests**: 25+ test cases for user flows

Total: **195+ comprehensive tests**

## Common Issues

### Issue: "No module named 'agent_app'"
**Solution**: Make sure you're in the `agent_ui` directory when running Django tests

### Issue: "Cannot find module 'jest'"
**Solution**: Run `npm install` in the `tests` directory

### Issue: "Playwright browser not found"
**Solution**: Run `npx playwright install` in the `tests` directory

### Issue: "Connection refused" in E2E tests
**Solution**: Make sure Django dev server is running on port 8002
