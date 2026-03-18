# RealtyIQ Docker Setup - Consolidated Services

## Overview

All RealtyIQ services are now managed through a **single consolidated `docker-compose.yml`** in the root directory.

### Services Included

| Service | Port | Purpose |
|---------|------|---------|
| **Redis** | 6379 | Cache server (shared by UI and API) |
| **API** | 8000 | GSA Auction API (Django) |
| **PostgreSQL** | 8080→5432 | Database for API |
| **pgAdmin** | 5555 | Database management UI |
| **UI** | 8002 | RealtyIQ Web Interface (optional) |

## Quick Start

### Option 1: Full Docker Deployment

Start all services:
```bash
# From root directory
make docker-up

# Or directly
docker-compose up -d
```

Access:
- UI: http://localhost:8002 (if enabled)
- API: http://localhost:8000
- pgAdmin: http://localhost:5555
- Redis: localhost:6379

### Option 2: Hybrid (UI Local, Services Docker)

Start backend services only:
```bash
# Start Redis, API, DB, pgAdmin
make docker-up

# Start UI locally (in another terminal)
make dev-ui
```

This is the **recommended setup** for UI development.

### Option 3: Redis Only (Minimal)

Just start Redis for caching:
```bash
# Start Redis only
make redis-start

# Or
docker-compose up -d redis

# Start UI locally with Redis caching
make dev
```

## Architecture

### Consolidated docker-compose.yml

**Location:** `/docker-compose.yml` (root directory)

**Previous Setup:**
- ❌ `Api/Docker-compose.yml` (deleted)
- ❌ `docker-compose.yml` (replaced)

**New Setup:**
- ✅ Single `docker-compose.yml` in root
- ✅ All services defined
- ✅ Shared Redis instance
- ✅ Unified network

### Service Configuration

#### Redis (Shared Cache)

```yaml
redis:
  image: redis:7-alpine
  container_name: realtyiq-redis
  ports: ["6379:6379"]
  volumes: [redis-data:/data]
  command: >
    redis-server
    --appendonly yes
    --maxmemory 256mb
    --maxmemory-policy allkeys-lru
  networks: [realtyiq-network]
```

**Used by:**
- RealtyIQ UI (LLM response caching)
- API (query caching)
- Both share the same Redis instance

#### API Service

```yaml
api:
  container_name: realtyiq-api
  build: ./Api
  ports: ["8000:8000"]
  environment:
    - REDIS_URL=redis://redis:6379
  depends_on: [redis, db]
  networks: [realtyiq-network]
```

#### Database (PostgreSQL)

```yaml
db:
  container_name: realtyiq-postgres
  image: postgres:16
  ports: ["8080:5432"]
  volumes: [postgres-data:/var/lib/postgresql/data]
  networks: [realtyiq-network]
```

#### pgAdmin

```yaml
pgadmin:
  container_name: realtyiq-pgadmin
  image: dpage/pgadmin4
  ports: ["5555:80"]
  depends_on: [db]
  networks: [realtyiq-network]
```

### Network

All services connected via `realtyiq-network`:
- Inter-service communication
- Service discovery by name
- Isolated from host

## Commands Reference

### Makefile (Root Directory)

#### Quick Commands
```bash
make all         # Complete setup
make dev         # Start UI with Redis
make docker-up   # Start all Docker services
make help        # Show all commands
```

#### Redis Commands
```bash
make redis-start    # Start Redis
make redis-stop     # Stop Redis
make redis-status   # Show stats
make redis-cli      # Open CLI
make redis-flush    # Clear cache
make redis-logs     # View logs
```

#### Docker Commands
```bash
make docker-up         # Start all services
make docker-down       # Stop all services
make docker-ps         # Show status
make docker-logs       # View all logs
make docker-redis      # Start Redis only
make docker-api        # Start API + deps
make docker-restart    # Restart services
```

### Makefile (Api Directory)

