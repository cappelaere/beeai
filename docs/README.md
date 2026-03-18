# RealtyIQ Documentation

Welcome to the RealtyIQ documentation. This directory contains comprehensive guides for setting up, configuring, and using the RealtyIQ AI Agent platform.

## Table of Contents

## Documentation Structure

Documentation is organized into two main sections: **User Guide** (how to use) and **Developer Guide** (how to develop/extend).

---

## [User Guide](user-guide/README.md) - How to Use RealtyIQ

**For end users, analysts, and administrators**

Everything you need to use RealtyIQ effectively:

### Quick References
- **[Commands](user-guide/COMMANDS.md)** - All slash commands - START HERE
- **[Troubleshooting](user-guide/TROUBLESHOOTING.md)** - Common issues and solutions

### Topics

#### [Workflows & Tasks](user-guide/workflow_management/README.md)
Execute workflows and manage tasks:
- [Quick Reference](user-guide/workflow_management/QUICK_REFERENCE.md) - One-page command cheatsheet
- [Complete Guide](user-guide/workflow_management/WORKFLOW_AND_TASK_GUIDE.md) - Comprehensive reference
- Commands: `/workflow list`, `/task claim`, `/task submit`

#### [Features](user-guide/features/README.md)
How to use specific features:
- RAG Tool (semantic document search)
- Session Context (conversation memory)
- Error handling and recovery

#### Accessibility
Enable accessibility features with `/settings 508 on`:
- Larger fonts and better contrast
- Text-to-Speech with audio controls
- Enhanced keyboard navigation

For technical implementation, see [Developer Guide - Section 508](developer-guide/section508/README.md)

---

## [Developer Guide](developer-guide/README.md) - How to Develop & Extend

**For developers, contributors, and system administrators**

Everything you need to develop, test, and deploy RealtyIQ:

### Essential

- **[Technical Specs](SPECS.md)** - Complete technical specifications
- **[Developer Guide Index](developer-guide/README.md)** - Main developer documentation hub

### Development Setup

#### [Setup](developer-guide/setup/README.md)
Development environment and infrastructure:
- [Shell Setup](developer-guide/setup/SHELL_SETUP.md) - Automated development environment
- [Docker Setup](developer-guide/setup/DOCKER_SETUP.md) - Service management
- [Node.js Setup](developer-guide/setup/NODE_SETUP.md) - Frontend tooling

#### [Testing](developer-guide/testing/README.md)
Test strategy and execution:
- [Testing Guide](developer-guide/testing/TESTING.md) - Test strategy
- [Test Troubleshooting](developer-guide/testing/TEST_TROUBLESHOOTING.md) - Fix issues
- Status: 92 tests passing

### Architecture & Systems

#### [Observability](developer-guide/observability/README.md)
Monitoring, tracing, and metrics:
- Langfuse integration (tracing)
- Prometheus metrics (performance)
- Logging system (debugging)
- Tool tracking (execution monitoring)

#### [Caching](developer-guide/caching/README.md)
Redis caching architecture:
- LLM response caching (<100ms)
- Dual database architecture (UI + API)
- Performance optimization

#### [Reference](developer-guide/reference/README.md)
Technical references:
- [Tools Documentation](developer-guide/reference/tools.md) - All 15 API tools
- [MCP Server](developer-guide/reference/MCP_SERVER.md) - 16 MCP tools
- [App Architecture](developer-guide/reference/app.md) - System design

### Implementation Details

#### [Implementation](developer-guide/implementation/README.md)
Detailed implementation guides:
- Agent registry refactoring
- Database consolidation
- Skills loading
- Feature development

#### [Implementation History](developer-guide/implementation_history/README.md)
Historical development notes:
- Feature implementation timeline
- Organization changes
- Migration history

---

## Context Documentation

**For creating agents and workflows**:
- **[Context Documentation](../context/README.md)** - Complete application context
- **[Agent Guidelines](../context/AGENT_GUIDELINES.md)** - Agent design and best practices
- **[Workflow Guidelines](../context/WORKFLOW_GUIDELINES.md)** - Workflow design patterns
- **[Use Cases Library](../context/USE_CASES.md)** - Real-world scenarios and examples

---

## Workflow Development

