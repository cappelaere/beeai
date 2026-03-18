# Property metrics for Prometheus (BI)

Property-related Prometheus metrics are exposed and scraped on the **RealtyIQ side only**. They are used for **business intelligence**: alerting and Grafana visualization so Real Estate Specialists (RS), SDA, and Management can discuss property auctions and marketing efficiency.

## Scope

- **RealtyIQ only:** RealtyIQ (agent_ui) exposes property metrics; Prometheus scrapes RealtyIQ. The Api service that manages the PostgreSQL property-metrics database is **not** monitored or scraped.
- **Scrape interval:** 5 minutes for the dedicated property-metrics job.
- **Active properties only:** Per-property gauges are fetched only for properties with at least one event in the last 7 days (from Api `properties-with-activity?days=7`).

## Where metrics are exposed

- **Application:** [agent_ui/agent_app/metrics_collector.py](../../../agent_ui/agent_app/metrics_collector.py) (extend with property gauges).
- **Data source:** RealtyIQ calls the Api’s **read APIs** (e.g. `GET /api/metrics/properties-with-activity?days=7`, `GET /api/metrics/properties/<id>/summary?days=7`) when generating `/metrics`. The Api is the data source via HTTP; Prometheus never scrapes the Api.

## Prometheus scrape config

Add a dedicated job in `prometheus/prometheus.yml`:

```yaml
  - job_name: 'realtyiq-property-metrics'
    scrape_interval: 5m
    scrape_timeout: 30s
    metrics_path: /metrics
    static_configs:
      - targets: ['agent_ui:8000']
        labels:
          service: 'realtyiq'
          usage: 'bi'
```

Replace `agent_ui:8000` with the actual RealtyIQ metrics URL if different.

## Recommended metrics

### Portfolio-level gauges

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `property_metrics_properties_with_activity_24h` | Gauge | none | Count of property_ids with activity in last 24h |
| `property_metrics_properties_with_activity_7d` | Gauge | none | Count of property_ids with activity in last 7d |
| `property_metrics_funnel_last_7d` | Gauge | `metric` | Portfolio 7d totals: views, brochure_downloads, ifb_downloads, bidder_registrations, subscriber_registrations, photo_clicks |

### Per-property gauges (active properties only)

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `property_metrics_num_viewers` | Gauge | `property_id` | Page views (e.g. last 7d) |
| `property_metrics_num_bidders` | Gauge | `property_id` | Bidder registrations |
| `property_metrics_num_subscribers` | Gauge | `property_id` | Subscriber registrations |
| `property_metrics_brochure_downloads` | Gauge | `property_id` | Optional |
| `property_metrics_ifb_downloads` | Gauge | `property_id` | Optional |
| `property_metrics_unique_sessions` | Gauge | `property_id` | Optional |

**Active properties:** Fetch property IDs from `properties-with-activity?days=7` only; then for each ID call `properties/<id>/summary?days=7` and set the per-property gauges.

## Implementation order

1. In `metrics_collector.py`, define gauges for portfolio-level and per-property metrics (with label `property_id`).
2. Add a function that, on each scrape (every 5m): (a) calls `properties-with-activity?days=1` and `?days=7` and sets portfolio gauges; (b) gets active property IDs from `properties-with-activity?days=7`; (c) for each ID calls `properties/<id>/summary?days=7` and sets per-property gauges.
3. Ensure the existing Prometheus endpoint includes these gauges.
4. Add the `realtyiq-property-metrics` scrape job in `prometheus/prometheus.yml` with `scrape_interval: 5m`.
5. Add Grafana dashboards and BI-oriented alerts. An importable dashboard is provided: [prometheus/grafana/dashboards/property-metrics-bi.json](../../../prometheus/grafana/dashboards/property-metrics-bi.json) (portfolio stats, funnel pie, per-property table).

## Grafana and alerting

- **Dashboards:** Portfolio funnel (7d totals and conversion rates); per-property viewers/bidders/subscribers (table or panels by `property_id`); underperformers (e.g. high viewers / low bidders).
- **Alerting:** BI-oriented only, e.g. drop in properties with activity, funnel conversion below threshold, or per-property (e.g. zero bidders when relevant).

## Seed data for testing

Two options let you inject data and test before or without the full RealtyIQ collector.

### 1. Api daily rollups (last 30 days, 10 properties)

**File:** `data/source/property_metric_daily_seed_30d_10properties.csv`

- **Content:** 30 days of daily rollups for property_id 1–10 (300 rows). Columns: `property_id`, `date`, `views`, `unique_sessions`, `brochure_downloads`, `ifb_downloads`, `bidder_registrations`, `subscriber_registrations`, `photo_clicks`.
- **Use:** Load into the Api database so summary endpoints return realistic totals. From the Api project directory:
  ```bash
  python manage.py load_metrics_daily_csv --file /path/to/beeai/data/source/property_metric_daily_seed_30d_10properties.csv
  ```
- **Effect:** Once the RealtyIQ property-metrics collector is implemented and calls the Api, Prometheus will scrape real aggregates from this data.

### 2. Grafana (CSV + Infinity)

Simulated property-metrics data in Grafana comes from the same CSV via the **Infinity** datasource. Use the **Property metrics (CSV)** dashboard for tables and stats. Setup (Infinity plugin, datasource, CSV URL) is described in [prometheus/grafana/dashboards/README.md](../../../prometheus/grafana/dashboards/README.md).

## Troubleshooting (live scraping)

If **"too old sample"** or **"out of bounds"** appears on scrape jobs, a target may be exposing a sample with **timestamp 0** (epoch), which Prometheus rejects. Check each target: `curl -s http://<target>/metrics` and look for lines ending with ` 0` (value and timestamp). Fix or filter that metric in the exporter. Ensure all scrape jobs have `honor_timestamps: false` so Prometheus uses scrape time. The project pins Prometheus to `prom/prometheus:v2.47.2`.

## See also

- [PROMETHEUS_METRICS.md](PROMETHEUS_METRICS.md) — General Prometheus metrics in RealtyIQ
- [ROADMAP](../../ROADMAP.md) — Section 21: Property metrics for Prometheus (BI)
- Plan file: `.cursor/plans/` (property_metrics_for_prometheus)
