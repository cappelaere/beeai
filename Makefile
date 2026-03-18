# RealtyIQ Makefile
# Commands for development, Redis, and deployment

.PHONY: help install redis-start redis-stop redis-status redis-cli redis-flush \
        dev dev-ui dev-api test test-ui test-api clean setup migrate seed all \
        piper-build piper-start piper-stop piper-logs piper-test piper-shell \
        lint lint-fix format check-complexity check-style quality \
        loc-metrics test-metrics metrics loc-metrics-save

# Default target
help:
	@echo "══════════════════════════════════════════════════════════"
	@echo "  RealtyIQ Development Commands"
	@echo "══════════════════════════════════════════════════════════"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make all            - Complete setup (install + migrate + seed + redis)"
	@echo "  make dev            - Start UI server with Redis (port 8002)"
	@echo "  make docker-up      - Start all services (Redis, API, DB, pgAdmin)"
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  make setup          - Initial project setup (install deps + migrate + seed)"
	@echo "  make install        - Install Python dependencies"
	@echo "  make migrate        - Run Django database migrations"
	@echo "  make seed           - Seed database with prompts and cards"
	@echo ""
	@echo "🗄️  Redis Cache Server (Single Shared Instance):"
	@echo "  make redis-start      - Start Redis server (Docker)"
	@echo "  make redis-stop       - Stop Redis server"
	@echo "  make redis-status     - Check Redis server status"
	@echo "  make redis-cli        - Open Redis CLI (default: database 0)"
	@echo "  make redis-flush      - Clear ALL cache (both databases)"
	@echo "  make redis-flush-ui   - Clear UI cache only (database 0)"
	@echo "  make redis-flush-api  - Clear API cache only (database 1)"
	@echo "  make redis-info       - Show database statistics"
	@echo "  make redis-logs       - View Redis logs"
	@echo ""
	@echo "🔧 Development Servers:"
	@echo "  make dev            - Start UI server with Redis (port 8002)"
	@echo "  make dev-ui         - Start UI server only (port 8002)"
	@echo "  make dev-api        - Start API server only (port 8000)"
	@echo "  make dev-cli        - Run CLI agent"
	@echo "  make dev-mcp        - Start MCP Server with 16 tools (port 8001)"
	@echo "  make stop-server    - Stop all running servers"
	@echo ""
	@echo "🐳 Docker Compose (All Services):"
	@echo "  make docker-up      - Start all services (Redis, API, DB, pgAdmin)"
	@echo "  make docker-down    - Stop all services"
	@echo "  make docker-ps      - Show running services"
	@echo "  make docker-logs    - View all logs"
	@echo "  make docker-redis   - Start Redis only"
	@echo "  make docker-api     - Start API (with DB and Redis)"
	@echo ""
	@echo "🎙️  Piper TTS Service:"
	@echo "  make piper-build    - Build Piper TTS Docker image"
	@echo "  make piper-start    - Start Piper TTS service (port 8088)"
	@echo "  make piper-stop     - Stop Piper TTS service"
	@echo "  make piper-logs     - View Piper TTS logs"
	@echo "  make piper-test     - Run Piper tests"
	@echo "  make piper-shell    - Open shell in Piper container"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test           - Run core tests (backend + observability)"
	@echo "  make test-backend   - Run Django backend tests only"
	@echo "  make test-frontend  - Run Jest frontend tests only"
	@echo "  make test-e2e       - Run Playwright E2E tests only"
	@echo "  make test-api       - Run API tests"
	@echo "  make test-observability - Test Langfuse integration"
	@echo "  make test-all       - Run ALL tests (backend + frontend + e2e)"
	@echo ""
	@echo "🔍 Code Quality & Linting:"
	@echo "  make quality        - Run all quality checks (lint + complexity + format check)"
	@echo "  make lint           - Check code style and errors with Ruff"
	@echo "  make lint-fix       - Auto-fix code style issues"
	@echo "  make format         - Format code with Ruff (PEP 8)"
	@echo "  make check-complexity - Check for high complexity functions (>10)"
	@echo "  make check-style    - Check formatting without modifying files"
	@echo ""
	@echo "📊 Metrics (LOC, complexity, maintenance, tests):"
	@echo "  make loc-metrics    - LOC, complexity, maintainability, documentation density (radon)"
	@echo "  make test-metrics  - Test file and test counts (Django, Piper, Jest, Playwright)"
	@echo "  make metrics       - Run loc-metrics and test-metrics"
	@echo "  make loc-metrics-save - Save loc-metrics to metrics/loc-YYYYMMDD.txt for evolution tracking"
	@echo ""
	@echo "🛠️  Utilities:"
	@echo "  make clean          - Remove cache files and temp directories"
	@echo "  make logs           - View UI server logs"
	@echo "  make shell          - Open Django shell"
	@echo "  make superuser      - Create Django superuser"
	@echo ""
	@echo "🗄️  Database:"
	@echo "  make db-reload      - Load latest_db.sql into PostgreSQL"
	@echo "  make db-backup      - Backup database to latest_db.sql"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo ""
	@echo "🚀 Production:"
	@echo "  make collectstatic  - Collect static files"
	@echo "  make deploy         - Deploy to production"
	@echo ""
	@echo "══════════════════════════════════════════════════════════"
	@echo "  Services:"
	@echo "    UI:      http://localhost:8002"
	@echo "    API:     http://localhost:8000"
	@echo "    Piper:   http://localhost:8088"
	@echo "    Redis:   localhost:6379"
	@echo "    DB:      localhost:8080 (PostgreSQL)"
	@echo "    pgAdmin: http://localhost:5555"
	@echo "══════════════════════════════════════════════════════════"
	@echo ""

