# LLM Response Caching Implementation

## Overview

Implemented Redis-based caching for LLM responses in the RealtyIQ Chat UI to improve performance, reduce API costs, and enhance user experience.

## Features Implemented

### ✅ 1. Redis Cache Module (`agent_ui/cache.py`)

A dedicated caching module with the following capabilities:

- **Automatic prompt hashing** - SHA256 hash of prompts for consistent keys
- **TTL management** - Configurable time-to-live (default: 1 hour)
- **Error handling** - Graceful degradation if Redis is unavailable
- **Cache statistics** - Hit rate, miss rate, and key counts
- **Logging** - Detailed logs for cache hits/misses

### ✅ 2. Integration with Agent Runner

Updated `agent_ui/agent_runner.py` to:

- Check cache before running agent
- Store responses in cache after generation
- Log cache operations with emojis for visibility:
  - `✅` - Cache hit (response retrieved)
  - `💾` - Response cached
  - `🎯` - Cache HIT in cache module
  - `❌` - Cache MISS in cache module

### ✅ 3. API Endpoints

Added cache management endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/cache/stats/` | GET | Get cache statistics |
| `/api/cache/clear/` | POST | Clear all cached responses |

### ✅ 4. Visual Indicators

Added UI elements to show cached responses:

- **Cache badge** - Blue badge showing "Cached" with clock icon
- **Border highlight** - Left border on cached messages (blue)
- **Dark mode support** - Adjusted colors for dark theme

### ✅ 5. Logging

Comprehensive logging at multiple levels:

**Backend (Python):**
```python
logger.info(f"🎯 Cache HIT for prompt (key: {key[:32]}...)")
logger.info(f"❌ Cache MISS for prompt (key: {key[:32]}...)")
logger.info(f"💾 Cached response for prompt (key: {key[:32]}..., TTL: {ttl}s)")
logger.info(f"✅ Returning cached response for prompt: {prompt[:50]}...")
logger.info(f"⚙️  Cache MISS - Generated new response for prompt: {prompt[:50]}...")
```

**Frontend (JavaScript):**
- Cache indicator badge in message metadata
- Visual border on cached messages

## Architecture

```
User Prompt
    ↓
┌───────────────────────────────────┐
│  Django View (views.py)           │
│  - Receives prompt                │
│  - Calls agent_runner             │
└───────────────┬───────────────────┘
                ↓
┌───────────────────────────────────┐
│  Agent Runner (agent_runner.py)   │
│  1. Check cache.get(prompt)       │
│  2. If HIT: return cached         │
│  3. If MISS: run agent            │
│  4. cache.set(prompt, response)   │
└───────────────┬───────────────────┘
                ↓
┌───────────────────────────────────┐
│  Cache Module (cache.py)          │
│  - Redis connection (DB 0)        │
│  - Key: llm:prompt:<hash>         │
│  - TTL: 3600s (1 hour)           │
└───────────────────────────────────┘
```

## Cache Key Strategy

### Key Format
```
llm:prompt:<hash>
```

Where `<hash>` is the first 16 characters of SHA256(prompt).

### Examples
```
llm:prompt:a3f2e1d4c5b6a798  # "What properties are available?"
llm:prompt:7c8d9e0f1a2b3c4d  # "Show me auction dashboard"
```

### Why This Works

1. **Deterministic** - Same prompt always generates same key
2. **Compact** - 16-char hash keeps keys short
3. **Collision-resistant** - SHA256 ensures uniqueness
4. **Scannable** - Pattern `llm:prompt:*` for bulk operations

## Configuration

### Environment Variables

```bash
# Enable/disable caching
REDIS_ENABLED=true

# Redis connection (Database 0 for UI)
REDIS_URL=redis://localhost:6379/0

# Cache TTL in seconds (1 hour = 3600)
REDIS_TTL=3600

# Max connections to Redis
REDIS_MAX_CONNECTIONS=10
```

### Cache Behavior

| Setting | Value | Impact |
|---------|-------|--------|
| `REDIS_ENABLED=true` | Cache ON | Responses cached |
| `REDIS_ENABLED=false` | Cache OFF | No caching, always generate |
| `REDIS_TTL=3600` | 1 hour | Responses expire after 1 hour |
| `REDIS_TTL=7200` | 2 hours | Longer cache retention |

## Usage

### Automatic Caching

Caching happens automatically - no code changes needed:

```python
# This automatically checks cache
response, metadata = run_agent_sync(prompt, session_id, user_id)

# Check if from cache
if metadata.get('from_cache'):
    print("Response was cached!")
```

### Manual Cache Management

```python
from cache import get_cache

cache = get_cache()

