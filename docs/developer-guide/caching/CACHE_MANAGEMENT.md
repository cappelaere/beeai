# Cache Management in Settings

## Overview

The Settings page now includes a comprehensive Cache Management section where you can:
- View real-time cache statistics
- Monitor cache performance (hit rate, hits, misses)
- Clear all cached LLM responses with one click
- See cache configuration details

## Features

### 1. Cache Status Display

Shows whether Redis caching is enabled:
- ✅ **Enabled** (green badge) - Cache is working
- **Disabled** (gray badge) - Cache is not configured

### 2. Cache Statistics

Real-time metrics displayed:
- **Cached Prompts**: Total number of unique prompts cached
- **Cache Hits**: Number of times cache was used (green)
- **Cache Misses**: Number of times fresh API calls were needed (yellow)
- **Hit Rate**: Percentage of requests served from cache (blue)

Additional info:
- Cache TTL (Time To Live)
- Redis database number (0 for UI)
- Memory usage

### 3. Clear Cache Button

**Function**: Clears all cached LLM responses from Redis

**Behavior**:
1. Shows confirmation dialog
2. Displays loading spinner
3. Calls `/api/cache/clear/` endpoint
4. Shows success/error alert
5. Auto-refreshes page to update statistics

**Safety**:
- Requires confirmation before clearing
- Only enabled when cache is active
- Provides clear feedback
- Handles errors gracefully

## Usage

### Access Settings Page

```
Left Navbar → Settings → Cache Management section
```

Or directly: `http://localhost:8002/settings/`

### View Cache Stats

The statistics update automatically when you load the Settings page:

```
┌─────────────────────────────────────────────┐
│ Cache Management                            │
├─────────────────────────────────────────────┤
│ Redis Cache Status        [✓ Enabled]       │
│                      [Clear Cache] button   │
│                                             │
│ Cached Prompts:  42                         │
│ Cache Hits:      156  (green)               │
│ Cache Misses:    73   (yellow)              │
│ Hit Rate:        68%  (blue)                │
│                                             │
│ ℹ Cache TTL: 3600s | Redis DB: 0 (UI) |    │
│   Memory: 2.4 MB                            │
└─────────────────────────────────────────────┘
```

### Clear Cache

1. Click the **Clear Cache** button
2. Confirm in the dialog:
   ```
   Are you sure you want to clear all cached LLM responses?
   This will reset cache statistics and force fresh API calls.
   ```
3. Wait for confirmation:
   - ✓ Success: "Cache cleared successfully!"
   - ✗ Error: Shows error message
4. Page refreshes automatically after 2 seconds

## When to Clear Cache

### Good Reasons to Clear

1. **Testing**: Verify fresh LLM responses
2. **Model Changes**: After changing LLM model in .env
3. **Stale Data**: Remove old cached responses
4. **Debugging**: Isolate caching vs LLM issues
5. **Memory**: Free up Redis memory

### You Don't Need to Clear

- ❌ Cache automatically expires after TTL (1 hour default)
- ❌ Cache is automatically managed by Redis LRU policy
- ❌ Old entries are automatically evicted when memory limit reached

## Cache Statistics Explained

### Cached Prompts
Total unique prompts stored in Redis cache.

**What it means**:
- Higher number = more diverse queries cached
- Grows over time until TTL expires or cache cleared

### Cache Hits
Number of times a cached response was returned.

**What it means**:
- Higher number = better cache utilization
- Saves LLM API costs
- Faster response times (<100ms)

### Cache Misses
Number of times a fresh LLM call was needed.

**What it means**:
- Normal for new or unique prompts
- Expected on first query
- Higher on diverse workloads

### Hit Rate
Percentage of requests served from cache.

**What it means**:
- **0-25%**: Low cache efficiency (diverse queries)
- **25-50%**: Moderate caching (varied usage)
- **50-75%**: Good caching (common queries repeated)
- **75%+**: Excellent caching (high repetition)

**Target**: 50%+ for typical workloads

## Technical Details

### API Endpoints Used

**Get Stats** (automatic):
```bash
GET /api/cache/stats/
```

**Clear Cache** (button click):
```bash
POST /api/cache/clear/
```