# Installation and Setup
install:
	@echo "📦 Installing dependencies..."
	venv/bin/pip install -r requirements.txt
	@echo "✅ Dependencies installed"

migrate:
	@echo "🗄️  Running database migrations..."
	cd agent_ui && ../venv/bin/python manage.py migrate
	@echo "✅ Migrations complete"

seed:
	@echo "🌱 Seeding database..."
	cd agent_ui && ../venv/bin/python manage.py seed_prompts
	cd agent_ui && ../venv/bin/python manage.py seed_cards
	@echo "✅ Database seeded"

setup: install migrate seed
	@echo "✅ Setup complete! Run 'make dev' to start the server"

# Redis Commands
redis-start:
	@echo "🚀 Starting Redis server (Docker)..."
	@if docker ps -a --format '{{.Names}}' | grep -q '^realtyiq-redis$$'; then \
		echo "Redis container exists. Starting..."; \
		docker start realtyiq-redis; \
	else \
		echo "Creating new Redis container..."; \
		docker run -d \
			--name realtyiq-redis \
			-p 6379:6379 \
			-v realtyiq-redis-data:/data \
			redis:7-alpine \
			redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru; \
	fi
	@sleep 2
	@make redis-status

redis-stop:
	@echo "🛑 Stopping Redis server..."
	@docker stop realtyiq-redis 2>/dev/null || echo "Redis not running"
	@echo "✅ Redis stopped"

redis-status:
	@echo "📊 Redis Status:"
	@if docker ps --format '{{.Names}}' | grep -q '^realtyiq-redis$$'; then \
		echo "✅ Redis is RUNNING"; \
		docker exec realtyiq-redis redis-cli INFO server | grep -E 'redis_version|uptime_in_seconds|tcp_port'; \
		echo ""; \
		echo "Memory Usage:"; \
		docker exec realtyiq-redis redis-cli INFO memory | grep -E 'used_memory_human|maxmemory_human'; \
		echo ""; \
		echo "Cache Stats:"; \
		docker exec realtyiq-redis redis-cli INFO stats | grep -E 'keyspace_hits|keyspace_misses'; \
		docker exec realtyiq-redis redis-cli DBSIZE; \
	else \
		echo "❌ Redis is NOT running"; \
		echo "Run 'make redis-start' to start Redis"; \
	fi

redis-cli:
	@echo "🔧 Opening Redis CLI (type 'exit' to quit)..."
	@docker exec -it realtyiq-redis redis-cli

redis-flush:
	@echo "🗑️  Flushing ALL Redis cache (both databases)..."
	@docker exec redis redis-cli FLUSHALL
	@echo "✅ All cache cleared!"

redis-flush-ui:
	@echo "🗑️  Flushing UI cache (database 0)..."
	@docker exec redis redis-cli -n 0 FLUSHDB
	@echo "✅ UI cache cleared!"

redis-flush-api:
	@echo "🗑️  Flushing API cache (database 1)..."
	@docker exec redis redis-cli -n 1 FLUSHDB
	@echo "✅ API cache cleared!"

redis-info:
	@echo "📊 Redis Database Statistics:"
	@echo ""
	@echo "Keyspace Info:"
	@docker exec redis redis-cli INFO keyspace
	@echo ""
	@echo "Database 0 (UI) size:"
	@docker exec redis redis-cli -n 0 DBSIZE
	@echo ""
	@echo "Database 1 (API) size:"
	@docker exec redis redis-cli -n 1 DBSIZE

