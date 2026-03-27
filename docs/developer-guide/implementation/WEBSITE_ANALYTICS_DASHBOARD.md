# Website Analytics Dashboard (Issue #14)

This adds an internal dashboard for first-party website analytics captured by Issue #12.

## Route and Access

- Page route: `/analytics/dashboard/`
- URL name: `analytics_dashboard`
- Access: internal staff users only
  - requires Django authentication
  - requires `user.is_staff == True`

Unauthenticated requests receive HTTP `403`.

## Dashboard Filters

- `range`: one of `24h`, `7d`, `30d`, `90d` (default `30d`)
- `page`: optional canonical path (example: `/chat`)

## Data Source Precedence

The dashboard query layer is in:

- `agent_ui/agent_app/analytics/dashboard_queries.py`

Query behavior:

1. Prefer Timescale rollup views for trend/summary/top-pages when available:
   - `analytics_pageviews_hourly`
   - `analytics_pageviews_daily`
   - `analytics_pageviews_weekly`
   - `analytics_pageviews_monthly`
2. If rollups are unavailable or fail, fallback to raw events:
   - `agent_app_pageviewevent` / `PageViewEvent` ORM queries

The page indicates source mode (`rollup_*`, `raw_events`, or `raw_events_fallback`).

## UI Components

- Summary cards
  - page views
  - unique visitors
  - unique users
- Trend charts (standalone canvas JS, no external CDN dependency):
  - hourly
  - daily
  - weekly
  - monthly
  - `agent_ui/static/js/analytics/dashboard_trends.js`
- Top pages table
- Date/page filter form

## Prerequisites

Issue #12 analytics foundation must be present:

- `TrackedPage`, `TrackedPageQueryParam`, `PageViewEvent`
- related migrations

For rollup-backed mode on PostgreSQL, Timescale rollup setup should exist (with non-blocking behavior when extension is unavailable).

## Tests

Run targeted analytics dashboard tests:

```bash
cd agent_ui
../venv/bin/python manage.py test agent_app.tests.test_analytics_dashboard
```

Run full analytics tests:

```bash
cd agent_ui
../venv/bin/python manage.py test agent_app.tests.test_analytics_models agent_app.tests.test_analytics_middleware agent_app.tests.test_analytics_query_filter agent_app.tests.test_analytics_location agent_app.tests.test_analytics_views agent_app.tests.test_analytics_command agent_app.tests.test_analytics_timescale agent_app.tests.test_analytics_js_wiring agent_app.tests.test_analytics_dashboard
```

