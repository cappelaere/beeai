# Prometheus Monitoring Setup

This directory contains the configuration for monitoring your RealtyIQ application with Prometheus and Grafana.

## Two Monitoring Approaches

### Approach 1: Black-box Monitoring (NO CODE CHANGES)
Monitor your application from the outside - endpoint availability, response times, and status codes.

**Pros**: No code changes, works immediately  
**Cons**: Limited visibility into application internals

### Approach 2: White-box Monitoring (Requires django-prometheus)
Deep application metrics - request rates, database queries, cache hits, custom business metrics.

**Pros**: Detailed insights into application behavior  
**Cons**: Requires installing django-prometheus package

## Quick Start (Black-box Monitoring - Recommended)

### 1. Create Volumes

```bash
docker volume create realtyiq-prometheus-data
docker volume create realtyiq-grafana-data
```

### 2. Start Services

```bash
docker compose up -d blackbox-exporter prometheus grafana
```

### 3. Access Dashboards

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

That's it! Prometheus is now monitoring:
- API endpoint availability (`/healthz`)
- Piper TTS health (`/healthz`)
- Response times and status codes

## Optional: Add Detailed App Metrics

If you want deeper application insights, follow these steps:

### 1. Install Django Prometheus

```bash
pip install django-prometheus
```

Update `requirements.txt`:
```
django-prometheus>=2.3.1
```

### 2. Configure Django

Add to `settings.py`:

```python
INSTALLED_APPS = [
    'django_prometheus',
    # ... other apps
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ... other middleware
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
```

Add to `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    path('', include('django_prometheus.urls')),
    # ... other urls
]
```

### 3. Uncomment in prometheus.yml

Uncomment the `realtyiq-api-detailed` job in `prometheus/prometheus.yml`

### 4. Restart Services

```bash
docker compose restart prometheus
```

## What You'll Monitor (Without Code Changes)

### Black-box Metrics (Available Immediately)
- **Endpoint availability** - Is the service up?
- **Response time** - How fast does it respond?
- **HTTP status codes** - Success vs error rates
- **Service uptime** - How long has it been running?

### Additional Metrics (With django-prometheus)
- HTTP request counts, durations, sizes
- Database query counts and durations
- Cache hit/miss rates
- Model operation counts
- Migration status
- Custom business metrics

## Setting Up Grafana

1. Open http://localhost:3000 (admin/admin)
2. Add Prometheus data source:
   - Configuration → Data Sources → Add data source → Prometheus
   - URL: `http://prometheus:9090`
   - Save & Test
3. Import dashboard:
   - For blackbox monitoring: Dashboard ID 7587 (Prometheus Blackbox Exporter)
   - For Django metrics (if installed): Dashboard ID 9528

## Custom Metrics Example

```python
from prometheus_client import Counter, Histogram

# Define custom metrics
property_searches = Counter(
    'realtyiq_property_searches_total',
    'Total property searches',
    ['search_type']
)

api_response_time = Histogram(
    'realtyiq_api_response_seconds',
    'API response time in seconds',
    ['endpoint']
)

# Use in your code
property_searches.labels(search_type='auction').inc()
with api_response_time.labels(endpoint='/api/properties').time():
    # Your API logic here
    pass
```

## Adding More Exporters

### Redis Exporter

Add to `docker-compose.yml`:

```yaml
redis-exporter:
  image: oliver006/redis_exporter:latest
  ports:
    - "9121:9121"
  environment:
    - REDIS_ADDR=redis:6379
  networks:
    - realtyiq-network
```

### PostgreSQL Exporter

Add to `docker-compose.yml`:

```yaml
postgres-exporter:
  image: prometheuscommunity/postgres-exporter:latest
  ports:
    - "9187:9187"
  environment:
    - DATA_SOURCE_NAME=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}?sslmode=disable
  networks:
    - realtyiq-network
```

Then uncomment the corresponding sections in `prometheus/prometheus.yml`.

## Troubleshooting

**Metrics endpoint not found?**
- Ensure `django-prometheus` is installed and configured
- Check that the `/metrics` endpoint is accessible: `curl http://localhost:8000/metrics`

**Prometheus can't scrape targets?**
- Verify all services are on the same network
- Check service names match in prometheus.yml
- View targets status in Prometheus UI: http://localhost:9090/targets

**Grafana can't connect to Prometheus?**
- Use the Docker network URL: `http://prometheus:9090`
- Don't use `localhost` from within Grafana container
