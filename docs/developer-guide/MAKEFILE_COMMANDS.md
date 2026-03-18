# Makefile Commands Reference

**Complete reference for all `make` commands in RealtyIQ**

---

## Quick Reference

```bash
make help               # Show all available commands
make all                # Complete setup (new developers)
make dev                # Start development server
make quality            # Check code quality (before commit)
make test-backend       # Run tests
make metrics            # LOC, complexity, maintainability, doc density, test counts
```

---

## Setup & Installation

### Initial Setup

```bash
make all                # Complete setup (install + migrate + seed + redis)
```

This runs:
1. `make install` - Install dependencies
2. `make migrate` - Run database migrations
3. `make seed` - Seed database with prompts/cards
4. `make redis-start` - Start Redis cache

### Individual Setup Commands

```bash
make setup              # Initial project setup (install + migrate + seed)
make install            # Install Python dependencies from requirements.txt
make migrate            # Run Django database migrations
make seed               # Seed database with prompts and assistant cards
```

---

## Development Servers

### Starting Servers

```bash
make dev                # Start UI server with Redis (port 8002) ⭐ Most common
make dev-ui             # Start UI server only (port 8002)
make dev-api            # Start API server (port 8000)
make dev-cli            # Run CLI agent in terminal
make dev-mcp            # Start MCP server (port 8001)
```

### Stopping Servers

```bash
make stop-server        # Stop all running servers (ports 8000, 8002)
```

**Note**: Use `Ctrl+C` to stop servers started with `make dev`.

---

## Code Quality & Linting ⭐ NEW

### Recommended Workflow

**Before Every Commit**:
```bash
make quality            # Run all quality checks
```

This checks:
1. ✅ Cyclomatic complexity (max: 10)
2. ✅ Code formatting (PEP 8)
3. ✅ Style and error linting

### Individual Quality Commands

```bash
make lint               # Check code style and errors with Ruff
make lint-fix           # Auto-fix fixable style issues
make format             # Format code with Ruff (PEP 8 compliant)
make check-complexity   # Check for high complexity functions (>10)
make check-style        # Check formatting without modifying files
```

### Full Codebase

```bash
make lint-all           # Lint entire codebase (including workflows)
make format-all         # Format entire codebase
```

### What Gets Checked?

**Complexity** (C901):
- All functions must have cyclomatic complexity ≤10
- Prevents hard-to-maintain code

**Style** (PEP 8):
- Line length ≤100 characters
- Proper indentation (4 spaces)
- Import organization
- Naming conventions

**Quality**:
- Unused imports
- Unused variables
- Security issues (flake8-bandit)
- Bug patterns (flake8-bugbear)
- Code simplification opportunities

### Output Example

```bash
$ make quality
🔍 Running comprehensive code quality checks...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣  Checking complexity (max: 10)...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All checks passed!
   ✅ No high-complexity functions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2️⃣  Checking code formatting...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
150 files already formatted
   ✅ Code is properly formatted

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3️⃣  Linting code (style & errors)...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
184 errors found (mostly non-critical suggestions)
```

---

## Metrics (LOC, complexity, maintenance, tests)

