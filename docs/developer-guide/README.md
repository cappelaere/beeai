# Developer Guide

**How to develop and extend RealtyIQ - Documentation for developers**

This section contains all technical documentation for setting up, developing, testing, and deploying RealtyIQ.

---

## Quick Start for Developers

### Essential Setup
1. **[Setup Guide](setup/README.md)** - Development environment setup
   - [Shell Setup](setup/SHELL_SETUP.md) - Automated environment
   - [Docker Setup](setup/DOCKER_SETUP.md) - Container services
   - [Node.js Setup](setup/NODE_SETUP.md) - Frontend tooling

2. **[Technical Specs](../SPECS.md)** - Complete technical specifications

3. **[Testing Guide](testing/README.md)** - Test strategy and execution
   - [Testing](testing/TESTING.md) - Main testing guide
   - [Troubleshooting](testing/TEST_TROUBLESHOOTING.md) - Fix test issues

---

## Development Topics

### Creating Agents & Workflows

#### [Context Documentation](../../context/README.md)
Comprehensive context for creating agents and workflows:
- **[Context Overview](../../context/CONTEXT.md)** - Application context and domain knowledge
- **[Agent Guidelines](../../context/AGENT_GUIDELINES.md)** - Agent design patterns and best practices
- **[Workflow Guidelines](../../context/WORKFLOW_GUIDELINES.md)** - Workflow design patterns and implementation
- **[Use Cases Library](../../context/USE_CASES.md)** - Real-world scenarios and examples

**Use this when:**
- Creating new agents via Agent Studio
- Designing new workflows via Workflow Studio
- Understanding RealtyIQ domain and architecture
- Generating agent SKILLS.md documentation

---

### Infrastructure & Setup

#### [Setup](setup/README.md)
Development environment and infrastructure:
- Shell automation (`dev-setup.sh`)
- Docker services (Redis, PostgreSQL, etc.)
- Node.js and nvm configuration
- Database setup

**Quick Start**:
```bash
source dev-setup.sh     # Auto-setup environment
make all                # Complete setup
make dev                # Start dev server
```

**Code Quality** (before committing):
```bash
make quality            # Run all quality checks
make format             # Format code (PEP 8)
make lint-fix           # Auto-fix style issues
```

---

### Testing

#### [Testing](testing/README.md)
Test strategy, execution, and troubleshooting:
- Backend Django tests (92 tests)
- Frontend Jest tests
- E2E Playwright tests
- Workflow command tests

**Run Tests**:
```bash
make test-backend       # Django backend tests (141 tests)
make test-frontend      # Jest frontend tests
make test-e2e           # Playwright E2E tests
make test-all           # All tests
```

---

### Implementation Details

#### [Implementation](implementation/README.md)
Detailed technical implementation guides:
- Agent registry refactoring
- Bidder verification orchestration
- Database consolidation
- Skills.md loading

#### [Code Quality](CODE_QUALITY.md)
Code quality standards and tooling:
- Ruff linter/formatter setup
- Complexity management (max: 10)
- PEP 8 compliance
- Makefile commands

#### [Makefile Commands](MAKEFILE_COMMANDS.md)
Complete reference for all development commands:
- Setup and installation
- Development servers
- Code quality and linting
- Testing
- Redis cache
- Docker services
- Database operations

#### [Implementation History](implementation_history/README.md)
Historical notes about feature implementations:
- Documentation organization
- Navbar integration
- Feature development timeline

---

### Architecture & Systems

#### [Section 508 & Accessibility](section508/README.md)
Accessibility implementation and compliance:
- **[Section 508 Summary](section508/SECTION_508_SUMMARY.md)** - Quick overview
- **[Section 508 Guide](section508/SECTION_508.md)** - Complete implementation
- **[TTS Integration](section508/TTS_INTEGRATION.md)** - Text-to-Speech system
- **[Compliance Audit](section508/SECTION_508_AUDIT.md)** - Compliance report
- **[Implementation Details](section508/SECTION_508_IMPLEMENTATION.md)** - Technical specs

#### [Observability](observability/README.md)
Monitoring, tracing, metrics, and logging:
- **[Langfuse Integration](observability/OBSERVABILITY.md)** - Tracing and observability
- **[Prometheus Metrics](observability/PROMETHEUS_METRICS.md)** - Real-time metrics
- **[Logging System](observability/LOGGING.md)** - Application logging
- **[Tool Tracking](observability/TOOL_TRACKING_COMPLETE.md)** - Track all tool calls
- **[Health Checks](observability/HEALTH_CHECKS.md)** - Service monitoring

