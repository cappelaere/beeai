# Redis Database Separation Strategy

## Overview

The consolidated Redis instance serves **both** the RealtyIQ UI and GSA Auction API, but they use **separate Redis databases** to maintain isolation and prevent cache conflicts.

## Database Allocation

| Component | Redis Database | URL Format | Purpose |
|-----------|----------------|------------|---------|
| **RealtyIQ UI** | Database 0 | `redis://redis:6379/0` | LLM response caching |
| **API (Django)** | Database 1 | `redis://redis:6379/1` | API response caching |

## Why Separate Databases?

### 1. **Isolation**
- UI cache changes don't affect API cache
- API cache changes don't affect UI cache
- Independent data lifecycle

### 2. **Different TTL Strategies**
- **UI Cache**: 3600 seconds (1 hour) - LLM responses are expensive, keep longer
- **API Cache**: 300 seconds (5 minutes) - API data changes more frequently

### 3. **Selective Cache Clearing**
```bash
# Clear only UI cache (database 0)
docker exec redis redis-cli -n 0 FLUSHDB

# Clear only API cache (database 1)
docker exec redis redis-cli -n 1 FLUSHDB

# Clear all (both databases)
docker exec redis redis-cli FLUSHALL
```

### 4. **Easier Debugging**
```bash
# Inspect UI cache keys
docker exec redis redis-cli -n 0 KEYS '*'

# Inspect API cache keys
docker exec redis redis-cli -n 1 KEYS '*'

# Get database info
docker exec redis redis-cli INFO keyspace
```

### 5. **Independent Monitoring**
```bash
# UI cache stats
docker exec redis redis-cli -n 0 DBSIZE
docker exec redis redis-cli -n 0 INFO

# API cache stats
docker exec redis redis-cli -n 1 DBSIZE
docker exec redis redis-cli -n 1 INFO
```

## Configuration

### Environment Variables

#### Root `.env` (RealtyIQ UI)
```bash
# RealtyIQ UI - Database 0
REDIS_URL=redis://localhost:6379/0  # Local development
# REDIS_URL=redis://redis:6379/0    # Docker deployment
REDIS_ENABLED=true
REDIS_TTL=3600  # 1 hour
```

#### `Api/.env` (GSA Auction API)
```bash
# API - Database 1
REDIS_LOCATION=redis://redis:6379/1  # Docker
# REDIS_LOCATION=redis://127.0.0.1:6379/1  # Local
REDIS_CACHE=True
CACHE_TTL=300  # 5 minutes
```

### Docker Compose

```yaml
services:
  api:
    environment:
      - REDIS_LOCATION=redis://redis:6379/1  # API uses database 1
      - REDIS_URL=redis://redis:6379/0       # UI uses database 0
```

## Redis Database Limits

**Default Configuration:**
- Redis supports **16 databases** by default (0-15)
- We're using **2 databases** (0 and 1)
- **14 databases** available for future use

**To change the limit:**
```yaml
# In docker-compose.yml
redis:
  command: >
    redis-server
    --databases 32  # Increase to 32 databases
```

## Cache Key Patterns

### UI (Database 0)
```
llm:prompt:<hash>              # LLM response cache
session:<session_id>:history   # Chat history (if cached)
user:<user_id>:preferences     # User settings
```

### API (Database 1)
```
:1:django_cache:<key>          # Django cache framework keys
auctions:list:<params>         # Auction listings
property:<id>:details          # Property details
user:<id>:profile              # User profiles
```

Note: Django automatically prefixes keys with `:1:` for database 1.

## Monitoring Commands

### Check Which Databases Have Data
```bash
docker exec redis redis-cli INFO keyspace
```

Output example:
```
# Keyspace
db0:keys=42,expires=42,avg_ttl=3245123
db1:keys=158,expires=120,avg_ttl=298456
```

### Memory Usage Per Database
```bash
# UI cache memory
docker exec redis redis-cli -n 0 MEMORY USAGE <key>

# API cache memory
docker exec redis redis-cli -n 1 MEMORY USAGE <key>
```

### Connection Info
```bash
# See which databases have active connections
docker exec redis redis-cli CLIENT LIST
```

### Key Statistics
```bash
# UI cache key count
echo "DB0 keys:" && docker exec redis redis-cli -n 0 DBSIZE

# API cache key count
echo "DB1 keys:" && docker exec redis redis-cli -n 1 DBSIZE
```

## Development Workflow

### Local Development
```bash
# Start Redis
make redis-start

# UI connects to database 0
make dev-ui

# API connects to database 1
cd Api && make up
```

### Docker Development
```bash
# Start all services
make docker-up

# API and UI both use redis:6379 but different databases
# API: redis://redis:6379/1
# UI: redis://redis:6379/0
```

## Testing Database Separation

### Test UI Cache (Database 0)
```bash
# Enter Redis CLI for database 0
docker exec -it redis redis-cli -n 0

# In Redis CLI:
SET test:ui "Hello from UI"
GET test:ui
# Output: "Hello from UI"

# Check from database 1 (should not exist)
SELECT 1
GET test:ui
# Output: (nil)
```

