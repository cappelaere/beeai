# Caching & Redis Documentation

Documentation for Redis caching system and LLM response caching.

---

## Main Documentation

- **[CACHE_IMPLEMENTATION.md](CACHE_IMPLEMENTATION.md)** - Complete caching implementation
- **[CACHE_MANAGEMENT.md](CACHE_MANAGEMENT.md)** - Cache management UI in settings
- **[REDIS_DATABASE_SEPARATION.md](REDIS_DATABASE_SEPARATION.md)** - Redis database architecture
- **[REDIS_CONFIG_FIX.md](REDIS_CONFIG_FIX.md)** - Configuration troubleshooting
- **[REDIS_CACHE_SUMMARY.md](REDIS_CACHE_SUMMARY.md)** - Caching summary
- **[README_REDIS.md](README_REDIS.md)** - Redis setup guide

---

## Key Features

- **Dual Database Architecture** - Database 0 for UI, Database 1 for API
- **LLM Response Caching** - <100ms response time for cached queries
- **Cache Management UI** - View stats and clear cache from settings
- **Smart Invalidation** - Clear cache on startup
- **Performance Monitoring** - Hit/miss rates and statistics

---

## Commands

```bash
make redis-start        # Start Redis
make redis-info         # View statistics  
make redis-flush-ui     # Clear UI cache (DB 0)
make redis-flush-api    # Clear API cache (DB 1)
```

---

**Back to**: [Documentation Index](../README.md)