**NOTE:** Api/Makefile now uses the consolidated docker-compose.yml

```bash
cd Api

make up        # Start API services
make down      # Stop API services
make build     # Build API image
make rebuild   # Rebuild with no cache
make logs      # View API logs
make shell     # Open API container shell
make ps        # Show services
```

### Direct Docker Compose

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d redis api

# Stop all
docker-compose down

# View logs
docker-compose logs -f redis
docker-compose logs -f api

# Check status
docker-compose ps

# Restart service
docker-compose restart redis
```

## Redis URL Configuration

### Development (Local)

When running UI locally:
```bash
# In .env
REDIS_URL=redis://localhost:6379
```

### Docker Deployment

When running UI in Docker:
```bash
# In .env or docker-compose environment
REDIS_URL=redis://redis:6379
```

The service name `redis` resolves to the Redis container IP within the Docker network.

## Migration from Old Setup

### What Changed

**Before:**
```
Api/Docker-compose.yml
- api, cache (Redis on 7379), db, pgadmin
- Network: gsa_auction_ntwk

docker-compose.yml (root)
- redis (standalone)
- Network: realtyiq-network
```

**After:**
```
docker-compose.yml (root - consolidated)
- api, redis (shared on 6379), db, pgadmin, ui (optional)
- Network: realtyiq-network (unified)
```

### Migration Steps

1. ✅ **Stop old services**
   ```bash
   cd Api && docker-compose down
   cd .. && docker-compose down
   ```

2. ✅ **Remove old Docker-compose.yml**
   - Deleted `Api/Docker-compose.yml`

3. ✅ **Use consolidated file**
   - All services now in root `docker-compose.yml`

4. ✅ **Update Makefiles**
   - Root Makefile: Enhanced commands
   - Api/Makefile: Points to `../docker-compose.yml`

5. ✅ **Start new services**
   ```bash
   make docker-up
   ```

## Service Dependencies

```
pgAdmin
  └── depends on: db

api
  ├── depends on: redis (healthy)
  └── depends on: db (started)

ui (optional)
  └── depends on: redis (healthy)

redis
  └── no dependencies

db
  └── no dependencies
```

### Health Checks

**Redis:**
```bash
redis-cli ping
# Expected: PONG
```

**PostgreSQL:**
```bash
pg_isready -U postgres
# Expected: accepting connections
```

**API:**
```bash
curl http://localhost:8000/health
# Expected: 200 OK
```

## Volume Management

### Persistent Volumes

```bash
# List volumes
docker volume ls | grep realtyiq

# Inspect volume
docker volume inspect realtyiq-redis-data

# Remove volume (WARNING: deletes data)
docker volume rm realtyiq-redis-data
```

### Backup Redis Data

```bash
# Create backup
docker exec realtyiq-redis redis-cli SAVE
docker cp realtyiq-redis:/data/dump.rdb ./backups/redis-backup-$(date +%Y%m%d).rdb

# Restore backup
docker cp ./backups/redis-backup-20260215.rdb realtyiq-redis:/data/dump.rdb
docker restart realtyiq-redis
```

### Backup PostgreSQL

```bash
# Backup database
docker exec realtyiq-postgres pg_dump -U postgres auction_db > backup.sql

# Restore database
cat backup.sql | docker exec -i realtyiq-postgres psql -U postgres auction_db
```

## Troubleshooting

### Port Conflicts

**Problem:** Port already in use

**Check what's using the port:**
```bash
lsof -i :6379  # Redis
lsof -i :8000  # API
lsof -i :8002  # UI
lsof -i :8080  # PostgreSQL
lsof -i :5555  # pgAdmin
```

**Solution:** Stop the conflicting service or change port in docker-compose.yml

### Redis Connection Issues

**From UI (local):**
```bash
# Use localhost
REDIS_URL=redis://localhost:6379
```

**From API (Docker):**
```bash
# Use service name
REDIS_URL=redis://redis:6379
```

### Services Not Starting

**Check logs:**
```bash
make docker-logs