**To start a new workflow:**
- **Workflow Studio** (recommended): Admin → Workflows → Workflow Studio (`/workflows/studio/`). AI-generated BPMN, code, and docs. See [How to start a new workflow](../workflows/docs/DEVELOPER_GUIDE.md#how-to-start-a-new-workflow) in the developer guide.

**Reference:**
- **[Workflow Developer Guide](../workflows/docs/DEVELOPER_GUIDE.md)** - Full guide (Studio + manual)
- **[Workflow Templates](../workflows/templates/)** - Templates for manual creation
- **[Workflow Examples](../workflows/EXAMPLES.md)** - 7 detailed examples
- **[BPMN Engine Review](architecture/BPMN_ENGINE_REVIEW.md)** - Current BPMN execution model and limitations
- **[BPMN Engine V2 Design Spec](architecture/BPMN_V2_PLAN.md)** - Proposed v2 runtime design

---

## Quick Navigation

### I want to...

**Use the system**:
→ [User Guide](user-guide/README.md) - Start here!

**Develop features**:
→ [Developer Guide](developer-guide/README.md) - Technical docs

**Create workflows**:
→ [Workflow Developer Guide](../workflows/docs/DEVELOPER_GUIDE.md)

**Find a command**:
→ [Commands Reference](user-guide/COMMANDS.md)

**Fix an issue**:
→ [Troubleshooting](user-guide/TROUBLESHOOTING.md) (users)
→ [Testing Guide](developer-guide/testing/README.md) (developers)

**Understand architecture**:
→ [Technical Specs](SPECS.md)
→ [Reference Docs](developer-guide/reference/README.md)

---

## File Locations

```
docs/
├── README.md                    # This file - main index
├── SPECS.md                     # Technical specifications
│
├── user-guide/                  # For users
│   ├── README.md                # User guide index
│   ├── COMMANDS.md              # All commands
│   ├── TROUBLESHOOTING.md       # Common issues
│   ├── workflow_management/     # Workflows & tasks
│   └── features/                # Feature usage
│
└── developer-guide/             # For developers
    ├── README.md                # Developer guide index
    ├── section508/              # Accessibility implementation
    ├── setup/                   # Development setup
    ├── testing/                 # Test documentation
    ├── observability/           # Monitoring & tracing
    ├── caching/                 # Redis & caching
    ├── reference/               # Technical references
    ├── implementation/          # Implementation details
    └── implementation_history/  # Historical notes
```

---

## Contributing

When adding documentation:

**User-facing features** → Add to `user-guide/`
- How to use commands, workflows, features
- Troubleshooting common issues
- Non-technical language

**Technical/development** → Add to `developer-guide/`
- Setup and configuration
- Testing strategies
- Architecture details
- API references
- Implementation notes

---

**Project Home**: [Main README](../README.md)

### Infrastructure & Setup
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)** - Docker consolidation and service management
- **[REDIS_DATABASE_SEPARATION.md](REDIS_DATABASE_SEPARATION.md)** - Redis database architecture
- **[REDIS_CONFIG_FIX.md](REDIS_CONFIG_FIX.md)** - Redis configuration troubleshooting
- **[LOGGING.md](LOGGING.md)** - Timestamped log files for monitoring and debugging - NEW
- **[PROMETHEUS_METRICS.md](PROMETHEUS_METRICS.md)** - Prometheus metrics integration and observability - NEW
- **[PROMETHEUS_QUICKSTART.md](PROMETHEUS_QUICKSTART.md)** - Get started with metrics in 5 minutes - NEW

### Features & Implementation
- **[CACHE_IMPLEMENTATION.md](CACHE_IMPLEMENTATION.md)** - LLM response caching system
- **[CACHE_MANAGEMENT.md](CACHE_MANAGEMENT.md)** - Cache management UI in Settings
- **[SESSION_CONTEXT_IMPLEMENTATION.md](SESSION_CONTEXT_IMPLEMENTATION.md)** - Conversation memory & context
- **[OBSERVABILITY_SETUP.md](OBSERVABILITY_SETUP.md)** - Langfuse observability integration
- **[OBSERVABILITY.md](OBSERVABILITY.md)** - Detailed observability guide
- **[OBSERVABILITY_QUICKSTART.md](OBSERVABILITY_QUICKSTART.md)** - Quick observability setup
- **[OBSERVABILITY_FIX.md](OBSERVABILITY_FIX.md)** - Trace context fixes
- **[LANGFUSE_TOOL_TRACKING.md](LANGFUSE_TOOL_TRACKING.md)** - Tool call tracking in Langfuse
- **[TOOL_TRACKING_COMPLETE.md](TOOL_TRACKING_COMPLETE.md)** - Complete tool tracking implementation
- **[NESTED_TRACES_FIX.md](NESTED_TRACES_FIX.md)** - Proper trace nesting
- **[DEBUG_TOOL_TRACKING.md](DEBUG_TOOL_TRACKING.md)** - Troubleshooting tool tracking

