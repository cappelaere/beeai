# RealtyIQ – GSA Real Estate Sales Auction Assistant

**RealtyIQ** is an AI agent that supports the **GSA Real Estate Sales Auction** business line and real estate specialists with **reports and business intelligence** for past, current, and future real estate auctions.

## ⚡ Quick Start

### Automatic Environment Setup (Recommended)

```bash
# In any new terminal, run this once
source dev-setup.sh
```

This automatically:
- ✅ Checks and loads correct Node.js version
- ✅ Activates Python virtual environment
- ✅ Loads environment variables from .env
- ✅ Shows service status and quick commands

For automatic setup in every new terminal, add to `~/.bashrc` or `~/.zshrc`:
```bash
source /path/to/beeai/.shellrc
```

### Manual Setup

```bash
# Complete setup (install, migrate, seed, start Redis)
make all

# Start development server
make dev

# Or start all services with Docker
make docker-up
```

Open **http://localhost:8002** to access the chat interface.

## 📚 Documentation

Documentation is organized by audience - clear paths for users and developers:

### 👤 For Users - How to Use RealtyIQ
- **[User Guide](docs/user-guide/)** - Start here for using the system
- **[Commands Quick Reference](docs/user-guide/workflow_management/QUICK_REFERENCE.md)** - One-page command cheatsheet
- **[Workflow & Task Guide](docs/user-guide/workflow_management/)** - Execute workflows and manage tasks
- **[Troubleshooting](docs/user-guide/TROUBLESHOOTING.md)** - Common issues

### 🔧 For Developers - How to Build & Extend
- **[Developer Guide](docs/developer-guide/)** - Technical documentation hub
- **[Makefile Commands](docs/developer-guide/MAKEFILE_COMMANDS.md)** - Complete command reference
- **[Setup Guide](docs/developer-guide/setup/)** - Development environment
- **[Testing Guide](docs/developer-guide/testing/)** - Test strategy (141 tests)
- **[Code Quality](docs/developer-guide/CODE_QUALITY.md)** - Linting & formatting
- **[Technical Specs](docs/SPECS.md)** - Complete specifications
- **[Section 508 Implementation](docs/developer-guide/section508/)** - Accessibility compliance
- **[Observability](docs/developer-guide/observability/)** - Monitoring and tracing
- **[Reference](docs/developer-guide/reference/)** - API and tool docs

### 📖 Documentation Hub
- **[Main Documentation Index](docs/)** - Navigate all documentation

## 🏗️ Architecture

