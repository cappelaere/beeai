# Testing Documentation

Documentation for test strategy, execution, and troubleshooting.

---

## Main Documentation

- **[TESTING.md](TESTING.md)** - Main testing strategy and guidelines
- **[TEST_SUMMARY.md](TEST_SUMMARY.md)** - Test implementation summary
- **[TEST_TROUBLESHOOTING.md](TEST_TROUBLESHOOTING.md)** - Fix test crashes and hangs
- **[TEST_FIX_SUMMARY.md](TEST_FIX_SUMMARY.md)** - How we fixed test issues
- **[TESTS_CREATED.md](TESTS_CREATED.md)** - Detailed test documentation

---

## Quick Commands

```bash
# Backend tests (safe, fast)
make test-backend       # Django tests (~25s, 141 tests)

# BPMN/agent_app tests (pytest from repo root; Django bootstrap via agent_ui/conftest.py)
make test-bpmn          # pytest agent_ui/agent_app/tests/

# From agent_ui directory (alternative entrypoint)
cd agent_ui && python manage.py test agent_app.tests   # Django test runner

# All tests
make test-all           # Backend + Frontend + E2E

# Frontend tests
make test-frontend      # Jest tests

# E2E tests
make test-e2e           # Playwright tests (requires server running)

# Specific test file
cd agent_ui && ../venv/bin/python manage.py test agent_app.tests.test_workflow_commands
```

**BPMN tests:** Use `make test-bpmn` from repo root (one command; no need to `cd agent_ui`). From inside `agent_ui/`, use `python manage.py test agent_app.tests`. Both use the same Django settings; pytest uses `agent_ui/conftest.py` for path and `DJANGO_SETTINGS_MODULE`.

**See**: [MAKEFILE_COMMANDS.md](../MAKEFILE_COMMANDS.md) for complete command reference.

---

## Test Status

**Current**: ✅ All 141 backend tests passing (100%)

- 50 API tests
- 27 command tests
- 11 TTS integration tests
- 16 workflow tests
- 37 other tests

**Results**: See [TEST_RESULTS.md](../TEST_RESULTS.md) and [TEST_FIXES.md](../TEST_FIXES.md)

---

**Back to**: [Documentation Index](../README.md)