Metrics targets help with **complexity management**, **maintenance effort**, **evolution tracking**, and **documentation density**. They also report **test file and test counts** across the project. Requires [radon](https://pypi.org/project/radon/) for LOC metrics (`pip install radon` or `venv/bin/pip install radon`).

### LOC and code quality metrics

```bash
make loc-metrics        # Print LOC, complexity (radon cc), maintainability (radon mi), raw LOC & doc density (radon raw)
make loc-metrics-save   # Save same output to metrics/loc-YYYYMMDD.txt for evolution tracking
```

**Exclusions** (so only project source is measured): `Api`, `data`, `media`, `venv`, `node_modules`, `__pycache__`, `.git`, `.pytest_cache`, `htmlcov`, `logs`, `staticfiles`, `migrations`. Radon is run from the repo root with these directories ignored.

**Output**:
- **Complexity**: Cyclomatic complexity by grade (A–F); high-complexity items listed.
- **Maintainability**: Index per file; files below threshold (e.g. 20) flagged.
- **Raw LOC**: SLOC, LLOC, comments, single- and multi-line docstrings; use for documentation density (comments+docstrings vs total).

**Evolution tracking**: Run `make loc-metrics-save` periodically (e.g. weekly or before releases). The file `metrics/loc-YYYYMMDD.txt` can be committed or archived to compare LOC and quality over time.

### Test metrics

```bash
make test-metrics       # Print test file count and test count per area (Django, Piper, Jest, Playwright)
make metrics            # Run both loc-metrics and test-metrics
```

**Reported areas**:
- **Django (agent_ui)**: Test files in `agent_ui/agent_app/tests`, test method count (from `def test_`).
- **Piper**: Test files in `piper/tests`, tests collected via `pytest --collect-only`.
- **Frontend (Jest)**: `*.spec.js` files and Jest listTests count.
- **E2E (Playwright)**: E2E test files and Playwright list count.

If a suite is not installed or not runnable, that area shows "N/A" and the command still succeeds.

---

## Testing

### Quick Test Commands

```bash
make test               # Core tests (backend only)
make test-backend       # Django backend tests (141 tests, ~25s)
make test-frontend      # Jest frontend tests
make test-e2e           # Playwright E2E tests (requires server running)
make test-all           # All tests (backend + frontend + e2e)
```

### Test Workflow

**During Development**:
```bash
# After making changes
make test-backend       # Quick feedback (~25s)
```

**Before Committing**:
```bash
make quality            # Check code quality
make test-backend       # Verify tests pass
```

**Before Deploying**:
```bash
make test-all           # Run complete test suite
```

### Current Test Status

✅ **141/141 backend tests passing (100%)**
- 50 API tests
- 27 command tests
- 11 TTS integration tests
- 16 workflow tests
- 37 other tests

---

## Redis Cache

### Managing Redis

```bash
make redis-start        # Start Redis server (Docker)
make redis-stop         # Stop Redis server
make redis-status       # Check Redis status and stats
make redis-cli          # Open Redis CLI interactive shell
make redis-restart      # Restart Redis
```

### Cache Operations

```bash
make redis-flush        # Clear ALL cache (both databases)
make redis-flush-ui     # Clear UI cache only (database 0)
make redis-flush-api    # Clear API cache only (database 1)
make redis-info         # Show database statistics
make redis-logs         # View Redis logs (follow mode)
```

### Redis Details

- **Port**: 6379
- **Container**: `realtyiq-redis`
- **Database 0**: UI cache (LLM responses, sessions)
- **Database 1**: API cache (reserved for API server)
- **Max Memory**: 256MB (LRU eviction)
- **Persistence**: Append-only file (AOF)

---

## Docker Services

### Docker Compose

```bash
make docker-up          # Start all services (Redis, API, DB, pgAdmin)
make docker-down        # Stop all services
make docker-ps          # Show running services
make docker-logs        # View all logs (follow mode)
make docker-restart     # Restart all services
```

### Individual Services

```bash
make docker-redis       # Start Redis only
make docker-api         # Start API (with dependencies)
make docker-db          # Start PostgreSQL only
```

### Service Logs

```bash
make docker-logs-redis  # View Redis logs
make docker-logs-api    # View API logs
```

### Service Ports

- **Redis**: localhost:6379
- **API**: http://localhost:8000
- **PostgreSQL**: localhost:8080
- **pgAdmin**: http://localhost:5555

---

## Database

### Database Operations

```bash
make db-reload          # Load latest_db.sql into PostgreSQL
make db-backup          # Backup database to latest_db.sql
make db-shell           # Open PostgreSQL interactive shell
```

### Database Management

```bash
make migrate            # Run Django migrations
cd agent_ui && ../venv/bin/python manage.py makemigrations  # Create migrations
```

---

## Piper TTS Service

### Managing Piper

```bash
make piper-build        # Build Piper Docker image (~300MB, 2-3 min)
make piper-start        # Start Piper TTS service (port 8088)
make piper-stop         # Stop Piper TTS service
make piper-restart      # Restart Piper
```

### Piper Operations

```bash
make piper-logs         # View Piper logs (follow mode)
make piper-test         # Run Piper tests
make piper-shell        # Open shell in Piper container
```

### Piper Details

- **Port**: 8088
- **Endpoints**:
  - Health: http://localhost:8088/healthz
  - Voices: http://localhost:8088/v1/voices
  - Docs: http://localhost:8088/docs
- **Audio Cache**: `./piper/audio/`

---

## Utilities

### Cleanup

```bash
make clean              # Remove cache files and temp directories
```

Removes:
- `__pycache__` directories
- `*.pyc` files
- `*.egg-info` directories
- `.pytest_cache` directories
- `.coverage` and `htmlcov/`

### Django Utilities

```bash
make logs               # View UI server logs (tail -f)
make shell              # Open Django shell (Python REPL with models)
make superuser          # Create Django superuser account
```

### Static Files

```bash
make collectstatic      # Collect static files for production
```

---

## Production Deployment

### Deploy Command

```bash
make deploy             # Deploy to production
```

Runs:
1. `make install` - Install dependencies
2. `make migrate` - Run migrations
3. `make collectstatic` - Collect static files

**Remember to**:
- Set `DEBUG=False` in settings
- Configure `ALLOWED_HOSTS`
- Use production database
- Set up HTTPS
- Start Redis in production mode

---

## Service URLs

### Local Development

| Service | URL | Purpose |
|---------|-----|---------|
| **UI** | http://localhost:8002 | Main web interface |
| **API** | http://localhost:8000 | REST API server |
| **Piper** | http://localhost:8088 | TTS service |
| **Redis** | localhost:6379 | Cache server |
| **PostgreSQL** | localhost:8080 | Database |
| **pgAdmin** | http://localhost:5555 | DB admin UI |

---

## Common Workflows

### Starting Fresh (New Developer)

```bash
# 1. Clone repository
git clone <repo-url>
cd beeai

# 2. Run complete setup
make all

# 3. Start development server
make dev
```

### Daily Development

```bash
# Morning - start services
make redis-start
make dev

# During development - check code quality
make format             # Format as you code

# Before committing
make quality            # All quality checks
make test-backend       # Run tests

# End of day
# Ctrl+C to stop server
make redis-stop
```

### Before Committing Code

```bash
# 1. Format and fix
make format
make lint-fix

# 2. Run quality checks
make quality

# 3. Run tests
make test-backend

# 4. If all pass, commit
git add .
git commit -m "Your message"
```

### Fixing Issues

```bash
# Code won't format?
make format

# Tests failing?
make test-backend --verbosity=2  # See detailed errors

# Server won't start?
make stop-server        # Kill existing processes
make redis-status       # Check Redis
make clean              # Clear cache
make dev                # Try again

# Complexity too high?
# Extract helper functions to reduce complexity
# See: docs/developer-guide/CODE_QUALITY.md
```

---

## Troubleshooting

### Port Already in Use

```bash
# Stop existing server
make stop-server

# Or manually
lsof -ti:8002 | xargs kill -9
```

### Redis Not Connecting

```bash
# Check Redis status
make redis-status

# Start if not running
make redis-start

# View logs
make redis-logs
```

### Tests Failing

```bash
# Run with verbosity
cd agent_ui && ../venv/bin/python manage.py test --verbosity=2

# Keep test database for faster runs
cd agent_ui && ../venv/bin/python manage.py test --keepdb

# Run specific test
cd agent_ui && ../venv/bin/python manage.py test agent_app.tests.test_api
```

### Code Quality Issues

```bash
# See what needs fixing
make lint

# Auto-fix what can be fixed
make lint-fix

# Format code
make format

# Check complexity
make check-complexity

# If complexity too high, refactor the function:
# - Extract helper functions
# - Use early returns
# - Simplify nested logic
```

---

## Configuration Files

### Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Ruff linter/formatter config ⭐ NEW |
| `requirements.txt` | Python dependencies |
| `.env` | Environment variables |
| `docker-compose.yml` | Docker services |
| `Makefile` | Development commands |

### pyproject.toml (NEW)

Ruff configuration for code quality:
```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint.mccabe]
max-complexity = 10
```

---

## Best Practices

### 1. Code Quality First

```bash
# After coding session
make format             # Format code
make quality            # Run checks
```

### 2. Test Regularly

```bash
# After changes
make test-backend       # Quick verification
```

### 3. Keep Redis Running

```bash
# Start once, keep running
make redis-start

# Check status anytime
make redis-status
```

### 4. Clean Regularly

```bash
# Weekly cleanup
make clean              # Remove temp files
make redis-flush        # Clear stale cache
```

### 5. Monitor Complexity

```bash
# After refactoring
make check-complexity   # Verify ≤10
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: CI

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install ruff
          pip install -r requirements.txt
      
      - name: Code quality
        run: make quality
      
      - name: Run tests
        run: make test-backend
```

---

## Advanced Usage

### Custom Ruff Commands

```bash
# Check specific file
venv/bin/ruff check path/to/file.py

# Check specific rule
venv/bin/ruff check . --select E501  # Line too long

# Format specific file
venv/bin/ruff format path/to/file.py

# Get help
venv/bin/ruff help
```

### Custom Test Commands

```bash
# Run specific test class
cd agent_ui && ../venv/bin/python manage.py test agent_app.tests.test_api.DocumentAPITests

# Run specific test method
cd agent_ui && ../venv/bin/python manage.py test agent_app.tests.test_api.DocumentAPITests.test_list_documents

# Run with coverage
cd agent_ui && ../venv/bin/python -m coverage run manage.py test
cd agent_ui && ../venv/bin/python -m coverage report
```

---

## Aliases & Shortcuts

### Useful Shell Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# RealtyIQ shortcuts
alias riq-dev='cd ~/path/to/beeai && make dev'
alias riq-test='cd ~/path/to/beeai && make test-backend'
alias riq-quality='cd ~/path/to/beeai && make quality'
alias riq-format='cd ~/path/to/beeai && make format'
```

---

## FAQ

### Q: What's the difference between `make test` and `make test-backend`?

**A**: They're the same now. `make test` runs `make test-backend`.

### Q: Do I need to run `make quality` every time?

**A**: Yes, before committing. It ensures your code meets quality standards and prevents CI failures.

### Q: Can I skip `make format`?

**A**: No. Consistent formatting makes code reviews easier and reduces merge conflicts.

### Q: What if `make quality` finds issues?

**A**: 
1. Run `make format` to fix formatting
2. Run `make lint-fix` to auto-fix style issues
3. Manually fix complexity issues (see CODE_QUALITY.md)

### Q: Why is complexity limited to 10?

**A**: Functions with complexity >10 are:
- Hard to understand
- Hard to test
- Hard to maintain
- More likely to have bugs

Extract helper functions to reduce complexity.

### Q: How long do tests take?

**A**: 
- Backend tests: ~25 seconds
- Frontend tests: ~10 seconds (if Node.js configured)
- E2E tests: ~2-3 minutes

---

## Related Documentation

- **[CODE_QUALITY.md](CODE_QUALITY.md)** - Detailed linting and formatting guide
- **[REFACTORING_COMPLETE.md](REFACTORING_COMPLETE.md)** - Refactoring details
- **[TEST_RESULTS.md](TEST_RESULTS.md)** - Test analysis
- **[TEST_FIXES.md](TEST_FIXES.md)** - Test fix details
- **[testing/README.md](testing/README.md)** - Complete testing guide

---

## Quick Command Cheatsheet

```bash
# Setup (once)
make all

# Daily development
make redis-start        # Start cache
make dev                # Start server

# Before commit
make format             # Format code
make quality            # Check quality
make test-backend       # Run tests

# If issues
make lint-fix           # Auto-fix
make clean              # Clear cache

# Help
make help               # Show all commands
```

---

**Last Updated**: March 3, 2026  
**Version**: 1.3.0
