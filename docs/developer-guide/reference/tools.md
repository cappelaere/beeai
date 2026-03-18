# RealtyIQ Tools Reference

All property/auction tools use **Token authentication** (`Authorization: Token {AUTH_TOKEN}`) against the backend API. They read `API_URL`, `AUTH_TOKEN`, `SITE_ID`, and optionally `USER_ID` and `TLS_VERIFY` from the environment.

The RAG document search tools operate locally on uploaded PDF documents using FAISS vector search.

---

## Core listing tools

### `list_properties`

Paginated list of properties from the front property listing. Each property in the response includes `id`, `name`, `status`, `auction_type`, `bidding_start`, `bidding_end`, `city`, `state`, `postal_code`, `asset_type`, `list_price`, `current_price`, `is_featured`, and when available **`latitude`** and **`longitude`** (from the backend; may be null if not set).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `site_id` | int | `SITE_ID` env | Site/domain id. |
| `page_size` | int | 12 | Items per page (capped at 50). |
| `page` | int | 1 | Page number. |
| `search` | str | "" | Search string. |
| `filter` | str | "" | Filter (e.g. recent_sold_listing). |
| `sort_by` | str | "ending_soonest" | Sort field. |
| `sort_order` | str | "asc" | Sort direction. |
| `agent_id` | str | "" | Filter by agent. |
| `user_id` | int \| None | None | Filter by user. |

**API:** `POST /api-property/front-property-listing/`

**Example prompts**

- "List active properties for site 3"
- "Show the first 20 properties ending soonest"
- "Properties for agent 5"

To **show properties on a map**: use the returned `properties` array as `data_json` for `chart_map`; include only properties that have non-empty `latitude` and `longitude` (the map tool ignores invalid or missing coordinates).

---

### `list_agents_summary`

PII-safe list of agents (no email, phone, or full address).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `site_id` | int | `SITE_ID` env | Site id. |
| `page_size` | int | 12 | Items per page (capped at 50). |
| `page` | int | 1 | Page number. |
| `search` | str | "" | Search string. |
| `filter` | str | "" | Filter. |
| `user_id` | int \| None | None | Filter by user. |

**API:** `POST /api-users/agent-list/`

**Example prompts**

- "List agents for site 3"
- "How many agents are there?"
- "Search agents by company name"

---

## Tier 1 – Property & reference data (Token auth only)

### `get_property_detail`

Full details for a single property (status, bidding dates, reserve, images, etc.).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `property_id` | int | *(required)* | Property id. |
| `site_id` | int | `SITE_ID` env | Site id. |

**API:** `POST /api-property/property-detail/`

**Example prompts**

- "Show me full details for property 12345"
- "What's the status and reserve for property 500?"
- "Get property 100 details including bidding dates"

---

### `list_property_types`

Property type reference data (for filtering/reporting).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `asset_id` | int \| None | None | Optional filter by asset. |

**API:** `POST /api-property/property-type-listing/`

**Example prompts**

- "What property types are available?"
- "List property types for asset 2"

---

### `list_asset_types`

Asset type reference data.

**Parameters:** None.

**API:** `POST /api-property/asset-listing/`

**Example prompts**

- "What asset types exist in the system?"
- "List all asset types"

---

### `get_auction_types`

Auction type reference data (English, Dutch, Sealed, etc.) for a site.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `site_id` | int | `SITE_ID` env | Site id (required by API). |

**API:** `POST /api-cms/get-auction-type/`

**Example prompts**

- "List all auction types"
- "What auction types are configured for site 3?"

---

### `get_site_detail`

Site/domain configuration and metadata.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain` | str | *(required)* | Domain name (e.g. `example.com`), without `https://`. |

**API:** `POST /api-users/get-site-detail/`

**Example prompts**

- "Get site configuration for example.com"
- "What domains are configured?"

---

### `property_count_summary`

Total count of properties matching filters (no full listing).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `site_id` | int | `SITE_ID` env | Site id. |
| `filter` | str | "" | Filter. |
| `search` | str | "" | Search string. |
| `sort_by` | str | "ending_soonest" | Sort field. |
| `sort_order` | str | "asc" | Sort direction. |
| `agent_id` | str | "" | Filter by agent. |
| `user_id` | int \| None | None | Filter by user. |

**API:** `POST /api-property/front-property-listing/` (with `page_size=1`; returns `total`).

**Example prompts**

- "How many active properties are there for site 3?"
- "Count properties ending soon"
- "How many properties does agent 5 have?"

---

## Tier 2 – Auctions & bids (Token + OAuth2)

These tools call endpoints that support both **Token** and **OAuth2** authentication. For tools that require `user_id`, you can pass it explicitly or set the `USER_ID` environment variable.