### Testing
- **[TESTING.md](TESTING.md)** - Testing strategy and guidelines
- **[TEST_FIXES_COMPLETE.md](TEST_FIXES_COMPLETE.md)** - All tests passing! Complete fix history
- **[TEST_TROUBLESHOOTING.md](TEST_TROUBLESHOOTING.md)** - Fix test crashes and hangs
- **[TEST_FIX_SUMMARY.md](TEST_FIX_SUMMARY.md)** - How we fixed test crashes
- **[TEST_SUMMARY.md](TEST_SUMMARY.md)** - Test implementation summary
- **[TESTS_CREATED.md](TESTS_CREATED.md)** - Detailed test documentation
- **[../tests/README.md](../tests/README.md)** - Test suite README
- **[../tests/QUICK_START.md](../tests/QUICK_START.md)** - Quick test guide
- **[../TEST_COMMANDS.md](../TEST_COMMANDS.md)** - Quick command reference

### API & Tools Reference
- **[tools.md](tools.md)** - Available tools documentation (15 tools)
- **[MCP_SERVER.md](MCP_SERVER.md)** - MCP Server setup and all 16 tools
- **[business-intelligence.md](business-intelligence.md)** - Business intelligence prompts
- **[app.md](app.md)** - Application structure
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

### Implementation Documentation
- **[implementation/](implementation/)** - Detailed implementation summaries
  - [AGENT_REGISTRY_REFACTORING.md](implementation/AGENT_REGISTRY_REFACTORING.md) - Centralized agent registry
  - [BIDDER_VERIFICATION_ORCHESTRATION.md](implementation/BIDDER_VERIFICATION_ORCHESTRATION.md) - Multi-agent orchestration
  - [SKILLS_MD_LOADING.md](implementation/SKILLS_MD_LOADING.md) - Auto-loading agent documentation
  - [DATABASE_CONSOLIDATION.md](implementation/DATABASE_CONSOLIDATION.md) - Data organization
  - [SESSION_SUMMARY.md](implementation/SESSION_SUMMARY.md) - Complete session summary
  - [See implementation/README.md for details](implementation/README.md)

## Quick Links

### Setup & Configuration

```bash
# Complete setup
make all

# Start services
make docker-up

# Start development
make dev
```

### Redis Caching

```bash
# Start Redis
make redis-start

# Check cache statistics
make redis-info

# Clear cache
make redis-flush
```

### Testing

```bash
# Run all tests
make test

# Run specific tests
make test-ui
make test-api
make test-observability
```

## Documentation Structure

```
docs/
├── README.md                          # This file - documentation index
├── SPECS.md                           # Complete technical specifications
│
├── Infrastructure/
│   ├── DOCKER_SETUP.md               # Docker & services
│   ├── REDIS_DATABASE_SEPARATION.md   # Redis architecture
│   └── REDIS_CONFIG_FIX.md           # Redis troubleshooting
│
├── Features/
│   ├── CACHE_IMPLEMENTATION.md        # LLM caching
│   ├── OBSERVABILITY_SETUP.md         # Langfuse setup summary
│   ├── OBSERVABILITY.md               # Detailed observability guide
│   └── OBSERVABILITY_QUICKSTART.md    # Quick setup
│
├── Testing/
│   ├── TESTING.md                     # Testing strategy
│   ├── TEST_SUMMARY.md                # Implementation summary
│   └── TESTS_CREATED.md               # Detailed test docs
│
└── Reference/
    ├── business-intelligence.md       # BI prompts
    ├── tools.md                       # Tool documentation
    └── app.md                         # App structure
```

## Key Features Documented

### 1. Redis Caching
- **Database 0**: UI/Chat LLM response cache (1 hour TTL)
- **Database 1**: API Django cache (5 minutes TTL)
- **Benefits**: <100ms cached responses, cost savings, better UX