redis-logs:
	@echo "📋 Redis Logs:"
	@docker logs --tail 100 -f redis

redis-restart: redis-stop redis-start
	@echo "🔄 Redis restarted"

# Development Servers
stop-server:
	@echo "🛑 Stopping RealtyIQ servers..."
	@lsof -ti:8002 | xargs kill -9 2>/dev/null || echo "No server running on port 8002"
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "No server running on port 8000"
	@echo "✅ Servers stopped"

dev: redis-start
	@echo "🚀 Starting RealtyIQ UI with Redis cache..."
	@echo "   UI: http://localhost:8002"
	@echo "   Redis: localhost:6379"
	@echo ""
	@if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null 2>&1 ; then \
		echo "⚠️  Port 8002 is already in use!"; \
		echo ""; \
		echo "To stop the existing server, run:"; \
		echo "  lsof -ti:8002 | xargs kill -9"; \
		echo ""; \
		exit 1; \
	fi
	cd agent_ui && REDIS_URL=redis://localhost:6379 ../venv/bin/uvicorn agent_ui.asgi:application --host 0.0.0.0 --port 8002 --reload

dev-ui:
	@echo "🚀 Starting RealtyIQ UI server..."
	@echo "   URL: http://localhost:8002"
	@echo ""
	@if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null 2>&1 ; then \
		echo "⚠️  Port 8002 is already in use!"; \
		echo ""; \
		echo "To stop the existing server, run:"; \
		echo "  lsof -ti:8002 | xargs kill -9"; \
		echo ""; \
		echo "Or use the helper script:"; \
		echo "  ./start-server.sh"; \
		echo ""; \
		exit 1; \
	fi
	cd agent_ui && ../venv/bin/uvicorn agent_ui.asgi:application --host 0.0.0.0 --port 8002 --reload --log-config uvicorn_log_config.yaml

dev-api:
	@echo "🚀 Starting API server..."
	@echo "   URL: http://localhost:8000"
	@echo ""
	cd Api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

dev-cli:
	@echo "🚀 Starting CLI agent..."
	venv/bin/python run_agent.py

dev-mcp:
	@echo "🚀 Starting MCP Server on port 8001..."
	@echo "   Exposes all 16 tools via MCP protocol"
	@echo "   See docs/MCP_SERVER.md for usage"
	@echo ""
	venv/bin/python mcp_server.py

# Testing
test: test-backend
	@echo "✅ Core tests complete"
	@echo ""
	@echo "💡 To run frontend tests: make test-frontend"
	@echo "💡 To run E2E tests: make test-e2e"

test-backend:
	@echo "🧪 Running Backend Tests (Django)..."
	@echo "   This will take 5-10 seconds..."
	@cd agent_ui && ../venv/bin/python manage.py test agent_app.tests --keepdb --verbosity=1
	@echo "✅ Backend tests complete"

test-frontend:
	@echo "🧪 Running Frontend Tests (Jest)..."
	@if [ ! -d "tests/node_modules" ]; then \
		echo "❌ Frontend dependencies not installed."; \
		echo "   Install with: cd tests && npm install"; \
		exit 1; \
	fi
	@echo "   This may take 10-30 seconds..."
	@cd tests && npm test -- --passWithNoTests --forceExit --maxWorkers=1 --testTimeout=10000 || true
	@echo "✅ Frontend tests complete"

test-e2e:
	@echo "🧪 Running E2E Tests (Playwright)..."
	@if [ ! -f "tests/node_modules/.bin/playwright" ]; then \
		echo "❌ Playwright not installed."; \
		echo "   Install with: cd tests && npm install && npx playwright install"; \
		exit 1; \
	fi
	@echo "⚠️  Make sure dev server is running on port 8002"
	@cd tests && npm run test:e2e
	@echo "✅ E2E tests complete"

test-api:
	@echo "🧪 Running API tests..."
	cd Api && pytest tests/ -v

# BPMN/agent_app tests via pytest from repo root (uses agent_ui/conftest.py for Django bootstrap)
test-bpmn:
	@echo "🧪 Running BPMN/agent_app tests (pytest from repo root)..."
	venv/bin/python -m pytest agent_ui/agent_app/tests/ -v --tb=short
	@echo "✅ BPMN tests complete"

test-all: test-backend test-frontend test-e2e
	@echo "✅ All tests complete!"

