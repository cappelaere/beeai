# Prometheus Metrics Integration

This document describes the Prometheus metrics integration for RealtyIQ Agent.

## Overview

RealtyIQ Agent exposes application metrics in Prometheus format for monitoring, alerting, and observability. Metrics are automatically collected and updated, accessible via HTTP endpoints.

## Features

- **Auto-refreshing Web UI**: Real-time metrics dashboard at `/prometheus/` (refreshes every 10 seconds)
- **Prometheus Scrape Endpoint**: Text format metrics at `/metrics/` for Prometheus server scraping
- **Comprehensive Metrics**: HTTP requests, agent executions, database operations, cache, system resources
- **Automatic Tracking**: Middleware automatically tracks HTTP requests and response times
- **Search & Filter**: Web UI includes search functionality to filter metrics
- **Copy & Download**: Easy export of metrics data

## Endpoints

### Metrics Scrape Endpoint

```
GET /metrics/
```

Returns metrics in Prometheus text format:

```
# HELP realtyiq_http_requests_total Total HTTP requests
# TYPE realtyiq_http_requests_total counter
realtyiq_http_requests_total{endpoint="/",method="GET",status="200"} 42.0

# HELP realtyiq_system_cpu_usage_percent System CPU usage percentage
# TYPE realtyiq_system_cpu_usage_percent gauge
realtyiq_system_cpu_usage_percent 15.2
```

**Content-Type**: `text/plain; version=0.0.4; charset=utf-8`

### Metrics Web Interface

```
GET /prometheus/
```

Returns HTML page with:
- Auto-refresh every 10 seconds
- Real-time metrics display
- Search/filter functionality
- Metrics statistics (total, counters, gauges, histograms)
- Copy to clipboard button

## Available Metrics

### Application Metrics

#### HTTP Requests
```prometheus
# Total HTTP requests by method, endpoint, and status
realtyiq_http_requests_total{method="GET", endpoint="/", status="200"}

# HTTP request latency in seconds
realtyiq_http_request_duration_seconds{method="GET", endpoint="/"}
```

#### Agent Execution
```prometheus
# Total agent executions by type and status
realtyiq_agent_executions_total{agent_type="gres", status="success"}

# Agent execution duration in seconds
realtyiq_agent_execution_duration_seconds{agent_type="gres"}

# Total tokens used by agents
realtyiq_agent_tokens_used_total{agent_type="gres", model="claude-3-5-sonnet"}
```

#### Chat Sessions
```prometheus
# Number of active chat sessions (last 24 hours)
realtyiq_chat_sessions_active

# Total chat messages by role
realtyiq_chat_messages_total{role="user"}
realtyiq_chat_messages_total{role="assistant"}
```

#### Assistant Cards
```prometheus
# Total assistant cards
realtyiq_cards_total

# Total card executions by ID and status
realtyiq_card_executions_total{card_id="1", status="success"}
```

### Infrastructure Metrics

#### Database Operations
```prometheus
# Total database queries by operation type
realtyiq_database_queries_total{operation="select"}
realtyiq_database_queries_total{operation="insert"}

# Database query duration in seconds
realtyiq_database_query_duration_seconds{operation="select"}
```

#### Cache Operations
```prometheus
# Total cache operations by operation and status
realtyiq_cache_operations_total{operation="get", status="hit"}
realtyiq_cache_operations_total{operation="get", status="miss"}
realtyiq_cache_operations_total{operation="set", status="success"}

# Current cache size in bytes
realtyiq_cache_size_bytes
```

#### Document Library
```prometheus
# Total documents in library
realtyiq_documents_total

# Total document searches by status
realtyiq_document_searches_total{status="success"}
```

#### API Health
```prometheus
# Total API health checks by service and status
realtyiq_api_health_checks_total{service="bidhom_api", status="healthy"}
```

### System Resource Metrics

```prometheus
# System CPU usage percentage
realtyiq_system_cpu_usage_percent

# System memory usage in bytes
realtyiq_system_memory_usage_bytes

# System memory available in bytes
realtyiq_system_memory_available_bytes

# System disk usage percentage
realtyiq_system_disk_usage_percent
```

### Error Metrics

```prometheus
# Total errors by type and component
realtyiq_errors_total{error_type="api_error", component="agent_runner"}
```

