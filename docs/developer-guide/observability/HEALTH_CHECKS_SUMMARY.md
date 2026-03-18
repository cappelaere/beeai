# Health Checks Summary

## Overview

RealtyIQ now includes comprehensive health monitoring for all critical services. Health status is displayed on the dashboard and available via the `/metrics` command.

## What Was Implemented

### 1. Health Check System

**Module:** `agent_ui/agent_app/health_checks.py`

Four service health checks were implemented:

| Service | Endpoint | Key Metrics |
|---------|----------|-------------|
| BidHom API | `/healthz` | Response time, version |
| Piper TTS | `/healthz` | Response time, version, engine |
| Redis Cache | Connection check | Memory usage, hit rate, cached items |
| PostgreSQL | Database query | Response time, version |

### 2. Dashboard Display

**Location:** `agent_ui/templates/dashboard.html`

Added a "Service Health" card at the top of the dashboard showing:
- Overall system status badge (Healthy/Degraded/Unhealthy)
- Grid of 4 service cards with:
  - Service name and icon
  - Connection URL
  - Status indicator (✓/✗/○/?)
  - Response time and metrics (if healthy)
  - Error message (if unhealthy)

**Visual Design:**
- Color-coded status badges (green/red/gray)
- Responsive grid layout (adapts to screen size)
- Dark theme support
- Accessible ARIA labels

### 3. `/metrics` Command Enhancement

**Location:** `agent_ui/agent_app/commands/metrics.py`

Updated the `/metrics` command to include:
```
═══ Service Health ═══
Overall Status: ✓ All Systems Operational
BidHom API: ✓ 10ms
Piper TTS: ✓ 15ms
Redis Cache: ✓ 5ms
PostgreSQL: ✓ 2ms
```

Status indicators:
- `✓` = Healthy (service operational)
- `✗` = Unhealthy (service down or error)
- `○` = Disabled (service not enabled)
- `?` = Unknown (status cannot be determined)

### 4. Comprehensive Tests

**Location:** `agent_ui/agent_app/tests/test_health_checks.py`

Added 14 unit tests covering:
- Individual service health checks (healthy/unhealthy paths)
- Redis disabled state
- Overall status calculation
- Dashboard integration
- `/metrics` command integration

**Test Results:** All 14 tests passing ✅

## Files Modified/Created

### New Files:
1. `agent_ui/agent_app/health_checks.py` - Health check module (243 lines)
2. `agent_ui/agent_app/tests/test_health_checks.py` - Test suite (260 lines)
3. `docs/HEALTH_CHECKS.md` - Full documentation
4. `docs/HEALTH_CHECKS_SUMMARY.md` - This summary

### Modified Files:
1. `agent_ui/agent_app/views.py` - Import health checks in dashboard_view
2. `agent_ui/templates/dashboard.html` - Add service health display section
3. `agent_ui/agent_app/commands/metrics.py` - Include service health in output
4. `docs/COMMANDS.md` - Update `/metrics` documentation
5. `README.md` - Add HEALTH_CHECKS.md link

## Usage

### View in Dashboard

1. Navigate to http://localhost:8002/dashboard/
2. Service health status appears at the top
3. Click any service card to see details

### View via Command

In any chat session:
```
/metrics
```

Output includes service health at the top.

## Configuration

No additional configuration required. Uses existing environment variables:

```bash
# API endpoint (default: http://127.0.0.1:8000)
API_URL=http://127.0.0.1:8000

# Piper TTS endpoint (default: http://localhost:8088)
PIPER_BASE_URL=http://localhost:8088

# Redis configuration
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0

# PostgreSQL (configured in Django settings)
```

## Health Check Logic

### Individual Service Status

Each service returns one of:
- `healthy` - Service responding correctly
- `unhealthy` - Connection failed or error response
- `disabled` - Service intentionally disabled (e.g., `REDIS_ENABLED=false`)
- `unknown` - Cannot determine status

### Overall System Status

Calculated based on active services (excluding disabled):

| Condition | Overall Status |
|-----------|----------------|
| All active services healthy | `healthy` |
| <50% of active services unhealthy | `degraded` |
| ≥50% of active services unhealthy | `unhealthy` |

## Performance

- Each health check has a 5-second timeout
- Health checks run in parallel (non-blocking)
- Dashboard refresh includes fresh health data
- Minimal overhead (~50-100ms total for all checks)

## Error Handling

Common error messages and resolutions:

| Error | Service | Resolution |
|-------|---------|------------|
| Connection refused | Piper TTS | Run `make piper-start` |
| Connection refused | Redis | Run `make redis` or `docker compose up redis` |
| REDIS_ENABLED=false | Redis | Set `REDIS_ENABLED=true` in `.env` |
| Timeout (>5s) | Any | Check network/firewall, restart service |
| Not connected | Redis | Verify `REDIS_URL` in `.env` |

## Future Enhancements

Potential improvements (not currently planned):
- Health check caching (refresh every N seconds)
- Historical health metrics (uptime percentage)
- Email/Slack alerts on service degradation
- Custom health check intervals per service
- Health check API endpoint (`/api/health/`)
- Prometheus metrics export

## Testing

Run health check tests:

```bash
cd agent_ui
../venv/bin/python manage.py test agent_app.tests.test_health_checks -v 2
```

Expected output:
```
Ran 14 tests in 0.068s
OK
```

## Documentation

Full documentation available at:
- **[docs/HEALTH_CHECKS.md](HEALTH_CHECKS.md)** - Complete implementation guide
- **[docs/COMMANDS.md](COMMANDS.md)** - `/metrics` command reference

## Benefits

1. **Proactive Monitoring** - Catch service issues before they affect users
2. **Quick Diagnostics** - Identify which service is down at a glance
3. **Accessibility** - Health status available via keyboard (`/metrics` command)
4. **Operational Visibility** - Clear status for all dependencies
5. **Troubleshooting** - Response times help identify performance issues

## Completion Status

✅ **COMPLETE** - All features implemented and tested

- [x] Health check module created
- [x] Dashboard display implemented
- [x] `/metrics` command enhanced
- [x] 14 tests written and passing
- [x] Documentation complete
- [x] Dark theme support
- [x] Accessibility features
- [x] Error handling

---

**Implementation Date:** February 17, 2026  
**Version:** 1.0.0  
**Status:** Production Ready