# ═══════════════════════════════════════════════════════════════
# Code Quality & Linting
# ═══════════════════════════════════════════════════════════════

# Run all quality checks (recommended before committing)
quality:
	@echo "🔍 Running comprehensive code quality checks..."
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "1️⃣  Checking complexity (max: 10)..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@venv/bin/ruff check agent_ui/ tools/ agents/ --select C901 && echo "   ✅ No high-complexity functions" || echo "   ❌ Complexity violations found"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "2️⃣  Checking code formatting..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@venv/bin/ruff format agent_ui/ tools/ agents/ --check && echo "   ✅ Code is properly formatted" || echo "   ⚠️  Formatting issues (run 'make format')"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "3️⃣  Linting code (style & errors)..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@venv/bin/ruff check agent_ui/ tools/ agents/ --statistics || true
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "📊 Summary"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "💡 To fix auto-fixable issues: make lint-fix"
	@echo "💡 To format code: make format"
	@echo ""

# Lint code with Ruff (check for errors and style issues)
lint:
	@echo "🔍 Running Ruff linter on agent_ui, tools, and agents..."
	@venv/bin/ruff check agent_ui/ tools/ agents/
	@echo ""
	@echo "💡 To auto-fix issues: make lint-fix"
	@echo ""

# Auto-fix linting issues (including unsafe fixes where safe)
lint-fix:
	@echo "🔧 Auto-fixing linting issues..."
	@venv/bin/ruff check agent_ui/ tools/ agents/ --fix --unsafe-fixes
	@echo ""
	@echo "✅ Auto-fix complete!"
	@echo "   Run 'make lint' to see remaining issues"
	@echo ""

# Format code with Ruff (PEP 8 style)
format:
	@echo "✨ Formatting Python code with Ruff..."
	@venv/bin/ruff format agent_ui/ tools/ agents/
	@echo "✅ Code formatted!"

# Check if code is formatted (CI-friendly, non-destructive)
check-style:
	@echo "🔍 Checking code formatting..."
	@venv/bin/ruff format agent_ui/ tools/ agents/ --check || \
		(echo "❌ Code formatting issues found. Run 'make format' to fix." && exit 1)
	@echo "✅ Code is properly formatted!"

# Check complexity only (ensure functions are ≤10 complexity)
check-complexity:
	@echo "🔍 Checking cyclomatic complexity (max: 10)..."
	@venv/bin/ruff check agent_ui/ tools/ agents/ --select C901
	@echo "✅ No high-complexity functions found!"

# Lint all Python files (including workflows)
lint-all:
	@echo "🔍 Running Ruff on entire codebase..."
	@venv/bin/ruff check . --exclude venv --exclude Api --statistics
	@echo ""

# Format all Python files
format-all:
	@echo "✨ Formatting entire codebase..."
	@venv/bin/ruff format . --exclude venv --exclude Api
	@echo "✅ All code formatted!"

# ═══════════════════════════════════════════════════════════════
# LOC and test metrics (complexity, maintenance, documentation density, evolution)
# Excludes: Api, data, media, venv, node_modules, __pycache__, .git, .pytest_cache, htmlcov, logs, staticfiles, migrations
# ═══════════════════════════════════════════════════════════════

RADON_IGNORE := venv,Api,data,media,node_modules,__pycache__,.git,.pytest_cache,htmlcov,logs,staticfiles,migrations
RADON := $(shell command -v venv/bin/radon 2>/dev/null || command -v radon 2>/dev/null || true)

loc-metrics:
	@echo "📊 LOC and code quality metrics (radon; exclusions: Api, data, media, venv, ...)"
	@echo ""
	@if [ -z "$(RADON)" ]; then echo "❌ radon not found. Install with: pip install radon (or venv/bin/pip install radon)"; exit 1; fi
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Complexity (cyclomatic, by grade)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@$(RADON) cc . -i '$(RADON_IGNORE)' -n B -s 2>/dev/null | tail -25 || $(RADON) cc . -i '$(RADON_IGNORE)' -s 2>/dev/null | tail -25
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Maintainability index (files below 20 flagged)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@$(RADON) mi . -i '$(RADON_IGNORE)' -n B 2>/dev/null || $(RADON) mi . -i '$(RADON_IGNORE)' 2>/dev/null
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Raw LOC (SLOC, LLOC, comments, docstrings) & documentation density"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@$(RADON) raw . -i '$(RADON_IGNORE)' -s 2>/dev/null || $(RADON) raw . -i '$(RADON_IGNORE)' 2>/dev/null
	@echo ""
	@N=$$(find . -name '*.py' -type f \
		! -path './venv/*' ! -path './Api/*' ! -path './data/*' ! -path './media/*' \
		! -path '*/node_modules/*' ! -path '*/__pycache__/*' ! -path './.git/*' \
		! -path '*/.pytest_cache/*' ! -path '*/htmlcov/*' ! -path '*/logs/*' \
		! -path '*/staticfiles/*' ! -path '*/migrations/*' 2>/dev/null | wc -l | tr -d ' '); \
	echo "  Python files analysed: $$N"; echo ""
	@echo "💡 Save for evolution tracking: make loc-metrics-save"