#### [Caching](caching/README.md)
Redis caching architecture and implementation:
- **[Cache Implementation](caching/CACHE_IMPLEMENTATION.md)** - LLM response caching
- **[Redis Architecture](caching/REDIS_DATABASE_SEPARATION.md)** - Dual database setup
- **[Cache Management](caching/CACHE_MANAGEMENT.md)** - UI management

#### [Reference](reference/README.md)
Technical references and API documentation:
- **[Tools Reference](reference/tools.md)** - All 15 API tools
- **[MCP Server](reference/MCP_SERVER.md)** - MCP Server with 16 tools
- **[App Architecture](reference/app.md)** - Application structure
- **[Business Intelligence](reference/business-intelligence.md)** - BI prompts

---

## Development Workflows

### Creating a New Agent
1. Read context documentation: `../../context/AGENT_GUIDELINES.md`
2. Use Agent Studio UI (admin only) or manually create agent directory
3. Define agent configuration with appropriate tools
4. Write or generate SKILLS.md documentation
5. Add to `agents.yaml` registry
6. Test with example queries

### Creating a New Workflow
1. **Start with Workflow Studio** (recommended): Log in as admin → Workflows → **Workflow Studio** (`/workflows/studio/`). Fill the form and use a step-by-step prompt; the app generates BPMN, `workflow.py`, README, and metadata. See [Workflow Developer Guide](../../workflows/docs/DEVELOPER_GUIDE.md#how-to-start-a-new-workflow).
2. Or create manually: Read [Workflow Guidelines](../../context/WORKFLOW_GUIDELINES.md) and [Workflow Developer Guide](../../workflows/docs/DEVELOPER_GUIDE.md), copy templates from `workflows/templates/`, implement with BeeAI Framework, add tests, and update the user guide.

### Adding a New Feature
1. Review technical specs: `../SPECS.md`
2. Implement feature with proper error handling
3. Add observability (Langfuse traces)
4. Add caching if needed (Redis)
5. Write tests (see `testing/`)
6. Document in user guide
7. Update CHANGELOG

### Debugging Issues
1. Check logs: `/api/logs/` or `developer-guide/observability/LOGGING.md`
2. Check metrics: Prometheus dashboard or `/metrics/`
3. Check traces: Langfuse dashboard
4. Review troubleshooting: `../TROUBLESHOOTING.md`
5. Check health: `/api/health/`

---

## Architecture Overview

### Tech Stack
- **Backend**: Django + BeeAI Framework
- **Frontend**: HTML/CSS/JS (vanilla)
- **LLM**: Anthropic Claude Sonnet 4.5
- **Caching**: Redis (dual database)
- **Observability**: Langfuse
- **Metrics**: Prometheus + Grafana
- **Database**: PostgreSQL + 2 SQLite DBs

### Key Components
- **Agents**: 7 specialized agents (GRES, SAM, OFAC, etc.)
- **Tools**: 15 API tools + 16 MCP tools
- **Workflows**: BeeAI dynamic workflows
- **Tasks**: Human review task system
- **UI**: Chat interface with cards and documents

---

## Testing

### Test Suites
- **Backend**: 92 Django tests (all passing)
- **Frontend**: Jest unit tests
- **E2E**: Playwright tests
- **Workflows**: 8 command tests

### Test Strategy
- Unit tests for individual components
- Integration tests for workflows
- E2E tests for critical user flows
- Manual testing checklist

See [Testing Guide](testing/) for complete documentation.

---

## Deployment

### Docker Services
```bash
make docker-up          # Start all services
make docker-ps          # View status
make docker-logs        # View logs
make docker-down        # Stop services
```

### Environment Configuration
All config via `.env` file:
- LLM settings (Anthropic API key)
- Redis configuration
- Langfuse observability
- Section 508 settings
- Database URLs

See `../SPECS.md` for complete configuration reference.

---

## Code Quality & Linting

### [Code Quality Guide](CODE_QUALITY.md)

RealtyIQ enforces Python best practices with automated linting and formatting.

#### Requirements
- ✅ All files under 1,000 lines
- ✅ All functions complexity ≤10
- ✅ PEP 8 style compliance
- ✅ Single responsibility principle

#### Quick Commands

**Before Every Commit**:
```bash
make quality            # Run all quality checks (recommended)
```

**Quality Checks**:
```bash
make lint               # Check code style & errors
make lint-fix           # Auto-fix style issues
make format             # Format code (PEP 8)
make check-complexity   # Verify complexity ≤10
make check-style        # Check formatting (CI-friendly)
```

**Full Codebase**:
```bash
make lint-all           # Lint entire codebase
make format-all         # Format entire codebase
```

#### Ruff Configuration

Located in `pyproject.toml`:
- Line length: 100 characters
- Max cyclomatic complexity: 10
- Target: Python 3.10+
- Rules: PEP 8, security, bugbear, simplify

#### Development Workflow

1. **While coding**: `make format` (format as you go)
2. **Before committing**: `make quality` (all checks)
3. **If issues found**: `make lint-fix` (auto-fix)
4. **Run tests**: `make test-backend` (verify no breakage)

See **[CODE_QUALITY.md](CODE_QUALITY.md)** for complete guide.

---

## Testing

### Test Commands

**Quick Tests**:
```bash
make test               # Core tests (backend)
make test-backend       # Django backend tests (141 tests)
```

**Full Test Suite**:
```bash
make test-frontend      # Jest frontend tests
make test-e2e           # Playwright E2E tests
make test-all           # All tests (backend + frontend + e2e)
```

**Specific Tests**:
```bash
# Run specific test file
cd agent_ui && ../venv/bin/python manage.py test agent_app.tests.test_api

# Run with verbosity
cd agent_ui && ../venv/bin/python manage.py test --verbosity=2

# Run and keep test database
cd agent_ui && ../venv/bin/python manage.py test --keepdb
```

### Current Test Status
✅ **141/141 backend tests passing (100%)**

See **[TEST_RESULTS.md](TEST_RESULTS.md)** and **[TEST_FIXES.md](TEST_FIXES.md)** for details.

---

## Development Commands

### Complete Command Reference

**Setup & Installation**:
```bash
make all                # Complete setup (install + migrate + seed + redis)
make setup              # Initial project setup
make install            # Install Python dependencies
make migrate            # Run database migrations
make seed               # Seed database with prompts and cards
```

**Development Servers**:
```bash
make dev                # Start UI server with Redis (port 8002)
make dev-ui             # Start UI server only
make dev-api            # Start API server (port 8000)
make dev-cli            # Run CLI agent
make dev-mcp            # Start MCP server (port 8001)
make stop-server        # Stop all running servers
```

**Redis Cache**:
```bash
make redis-start        # Start Redis (Docker)
make redis-stop         # Stop Redis
make redis-status       # Check Redis status
make redis-cli          # Open Redis CLI
make redis-flush        # Clear all cache
make redis-logs         # View Redis logs
```

**Code Quality** ⭐ NEW:
```bash
make quality            # Run all quality checks
make lint               # Check code style
make lint-fix           # Auto-fix issues
make format             # Format code
make check-complexity   # Check complexity
make check-style        # Check formatting
```

**Testing**:
```bash
make test               # Core backend tests
make test-backend       # Django tests (141 tests)
make test-frontend      # Jest tests
make test-e2e           # Playwright tests
make test-all           # All tests
```

**Docker Services**:
```bash
make docker-up          # Start all services
make docker-down        # Stop all services
make docker-ps          # Show status
make docker-logs        # View logs
```

**Utilities**:
```bash
make clean              # Remove cache and temp files
make logs               # View server logs
make shell              # Open Django shell
make superuser          # Create superuser
```

**Database**:
```bash
make db-reload          # Load latest_db.sql
make db-backup          # Backup to latest_db.sql
make db-shell           # PostgreSQL shell
```

**Help**:
```bash
make help               # Show all available commands
```

---

## Contributing

### Code Standards
- Follow PEP 8 style guide (enforced by Ruff)
- All files under 1,000 lines
- All functions complexity ≤10
- Run `make quality` before committing
- Add tests for new features
- Document user-facing features
- Update CHANGELOG
- Use Section 508 compliant UI

### Documentation Standards
- User docs in `user-guide/`
- Developer docs in `developer-guide/`
- Update README indexes
- Add examples and usage

---

**For Users**: See [User Guide](../user-guide/README.md) for how to use RealtyIQ.

**Back to**: [Documentation Index](../README.md)
