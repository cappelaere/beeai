# Database Health Check Fix

**Date:** February 21, 2026  
**Issue:** PostgreSQL health check failing with "no such function: version"  
**Status:** ✅ RESOLVED

## Problem

When viewing dashboard metrics or running `/metrics` command, the PostgreSQL health check failed with:

```
PostgreSQL: ✗ Connection error: no such function: version
```

## Root Cause

The Django UI application uses **SQLite** (not PostgreSQL), but the health check was hardcoded to use PostgreSQL's `version()` function. SQLite uses a different function: `sqlite_version()`.

**Database Configuration:**
```python
# agent_ui/agent_ui/settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

**Verification:**
```bash
$ python manage.py shell -c "from django.db import connection; print(connection.settings_dict['ENGINE'])"
django.db.backends.sqlite3
```

## Solution

Updated `check_postgres_health()` to be database-agnostic and handle both SQLite and PostgreSQL:

### Code Changes

**File:** `agent_ui/agent_app/health_checks.py`

```python
# Before (PostgreSQL only)
with connection.cursor() as cursor:
    cursor.execute("SELECT version();")  # ❌ Fails on SQLite
    version_info = cursor.fetchone()

# After (Database agnostic)
is_sqlite = 'sqlite' in db_engine.lower()
is_postgres = 'postgres' in db_engine.lower()

with connection.cursor() as cursor:
    if is_sqlite:
        cursor.execute("SELECT sqlite_version();")
        version = f"SQLite {version_info[0]}"
    elif is_postgres:
        cursor.execute("SELECT version();")
        version = version_info[0].split(',')[0]
    else:
        cursor.execute("SELECT 1;")  # Generic test
        version = 'Unknown'
```

### UI Updates

**File:** `agent_ui/templates/dashboard.html`
- Changed label from "PostgreSQL" to "Database" (generic)

**File:** `agent_ui/agent_app/commands/metrics.py`
- Changed label from "PostgreSQL" to "Database" in `/metrics` output

## Test Results

### Health Check ✅
```bash
$ python manage.py shell -c "from agent_app.health_checks import check_postgres_health; import json; print(json.dumps(check_postgres_health(), indent=2))"

{
  "status": "healthy",
  "database": "/Users/patrice/.../db.sqlite3",
  "engine": "sqlite3",
  "response_time_ms": 0,
  "version": "SQLite 3.50.4"
}
```

### Dashboard Display ✅
```
Database: ✓ 0ms
SQLite 3.50.4
```

### /metrics Command ✅
```
═══ Service Health ═══
Overall Status: ✓ All Systems Operational
BidHom API: ✓ 15ms
Piper TTS: ✓ 18ms
Redis Cache: ✓ 2ms
Database: ✓ 0ms
```

## Database Comparison

| Feature | PostgreSQL | SQLite |
|---------|-----------|---------|
| Version Query | `SELECT version();` | `SELECT sqlite_version();` |
| Version Format | `PostgreSQL 16.2 on...` | `3.50.4` |
| Connection Type | Network (port 5432) | File-based |
| Use Case | Production (API) | Development (UI) |

## Architecture

**RealtyIQ uses TWO databases:**

1. **PostgreSQL (API)** - Port 5432 (Docker)
   - Used by: BidHom API - Django REST (`Api/` folder)
   - Purpose: Production data, property listings, auctions
   - Connection: Network socket

2. **SQLite (UI)** - File-based
   - Used by: Django UI (`agent_ui/` folder)
   - Purpose: Chat sessions, messages, cards, preferences
   - File: `agent_ui/db.sqlite3`

## Files Modified

1. **`agent_ui/agent_app/health_checks.py`**
   - Updated `check_postgres_health()` to detect and handle both SQLite and PostgreSQL
   - Added database type detection logic
   - Database-specific version queries
   - Better error handling

2. **`agent_ui/templates/dashboard.html`**
   - Changed "PostgreSQL" label to "Database"
   - More accurate representation

3. **`agent_ui/agent_app/commands/metrics.py`**
   - Changed "PostgreSQL" to "Database" in output
   - Consistent with dashboard

## Benefits

✅ **Works with Both Databases** - Automatically detects and uses correct SQL syntax  
✅ **Production Ready** - When migrating to PostgreSQL, no code changes needed  
✅ **Better Error Messages** - Clear indication of database type  
✅ **Accurate Metrics** - Shows correct version information  
✅ **No False Errors** - Health check passes correctly

## Future Migration Path

If you want to migrate the UI to PostgreSQL:

1. Update `agent_ui/agent_ui/settings.py`:
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "realtyiq_ui",
        "USER": "postgres",
        "PASSWORD": "your_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

2. Run migrations: `python manage.py migrate`
3. Health check will automatically detect PostgreSQL and use `version()` function

**No code changes needed** - the health check is database-agnostic!

## Testing

### Test SQLite Health
```bash
python manage.py shell -c "from agent_app.health_checks import check_postgres_health; print(check_postgres_health())"
```

### Test in Dashboard
1. Open http://localhost:8002/dashboard
2. Check "Service Health" card
3. Verify "Database" shows green checkmark

### Test in /metrics Command
1. Open chat
2. Type `/metrics`
3. Verify "Database: ✓ 0ms" in output

---

**Fixed By:** AI Assistant  
**Date:** February 21, 2026  
**Status:** ✅ WORKING  
**Database:** SQLite 3.50.4