### Property metrics (BI)

Property-related metrics for business intelligence (alerting and Grafana) are exposed on the **RealtyIQ side only**, scraped every **5 minutes**, and include **active properties only**. They are populated by RealtyIQ calling the Api’s read APIs (no monitoring of the Api).

- **Portfolio-level:** `property_metrics_properties_with_activity_24h`, `property_metrics_properties_with_activity_7d`, `property_metrics_funnel_last_7d{metric="..."}`.
- **Per-property (active only):** `property_metrics_num_viewers`, `property_metrics_num_bidders`, `property_metrics_num_subscribers` (and optional brochure/ifb/unique_sessions) with label `property_id`.

For the full plan, scrape config, and implementation order, see **[PROPERTY_METRICS_PROMETHEUS.md](PROPERTY_METRICS_PROMETHEUS.md)**.

## Metric Types

### Counter
Cumulative metrics that only increase (or reset to zero on restart).

**Examples**: 
- `realtyiq_http_requests_total`
- `realtyiq_agent_executions_total`
- `realtyiq_errors_total`

### Gauge
Metrics that can go up or down.

**Examples**:
- `realtyiq_chat_sessions_active`
- `realtyiq_system_cpu_usage_percent`
- `realtyiq_cache_size_bytes`

### Histogram
Samples observations and counts them in configurable buckets.

**Examples**:
- `realtyiq_http_request_duration_seconds`
- `realtyiq_agent_execution_duration_seconds`
- `realtyiq_database_query_duration_seconds`

### Info
Static information about the application.

**Examples**:
- `realtyiq_app_info{version="1.0.0", application="RealtyIQ Agent"}`

## Usage

### In Python Code

```python
from agent_app.metrics_collector import (
    agent_executions_total,
    agent_execution_duration_seconds,
    agent_tokens_used,
    errors_total
)
import time

# Track agent execution
start_time = time.time()
try:
    # Execute agent
    result = agent.run(prompt)
    
    # Track success
    agent_executions_total.labels(
        agent_type="gres",
        status="success"
    ).inc()
    
    # Track tokens
    agent_tokens_used.labels(
        agent_type="gres",
        model="claude-3-5-sonnet"
    ).inc(result.tokens_used)
    
except Exception as e:
    # Track error
    agent_executions_total.labels(
        agent_type="gres",
        status="error"
    ).inc()
    
    errors_total.labels(
        error_type=type(e).__name__,
        component="agent_runner"
    ).inc()

finally:
    # Track duration
    duration = time.time() - start_time
    agent_execution_duration_seconds.labels(
        agent_type="gres"
    ).observe(duration)
```

### Automatic HTTP Tracking

HTTP requests are automatically tracked by `PrometheusMiddleware`:

```python
# In settings.py
MIDDLEWARE = [
    # ... other middleware ...
    "agent_app.middleware.prometheus_middleware.PrometheusMiddleware",
]
```

No code changes needed - all HTTP requests are automatically tracked!

## Prometheus Server Configuration

### Scrape Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'realtyiq_agent'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets: ['localhost:8002']
    metrics_path: '/metrics/'
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    depends_on:
      - agent_ui

  agent_ui:
    # Your RealtyIQ Agent service
    ports:
      - "8002:8002"

volumes:
  prometheus_data:
```

## Querying Metrics

### PromQL Examples

```promql
# Request rate (requests per second)
rate(realtyiq_http_requests_total[5m])

# Average request duration
rate(realtyiq_http_request_duration_seconds_sum[5m]) / 
rate(realtyiq_http_request_duration_seconds_count[5m])

# Error rate
rate(realtyiq_errors_total[5m])

# Agent execution success rate
sum(rate(realtyiq_agent_executions_total{status="success"}[5m])) /
sum(rate(realtyiq_agent_executions_total[5m]))

# CPU usage over time
realtyiq_system_cpu_usage_percent

