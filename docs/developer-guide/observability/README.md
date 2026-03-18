# Observability & Monitoring Documentation

Documentation for observability, tracing, metrics, and monitoring systems.

---

## Core Observability

### Langfuse Integration
- **[OBSERVABILITY.md](OBSERVABILITY.md)** - Main Langfuse integration guide
- **[OBSERVABILITY_SETUP.md](OBSERVABILITY_SETUP.md)** - Setup instructions
- **[OBSERVABILITY_QUICKSTART.md](OBSERVABILITY_QUICKSTART.md)** - Quick start guide
- **[OBSERVABILITY_FIX.md](OBSERVABILITY_FIX.md)** - Trace context fixes

### Tool Tracking
- **[TOOL_TRACKING_COMPLETE.md](TOOL_TRACKING_COMPLETE.md)** - Complete tool tracking implementation
- **[LANGFUSE_TOOL_TRACKING.md](LANGFUSE_TOOL_TRACKING.md)** - Tool call tracking in Langfuse
- **[DEBUG_TOOL_TRACKING.md](DEBUG_TOOL_TRACKING.md)** - Troubleshooting tool tracking
- **[NESTED_TRACES_FIX.md](NESTED_TRACES_FIX.md)** - Proper trace nesting

---

## Metrics & Monitoring

### Prometheus
- **[PROMETHEUS_METRICS.md](PROMETHEUS_METRICS.md)** - Prometheus integration and metrics
- **[PROMETHEUS_QUICKSTART.md](PROMETHEUS_QUICKSTART.md)** - 5-minute quick start
- **[PROMETHEUS_IMPLEMENTATION.md](PROMETHEUS_IMPLEMENTATION.md)** - Implementation details
- **[PROPERTY_METRICS_PROMETHEUS.md](PROPERTY_METRICS_PROMETHEUS.md)** - Property metrics for Prometheus (BI): RealtyIQ-only, 5m scrape, active properties, portfolio and per-property gauges
- **Grafana dashboards** - `prometheus/grafana/dashboards/`: **RealtyIQ Overview** (service health, probes, samples), **Infrastructure** (Redis, Prometheus, blackbox), **Property metrics (BI)**, **Property metrics (CSV)** via Infinity. Auto-loaded when Grafana starts with the repo’s docker-compose volumes.
- **[NAVBAR_OBSERVABILITY.md](NAVBAR_OBSERVABILITY.md)** - Navbar integration

### Health Checks
- **[HEALTH_CHECKS.md](HEALTH_CHECKS.md)** - Service health monitoring
- **[HEALTH_CHECKS_SUMMARY.md](HEALTH_CHECKS_SUMMARY.md)** - Health check summary

### Logging
- **[LOGGING.md](LOGGING.md)** - Logging system documentation
- **[LOGGING_IMPLEMENTATION.md](LOGGING_IMPLEMENTATION.md)** - Implementation details

---

## Key Features

- **Langfuse Tracing** - Complete execution traces
- **Prometheus Metrics** - Real-time performance metrics
- **Health Checks** - Service status monitoring
- **Tool Tracking** - Track all tool calls and results
- **Cost Tracking** - LLM usage and costs
- **Logging** - Timestamped log files

---

**Back to**: [Documentation Index](../README.md)
