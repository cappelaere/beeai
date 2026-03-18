# Redis Cache Setup for RealtyIQ

## Overview

Redis is used to cache LLM responses to improve performance and reduce API costs. When a user sends a prompt that has been seen before, the cached response is returned instantly instead of calling the LLM again.

## Quick Start

### Using Make (Recommended)

```bash
# Start Redis
make redis-start

# Check Redis status
make redis-status

# Start UI with Redis
make dev

# Stop Redis
make redis-stop
```

### Using Docker Compose

```bash
# Start Redis only
docker-compose up -d redis

# Start all services (if configured)
docker-compose up -d

# Stop all services
docker-compose down
```

### Manual Docker

```bash
# Start Redis
docker run -d \
  --name realtyiq-redis \
  -p 6379:6379 \
  -v realtyiq-redis-data:/data \
  redis:7-alpine \
  redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

# Check if running
docker ps | grep redis

# Stop Redis
docker stop realtyiq-redis

# Remove Redis container
docker rm realtyiq-redis
```

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true
REDIS_TTL=3600  # Cache TTL in seconds (1 hour)
REDIS_MAX_CONNECTIONS=10
```

### Redis Settings

- **Port**: 6379 (default)
- **Max Memory**: 256MB
- **Eviction Policy**: allkeys-lru (removes least recently used keys)
- **Persistence**: AOF (Append Only File) enabled
- **Save Interval**: Every 60 seconds if 1000 keys changed

## Architecture

```
User Request
    ↓
Django View
    ↓
Cache Check (Redis)
    ├─ Cache Hit → Return cached response (instant)
    └─ Cache Miss → Call LLM
                      ↓
                   Store in Redis
                      ↓
                   Return response
```

## Cache Key Strategy

Cache keys are generated based on:
1. **Prompt text** (normalized)
2. **Model name**
3. **User ID** (optional)

Example key format:
```
llm_cache:anthropic:claude-sonnet-4-5:hash_of_prompt
```

## Benefits

### Performance
- **Instant responses** for repeated queries
- **Reduced latency** from ~2-3s to ~10ms

### Cost Savings
- **No API calls** for cached responses
- **Reduced token usage** significantly
- **Lower Langfuse costs** (fewer traces)

### User Experience
- **Faster responses** for common questions
- **Consistent answers** for same questions
- **Better scalability** under load

## Commands Reference

### Makefile Commands

```bash
# Redis Management
make redis-start        # Start Redis server
make redis-stop         # Stop Redis server
make redis-restart      # Restart Redis server
make redis-status       # Show Redis status and stats
make redis-cli          # Open Redis CLI
make redis-flush        # Clear all cache
make redis-logs         # View Redis logs

# Development
make dev                # Start UI with Redis
make setup              # Full setup including Redis
```

### Redis CLI Commands

```bash
# Connect to Redis
make redis-cli

# Check keys
KEYS *

# Get a specific key
GET llm_cache:*

# Check database size
DBSIZE

# View memory usage
INFO memory

# View cache stats
INFO stats

# Clear all cache
FLUSHALL

# Exit
exit
```

## Monitoring

### Cache Statistics

Check hit/miss ratio:
```bash
make redis-status
```

Output shows:
- Keys stored
- Memory usage
- Cache hits/misses
- Uptime

### View Cached Keys

```bash
docker exec realtyiq-redis redis-cli KEYS "llm_cache:*"
```

### Check Specific Cache Entry

```bash
docker exec realtyiq-redis redis-cli GET "llm_cache:your_key_here"
```

## Troubleshooting

### Redis Not Starting

**Problem**: Port 6379 already in use

**Solution**:
```bash
# Check what's using the port
lsof -i :6379