# Cache hit rate
rate(realtyiq_cache_operations_total{operation="get",status="hit"}[5m]) /
rate(realtyiq_cache_operations_total{operation="get"}[5m])
```

## Grafana Dashboard

### Sample Dashboard Panels

**HTTP Traffic**:
```promql
sum(rate(realtyiq_http_requests_total[5m])) by (endpoint)
```

**Agent Performance**:
```promql
histogram_quantile(0.95, 
  rate(realtyiq_agent_execution_duration_seconds_bucket[5m])
)
```

**System Resources**:
```promql
realtyiq_system_cpu_usage_percent
realtyiq_system_memory_usage_bytes / realtyiq_system_memory_available_bytes * 100
```

**Error Rate**:
```promql
sum(rate(realtyiq_errors_total[5m])) by (error_type)
```

## Web UI Features

### Auto-Refresh
- Automatically refreshes every 10 seconds
- Toggle on/off with button
- Manual refresh button available

### Search & Filter
- Type keyword to filter metrics
- Searches metric names and labels
- Real-time filtering

### Statistics
- Total metrics count
- Counters, gauges, histograms breakdown
- Last updated timestamp

### Export
- Copy to clipboard button
- Direct link to `/metrics/` endpoint
- Formatted display with syntax highlighting

## Architecture

### Components

1. **Metrics Collector** (`agent_app/metrics_collector.py`)
   - Defines all metrics
   - Collects system, database, and cache metrics
   - Uses `prometheus_client` library

2. **Prometheus Middleware** (`agent_app/middleware/prometheus_middleware.py`)
   - Automatically tracks HTTP requests
   - Measures request duration
   - Labels by method, endpoint, status

3. **Views** (`agent_app/views.py`)
   - `prometheus_metrics()` - Returns Prometheus text format
   - `prometheus_view()` - Renders web UI

4. **Templates** (`templates/prometheus.html`)
   - Auto-refreshing web interface
   - Search and filter functionality
   - Syntax highlighting

### Data Flow

```
HTTP Request
    ↓
PrometheusMiddleware (tracks request)
    ↓
View Handler (processes request)
    ↓
Metrics Collector (updates metrics)
    ↓
Prometheus Registry (stores metrics)
    ↓
/metrics/ endpoint (exposes for scraping)
    ↓
Prometheus Server (scrapes periodically)
```

## Best Practices

### 1. Use Appropriate Metric Types

```python
# Counter for cumulative counts
http_requests_total.labels(method="GET").inc()

# Gauge for current values
active_sessions.set(42)

# Histogram for distributions
request_duration.observe(0.234)
```

### 2. Label Carefully

```python
# Good: Bounded cardinality
agent_executions_total.labels(
    agent_type="gres",  # 5 possible values
    status="success"    # 2-3 possible values
).inc()

# Bad: Unbounded cardinality
# DON'T DO THIS - creates too many time series
request_total.labels(
    user_id=user_id,  # Could be millions
    request_id=req_id  # Unique per request
).inc()
```

### 3. Add Context

```python
# Include relevant labels for filtering
cache_operations_total.labels(
    operation="get",
    status="hit"
).inc()
```

### 4. Monitor Performance

```python
# Always measure durations
with request_duration.labels(endpoint="/api/chat/").time():
    response = process_request()
```

## Troubleshooting

### Metrics Not Appearing

1. **Check middleware is enabled**:
   ```python
   # In settings.py
   MIDDLEWARE = [
       # ...
       "agent_app.middleware.prometheus_middleware.PrometheusMiddleware",
   ]
   ```

2. **Verify prometheus_client is installed**:
   ```bash
   pip install prometheus-client
   ```

3. **Check logs for errors**:
   ```bash
   /logs current 100
   ```

### High Cardinality

If you see too many time series:

1. Review label values (should be bounded)
2. Remove labels with unique values
3. Use aggregation in PromQL queries

### Scraping Errors

If Prometheus can't scrape:

1. Verify endpoint is accessible: `curl http://localhost:8002/metrics/`
2. Check firewall rules
3. Verify `metrics_path` in `prometheus.yml`

## Related Documentation

- **[OBSERVABILITY.md](OBSERVABILITY.md)** - Langfuse observability integration
- **[LOGGING.md](LOGGING.md)** - Application logging system
- **[HEALTH_CHECKS.md](HEALTH_CHECKS.md)** - Service health monitoring

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [prometheus_client Python Library](https://github.com/prometheus/client_python)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Documentation](https://grafana.com/docs/)
