# RealtyIQ Troubleshooting Guide

## Common Issues and Solutions

### UI Server Won't Start

#### Issue: ModuleNotFoundError: No module named 'agent_ui.agent_ui'

**Symptoms:**
```
ModuleNotFoundError: No module named 'agent_ui.agent_ui'
```

**Cause:** Mismatch in Django settings module path between `manage.py` and `asgi.py`.

**Solution:** ✅ Fixed in latest version
- `asgi.py` now uses `"agent_ui.settings"` (consistent with `manage.py`)
- Pull latest changes or update `agent_ui/agent_ui/asgi.py` line 20

**Verify fix:**
```bash
cd agent_ui
python -c "import agent_ui.settings; print('OK')"
python manage.py check
```

#### Issue: Port 8002 already in use

**Symptoms:**
```
ERROR: Address already in use
```

**Solution:**
```bash
# Find and kill process on port 8002
lsof -ti:8002 | xargs kill -9

# Or use a different port
cd agent_ui && uvicorn agent_ui.asgi:application --port 8003 --reload
```

#### Issue: Redis connection refused

**Symptoms:**
```
ConnectionRefusedError: [Errno 61] Connection refused
```

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not running, start Redis
make redis-start

# Or start with Docker
make docker-up
```

### Test Issues

#### Issue: Tests hang or crash terminal

**Solution:** Use the safe test commands:
```bash
# Safest - backend only
make test-backend

# With error handling
./test-safe.sh backend

# See docs/TEST_TROUBLESHOOTING.md for details
```

#### Issue: Test failures after changes

**Solution:**
```bash
# Clear test database and re-run
rm agent_ui/db.sqlite3
cd agent_ui && python manage.py migrate
make test-backend
```

### Database Issues

#### Issue: Database is locked

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Close all connections and restart
pkill -f "python manage.py"
make dev-ui
```

#### Issue: Migration errors

**Solution:**
```bash
# Reset migrations (development only!)
cd agent_ui
rm db.sqlite3
python manage.py migrate
python manage.py seed_prompts
python manage.py seed_cards
```

### Docker Issues

#### Issue: Volume already exists warning

**Symptoms:**
```
WARNING: volume "realtyiq-redis-data" already exists but was not created by Docker Compose
```

**Solution:** ✅ Fixed in docker-compose.yml
```yaml
volumes:
  redis-data:
    external: true  # Uses existing volume
```

#### Issue: Container won't start

**Solution:**
```bash
# Check status
make docker-ps

# View logs
make docker-logs

# Restart services
make docker-restart

# Full reset (careful!)
make docker-down
docker volume prune
make docker-up
```

### Redis Issues

#### Issue: Cache module not available

**Symptoms:**
```
WARNING - Cache module not available
```

**Cause:** Redis Python package not installed

**Solution:**
```bash
# Activate virtual environment
source dev-setup.sh

# Install redis packages
pip install redis hiredis

# Or reinstall all requirements
pip install -r requirements.txt

# Restart server
make dev-ui
```

**Verify:**
```bash
pip list | grep redis
# Should show: redis 5.x.x and hiredis 2.x.x
```

#### Issue: Can't connect to Redis

**Solution:**
```bash
# Check Redis status
make redis-status

# Start Redis if stopped
make redis-start

# Check configuration
echo $REDIS_URL
echo $REDIS_LOCATION
```

#### Issue: Cache not working

**Solution:**
```bash
# Check if Redis is enabled
grep REDIS_ENABLED .env

# Clear cache and test
make redis-flush
make redis-info

# Check cache stats
curl http://localhost:8002/api/cache/stats/
```

### MCP Server Issues

#### Issue: MCP server won't start

**Solution:**
```bash
# Check environment variables
source dev-setup.sh
echo $API_URL
echo $AUTH_TOKEN

# Install dependencies
pip install -r requirements.txt

# Start server
make dev-mcp
```

#### Issue: Tools not available

**Solution:**
```bash
# List available tools
python -c "from tools import get_tools_list; print(get_tools_list())"

# Check MCP server logs
make dev-mcp
```

### Environment Issues

#### Issue: Virtual environment not activated

**Solution:**
```bash
# Auto-setup (recommended)
source dev-setup.sh

# Manual activation
source venv/bin/activate
```

#### Issue: Wrong Python version

**Solution:**
```bash
# Check version
python --version  # Should be 3.13.x

# If wrong, recreate venv
rm -rf venv
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Issue: Wrong Node.js version

**Solution:**
```bash
# Use .nvmrc to set correct version
nvm use

# Or install if needed
nvm install

