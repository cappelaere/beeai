# Prometheus Metrics - Quick Start Guide

Get started with Prometheus metrics monitoring in RealtyIQ Agent in 5 minutes.

## 1. View Metrics in Web UI

Navigate to the auto-refreshing metrics dashboard:

```
http://localhost:8002/prometheus/
```

Features:
- ✅ Auto-refreshes every 10 seconds
- ✅ Search and filter metrics
- ✅ Copy to clipboard
- ✅ Syntax highlighting

## 2. Access Raw Metrics

View Prometheus text format (for scraping):

```
http://localhost:8002/metrics/
```

Or via curl:

```bash
curl http://localhost:8002/metrics/
```

## 3. Start Prometheus Server (Optional)

### Using Docker

```bash
# Start Prometheus with provided config
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### Using Docker Compose

Add to your `docker-compose.yml`:

```yaml
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

volumes:
  prometheus_data:
```

Then start:

```bash
docker-compose up -d prometheus
```

### Access Prometheus UI

```
http://localhost:9090
```

## 4. Sample Queries

Try these PromQL queries in Prometheus UI:

### Request Rate
```promql
rate(realtyiq_http_requests_total[5m])
```

### Average Response Time
```promql
rate(realtyiq_http_request_duration_seconds_sum[5m]) / 
rate(realtyiq_http_request_duration_seconds_count[5m])
```

### CPU Usage
```promql
realtyiq_system_cpu_usage_percent
```

### Active Sessions
```promql
realtyiq_chat_sessions_active
```

### Error Rate
```promql
rate(realtyiq_errors_total[5m])
```

## 5. Set Up Grafana Dashboard (Optional)

### Start Grafana

```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

### Configure

1. Access Grafana: `http://localhost:3000` (admin/admin)
2. Add Prometheus data source: `http://prometheus:9090`
3. Import dashboard or create panels with queries above

## Key Metrics

### Application Health
- `realtyiq_http_requests_total` - Total requests
- `realtyiq_errors_total` - Error counts
- `realtyiq_agent_executions_total` - Agent runs

### Performance
- `realtyiq_http_request_duration_seconds` - Response times
- `realtyiq_agent_execution_duration_seconds` - Agent duration
- `realtyiq_database_query_duration_seconds` - DB latency

### Resources
- `realtyiq_system_cpu_usage_percent` - CPU usage
- `realtyiq_system_memory_usage_bytes` - Memory usage
- `realtyiq_cache_size_bytes` - Cache size

### Business Metrics
- `realtyiq_chat_sessions_active` - Active users
- `realtyiq_documents_total` - Document library size
- `realtyiq_cards_total` - Assistant cards

## Alerting Example

Create `alerts.yml`:

```yaml
groups:
  - name: realtyiq_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(realtyiq_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
      
      - alert: HighCPUUsage
        expr: realtyiq_system_cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"
      
      - alert: LowMemory
        expr: (realtyiq_system_memory_available_bytes / realtyiq_system_memory_usage_bytes) < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low memory available"
          description: "Only {{ $value }}% memory available"
```

## Next Steps

- 📖 Read [PROMETHEUS_METRICS.md](PROMETHEUS_METRICS.md) for comprehensive documentation
- 📊 Set up Grafana dashboards for visualization
- 🚨 Configure Prometheus alerting rules
- 🔗 Integrate with alerting services (PagerDuty, Slack, etc.)

## Troubleshooting

### Metrics not showing?

1. Check endpoint is accessible:
   ```bash
   curl http://localhost:8002/metrics/
   ```

2. Verify middleware is enabled in `settings.py`:
   ```python
   MIDDLEWARE = [
       # ...
       "agent_app.middleware.prometheus_middleware.PrometheusMiddleware",
   ]
   ```

3. Check logs:
   ```
   /logs current 100
   ```

### Prometheus can't scrape?

1. Verify `prometheus.yml` targets point to correct host:port
2. Check firewall rules
3. Ensure RealtyIQ Agent is running

### Need help?

See [PROMETHEUS_METRICS.md](PROMETHEUS_METRICS.md) for detailed troubleshooting.