### Cache Configuration

Controlled by environment variables in `.env`:

```bash
REDIS_ENABLED=true           # Enable/disable caching
REDIS_URL=redis://localhost:6379/0  # Redis connection (DB 0 for UI)
REDIS_TTL=3600              # Cache expiry in seconds (1 hour)
REDIS_MAX_CONNECTIONS=10     # Connection pool size
```

### Redis Database Separation

- **Database 0**: UI cache (Settings page manages this)
- **Database 1**: API cache (separate)

This ensures:
- UI and API caches don't interfere
- Independent TTLs and policies
- Separate clearing operations

### Makefile Commands

Alternative ways to manage cache:

```bash
# Clear UI cache only (Database 0)
make redis-flush-ui

# Clear API cache only (Database 1)
make redis-flush-api

# Clear ALL caches (both databases)
make redis-flush

# View Redis statistics
make redis-info

# Check Redis status
make redis-status
```

## User Interface

### Visual Design

**Light Mode**:
- Clean white card background
- Green badges for success states
- IBM Carbon color palette
- Clear hierarchy and spacing

**Dark Mode**:
- Dark gray card background
- Adjusted contrast for readability
- Consistent with app theme
- Reduced eye strain

### Responsive Behavior

- Statistics in responsive grid (4 columns on desktop)
- Stacks vertically on mobile
- Touch-friendly buttons
- Accessible ARIA labels

### Loading States

**When clearing cache**:
1. Button shows spinner
2. Button text changes to "Clearing..."
3. Button is disabled
4. Alert shows result
5. Page reloads on success

## Error Handling

### If Redis is Not Installed

Shows:
```
Cache is not enabled.
Set REDIS_ENABLED=true in .env and ensure Redis is running.
```

Button is disabled.

### If Clear Fails

Shows alert:
```
✗ Failed to clear cache: [error message]
```

Button returns to normal state.

### If Redis is Down

Shows:
```
Cache Status: Disabled
Error: Connection refused
```

Statistics show "N/A" or "0".

## Best Practices

### Cache Monitoring

1. **Check hit rate regularly** - Should be >50% for typical usage
2. **Monitor cached prompts** - Too many may indicate TTL is too long
3. **Watch memory usage** - Shouldn't exceed Redis max memory (256MB default)

### When to Use Clear Cache

✅ **Good times**:
- After updating prompt templates
- When testing specific prompts
- Before performance benchmarking
- After model configuration changes

❌ **Don't clear**:
- During normal operation
- To "fix" slow responses (cache makes things faster!)
- As part of regular maintenance (auto-managed)

### Performance Impact

**After clearing cache**:
- First queries will be slower (cache miss, LLM call required)
- Subsequent identical queries will be fast again
- Cache rebuilds naturally over time
- No impact on functionality

## Troubleshooting

### Cache Management Section Not Showing

**Check**:
1. Is Redis installed? `pip list | grep redis`
2. Is REDIS_ENABLED=true in .env?
3. Restart server after installing redis

### Clear Button Doesn't Work

**Solutions**:
1. Check browser console for JavaScript errors
2. Verify CSRF token is present
3. Check Redis is running: `make redis-status`
4. Check API endpoint: `curl -X POST http://localhost:8002/api/cache/clear/`

### Statistics Show All Zeros

**Causes**:
- Cache was just cleared
- No queries have been made yet
- Redis connection issue

**Check**: `make redis-status`

## Documentation

- **[CACHE_IMPLEMENTATION.md](CACHE_IMPLEMENTATION.md)** - Technical implementation details
- **[REDIS_DATABASE_SEPARATION.md](REDIS_DATABASE_SEPARATION.md)** - Database architecture
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - General troubleshooting

## Summary

✅ **Added**: Complete cache management UI in Settings  
✅ **Features**: Stats display + clear button  
✅ **Design**: Clean, modern, responsive  
✅ **Safety**: Confirmation required, error handling  
✅ **Integration**: Uses existing cache APIs  

**Access**: Settings → Cache Management → [Clear Cache]

---

**Last Updated**: February 16, 2026  
**Version**: 1.0.0