- **Agentic AI**: Built with [IBM BeeAI](https://github.com/IBM/BeeAI) for orchestration and tool use
- **LLM**: Anthropic Claude Sonnet 4.5 (configurable via environment)
- **Caching**: Redis with separate databases for UI (DB 0) and API (DB 1)
- **Observability**: Langfuse for tracing, monitoring, and cost tracking
- **Backend API**: BidHom API (Django REST) in `Api/` directory (properties, bids, users)
- **Databases**: PostgreSQL (GRES data) + 2 SQLite databases (SAM, OFAC)

## 📁 Repository Structure

| Path | Description |
|------|-------------|
| `agent_ui/` | Django frontend (chat, tools, cards, documents, dashboard) |
| `Api/` | BidHom API (Django REST) for auction platform |
| `agents/` | Agent definitions (GRES, SAM, OFAC, IDV, Library, 508, Bidder Verification) |
| `data/` | **Databases and source files** (see Data Management below) |
| `docs/` | **📚 All documentation** |
| `scripts/` | Utility scripts (database imports, etc.) |
| `tests/` | Test suite (backend, frontend, E2E) |
| `tools/` | BeeAI tools for property data and analytics |
| `workflows/` | **BeeAI dynamic workflows** for multi-step automation ⭐ NEW |
| `run_agent.py` | CLI agent with Langfuse observability |
| `docker-compose.yml` | **All services** (Redis, API, DB, pgAdmin, Prometheus, Grafana) |
| `Makefile` | Development commands |
| `agents.yaml` | Central agent registry (single source of truth) |

## 📋 Prerequisites

- **Python**: 3.10+ (for backend)
- **Node.js**: 24.x LTS (for frontend tests) - See [docs/NODE_SETUP.md](docs/NODE_SETUP.md)
- **Docker**: For Redis, PostgreSQL, and containerized services
- **PostgreSQL**: 16+ (via Docker or local)

## ⚙️ Configuration

All configuration is via environment variables in `.env` (never commit secrets).

## 💾 Data Management

RealtyIQ uses three databases with different purposes:

| Database | Type | Purpose | Agent(s) |
|----------|------|---------|----------|
| **GRES** | PostgreSQL | Auction/property data | GRES Agent |
| **SAM Exclusions** | SQLite | Federal contract exclusions | SAM Agent, Bidder Verification |
| **OFAC SDN** | SQLite | Sanctions screening | OFAC Agent, Bidder Verification |

### Quick Database Setup

```bash
# Rebuild all SQLite databases (3-4 minutes)
python scripts/rebuild_all_databases.py

# Restore PostgreSQL GRES data (via Docker)
docker exec -i beeai-postgres psql -U postgres -d gres_db < data/source/latest_db.sql
```

### Source Files

All source data files are in `data/source/`:
- `latest_db.sql` (5.2 MB) - GRES PostgreSQL dump
- `SAM_Exclusions_Public_Extract_V2.CSV` (69 MB) - SAM.gov data
- `sdn.csv` (3.0 MB) - OFAC SDN list

### Complete Documentation

See [`data/DATABASE_SETUP.md`](data/DATABASE_SETUP.md) for:
- Detailed rebuild procedures
- Database schemas
- Update procedures
- Troubleshooting
- Backup strategies

## 🔄 BeeAI Dynamic Workflows

RealtyIQ leverages BeeAI Framework workflows to automate complex, multi-step processes by orchestrating multiple agents.

### Implemented Workflows

1. **Bidder Onboarding & Verification** ✅
   - Automates complete bidder registration and compliance screening
   - Orchestrates SAM, OFAC, and GRES agents
   - 8-step workflow with business rules engine
   - <5 second execution vs hours manually

### Quick Start

```python
from workflows import BidderOnboardingWorkflow

workflow = BidderOnboardingWorkflow()
result = await workflow.run(
    bidder_name="John Smith",
    property_id=12345,
    registration_data={...}
)

print(f"Status: {result.state.approval_status}")
# Status: approved (or denied, pending, review_required)
```

### Additional Planned Workflows

See [`workflows/EXAMPLES.md`](workflows/EXAMPLES.md) for 6 additional high-value workflows:
- Property Due Diligence (multi-agent research)
- Property Valuation & Market Analysis (parallel processing)
- Conversational Research Assistant (stateful memory)
- Auction Lifecycle State Machine (complete automation)
- Compliance Audit Trail (comprehensive reporting)
- Document Intelligence Extraction (AI-powered processing)

### Documentation

- **[workflows/README.md](workflows/README.md)** - Complete workflows guide
- **[workflows/EXAMPLES.md](workflows/EXAMPLES.md)** - 7 detailed workflow examples with diagrams
- **[workflows/BIDDER_ONBOARDING_DIAGRAM.md](workflows/BIDDER_ONBOARDING_DIAGRAM.md)** - Visual diagrams
- **BeeAI Framework**: https://framework.beeai.dev/modules/workflows

### Essential Variables

```bash
# LLM Configuration
LLM_CHAT_MODEL_NAME=anthropic:claude-sonnet-4-5
ANTHROPIC_API_KEY=your_key_here

# Redis Caching (Database 0 for UI, Database 1 for API)
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0
REDIS_LOCATION=redis://redis:6379/1

# Observability (Langfuse)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
OBSERVABILITY_DASHBOARD=https://us.cloud.langfuse.com/project/YOUR_ID

# Accessibility (Section 508)
SECTION_508_MODE=false  # Set to 'true' to enable by default
PIPER_BASE_URL=http://localhost:8088
PIPER_DEFAULT_VOICE=en_US-lessac-medium

# API & Database
API_URL=http://127.0.0.1:8000
AUTH_TOKEN=your_token_here
DATABASE_URL=postgres://ibm_user:ibm_pass@db:5432/ibm_database
```

See [docs/SPECS.md](docs/SPECS.md) for complete configuration reference.

## 🚀 Usage

### Web UI (Recommended)

```bash
# Start development server with Redis
make dev

# Or start all services with Docker
make docker-up
```

Access at **http://localhost:8002**

**Features:**
- AI chat with LLM response caching (<100ms for cached responses)
- Dashboard with metrics and performance stats
- Prompt library and autocomplete
- Document management
- Session history
- Real-time observability tracking

### CLI Agent

```bash
# Interactive agent with observability
python run_agent.py

# Using local Ollama (if cloud APIs blocked)
python run_agent_ollama.py
```

### MCP Server (Optional)

Exposes all 16 tools via MCP protocol for Bedrock or external tool access:
```bash
# Start MCP server on port 8001
python mcp_server.py
```

## 🐳 Docker Services

All services managed through single `docker-compose.yml`:

```bash
# Start all services
make docker-up

# View status
make docker-ps

# View logs
make docker-logs

# Stop services
make docker-down
```

**Services:** Redis (6379), API (8000), PostgreSQL (8080), pgAdmin (5555), UI (8002)

See [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md) for complete guide.

## 💾 Database Management

```bash
# Load database from SQL dump
make db-reload

# Create backup
make db-backup

# Open PostgreSQL shell
make db-shell
```

## 🗄️ Redis Caching

```bash
# Start Redis
make redis-start

# View statistics
make redis-info

# Clear UI cache (database 0)
make redis-flush-ui

# Clear API cache (database 1)
make redis-flush-api
```

**Architecture:**
- **Database 0**: UI/Chat LLM responses (1 hour TTL)
- **Database 1**: API Django cache (5 minutes TTL)

See [docs/CACHE_IMPLEMENTATION.md](docs/CACHE_IMPLEMENTATION.md) for details.

## 🧪 Testing

**Status**: ✅ All 141 backend tests passing (100%)!

```bash
# Backend tests (recommended - fast, safe)
make test-backend      # Django tests (~25s, 141 tests)

# All tests
make test-all          # Backend + Frontend + E2E

# Individual suites
make test-frontend     # Jest unit tests
make test-e2e          # Playwright E2E tests (requires server)
```

**Test Results**: `141 passed in 25.2s` ✨

See [docs/developer-guide/testing/](docs/developer-guide/testing/) and [docs/developer-guide/TEST_RESULTS.md](docs/developer-guide/TEST_RESULTS.md) for details.

## ✅ Code Quality

**Standards**: PEP 8 compliant, max complexity 10, all files under 1,000 lines

```bash
# Before committing
make quality           # Run all quality checks

# Auto-fix and format
make format            # Format code (PEP 8)
make lint-fix          # Auto-fix style issues
```

See [docs/developer-guide/CODE_QUALITY.md](docs/developer-guide/CODE_QUALITY.md) and [docs/developer-guide/MAKEFILE_COMMANDS.md](docs/developer-guide/MAKEFILE_COMMANDS.md) for details.

## 📊 Features

- ✅ **Web Search** - DuckDuckGo integration for real-time internet research (no API key) ⭐ NEW
- ✅ **LLM Response Caching** - Redis-based caching with <100ms response time
- ✅ **Section 508 Accessibility** - Enhanced mode with on-prem TTS, larger text, focus indicators
- ✅ **Text-to-Speech (TTS)** - Piper TTS microservice with MP3 output, no autoplay
- ✅ **Observability** - Langfuse tracing, cost tracking, and feedback
- ✅ **Docker Services** - Unified service management (Redis, PostgreSQL, Piper TTS)
- ✅ **Dashboard** - Metrics, performance stats, and cache analytics
- ✅ **Prompt Library** - Autocomplete and suggestion system
- ✅ **Session Management** - Create, rename, delete, and export sessions
- ✅ **Document Upload** - PDF, DOCX, TXT support
- ✅ **Feedback System** - Thumbs up/down with Langfuse integration
- ✅ **Dark Mode** - Full theme support

## 🔗 Additional Resources

- **[Full Documentation](docs/README.md)** - Complete documentation index
- **[Technical Specs](docs/SPECS.md)** - Detailed specifications
- **[API Documentation](Api/README.md)** - Backend API guide