# Get cache statistics
stats = cache.get_stats()
print(stats)
# Output: {
#   'enabled': True,
#   'connected': True,
#   'cached_prompts': 42,
#   'total_hits': 128,
#   'total_misses': 56,
#   'hit_rate': 69.57
# }

# Clear all cached responses
cache.clear_all()

# Delete specific cache entry
cache.delete("What properties are available?")
```

### Via API

```bash
# Get cache statistics
curl http://localhost:8002/api/cache/stats/

# Clear cache
curl -X POST http://localhost:8002/api/cache/clear/
```

## Performance Benefits

### Before Caching

```
User sends: "Show me auction dashboard"
→ Agent runs (3-5 seconds)
→ LLM API call ($$$)
→ Response returned

Same prompt again:
→ Agent runs AGAIN (3-5 seconds)
→ LLM API call AGAIN ($$$)
→ Response returned
```

### After Caching

```
User sends: "Show me auction dashboard"
→ Cache MISS
→ Agent runs (3-5 seconds)
→ LLM API call ($$$)
→ Response cached
→ Response returned

Same prompt again:
→ Cache HIT
→ Return cached response (<100ms) ✨
→ No LLM call (FREE) 💰
→ Response returned instantly
```

### Metrics

| Metric | Without Cache | With Cache |
|--------|--------------|------------|
| **Response Time** | 3-5 seconds | <100ms |
| **LLM API Calls** | Every request | First request only |
| **Cost per Request** | $0.01-0.05 | $0.00 (cached) |
| **User Experience** | Slow | Instant ✨ |

## Logging Examples

### Cache Hit (Fast!)

```log
2026-02-16 13:45:23 - cache - INFO - 🎯 Cache HIT for prompt (key: llm:prompt:a3f2e1d4c5b6a798...)
2026-02-16 13:45:23 - agent_runner - INFO - ✅ Returning cached response for prompt: What properties are available?...
2026-02-16 13:45:23 - agent_app.views - INFO - 🎯 Cache HIT - Returning cached response for prompt: What properties are available?...
```

### Cache Miss (Generate)

```log
2026-02-16 13:45:30 - cache - INFO - ❌ Cache MISS for prompt (key: llm:prompt:7c8d9e0f1a2b3c4d...)
2026-02-16 13:45:35 - cache - INFO - 💾 Cached response for prompt (key: llm:prompt:7c8d9e0f1a2b3c4d..., TTL: 3600s)
2026-02-16 13:45:35 - agent_runner - INFO - 💾 Response cached for future use
2026-02-16 13:45:35 - agent_app.views - INFO - ⚙️  Cache MISS - Generated new response for prompt: Show me auction dashboard...
```

## Testing Cache

### Test Cache Hit/Miss

```bash
# Start UI with Redis
make dev

# Send first prompt (will be MISS)
# Check logs: ❌ Cache MISS

# Send SAME prompt again (will be HIT)
# Check logs: 🎯 Cache HIT

# Look for cache badge in UI: "Cached" with clock icon
```

### Test Cache Statistics

```bash
# Get cache stats
curl http://localhost:8002/api/cache/stats/

# Response:
{
  "enabled": true,
  "connected": true,
  "cached_prompts": 5,
  "total_hits": 12,
  "total_misses": 5,
  "hit_rate": 70.59
}
```

### Test Cache Clear

```bash
# Clear all cached responses
curl -X POST http://localhost:8002/api/cache/clear/

# Response:
{
  "success": true,
  "message": "Cache cleared successfully"
}
```

### Monitor Redis

```bash
# Connect to Redis CLI (database 0)
docker exec -it redis redis-cli -n 0

# List all cached prompts
KEYS llm:prompt:*

# Get a specific cached response
GET llm:prompt:a3f2e1d4c5b6a798

# Check TTL (time to live)
TTL llm:prompt:a3f2e1d4c5b6a798

# Monitor cache operations in real-time
MONITOR
```

## Cache Invalidation

### Automatic Expiration

Responses automatically expire after TTL (default: 1 hour)

### Manual Invalidation

```bash
# Clear all cached responses
make redis-flush-ui

# Or via API
curl -X POST http://localhost:8002/api/cache/clear/