### `auction_dashboard`

Auction-focused dashboard: auction properties with status, dates, and filters.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain_id` | int | `SITE_ID` env | Site/domain id. |
| `user_id` | int \| None | `USER_ID` env | User id (required if `USER_ID` not set). |
| `page` | int | 1 | Page number. |
| `page_size` | int | 12 | Items per page (capped at 50). |
| `status` | int \| None | None | Status filter (e.g. 1 = active, 17 = upcoming). |
| `agent_id` | int \| None | None | Filter by agent. |
| `auction_id` | int \| None | None | Filter by auction type. |
| `asset_id` | int \| None | None | Filter by asset. |
| `search` | str | "" | Search string. |

**API:** `POST /api-property/property-auction-dashboard/`

**Example prompts**

- "Show auction dashboard for site 3"
- "List active auctions for agent 5"
- "What auctions are upcoming (status 17)?"

---

### `auction_bidders`

Bidders registered for an auction (property).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `property_id` | int | *(required)* | Property/auction id. |
| `site_id` | int | `SITE_ID` env | Site id. |
| `user_id` | int \| None | `USER_ID` env | User id (required if `USER_ID` not set). |
| `page` | int | 1 | Page number. |
| `page_size` | int | 12 | Items per page (capped at 50). |

**API:** `POST /api-bid/auction-bidders/`

**Example prompts**

- "How many bidders are registered for property 100?"
- "List bidders for auction property 500"

---

### `auction_total_bids`

Bid activity summary per bidder for an auction property.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `property_id` | int | *(required)* | Property id. |
| `site_id` | int | `SITE_ID` env | Site id. |
| `user_id` | int \| None | `USER_ID` env | User id (required if `USER_ID` not set). |
| `page` | int | 1 | Page number. |
| `page_size` | int | 12 | Items per page (capped at 50). |

**API:** `POST /api-bid/auction-total-bids/`

**Example prompts**

- "Show bid summary for property 100"
- "Who has the highest bid on property 500?"
- "Bid activity for auction 100"

---

### `bid_history`

Full bid history for a property (summary per user).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `property_id` | int | *(required)* | Property id. |
| `domain_id` | int \| None | None | Domain/site id. |
| `site_id` | int \| None | None | Site id (used as domain_id if domain_id not set). |

**API:** `POST /api-bid/bid-history/`

**Example prompts**

- "Show bid history for property 100"
- "List all bids on auction 500"

---

### `auction_watchers`

Count and list of watchers for an auction property.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `property_id` | int | *(required)* | Property id. |
| `site_id` | int | `SITE_ID` env | Site id. |
| `user_id` | int \| None | `USER_ID` env | User id (required if `USER_ID` not set). |
| `page` | int | 1 | Page number. |
| `page_size` | int | 12 | Items per page (capped at 50). |

**API:** `POST /api-bid/auction-total-watching/`

**Example prompts**

- "How many people are watching property 100?"
- "Watcher count for auction 500"

---

### `admin_dashboard`

Admin dashboard counts and analytics for a site.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `site_id` | int | `SITE_ID` env | Site id. |
| `start_date` | str \| None | None | Start date (YYYY-MM-DD). |
| `end_date` | str \| None | None | End date (YYYY-MM-DD). |

**API:** `POST /api-users/admin-dashboard/`

**Example prompts**

- "Show admin dashboard for site 3"
- "What are the key metrics for the platform?"
- "Admin stats for last 30 days"

---

### `property_registration_graph`

Property registration over time (graph data).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `site_id` | int | `SITE_ID` env | Site id. |
| `start_date` | str \| None | None | Start date (YYYY-MM-DD). |
| `end_date` | str \| None | None | End date (YYYY-MM-DD). |

**API:** `POST /api-users/property-registration-graph/`

**Example prompts**

- "Property registration trend for last 30 days"
- "Show property signup graph for site 3"

---

## RAG / Document Search

### `search_documents`

Search indexed PDF documents using semantic similarity.

**Purpose:** Search indexed PDF documents using semantic similarity

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | *(required)* | The search query or question |
| `top_k` | int | 5 | Number of results to return (max: 20) |

**Returns:**

- `query`: The original search query
- `total_indexed_documents`: Count of unique documents in index
- `total_indexed_chunks`: Total number of text chunks indexed
- `results`: Array of top-K relevant chunks with:
  - `rank`: Result ranking (1-K)
  - `relevance_score`: Similarity score (0-1, higher is better)
  - `document_name`: Source document filename
  - `document_path`: Relative path in media folder
  - `chunk_index`: Position in document
  - `text`: Relevant text excerpt (truncated to 500 chars)

**Example prompts:**

- "What are the bidding requirements for GSA auctions?"
- "Search documents for information about reserve prices"
- "Find documents mentioning property inspection procedures"

**Example:**
```python
result = search_documents(
    query="What are the bidding requirements for GSA auctions?",
    top_k=3
)
```

---

### `reindex_all_documents`

Rebuild FAISS index from all PDFs in /media/documents.

**Purpose:** Rebuild FAISS index from all PDFs in /media/documents

**Use Cases:**
- Initial setup after installing RAG tool
- After bulk document uploads
- Index corruption recovery

**Parameters:** None

**Returns:**

- `status`: "success" or "error"
- `total_documents_found`: Count of PDFs found
- `documents_indexed`: Count successfully indexed
- `total_chunks_created`: Total text chunks created
- `failed_documents`: List of errors (if any)

**Example prompts:**

- "Reindex all documents"
- "Rebuild the document search index"
- "Index all uploaded PDFs"

---

## Time series charting

### `chart_time_series`

Plots time series data (e.g. from DAP or property metrics APIs) as a line or bar chart and returns markdown for chat. Used by **DAP Analyst** and **BI** agents. Renders with Plotly and exports PNG via Kaleido (offline, no external access).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_json` | str | *(required)* | JSON string: array of objects with a date and one or more numeric fields (e.g. DAP API response or `get_metrics_property_daily` result). |
| `title` | str | *(required)* | Chart title. |
| `date_column` | str \| None | None | Key for the date axis (auto-detected if not set, e.g. `date`, `dimensions[0]`). |
| `value_columns` | str \| None | None | Comma-separated numeric keys to plot (e.g. `visits`, `pageviews` or `views,unique_sessions`). Default: inferred. |
| `chart_type` | str | `"line"` | `"line"` or `"bar"`. |

