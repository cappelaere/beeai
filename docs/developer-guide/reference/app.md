# RealtyIQ Application Documentation

**RealtyIQ** is an AI agent that supports the **GSA Real Estate Sales Auction** business line and real estate specialists with **reports and business intelligence** for past, current, and future real estate auctions.

---

## Architecture

| Component | Technology |
|-----------|------------|
| **Agent** | [IBM BeeAI](https://github.com/IBM/BeeAI) for orchestration and tool use |
| **LLM** | Anthropic (or other providers) via environment; optional local Ollama |
| **Tools** | Python tools in `tools/` calling the backend API with Token auth |
| **Optional MCP** | MCP server for exposing tools (e.g. future AWS Bedrock) |
| **Backend API** | BidHom API (Django REST) in `Api/` (properties, bids, users, CMS) |
| **Database** | PostgreSQL (container or local); seed from `latest_db.sql` |

The agent is **read-only**: it uses tools to fetch data from the API and does not modify records. PII is minimized in tool outputs unless explicitly requested.

---

## Repository layout

| Path | Description |
|------|-------------|
| `run_agent.py` | Interactive agent (BeeAI + tools); LLM from env. |
| `run_agent_ollama.py` | Same agent with local Ollama LLM (no outbound API; use when cloud returns 405). |
| `mcp_server.py` | Optional MCP server for tools (e.g. Bedrock migration). |
| `tools/` | BeeAI tools (list properties, agents, property detail, auction dashboard, bid history, etc.). |
| `docs/` | Documentation (this folder). |
| `Api/` | Django API for the auction platform; runs in Docker or locally. |
| `latest_db.sql` | PostgreSQL dump for loading/restoring database state. |

---

## Environment variables

Credentials and config **must** be provided via environment variables (e.g. `.env`). Do not commit secrets.

### Agent / BeeAI

| Variable | Description |
|----------|-------------|
| `LLM_CHAT_MODEL_NAME` | LLM identifier (e.g. `anthropic:claude-3-5-sonnet-20240620`). Defaults to `openai:gpt-4.1-mini` if unset. |
| `API_URL` | Base URL of the Realty/API service (required by tools). Example: `http://127.0.0.1:8000`. |
| `AUTH_TOKEN` | API auth token for tool calls. |
| `SITE_ID` | Default site id (default `3`). |
| `USER_ID` | Optional default user id for Tier 2 tools (auction_dashboard, auction_bidders, auction_total_bids, auction_watchers). |
| `TLS_VERIFY` | Set to `false` to disable TLS verification for API calls (dev only). |

### API (Django)

When running or developing the API (see [API and database](#api-and-database)):

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key. |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts. |
| `DATABASE_URL` | Postgres URL, e.g. `postgres://user:password@host:port/dbname`. |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Used by Docker Compose for Postgres. |
| `REDIS_CACHE` | Redis URL if using cache. |
| Others | Email, FCM, etc. as in `Api/realityOneApi/settings.py`. |

---

## Running the agent locally

1. Create a virtualenv and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set `API_URL`, `AUTH_TOKEN`, and optionally `LLM_CHAT_MODEL_NAME`, `SITE_ID`, `USER_ID`, `TLS_VERIFY`.
3. Ensure the API is running and the database is loaded (see below).
4. Run the agent:
   ```bash
   python run_agent.py
   ```

At the `RealtyIQ>` prompt you can ask questions; the agent will call the appropriate tools and respond.

**If cloud APIs (OpenAI/Anthropic) return 405 (e.g. proxy blocked):** use local Ollama:

1. Install [Ollama](https://ollama.ai) and run `ollama pull llama3.1`.
2. Run:
   ```bash
   python run_agent_ollama.py
   ```

**Optional MCP server** (e.g. for Bedrock): install `beeai-framework[mcp]==0.1.76` and run `python mcp_server.py`.

---

## API and database

The Django API serves properties, bids, users, and CMS data. The agent tools call this API with Token authentication.

### Running API and database in containers

1. **Build the API image** (from repo root):
   ```bash
   docker build -t beeai-api ./Api
   ```
   Or from `Api/`: `docker build -t beeai-api .`

2. **Start the stack** (from `Api/`):
   - Ensure `Docker-compose.yml` uses env vars for `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (e.g. env_file or `${POSTGRES_USER}`).
   - Run:
     ```bash
     docker compose -f Docker-compose.yml up -d
     ```

3. **Load the database** (once):
   ```bash
   set -a && source Api/.env && set +a
   docker exec -i bidhom_db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < latest_db.sql
   ```

4. **Persistence:** In `Docker-compose.yml`, use a volume for the Postgres data directory so data survives restarts (see `Api/README.md`).

The API is typically available at `http://localhost:8000`. Set `API_URL` in the agent’s `.env` to this base URL.

### Local development (no Docker)

- **Python:** 3.10+. Use a venv and `pip install -r requirements.txt` in `Api/`.
- **PostgreSQL:** Install Postgres 16.x and client libs; create a DB and user; set `DATABASE_URL` in `Api/.env`.
- **Redis:** Optional; set `REDIS_CACHE` if used.
- **Migrations:**
  ```bash
  cd Api && python manage.py makemigrations && python manage.py migrate
  ```
- **Superuser:**
  ```bash
  python manage.py createsuperuser --username admin
  ```
- **Run server:**
  ```bash
  python manage.py runserver
  ```
  → http://127.0.0.1:8000/

See **`Api/README.md`** for detailed API setup, env vars, and Docker Compose usage.

---

## Tools overview

The agent uses 15 tools plus an optional think tool. Tools call the backend API with `Authorization: Token {AUTH_TOKEN}`.

- **Core:** `list_properties`, `list_agents_summary`
- **Tier 1 (property & reference):** `get_property_detail`, `list_property_types`, `list_asset_types`, `get_auction_types`, `get_site_detail`, `property_count_summary`
- **Tier 2 (auctions & bids):** `auction_dashboard`, `auction_bidders`, `auction_total_bids`, `bid_history`, `auction_watchers`, `admin_dashboard`, `property_registration_graph`

Full parameters, API endpoints, and example prompts: **[Tools reference](tools.md)**.
