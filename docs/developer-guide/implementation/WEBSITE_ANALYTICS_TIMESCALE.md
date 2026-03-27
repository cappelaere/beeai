# Website Analytics (Issue #12)

This implementation adds first-party page analytics for RealtyIQ with a TimescaleDB-first design.

## What Is Stored

- `canonical_path` for tracked pages only.
- Selected query params in `query_params_filtered` (JSON), based on per-path allowlist.
- Visitor/session/user attribution:
  - `visitor_id` (derived from session hash)
  - `session_key_hash`
  - `app_user_id` (session user id)
  - optional Django `auth_user`
- Request metadata:
  - `referrer` (query/fragments removed)
  - `user_agent`
- Location:
  - `location_city`, `location_state`, `location_country`
  - `location_source` (`proxy_header`, `client`, `unknown`)

## Privacy Guarantees

- No raw IP address is persisted.
- No full query string is persisted.
- Sensitive query keys are denylisted even if accidentally allowlisted.

## Data Model

- `TrackedPage`: explicit registry of trackable paths.
- `TrackedPageQueryParam`: selected query params for each tracked path.
- `PageViewEvent`: raw event table.

## Tracking Flow

1. `WebsiteAnalyticsMiddleware` checks request suitability (HTML GET page).
2. It resolves the canonical path and verifies it is enabled in `TrackedPage`.
3. Query params are filtered using:
   - selected per-path keys in `TrackedPageQueryParam`
   - global sensitive denylist
4. Location is resolved with precedence:
   - trusted proxy/CDN headers
   - client fallback payload from `/api/analytics/location/`
   - `unknown`

## Client JS

Standalone script:

- `agent_ui/static/js/analytics/website_analytics.js`

It optionally posts `window.REALTYIQ_CLIENT_LOCATION` (city/state/country) to `/api/analytics/location/` once per session.

## TimescaleDB Setup

Migration `0032_website_analytics_timescale` runs PostgreSQL-only setup:

- `timescaledb` extension
- hypertable for `agent_app_pageviewevent`
- continuous aggregates:
  - hourly
  - daily
  - weekly
  - monthly
- refresh policies
- retention policy for raw events (365 days)

SQLite/non-PostgreSQL environments no-op safely for Timescale operations.

## Management Command

Use `register_tracked_page`:

```bash
cd agent_ui
../venv/bin/python manage.py register_tracked_page /chat --key chat --param utm_source --param campaign
```

Examples:

- disable tracking:
  - `manage.py register_tracked_page /tools --disable`
- clear params before setting new:
  - `manage.py register_tracked_page /chat --clear-params --param utm_source`

## Tests

Run targeted tests:

```bash
cd agent_ui
../venv/bin/python manage.py test agent_app.tests.test_analytics_models agent_app.tests.test_analytics_middleware agent_app.tests.test_analytics_query_filter agent_app.tests.test_analytics_location agent_app.tests.test_analytics_command agent_app.tests.test_analytics_timescale agent_app.tests.test_analytics_js_wiring
```

