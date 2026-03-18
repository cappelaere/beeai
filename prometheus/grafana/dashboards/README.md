# Grafana dashboards

- **RealtyIQ Overview** – health, up status, probes (Prometheus).
- **Infrastructure** – Redis, Prometheus, blackbox (Prometheus).
- **Property metrics (BI)** – BI-style metrics (Prometheus).
- **Property metrics (CSV)** – table and stats from the property seed CSV via the **Infinity** datasource.

## Property metrics (CSV) and Infinity

1. Install the **Infinity** datasource plugin (e.g. **Configuration** → **Plugins** → search “Infinity” → Install).
2. Add a data source of type **Infinity** and give it a name (e.g. “Infinity”). Set its **UID** if you want the variable to match (e.g. `infinity`).
3. On the **Property metrics (CSV)** dashboard:
   - Choose **Infinity datasource** in the dropdown (the one where you loaded or will load the CSV).
   - **CSV URL**: the dashboard default is `http://host.docker.internal:8765/data/source/property_metric_daily_seed_30d_10properties.csv`. To use it, serve the repo over HTTP from your host, e.g. from the repo root: `python3 -m http.server 8765`. If you already loaded the CSV in Infinity via another URL or inline data, you can change the **CSV URL** variable to that URL (or use the same URL in the datasource and here).
4. Panels: **Property metric daily seed (CSV)** table, **Total views**, **Total bidders**, **Rows** stats.

---

If dashboards show **no data**:

1. **Add the Prometheus datasource** (if not already):
   - **Configuration** (gear) → **Data sources** → **Add data source** → **Prometheus**
   - **URL:** `http://prometheus:9090`
   - **UID:** set to `prometheus` (so the dashboard variable matches)
   - **Save & test** — must show "Data source is working"

2. **Pick the datasource on each dashboard**
   - Open the dashboard, use the **Datasource** dropdown at the top and select your Prometheus source.

3. **Time range**
   - Set to **Last 15 minutes** or **Last 1 hour** (in case the default range has no scrapes yet).

4. **Check Prometheus has data**
   - Open http://localhost:9090 → **Graph** (or **Explore**)
   - Run query: `up`
   - You should see series for each scrape job (prometheus, redis, blackbox-http, etc.). If you see nothing, fix Prometheus/targets first.