**Output:** When running via the web app (Django cache available), the tool stores the PNG in cache and returns markdown with an image URL: `![Chart: title](/api/agent-chart/<uuid>/)` so the LLM context stays small and avoids rate limits. When cache is unavailable (e.g. CLI), it returns markdown with an embedded base64 image.

**Serving charts:** The UI serves cached chart images via:

- **Endpoint:** `GET /api/agent-chart/<chart_id>/`
- **Response:** PNG image, or 404 if the chart is missing or expired (cache TTL 1 hour).

**Download and export:** In chat, each chart image has a "Download image" button to save the chart as a PNG. Session export supports **PDF** (`/api/sessions/<id>/export/?format=pdf` or "Download as PDF" from the browser view); charts still in cache are inlined into the PDF.

**macOS:** PDF export uses WeasyPrint and requires system libraries. If "Download as PDF" returns an error or 500, install Pango (and optionally related libs): `brew install pango` or `brew install pango gdk-pixbuf libffi`. See [Troubleshooting — PDF export](../../user-guide/TROUBLESHOOTING.md#session-export--pdf-export) for details.

**Example prompts**

- "Chart realestatesales.gov visits for the last 30 days"
- "Show me a line chart of property 123 metrics (views, brochure downloads) for last month"

---

## Map charting

### `chart_map`

Plots points on a map from latitude/longitude data. Used by **GRES**, **DAP Analyst**, and **BI** agents for location or property maps. Renders with Plotly Scattergeo and exports PNG via Kaleido (no Mapbox or external tile key required).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_json` | str | *(required)* | JSON string: array of objects with latitude and longitude (or `lat`/`lon`, `y`/`x`). |
| `title` | str | *(required)* | Map title. |
| `lat_column` | str \| None | None | Key for latitude (auto-detected from `latitude`, `lat`, `y`). |
| `lon_column` | str \| None | None | Key for longitude (auto-detected from `longitude`, `lon`, `lng`, `x`). |
| `label_column` | str \| None | None | Optional key for point labels/hover (e.g. name, address, title). |
| `size_column` | str \| None | None | Optional numeric key for marker size (e.g. views, count). |
| `scope` | str | `"world"` | Map extent: `"world"` or `"usa"`. |

**Output:** Same as `chart_time_series`: cache+URL in web app, base64 fallback in CLI. Map images use the same `/api/agent-chart/<chart_id>/` endpoint and get "Download image" in chat.

**Example prompts**

- "Show these locations on a map: [JSON with latitude, longitude, name]"
- "Plot our property portfolio on a USA map with marker size by views"
- "Display on a map all active properties" → call `list_properties`, filter to items with non-empty `latitude`/`longitude`, then pass that array to `chart_map` with `label_column='name'`, `scope='usa'`.

### `chart_choropleth`

Choropleth map: colors regions (e.g. US states) by a numeric value (e.g. property count). Used by **GRES** and **BI** for "property density by state" or "choropleth by location". Uses Plotly `go.Choropleth` with built-in USA-states geometry; no GeoJSON file required.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_json` | str | *(required)* | JSON string: array of objects with a region key (e.g. `state`) and a value key (e.g. `count`). |
| `title` | str | *(required)* | Map title (e.g. "Property density by state"). |
| `location_column` | str | `"state"` | Key for region identifier (full state name e.g. Kansas, or 2-letter code e.g. KS). |
| `value_column` | str | `"count"` | Key for the numeric value to color by. |
| `locationmode` | str | `"USA-states"` | `USA-states` for US state-level map, or `country names` for world by country. |

**Output:** Same as `chart_map`: cache+URL or base64, served at `/api/agent-chart/<chart_id>/`.

**Flow:** Call `list_properties`, aggregate by `state` (count per state), build an array like `[{"state": "Kansas", "count": 16}, ...]`, then call `chart_choropleth` with that as `data_json`.

**Example prompts**

- "Choropleth map showing the density of properties by state"
- "Property counts by location" / "Show property density by state"

---

## Flo workflow & schedule tools

The **Flo** agent (Workflow Management Specialist) uses tools from `tools/workflow_tools.py`, `tools/schedule_tools.py`, and `tools/notification_preferences_tools.py`. They run in the chat/agent context with `USER_ID` from the environment.

| Tool | Module | Description |
|------|--------|-------------|
| `list_workflows`, `get_workflow_detail`, `suggest_workflow` | workflow_tools | Discover and describe workflows |
| `list_workflow_runs`, `search_workflow_runs`, `get_run_detail`, `get_workflow_run_summary` | workflow_tools | List/search runs and one-line summary |
| `execute_workflow`, `rerun_workflow`, `bulk_run_workflow`, `manage_workflow_run` | workflow_tools | Execute, clone, bulk run, start/cancel/restart |
| `list_tasks`, `search_tasks`, `claim_task`, `submit_task` | workflow_tools | Tasks: list, search, claim, approve/deny |
| `get_my_work_summary` | workflow_tools | Pending tasks, recent runs, next schedules, unread count |
| `get_workflow_system_status` | workflow_tools | Run counts by status + scheduler note |
| `list_schedules`, `create_schedule`, `update_schedule`, `set_schedule_active`, `delete_schedule` | schedule_tools | Schedules: list, create, update, pause/resume, delete |
| `get_notification_preferences`, `set_notification_preferences` | notification_preferences_tools | Notify on workflow complete, daily digest |

Flo’s instructions (in `agents/flo/agent.py`) tell it when to use each tool (e.g. "what do I need to do?" → `get_my_work_summary`, "pause schedule 3" → `set_schedule_active(3, False)`). User preferences for notifications are stored in `UserPreference.notification_preferences` (JSONField, migration 0028).

---

## Environment variables used by tools

| Variable | Required | Description |
|----------|----------|-------------|
| `API_URL` | Yes | Base URL of the API (e.g. `http://127.0.0.1:8000`). |
| `AUTH_TOKEN` | Yes | Token for API authentication. |
| `SITE_ID` | No | Default site id (default `3`). |
| `USER_ID` | No | Default user id for Tier 2 tools that require it (auction_dashboard, auction_bidders, auction_total_bids, auction_watchers). |
| `TLS_VERIFY` | No | Set to `false` to disable TLS verification (dev only). |

---

## Summary

| Category | Tools |
|----------|--------|
| Core | `list_properties`, `list_agents_summary` |
| Tier 1 (property & reference) | `get_property_detail`, `list_property_types`, `list_asset_types`, `get_auction_types`, `get_site_detail`, `property_count_summary` |
| Tier 2 (auctions & bids) | `auction_dashboard`, `auction_bidders`, `auction_total_bids`, `bid_history`, `auction_watchers`, `admin_dashboard`, `property_registration_graph` |
| RAG / Document Search | `search_documents`, `reindex_all_documents` |
| Time series charting | `chart_time_series` (DAP Analyst, BI) |
| Map charting | `chart_map`, `chart_choropleth` (GRES, BI) |
| Flo workflow & schedule | Workflow/task/schedule/notification tools in `workflow_tools.py`, `schedule_tools.py`, `notification_preferences_tools.py` (see [Flo workflow & schedule tools](#flo-workflow--schedule-tools)) |

**Total:** 19 property/auction/RAG/chart tools plus Flo’s workflow/schedule tools (26 tools in Flo). Chart and map images are served by `GET /api/agent-chart/<chart_id>/` when the tool runs in the web app.