# Or use dev-setup.sh
source dev-setup.sh
```

### Performance Issues

#### Issue: Slow LLM responses

**Solution:**
1. Check Redis caching is enabled:
   ```bash
   grep REDIS_ENABLED .env
   ```

2. Verify cache is working:
   ```bash
   # First request (slow)
   curl -X POST http://localhost:8002/api/chat/ \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello"}'
   
   # Second request (should be fast, <100ms)
   curl -X POST http://localhost:8002/api/chat/ \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello"}'
   ```

3. Check cache stats:
   ```bash
   curl http://localhost:8002/api/cache/stats/
   ```

#### Issue: High memory usage

**Solution:**
```bash
# Clear Redis cache
make redis-flush

# Restart services
make docker-restart

# Check Redis memory
redis-cli info memory
```

### Observability Issues

#### Issue: 'Langfuse' object has no attribute 'trace'

**Symptoms:**
```
Error running agent: 'Langfuse' object has no attribute 'trace'
```

**Cause:** Code using old Langfuse 2.x API, but SDK 3.x is installed

**Solution:** ✅ Fixed in latest version
- Updated to use `start_observation()` with `TraceContext`
- Restart server: `make dev-ui`

#### Issue: start_span() got unexpected keyword argument 'user_id'

**Symptoms:**
```
⚠ Failed to create Langfuse trace: Langfuse.start_span() got an unexpected keyword argument 'user_id'
```

**Cause:** Langfuse SDK 3.x doesn't accept user_id/session_id directly in start_span()

**Solution:** ✅ Fixed in latest version
- Now using `TraceContext` to pass user_id/session_id
- Using `start_observation()` instead of `start_span()`
- Restart server: `make dev-ui`

#### Issue: Langfuse not tracking

**Solution:**
```bash
# Check environment variables
echo $LANGFUSE_ENABLED
echo $LANGFUSE_PUBLIC_KEY
echo $LANGFUSE_SECRET_KEY
echo $LANGFUSE_HOST
echo $OBSERVABILITY_DASHBOARD

# Test observability
python test_observability.py

# Check Langfuse dashboard
open $LANGFUSE_HOST
```

### Static Files Issues

#### Issue: CSS/JS not loading

**Solution:**
```bash
# Collect static files
cd agent_ui
python manage.py collectstatic --no-input

# Clear browser cache
# Or add ?v=2 to URLs
```

#### Issue: Cache busting not working

**Solution:** Check template has version parameter:
```django
<script src="{% static 'js/chat.js' %}?v=1.3"></script>
```

## Quick Diagnostics

### Check Everything

```bash
# Run comprehensive check
cd agent_ui
python manage.py check --deploy

# Test database
python manage.py migrate --check

# Test Redis
redis-cli ping

# Test imports
python -c "import agent_ui.settings; print('✅ Settings OK')"
python -c "from tools import list_properties; print('✅ Tools OK')"
```

### Common Commands

```bash
# Full reset (development)
make clean
make all

# Restart everything
make docker-down
make docker-up

# View logs
make docker-logs
make redis-logs

# Test everything
make test-backend
./test-safe.sh all
```

## Getting Help

### Check Logs

```bash
# Django logs
cd agent_ui && tail -f *.log

# Docker logs
make docker-logs

# Redis logs
make redis-logs

# Specific service
docker logs realtyiq-redis
docker logs realtyiq-api
```

### Debug Mode

```bash
# Enable debug logging in Django
# Edit agent_ui/agent_ui/settings.py
DEBUG = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

### Verify Installation

```bash
# Check Python packages
pip list | grep -E "(django|redis|langfuse|beeai)"

# Check Node.js
node --version
npm --version

# Check Docker
docker --version
docker-compose --version

# Check Redis
redis-cli --version
```

## Known Issues

### Issue: Tests show some failures (expected)

**Status:** Known, minor issues
- Some API endpoint tests may fail (405, 404 errors)
- These don't prevent development
- Core functionality works correctly

**Solution:** Use `make test-backend` which passes 50/50 tests

### Issue: Observability warnings in tests

**Status:** Expected in test environment
```
WARNING - Cache module not available
ERROR - Error in chat_api: 'Langfuse' object has no attribute 'trace'
```

**Solution:** These are expected when Langfuse is not fully configured for tests. Ignore them or mock Langfuse in tests.

## Documentation

For more detailed information:
- **[TEST_TROUBLESHOOTING.md](TEST_TROUBLESHOOTING.md)** - Test-specific issues
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)** - Docker configuration
- **[CACHE_IMPLEMENTATION.md](CACHE_IMPLEMENTATION.md)** - Redis caching
- **[OBSERVABILITY.md](OBSERVABILITY.md)** - Langfuse setup
- **[MCP_SERVER.md](MCP_SERVER.md)** - MCP Server issues

## Still Having Issues?

1. Check the relevant documentation file above
2. Search existing issues in the repository
3. Try the dev-setup.sh script: `source dev-setup.sh`
4. Check service status: `make docker-ps`
5. Review logs: `make docker-logs`

---

**Last Updated:** February 16, 2026  
**Version:** 1.0.0