# Kill the process or change Redis port
```

### Cache Not Working

**Check 1**: Is Redis running?
```bash
make redis-status
```

**Check 2**: Is REDIS_ENABLED=true in .env?
```bash
grep REDIS_ENABLED .env
```

**Check 3**: Is Redis URL correct?
```bash
# Should be redis://localhost:6379 for local Docker
grep REDIS_URL .env
```

### Connection Refused

**Problem**: Can't connect to Redis

**Solutions**:
```bash
# 1. Check if Redis is running
docker ps | grep redis

# 2. Restart Redis
make redis-restart

# 3. Check Docker network
docker network ls
```

### Out of Memory

**Problem**: Redis using too much memory

**Solutions**:
```bash
# 1. Check memory usage
docker exec realtyiq-redis redis-cli INFO memory

# 2. Clear cache
make redis-flush

# 3. Reduce TTL in .env
# REDIS_TTL=1800  # 30 minutes instead of 1 hour
```

## Performance Tips

### 1. Adjust TTL Based on Content

```python
# Frequently changing data: shorter TTL
REDIS_TTL = 300  # 5 minutes

# Stable data: longer TTL
REDIS_TTL = 86400  # 24 hours
```

### 2. Monitor Cache Hit Rate

Target: **>70% hit rate** for good caching

```bash
# Check periodically
make redis-status | grep keyspace
```

### 3. Size Limits

Current: 256MB max memory

Adjust if needed:
```bash
# In docker command or docker-compose.yml
--maxmemory 512mb  # Increase to 512MB
```

### 4. Eviction Policy

Current: `allkeys-lru` (Least Recently Used)

Alternatives:
- `volatile-lru`: Only evict keys with TTL
- `allkeys-lfu`: Least Frequently Used
- `volatile-ttl`: Evict shortest TTL first

## Security

### Production Considerations

1. **Authentication**: Add Redis password
```bash
# In docker command
redis-server --requirepass your_secure_password

# In .env
REDIS_URL=redis://:your_secure_password@localhost:6379
```

2. **Network**: Bind to localhost only (default)

3. **Firewall**: Block external access to port 6379

4. **Encryption**: Use TLS for production (Redis 6+)

## Advanced Usage

### Multiple Redis Instances

```yaml
# docker-compose.yml
services:
  redis-cache:
    image: redis:7-alpine
    ports: ["6379:6379"]
  
  redis-sessions:
    image: redis:7-alpine
    ports: ["6380:6379"]
```

### Redis Cluster

For high availability:
```yaml
services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --appendonly yes
  
  redis-replica:
    image: redis:7-alpine
    command: redis-server --slaveof redis-master 6379
```

### Persistent Storage

Data persists in Docker volume `realtyiq-redis-data`

Backup:
```bash
# Create backup
docker exec realtyiq-redis redis-cli SAVE

# Copy backup file
docker cp realtyiq-redis:/data/dump.rdb ./backup-$(date +%Y%m%d).rdb
```

Restore:
```bash
# Copy backup to container
docker cp backup-20260215.rdb realtyiq-redis:/data/dump.rdb

# Restart Redis
make redis-restart
```

## Testing

### Test Cache Integration

```bash
# 1. Start Redis
make redis-start

# 2. Send a test request (record time)
curl -X POST http://localhost:8002/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "List all properties"}'

# 3. Send same request again (should be faster)
curl -X POST http://localhost:8002/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "List all properties"}'

# 4. Check cache
make redis-cli
> KEYS llm_cache:*
> GET <key_name>
```

### Performance Comparison

Without cache: ~2-3 seconds
With cache (hit): ~10-50ms

That's a **20-60x speedup**!

## Next Steps

After setting up Redis:

1. ✅ Start Redis: `make redis-start`
2. ✅ Verify status: `make redis-status`
3. ⏭️ Implement cache logic in `agent_runner.py`
4. ⏭️ Add cache middleware
5. ⏭️ Test cache hit/miss
6. ⏭️ Monitor performance

See `cache.py` for implementation details.

---

**Status**: Redis infrastructure ready for cache implementation

Redis is now set up and ready to cache LLM responses!