### Test API Cache (Database 1)
```bash
# Enter Redis CLI for database 1
docker exec -it redis redis-cli -n 1

# In Redis CLI:
SET test:api "Hello from API"
GET test:api
# Output: "Hello from API"

# Check from database 0 (should not exist)
SELECT 0
GET test:api
# Output: (nil)
```

### Test from Django Shell (API)
```bash
docker exec -it realtyiq-api python manage.py shell
```

```python
from django.core.cache import cache

# Set in database 1 (API)
cache.set('api_test', 'API cache value', 300)
print(cache.get('api_test'))
# Output: API cache value
```

### Test from Python (UI)
```python
import redis
import os

# Connect to database 0 (UI)
r = redis.from_url('redis://localhost:6379/0')
r.set('ui_test', 'UI cache value', ex=3600)
print(r.get('ui_test'))
# Output: b'UI cache value'
```

## Cache Invalidation Strategies

### UI Cache Invalidation
```bash
# Clear specific LLM response
docker exec redis redis-cli -n 0 DEL "llm:prompt:<hash>"

# Clear all UI cache
docker exec redis redis-cli -n 0 FLUSHDB

# Or via make command
make redis-flush  # This flushes ALL databases
```

### API Cache Invalidation
```bash
# Clear specific key
docker exec redis redis-cli -n 1 DEL ":1:django_cache:auction_list"

# Clear all API cache
docker exec redis redis-cli -n 1 FLUSHDB

# Via Django management command
docker exec realtyiq-api python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

## Best Practices

### 1. **Always Specify Database Number**
❌ Bad:
```bash
REDIS_URL=redis://localhost:6379  # Ambiguous, uses default (0)
```

✅ Good:
```bash
REDIS_URL=redis://localhost:6379/0  # Explicit database 0
```

### 2. **Document Database Usage**
Add comments in configuration files:
```bash
# Database 0: UI LLM cache
# Database 1: API Django cache
# Database 2-15: Available for future use
```

### 3. **Use Consistent Naming**
```python
# UI cache keys
llm:prompt:<hash>
ui:session:<id>

# API cache keys
api:auction:<id>
api:user:<id>
```

### 4. **Monitor Both Databases**
```bash
# Create monitoring script
cat > monitor_redis.sh << 'EOF'
#!/bin/bash
echo "=== Redis Database Statistics ==="
echo ""
echo "Database 0 (UI):"
docker exec redis redis-cli -n 0 DBSIZE
docker exec redis redis-cli -n 0 INFO memory | grep used_memory_human
echo ""
echo "Database 1 (API):"
docker exec redis redis-cli -n 1 DBSIZE
docker exec redis redis-cli -n 1 INFO memory | grep used_memory_human
EOF
chmod +x monitor_redis.sh
```

### 5. **Set Appropriate TTLs**
```python
# UI - Long TTL (expensive LLM calls)
REDIS_TTL = 3600  # 1 hour

# API - Short TTL (data changes frequently)
CACHE_TTL = 300   # 5 minutes
```

## Troubleshooting

### Issue: Keys Not Persisting
```bash
# Check if keys are being set in the correct database
docker exec redis redis-cli -n 0 MONITOR  # Monitor database 0
docker exec redis redis-cli -n 1 MONITOR  # Monitor database 1
```

### Issue: Cache Not Working
```bash
# Verify database connection
docker exec redis redis-cli -n 0 PING  # Should return PONG
docker exec redis redis-cli -n 1 PING  # Should return PONG

# Check configuration
docker exec realtyiq-api printenv | grep REDIS
```

### Issue: Wrong Database Being Used
```bash
# Check which database has the keys
docker exec redis redis-cli INFO keyspace

# Example output:
# db0:keys=25,expires=25  <- UI cache
# db1:keys=150,expires=100 <- API cache
```

## Future Expansion

If more services need caching:

```bash
# Database 0: RealtyIQ UI (LLM cache)
# Database 1: GSA Auction API (Django cache)
# Database 2: Available for Document Processing
# Database 3: Available for Analytics
# Database 4-15: Reserved for future use
```

Update `docker-compose.yml` environment variables accordingly.

## Summary

✅ **Current Setup:**
- **Database 0**: RealtyIQ UI LLM responses
- **Database 1**: GSA Auction API Django cache
- **Single Redis instance** (efficient resource usage)
- **Isolated caches** (no interference)
- **Different TTLs** (optimized for use case)

✅ **Benefits:**
- Lower memory usage (shared Redis)
- Easier management (single container)
- Better isolation (separate databases)
- Clear separation of concerns
- Easier debugging and monitoring

🎯 **Result:**
- Efficient caching for both services
- No cache conflicts
- Easy to monitor and debug
- Cost-effective resource usage

---

**Configuration Status**: ✅ **OPTIMIZED**

Both services use the same Redis instance with different databases for optimal performance and isolation.