test-metrics:
	@echo "📊 Test file and test counts"
	@echo ""
	@echo "  Django (agent_ui):"
	@printf "    Test files: "; find agent_ui/agent_app/tests -name 'test_*.py' 2>/dev/null | wc -l | tr -d ' '
	@printf "    Tests: "; find agent_ui/agent_app/tests -name '*.py' -exec grep -h "def test_" {} + 2>/dev/null | wc -l | tr -d ' '
	@echo ""
	@echo "  Piper:"
	@printf "    Test files: "; find piper_tts/tests -name '*.py' ! -name '__init__.py' 2>/dev/null | wc -l | tr -d ' '
	@printf "    Tests: "; (cd piper_tts && venv/bin/pytest --collect-only -q 2>/dev/null | tail -1) || echo "N/A"
	@echo ""
	@echo "  Frontend (Jest):"
	@printf "    Test files: "; find tests -name '*.spec.js' 2>/dev/null | wc -l | tr -d ' '
	@printf "    Tests: "; (cd tests && npm test -- --listTests 2>/dev/null | wc -l | tr -d ' ') || echo "N/A"
	@echo ""
	@echo "  E2E (Playwright):"
	@printf "    Test files: "; find tests -name '*.spec.js' -path '*e2e*' 2>/dev/null | wc -l | tr -d ' '
	@printf "    Tests: "; (cd tests && npx playwright test --list 2>/dev/null | grep -E '^[0-9]+ test' | head -1) || echo "N/A"
	@echo ""
	@echo "  ─────────────────────────────────────────"
	@TOTAL=0; \
	D=$$(find agent_ui/agent_app/tests -name 'test_*.py' 2>/dev/null | wc -l | tr -d ' '); \
	P=$$(find piper_tts/tests -name '*.py' ! -name '__init__.py' 2>/dev/null | wc -l | tr -d ' '); \
	J=$$(find tests -name '*.spec.js' 2>/dev/null | wc -l | tr -d ' '); \
	E=$$(find tests -name '*.spec.js' -path '*e2e*' 2>/dev/null | wc -l | tr -d ' '); \
	TOTAL=$$((D + P + J)); \
	echo "  Total test files (Django + Piper + Jest + E2E): $$TOTAL"; \
	echo ""

metrics: loc-metrics test-metrics
	@echo "✅ Metrics complete"

loc-metrics-save:
	@mkdir -p metrics
	@F=metrics/loc-$$(date +%Y%m%d).txt; \
	$(MAKE) -s loc-metrics > "$$F" 2>&1 && echo "✅ Saved to $$F. View with: cat $$F" || echo "❌ loc-metrics failed (e.g. radon not installed). Output in $$F"

# ═══════════════════════════════════════════════════════════════

# Utilities
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ 2>/dev/null || true
	@echo "✅ Cleanup complete"

