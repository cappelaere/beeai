# Service Health Checks

RealtyIQ includes comprehensive health monitoring for all external services. Health status is displayed on the dashboard and available via the `/metrics` command.

## Overview

The health check system monitors four critical services:
1. **BidHom API** - Main application backend (Django REST)
2. **Piper TTS** - Text-to-speech service (Section 508 mode)
3. **Redis Cache** - Response caching layer
4. **PostgreSQL** - Primary database

## Implementation

### Health Check Module

Location: `agent_ui/agent_app/health_checks.py`

The module provides:
- Individual service health check functions
- Aggregate health status for all services
- Response time measurement
- Version and configuration reporting

### Service Status Values

Each service reports one of four status values:

| Status | Meaning | Display |
|--------|---------|---------|
| `healthy` | Service operational | ✓ Green |
| `unhealthy` | Service down or error | ✗ Red |
| `disabled` | Service not enabled | ○ Gray |
| `unknown` | Cannot determine status | ? Gray |

### Overall System Status

The system calculates an overall health status:

| Status | Condition |
|--------|-----------|
| `healthy` | All active services are healthy |
| `degraded` | Some services unhealthy (< 50%) |
| `unhealthy` | Majority of services unhealthy (≥ 50%) |

## Health Check Details

### 1. BidHom API

**Endpoint:** `{API_URL}/healthz`

**Checks:**
- HTTP response code (200 = healthy)
- Response time
- API version (if available)

**Configuration:**
```bash
API_URL=http://127.0.0.1:8000  # Default
```

**Timeout:** 5 seconds

### 2. Piper TTS Service

**Endpoint:** `{PIPER_BASE_URL}/healthz`

**Checks:**
- HTTP response code (200 = healthy)
- Response time
- Service version
- TTS engine type

**Configuration:**
```bash
PIPER_BASE_URL=http://localhost:8088  # Default
```

**Timeout:** 5 seconds

**Common Errors:**
- `Connection refused` - Service not running (run `make piper-start`)
- `Timeout` - Service overloaded or network issue

### 3. Redis Cache

**Checks:**
- Connection status
- Redis version
- Memory usage
- Cached item count
- Cache hit rate

**Configuration:**
```bash
REDIS_ENABLED=true  # Enable/disable Redis
REDIS_URL=redis://localhost:6379/0  # Connection string
```

**Status Logic:**
- If `REDIS_ENABLED=false` → status is `disabled`
- If cannot connect → status is `unhealthy`
- If connected → status is `healthy`

**Common Errors:**
- `REDIS_ENABLED=false in .env` - Cache is disabled
- `Connection refused` - Redis server not running
- `Not connected` - Connection string incorrect

### 4. PostgreSQL Database

**Checks:**
- Database connection
- Query execution (`SELECT version();`)
- Response time
- Database version

**Configuration:**
Set via Django settings (`DATABASES` in `settings.py`)

**Common Errors:**
- `Connection error` - Database server not running
- `OperationalError` - Credentials or connection string invalid

## Dashboard Display

The dashboard shows service health at the top with:
- Overall system status badge
- Individual service cards with:
  - Service name and icon
  - Connection URL/endpoint
  - Status indicator (✓/✗/○/?)
  - Response time (if healthy)
  - Version and metadata (if healthy)
  - Error message (if unhealthy)

### Visual Design

**Service Card Layout:**
```
┌─────────────────────────────────────┐
│ 🔵 Service Name              [✓]    │
│    http://localhost:8088            │
│    ─────────────────────────────    │
│    15ms  v1.0.0  piper              │
└─────────────────────────────────────┘
```

**Status Colors:**
- Green (✓) = Healthy
- Red (✗) = Unhealthy
- Gray (○) = Disabled
- Gray (?) = Unknown

## Using Health Checks

### In Dashboard

Navigate to `/dashboard/` to see real-time service health:

```
Service Health [All Systems Operational]

┌─ BidHom API ✓ ─┐  ┌─ Piper TTS ✓ ─┐
│ http://localhost:8000 │  │ http://...:8088 │
│ 10ms  v1.0.0         │  │ 15ms  piper     │
└──────────────────────┘  └─────────────────┘

┌─ Redis Cache ✓ ────┐  ┌─ PostgreSQL ✓ ──┐
│ redis://...:6379/0  │  │ beeai_db         │
│ 5ms  42 items  85%  │  │ 2ms  PostgreSQL  │
└─────────────────────┘  └──────────────────┘
```

### Via `/metrics` Command

Run `/metrics` in any chat session:

```
User: /metrics

Response:
📊 Dashboard Metrics

═══ Service Health ═══
Overall Status: ✓ All Systems Operational
BidHom API: ✓ 10ms
Piper TTS: ✓ 15ms
Redis Cache: ✓ 5ms
PostgreSQL: ✓ 2ms

... (rest of metrics)
```

## API Integration

### Direct Usage in Python

```python
from agent_app.health_checks import check_all_services, get_overall_status

# Check all services
services = check_all_services()

# Get overall status
status = get_overall_status(services)

# Access individual service status
api_health = services['api']
if api_health['status'] == 'healthy':
    print(f"API response time: {api_health['response_time_ms']}ms")
else:
    print(f"API error: {api_health['error']}")
```

### Response Format

Each service returns a dict with:

```python
{
    "status": "healthy" | "unhealthy" | "disabled" | "unknown",
    "url": "http://...",  # Connection URL (if applicable)
    "response_time_ms": 15,  # Response time in milliseconds (if healthy)
    "version": "1.0.0",  # Service version (if available)
    "error": "Error message"  # Error details (if unhealthy)
    # Additional service-specific fields...
}
```

## Troubleshooting

### Service Won't Start

**Piper TTS:**
```bash
# Check if running
docker ps | grep piper

# Start service
make piper-start

# View logs
make piper-logs

# Rebuild if needed
make piper-build
```

**Redis:**
```bash
# Check if running
docker ps | grep redis

# Start service
docker compose up -d redis

# Test connection
redis-cli ping
```

**PostgreSQL:**
```bash
# Check if running
docker ps | grep postgres

# Start service
docker compose up -d db

# Test connection
psql -h localhost -U postgres -d beeai
```

### Health Check Showing "Unknown"

If a service shows `unknown` status:
1. Check Docker containers are running: `docker ps`
2. Verify environment variables in `.env`
3. Check network connectivity
4. Review service logs for errors

### Response Time High

If response times are consistently high (>500ms):
1. Check CPU/memory usage on host
2. Review Docker resource limits
3. Check network latency
4. Consider service restart

## Best Practices

### For Development

1. Check health status before starting work
2. Run `/metrics` after service restarts
3. Monitor health after deployments
4. Use health checks in CI/CD pipelines

### For Production

1. Set up external monitoring (e.g., Datadog, New Relic)
2. Configure alerts for service degradation
3. Log health check failures
4. Monitor response time trends
5. Implement automatic service restart on failure

### For Debugging

1. Check `/metrics` first for quick status
2. Review individual service logs if unhealthy
3. Test service endpoints manually (curl/requests)
4. Verify environment variables and configuration
5. Check Docker container health

## Security Considerations

- Health endpoints expose minimal information
- No sensitive data in health responses
- Version numbers are safe to expose
- Error messages are sanitized
- No authentication required (internal only)

## Related Documentation

- [Dashboard](../agent_ui/templates/dashboard.html) - UI implementation
- [Commands](COMMANDS.md) - `/metrics` command reference
- [Section 508](SECTION_508.md) - Accessibility features
- [Docker Setup](DOCKER_SETUP.md) - Service deployment

---

**Last Updated:** February 17, 2026  
**Version:** 1.0.0