# Or specific service
docker-compose logs redis
docker-compose logs api
```

**Verify health:**
```bash
docker-compose ps
```

**Restart services:**
```bash
make docker-restart
```

### Clean Start

```bash
# Stop and remove everything
docker-compose down -v

# Remove old networks
docker network prune

# Start fresh
make docker-up
```

## Production Deployment

### Environment Variables

Update `.env` for production:

```bash
# Redis with authentication
REDIS_URL=redis://:your_password@redis:6379

# Secure PostgreSQL
POSTGRES_PASSWORD=strong_secure_password

# Django production
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=your_production_secret_key
```

### Docker Compose Override

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  redis:
    command: redis-server --requirepass ${REDIS_PASSWORD}
  
  api:
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    environment:
      - DEBUG=False
  
  db:
    ports: []  # Don't expose publicly
```

Deploy:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Network Configuration

### Service Communication

Within Docker network, services communicate by name:

```python
# API connects to Redis
REDIS_URL = "redis://redis:6379"

# API connects to PostgreSQL
DB_HOST = "db"
DB_PORT = "5432"
```

### External Access

From host machine:

```python
# UI connects to Redis
REDIS_URL = "redis://localhost:6379"

# UI connects to API
API_URL = "http://localhost:8000"
```

## Monitoring

### Service Status

```bash
# Quick status check
make docker-ps

# Detailed health
docker-compose ps
docker inspect realtyiq-redis --format='{{.State.Health.Status}}'
```

### Resource Usage

```bash
# Container stats
docker stats

# Redis memory
docker exec realtyiq-redis redis-cli INFO memory | grep used_memory_human
```

### Logs

```bash
# All services
make docker-logs

# Specific service
make docker-logs-redis
make docker-logs-api

# Follow logs
docker-compose logs -f redis
```

## Development Workflow

### Typical Development Flow

```bash
# 1. Start services
make docker-up

# 2. Run UI locally (for development)
make dev-ui

# 3. Make changes to code
# ... edit files ...

# 4. UI auto-reloads (--reload flag)
# API auto-reloads (watch mode)

# 5. Check Redis cache
make redis-status

# 6. Clear cache if needed
make redis-flush

# 7. View logs
make docker-logs-api

# 8. Stop when done
make docker-down
```

### Testing Workflow

```bash
# Start services
make docker-up

# Run tests
make test

# Stop services
make docker-down
```

## Benefits of Consolidation

### Before (2 Docker Compose files)
- ❌ Two separate Redis instances
- ❌ Different networks
- ❌ Confusing service names
- ❌ Duplicate configuration
- ❌ Hard to manage

### After (1 Docker Compose file)
- ✅ Single shared Redis instance
- ✅ Unified network
- ✅ Clear service names
- ✅ Single source of truth
- ✅ Easy management
- ✅ Better resource efficiency
- ✅ Simplified commands

## Quick Reference

### Start Everything
```bash
make docker-up
```

### Start UI Only (with Redis)
```bash
make dev
```

### Start API Development
```bash
cd Api
make up
```

### Check Status
```bash
make docker-ps
make redis-status
```

### View Logs
```bash
make docker-logs          # All services
make docker-logs-redis    # Redis only
make docker-logs-api      # API only
```

### Stop Everything
```bash
make docker-down
```

## Support

For issues:
1. Check `docker-compose.yml` in root directory
2. Run `make help` for commands
3. Check service logs: `make docker-logs`
4. Verify `.env` configuration
5. See [CACHE_IMPLEMENTATION.md](CACHE_IMPLEMENTATION.md) for caching issues
6. See [REDIS_DATABASE_SEPARATION.md](REDIS_DATABASE_SEPARATION.md) for Redis architecture

---

**Status**: ✅ **CONSOLIDATED**

All services now managed through single docker-compose.yml with unified Redis instance.