# Or via Redis CLI
docker exec redis redis-cli -n 0 FLUSHDB
```

### When to Invalidate

- After significant data updates
- When prompt interpretation changes
- When LLM model is updated
- For testing purposes

## UI Indicators

### Cache Badge

Cached responses show a blue badge:

```
┌─────────────────────────────────┐
│ RealtyIQ  🕐 Cached             │
│                                  │
│ Here is the cached response...   │
│                                  │
│ Jan 15 2:30:45 PM • 50ms        │
└─────────────────────────────────┘
```

### Visual Border

Cached messages have a blue left border for easy identification.

### Dark Mode

Colors automatically adjust in dark theme:
- Badge: Darker blue with lighter text
- Border: Lighter blue for visibility

## Files Modified

### New Files

1. **`agent_ui/cache.py`** - Redis cache module (230 lines)

### Modified Files

1. **`agent_ui/agent_runner.py`**
   - Added logging
   - Integrated cache.get() before agent run
   - Integrated cache.set() after agent run

2. **`agent_ui/agent_app/views.py`**
   - Added logging for cache hits/misses
   - Added `from_cache` to response JSON
   - Added `/api/cache/stats/` endpoint
   - Added `/api/cache/clear/` endpoint

3. **`agent_ui/agent_app/urls.py`**
   - Added cache API routes

4. **`agent_ui/static/js/chat.js`**
   - Updated `appendMessage()` to accept `fromCache` parameter
   - Added cache badge rendering
   - Pass `data.from_cache` to `appendMessage()`

5. **`agent_ui/static/css/theme.css`**
   - Added `.cache-badge` styles
   - Added `.from-cache` message styles
   - Added dark mode cache styles

## Troubleshooting

### Cache Not Working

**Symptoms:**
- No cache badges appearing
- Logs show no cache operations

**Check:**
```bash
# 1. Verify Redis is running
docker ps | grep redis

# 2. Check REDIS_ENABLED
echo $REDIS_ENABLED  # Should be "true"

# 3. Test Redis connection
docker exec redis redis-cli -n 0 PING
# Should return: PONG

# 4. Check logs
tail -f agent_ui/logs/agent.log | grep -i cache
```

### Cache Always Missing

**Symptoms:**
- Always see ❌ Cache MISS
- Never see 🎯 Cache HIT

**Possible Causes:**
1. TTL too short - responses expiring quickly
2. Prompt variations - slight differences create new keys
3. Redis restarted - all data lost

**Fix:**
```bash
# Increase TTL
REDIS_TTL=7200  # 2 hours

# Check if keys exist
docker exec redis redis-cli -n 0 KEYS llm:prompt:*

# Check key TTL
docker exec redis redis-cli -n 0 TTL llm:prompt:<hash>
```

### High Memory Usage

**Symptoms:**
- Redis using too much memory

**Fix:**
```bash
# Check memory usage
docker exec redis redis-cli -n 0 INFO memory

# Reduce TTL
REDIS_TTL=1800  # 30 minutes

# Configure max memory in docker-compose.yml
redis:
  command: --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## Best Practices

### 1. Set Appropriate TTL

```bash
# Short TTL for frequently changing data
REDIS_TTL=600  # 10 minutes

# Long TTL for stable data
REDIS_TTL=7200  # 2 hours
```

### 2. Monitor Cache Hit Rate

```bash
# Aim for >50% hit rate
curl http://localhost:8002/api/cache/stats/ | jq '.hit_rate'
```

### 3. Clear Cache After Updates

```bash
# After data changes
curl -X POST http://localhost:8002/api/cache/clear/
```

### 4. Use Logging

```python
# In agent_runner.py logging is automatic
# Monitor logs for cache behavior
tail -f logs/agent.log | grep -E '🎯|❌|💾|✅'
```

## Future Enhancements

### Planned Features

1. **Per-session caching** - Session-specific cache keys
2. **Selective invalidation** - Clear cache by pattern
3. **Cache warming** - Pre-cache common queries
4. **Analytics dashboard** - Visual cache statistics
5. **Cache compression** - Reduce memory usage
6. **Multi-tier caching** - Memory + Redis

### Configuration Options

```python
# Planned configuration
CACHE_STRATEGY = "global"  # or "session" or "user"
CACHE_COMPRESSION = True
CACHE_WARMING = ["common queries list"]
```

## Summary

✅ **Implemented:**
- Redis-based LLM response caching
- Automatic cache check before agent run
- Response storage after generation
- Cache statistics and management APIs
- Visual UI indicators for cached responses
- Comprehensive logging
- Dark mode support

🎯 **Benefits:**
- **Fast responses** - <100ms for cached results
- **Cost savings** - No LLM API calls for cached responses
- **Better UX** - Instant responses for repeated queries
- **Visibility** - Clear logging and UI indicators
- **Manageable** - Stats and clear APIs

💡 **Result:**
A production-ready caching system that improves performance, reduces costs, and enhances user experience with clear visibility into cache operations.

---

**Status**: ✅ **COMPLETE**

LLM response caching fully implemented with logging, UI indicators, and management APIs.