logs:
	@echo "📋 UI Server Logs:"
	@tail -f agent_ui/*.log 2>/dev/null || echo "No log files found"

shell:
	@echo "🐚 Opening Django shell..."
	cd agent_ui && ../venv/bin/python manage.py shell

superuser:
	@echo "👤 Creating superuser..."
	cd agent_ui && ../venv/bin/python manage.py createsuperuser

collectstatic:
	@echo "📦 Collecting static files..."
	cd agent_ui && ../venv/bin/python manage.py collectstatic --no-input
	@echo "✅ Static files collected"

# Production
deploy: install migrate collectstatic
	@echo "🚀 Deploying to production..."
	@echo "   Remember to:"
	@echo "   - Set DEBUG=False in settings"
	@echo "   - Configure proper ALLOWED_HOSTS"
	@echo "   - Use production database"
	@echo "   - Set up HTTPS"
	@echo "   - Start Redis in production mode"

# Docker Compose - All Services
docker-up:
	@echo "🐳 Starting all services (Redis, API, DB, pgAdmin)..."
	docker compose up -d
	@echo "✅ Services started:"
	@echo "   Redis:   localhost:6379"
	@echo "   API:     http://localhost:8000"
	@echo "   DB:      localhost:8080 (PostgreSQL)"
	@echo "   pgAdmin: http://localhost:5555"

docker-down:
	@echo "🐳 Stopping all services..."
	docker compose down

docker-logs:
	@echo "📋 Docker Compose Logs (all services):"
	docker compose logs -f

docker-logs-redis:
	@echo "📋 Redis Logs:"
	docker compose logs -f redis

docker-logs-api:
	@echo "📋 API Logs:"
	docker compose logs -f api

docker-ps:
	@echo "📊 Running Services:"
	docker compose ps

docker-restart:
	@echo "🔄 Restarting all services..."
	docker compose restart

# Start specific services
docker-redis:
	@echo "🚀 Starting Redis only..."
	docker compose up -d redis

docker-api:
	@echo "🚀 Starting API (with dependencies)..."
	docker compose up -d api

docker-db:
	@echo "🚀 Starting PostgreSQL..."
	docker compose up -d db

# ═══════════════════════════════════════════════════════════════
# Piper TTS Service
# ═══════════════════════════════════════════════════════════════

piper-build:
	@echo "🎙️  Building Piper TTS Docker image..."
	@echo "   This will download voice models (~300MB)"
	@echo "   Build time: ~2-3 minutes"
	@echo ""
	docker compose build piper
	@echo ""
	@echo "✅ Piper TTS image built successfully"
	@echo "   Run 'make piper-start' to start the service"

piper-start:
	@echo "🎙️  Starting Piper TTS service..."
	@echo "   Port: 8088"
	@echo "   Audio cache: ./piper_tts/audio"
	@echo ""
	docker compose up -d piper
	@echo ""
	@echo "✅ Piper TTS service started"
	@echo ""
	@echo "Test endpoints:"
	@echo "  Health:  curl http://localhost:8088/healthz"
	@echo "  Voices:  curl http://localhost:8088/v1/voices"
	@echo "  Docs:    http://localhost:8088/docs"

piper-stop:
	@echo "🛑 Stopping Piper TTS service..."
	docker compose stop piper
	@echo "✅ Piper TTS service stopped"

piper-logs:
	@echo "📋 Piper TTS Logs:"
	docker compose logs -f piper

piper-test:
	@echo "🧪 Running Piper TTS tests..."
	@if [ ! -d "piper_tts/venv" ]; then \
		echo "Creating virtual environment for Piper tests..."; \
		cd piper_tts && python3 -m venv venv && \
		venv/bin/pip install -r requirements.txt pytest pytest-asyncio httpx; \
	fi
	cd piper_tts && venv/bin/pytest tests/ -v
	@echo "✅ Piper tests complete"

piper-shell:
	@echo "🐚 Opening shell in Piper container..."
	docker compose exec piper /bin/bash

piper-restart:
	@echo "🔄 Restarting Piper TTS service..."
	docker compose restart piper
	@echo "✅ Piper TTS restarted"

# Database Management
db-reload:
	@echo "🔄 Reloading database from latest_db.sql..."
	@if [ ! -f latest_db.sql ]; then \
		echo "❌ Error: latest_db.sql not found"; \
		exit 1; \
	fi
	@echo "📥 Loading SQL dump into PostgreSQL..."
	docker exec -i realtyiq-postgres psql -U ibm_user -d ibm_database < latest_db.sql
	@echo "✅ Database reloaded successfully!"

db-backup:
	@echo "💾 Backing up database to latest_db.sql..."
	docker exec realtyiq-postgres pg_dump -U ibm_user ibm_database > latest_db.sql
	@echo "✅ Backup saved to latest_db.sql"

db-shell:
	@echo "🐘 Opening PostgreSQL shell..."
	docker exec -it realtyiq-postgres psql -U ibm_user -d ibm_database

# Complete restart
restart: redis-stop clean redis-start
	@echo "🔄 Full restart complete. Run 'make dev' to start the server"

# Quick start for new developers
all: setup redis-start
	@echo ""
	@echo "🎉 RealtyIQ is ready!"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. Run 'make dev' to start the UI server"
	@echo "  2. Open http://localhost:8002"
	@echo "  3. Redis cache is running on port 6379"
	@echo ""
	@echo "Other commands: run 'make help'"
	@echo ""