**Docs**: [CACHE_IMPLEMENTATION.md](CACHE_IMPLEMENTATION.md), [REDIS_DATABASE_SEPARATION.md](REDIS_DATABASE_SEPARATION.md)

### 2. Observability
- **Platform**: Langfuse (cloud-based)
- **Features**: Tracing, cost tracking, feedback, performance monitoring
- **Integration**: Automatic for CLI and Web UI

**Docs**: [OBSERVABILITY.md](OBSERVABILITY.md), [OBSERVABILITY_QUICKSTART.md](OBSERVABILITY_QUICKSTART.md)

### 3. Docker Services
- **Single docker-compose.yml**: All services in root
- **Services**: Redis, API, PostgreSQL, pgAdmin, UI (optional)
- **Benefits**: Unified management, resource efficiency

**Docs**: [DOCKER_SETUP.md](DOCKER_SETUP.md)

### 4. Testing
- **Backend**: Django TestCase (API & models)
- **Frontend**: Jest (unit tests)
- **E2E**: Playwright (user flows)
- **Coverage**: All UI features

**Docs**: [TESTING.md](TESTING.md), [TEST_SUMMARY.md](TEST_SUMMARY.md)

## Common Tasks

### Cache Management

```bash
# View cache statistics
curl http://localhost:8002/api/cache/stats/

# Clear UI cache (database 0)
make redis-flush-ui

# Clear API cache (database 1)
make redis-flush-api

# Monitor cache in real-time
docker exec redis redis-cli -n 0 MONITOR
```

### Observability

```bash
# Check observability status
python test_observability.py

# View dashboard
# URL in .env: OBSERVABILITY_DASHBOARD

# Test trace creation
python run_agent.py
# Check Langfuse dashboard for traces
```

### Docker Management

```bash
# Start all services
make docker-up

# View service logs
make docker-logs
make docker-logs-redis
make docker-logs-api

# Restart services
make docker-restart

# Stop services
make docker-down
```

### Database Management

```bash
# Reload from SQL dump
make db-reload

# Create backup
make db-backup

# Open PostgreSQL shell
make db-shell
```

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| **UI** | 8002 | http://localhost:8002 |
| **API** | 8000 | http://localhost:8000 |
| **Redis** | 6379 | localhost:6379 |
| **PostgreSQL** | 8080 | localhost:8080 |
| **pgAdmin** | 5555 | http://localhost:5555 |

## Environment Variables

See [SPECS.md](SPECS.md#configuration) for complete configuration reference.

### Critical Variables

```bash
# LLM Configuration
LLM_CHAT_MODEL_NAME=anthropic:claude-sonnet-4-5
ANTHROPIC_API_KEY=your_key_here

# Redis Caching
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0  # UI cache
REDIS_LOCATION=redis://redis:6379/1  # API cache

# Observability
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
OBSERVABILITY_DASHBOARD=https://us.cloud.langfuse.com/project/YOUR_ID
```

## Troubleshooting

### Redis Connection Issues
See [REDIS_CONFIG_FIX.md](REDIS_CONFIG_FIX.md)

### Docker Service Issues
See [DOCKER_SETUP.md](DOCKER_SETUP.md#troubleshooting)

### Cache Not Working
See [CACHE_IMPLEMENTATION.md](CACHE_IMPLEMENTATION.md#troubleshooting)

### Observability Not Tracking
See [OBSERVABILITY.md](OBSERVABILITY.md#troubleshooting)

## Contributing

When adding new documentation:

1. **Place files in `/docs`** - Keep root clean (only README.md in root)
2. **Update this README** - Add links to new documentation
3. **Follow naming conventions** - Use UPPERCASE for setup/config, lowercase for reference
4. **Cross-reference** - Link related documents
5. **Update SPECS.md** - Reflect changes in the main specs

## External Resources

- **Langfuse**: https://langfuse.com/docs
- **Redis**: https://redis.io/docs
- **Django**: https://docs.djangoproject.com/
- **Docker**: https://docs.docker.com/
- **Playwright**: https://playwright.dev/python/docs/intro

## Support

For issues or questions:
1. Check the relevant documentation first
2. Review [SPECS.md](SPECS.md) for complete technical details
3. Check troubleshooting sections
4. Review logs: `make docker-logs` or `make redis-logs`

---

**Documentation Status**: ORGANIZED

All documentation consolidated in `/docs` with clear organization and cross-references.
