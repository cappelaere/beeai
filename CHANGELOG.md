# Changelog

All notable changes to the RealtyIQ BeeAI Agent project.

## [0.3.8] - 2026-03-03

### Added – Property coordinates and map/choropleth tools

#### Property latitude/longitude in tools
- **`list_properties`** now includes **`latitude`** and **`longitude`** in each property in the response (when provided by the API). Agents can use these for mapping and location-based analysis.
- **`get_property_detail`** already returned full API payload including lat/long; no change.

#### Map display (GRES and BI)
- **`chart_map`** added to the GRES agent so the default agent can show properties on a map. BI already had it.
- Agent instructions updated so that for "display on a map all active properties" the agent **calls `chart_map` and includes the map image** in the reply (not only a table of coordinates). Same flow for BI.
- **`chart_map`** registered in MCP server and in `tools/__init__.py` for listing.

#### Choropleth map (property density by location)
- **`chart_choropleth`** (`tools/chart_choropleth.py`): choropleth map by region (e.g. US states). Parameters: `data_json` (array of objects with region + value), `title`, `location_column` (default `state`), `value_column` (default `count`), `locationmode` (`USA-states` or `country names`). Uses Plotly `go.Choropleth` with built-in USA-states geometry; accepts full state names or 2-letter codes; aggregates duplicate states in the tool.
- GRES and BI agents: when the user asks for a "choropleth map" or "property density by state/location", the agent calls `list_properties`, aggregates by state, then `chart_choropleth`, and includes the image.
- Registered in `tools/__init__.py`, `list_tools.py`, GRES/BI agent configs, and MCP server.

#### Documentation and skills
- **docs/developer-guide/reference/tools.md:** `list_properties` response fields updated to include latitude/longitude; "Display on a map" flow and choropleth flow documented; new **`chart_choropleth`** section; Summary table updated for map tools (GRES, BI).
- **.cursor/rules/property-map-tools.mdc:** New Cursor rule describing property coordinates in list_properties and the map/choropleth tools (chart_map, chart_choropleth), agent usage, and pointer to tools.md.

---

## [0.3.7] - 2026-03-10

### Added - Flo UX tools and capabilities

Flo (Workflow Management Specialist) can now handle scheduling, search, bulk runs, notification preferences, system status, and guided workflow start from chat. New tools and UI are documented in [docs/IDEAS_UX_TOOLS_AGENTS.md](docs/IDEAS_UX_TOOLS_AGENTS.md).

#### Schedule from chat (5) and scheduler assistant (5)
- **tools/schedule_tools.py:** `list_schedules`, `create_schedule`, `delete_schedule`, `update_schedule`, `set_schedule_active`. Flo can list, create, update (run_at, interval, run_name), pause/resume, and delete schedules from natural language (e.g. "schedule workflow 1 every Monday at 9am", "pause schedule 3").

#### My work summary (2)
- **get_my_work_summary()** in workflow_tools.py: one-shot summary of pending tasks, recent runs, next scheduled runs, and unread notification count. Flo answers "what do I need to do?" and "what's running?".

#### Re-run and run summary (3, 4)
- **rerun_workflow(run_id)** in workflow_tools.py: creates a new run with the same workflow and inputs as a past run.
- **Run again** button on workflow run detail page: clones the run from the UI (same inputs, new run_id).
- **get_workflow_run_summary(run_id)** in workflow_tools.py: one-line summary (workflow name, status, outcome) for "what happened with run X?".

#### Search runs and tasks (6)
- **search_workflow_runs(workflow_id, status, date_from, date_to, user_id, limit)** in workflow_tools.py.
- **search_tasks(query, status, user_id, limit)** in workflow_tools.py (text search on title/description).

#### Bulk run workflow (7)
- **bulk_run_workflow(workflow_id, list_of_inputs, max_runs=20)** in workflow_tools.py: creates one run per input dict (e.g. "run bidder onboarding for these 5 companies"). Capped at 50.

#### Notification preferences (8)
- **UserPreference.notification_preferences** JSONField (migration 0028): e.g. `notify_on_workflow_complete`, `daily_digest`.
- **tools/notification_preferences_tools.py:** `get_notification_preferences`, `set_notification_preferences`. Flo can show and update settings from chat.

#### Health / system status (9)
- **get_workflow_system_status(user_id)** in workflow_tools.py: returns run counts (pending, running, waiting_for_task, completed_24h, failed_24h) and a scheduler note for "is everything okay?" and "why isn't my schedule running?".

#### Guided workflow start (10)
- Flo instructions updated: when the user asks for help running a workflow ("help me run workflow 1", "walk me through"), Flo asks for each required input one by one, then confirms and executes (same tools, clearer conversation).

#### Documentation and skills
- **docs/IDEAS_UX_TOOLS_AGENTS.md:** All 10 items marked done; doc kept for reference.
- **docs/user-guide/workflow_management/QUICK_REFERENCE.md:** "Chat with Flo" section added (summary of Flo capabilities from chat).
- **docs/user-guide/workflow_management/WORKFLOW_AND_TASK_GUIDE.md:** "Flo from chat" section added (schedule, my work, re-run, search, bulk run, notifications, system status, guided run).
- **docs/developer-guide/reference/tools.md:** "Flo workflow & schedule tools" section and summary table updated.
- **.cursor/rules/flo-workflow-tools.mdc:** Rule for AI assistants describing Flo's workflow/schedule tools and where they live.

---

## [0.3.6] - 2026-03-08

### Added - Workflow Scheduler (ROADMAP #14)

#### Schedule workflows to run once or on an interval
- **ScheduledWorkflow model:** Run a workflow at a specific time (once) or on a recurring interval (every N minutes). Each schedule has optional run name and input variables (JSON). Stored in DB with `next_run_at`; scheduler processes due entries.
- **Management command:** `python manage.py run_scheduled_workflows` — run every 1–5 minutes via cron or systemd. Creates a `WorkflowRun`, executes via shared workflow runner, then removes one-shot schedules or advances `next_run_at` for interval schedules.
- **Shared workflow runner:** [agent_ui/agent_app/workflow_runner.py](agent_ui/agent_app/workflow_runner.py) — `execute_workflow_run(run_id, send_message=None)` used by both the WebSocket consumer and the scheduler. Handles completion, failure, and task pause (TaskPendingException).

#### REST API
- **GET/POST** `/api/workflows/schedules/` — list (GET) or create (POST) schedules.
- **GET** `/api/workflows/schedules/<id>/` — schedule detail.
- **PATCH/PUT** `/api/workflows/schedules/<id>/update/` — update schedule.
- **DELETE** `/api/workflows/schedules/<id>/delete/` — delete schedule.
- **POST** `/api/workflows/schedules/<id>/run_now/` — run the workflow immediately without changing the schedule.

#### UI
- **Schedules page:** `/workflows/schedules/` — table of user’s schedules with Edit, Run now, Delete. **Schedule Workflow** button for create.
- **Schedule form:** `/workflows/schedules/new/` and `/workflows/schedules/<id>/edit/` — workflow dropdown, run name, input JSON, once (date/time) or interval (minutes, optional first run). Pre-select workflow via `?workflow_id=<id>`.
- **Workflow detail:** “Schedule” button links to new schedule form with workflow pre-selected.
- **Nav:** “Schedules” link under Workflows in the sidebar.

#### /schedule command
- **/schedule list** — list your scheduled workflows.
- **/schedule add \<workflow> ["name"] at \<datetime>** — schedule once (e.g. `at 2025-03-10 09:00`).
- **/schedule add \<workflow> every \<N> [minutes]** — schedule every N minutes.
- **/schedule show \<id>** — show schedule details.
- **/schedule edit \<id>** — link to edit in UI.
- **/schedule delete \<id>** — delete schedule.
- Workflow can be workflow number (e.g. `1`) or workflow id (e.g. `bidder_onboarding`). Registered in command dispatcher; help updated.

#### Documentation
- **ROADMAP:** Section 14 “Scheduled/Automated Workflows” — status set to Partially Implemented; implemented checklist and technical note for cron.
- **User guide:** [docs/user-guide/workflow_management/QUICK_REFERENCE.md](docs/user-guide/workflow_management/QUICK_REFERENCE.md) — Schedules section and schedules URL. [WORKFLOW_AND_TASK_GUIDE.md](docs/user-guide/workflow_management/WORKFLOW_AND_TASK_GUIDE.md) — Schedule commands table and Web UI Schedules subsection.

#### Files (summary)
- Model: [agent_ui/agent_app/models.py](agent_ui/agent_app/models.py) (ScheduledWorkflow), migration `0027_scheduled_workflow`.
- Runner: [agent_ui/agent_app/workflow_runner.py](agent_ui/agent_app/workflow_runner.py); [agent_ui/agent_app/consumers.py](agent_ui/agent_app/consumers.py) refactored to use it.
- Command: [agent_ui/agent_app/management/commands/run_scheduled_workflows.py](agent_ui/agent_app/management/commands/run_scheduled_workflows.py).
- API: [agent_ui/agent_app/views/api_schedules.py](agent_ui/agent_app/views/api_schedules.py); URLs in [agent_ui/agent_app/urls.py](agent_ui/agent_app/urls.py).
- UI: [agent_ui/templates/workflows/schedule_list.html](agent_ui/templates/workflows/schedule_list.html), [schedule_form.html](agent_ui/templates/workflows/schedule_form.html); Schedule button on [workflows/detail.html](agent_ui/templates/workflows/detail.html); Schedules link in [base.html](agent_ui/templates/base.html).
- Slash command: [agent_ui/agent_app/commands/schedule.py](agent_ui/agent_app/commands/schedule.py); registered in [command_dispatcher.py](agent_ui/agent_app/command_dispatcher.py); [help.py](agent_ui/agent_app/commands/help.py) updated.

---

## [0.3.5] - 2026-03-08

### Fixed - Chart tool rate limit (429 TPM)

#### Chart tool: cache + URL instead of base64 in chat
- **Problem:** The `chart_time_series` tool returned markdown with an embedded base64 PNG (~30k tokens). That output was sent to the LLM on the next turn, triggering OpenAI 429 (tokens-per-minute limit).
- **Solution:** When Django cache is available, the tool now stores the PNG in cache under a UUID and returns short markdown with an image URL only: `![Chart: title](/api/agent-chart/<uuid>/)`. The model sees a small string; the chat UI loads the image from the new endpoint. When cache is unavailable (e.g. CLI), the tool falls back to base64 so charting still works.
- **New endpoint:** `GET /api/agent-chart/<str:chart_id>/` serves the chart PNG from cache (404 if missing or expired). Cache key prefix: `agent_chart_`, TTL: 1 hour.
- **Files:** `tools/chart_time_series.py`, `agent_ui/agent_app/views/api_chat.py` (serve_agent_chart), `agent_ui/agent_app/urls.py`, `agent_ui/agent_app/views/__init__.py`.

#### Documentation
- **Tools reference:** [docs/developer-guide/reference/tools.md](docs/developer-guide/reference/tools.md) — added Time series charting section for `chart_time_series` and the agent-chart API endpoint.
- **Plan:** [.cursor/plans/charting_tool_for_time_series.plan.md](.cursor/plans/charting_tool_for_time_series.plan.md) — post-implementation note for cache+URL behavior.

### Added - Chart & report export (Option C)

#### Download chart as image
- **Chat UI:** For assistant messages that contain a chart image (URL `/api/agent-chart/<id>/` or embedded base64), a "Download image" button is shown below each chart. Clicking it saves the chart as a PNG file (filename derived from chart title/alt text).
- **Files:** [agent_ui/static/js/chat.js](agent_ui/static/js/chat.js) (`addChartDownloadButtons`, `downloadChartImage`, `isChartImage`), [agent_ui/static/css/theme.css](agent_ui/static/css/theme.css) (`.chart-image-wrapper`, `.chart-download-btn` and dark theme).

#### Export session as PDF (with charts)
- **Export API:** Session export supports `?format=pdf`. The PDF is generated from the same Markdown→HTML used for the browser view; chart images are inlined from cache (so charts created in that session and still in cache appear in the PDF). Uses WeasyPrint for HTML→PDF.
- **Browser view:** The "Export session" → view in browser page now has two links: "Download as Markdown" and "Download as PDF".
- **Export permission:** Export endpoint now checks session ownership (`session_obj.user_id == request.session user_id`); returns 403 for other users’ sessions.
- **Files:** [agent_ui/agent_app/views/api_sessions.py](agent_ui/agent_app/views/api_sessions.py) (user check, `_inline_chart_images`, PDF branch, shared HTML styles), [requirements.txt](requirements.txt) (weasyprint>=62.0). Duplicate `@require_GET` on export removed.

### Added - Task notifications & alerts (ROADMAP #2)

#### In-app notification center
- **Bell icon** in the top bar (next to the brand) shows an unread count badge. Click to open a dropdown with recent notifications (unread first).
- **Notification types:** Task assigned to you (when you claim a task), Task due soon (tasks expiring within 24 hours), Workflow completed, Workflow failed. Due-soon notifications are created on demand when the list is loaded.
- **Actions:** "Mark read" per notification, "Mark all read", and a link to **My Tasks**. Each notification links to the task or workflow run.
- **Backend:** New `Notification` model (`user_id`, `kind`, `title`, `message`, `task_id`, `workflow_run_id`, `created_at`, `read_at`). Notifications are created when a task is claimed ([agent_ui/agent_app/views/tasks.py](agent_ui/agent_app/views/tasks.py)), when a workflow completes or fails ([agent_ui/agent_app/consumers.py](agent_ui/agent_app/consumers.py) `update_workflow_status`), and when a task is cancelled ([agent_ui/agent_app/views/tasks.py](agent_ui/agent_app/views/tasks.py) task_cancel).
- **API:** `GET /api/notifications/` (list; ensures due-soon notifications for current user), `POST /api/notifications/<id>/read/`, `POST /api/notifications/read-all/`.
- **Files:** [agent_ui/agent_app/models.py](agent_ui/agent_app/models.py) (Notification), [agent_ui/agent_app/notifications.py](agent_ui/agent_app/notifications.py) (create helpers, ensure_due_soon), [agent_ui/agent_app/views/api_notifications.py](agent_ui/agent_app/views/api_notifications.py), [agent_ui/templates/base.html](agent_ui/templates/base.html) (bell + dropdown + script), [agent_ui/static/css/theme.css](agent_ui/static/css/theme.css) (notification styles and dark theme). Migration: `0026_add_notification_model`.

### Added - Map charting tool (objects on a map)

- **chart_map** tool in [tools/chart_map.py](tools/chart_map.py): plots points on a map from latitude/longitude data. Uses Plotly Scattergeo (world or USA scope), exports PNG via Kaleido, same cache+URL pattern as chart_time_series. Parameters: `data_json`, `title`, `lat_column`, `lon_column` (inferred from latitude/longitude, lat/lon, y/x), optional `label_column`, `size_column`, `scope` (world | usa). Served by existing `GET /api/agent-chart/<id>/`; download button in chat applies to map images too.
- **Agents:** Registered in DAP Analyst and BI ([agents/dap_analyst/agent.py](agents/dap_analyst/agent.py), [agents/bi/agent.py](agents/bi/agent.py)); instructions and SKILLS updated for when to use (locations, properties on a map).
- **Docs:** [docs/developer-guide/reference/tools.md](docs/developer-guide/reference/tools.md) — Map charting section and summary table updated (19 tools).

---

## [0.3.4] - 2026-03-03

### Added - Property metrics for Prometheus (BI) — plan and implementation

#### Implementation
- **RealtyIQ metrics_collector:** Added property metrics gauges (portfolio: `property_metrics_properties_with_activity_24h`, `_7d`, `property_metrics_funnel_last_7d`; per-property: `property_metrics_num_viewers`, `property_metrics_num_bidders`, `property_metrics_num_subscribers`, `property_metrics_brochure_downloads`, `property_metrics_ifb_downloads`, `property_metrics_unique_sessions` with label `property_id`). Added `update_property_metrics()` which calls Api `properties-with-activity` and `properties/<id>/summary?days=7` for **active properties only** and sets gauges; runs on each `/metrics` request. `collect_all_metrics()` now includes `update_property_metrics()`; `prometheus_metrics` view calls `collect_all_metrics()` before exporting.
- **Prometheus:** New scrape job `realtyiq-property-metrics` in [prometheus/prometheus.yml](prometheus/prometheus.yml) targeting RealtyIQ (`ui:8002`), `scrape_interval: 5m`, `metrics_path: /metrics/`.
- **Grafana:** Dashboard [prometheus/grafana/dashboards/property-metrics-bi.json](prometheus/grafana/dashboards/property-metrics-bi.json) for portfolio stats, funnel (7d), and per-property table (viewers, bidders, subscribers).

#### Seed data for testing
- **Api 30-day seed:** [data/source/property_metric_daily_seed_30d_10properties.csv](data/source/property_metric_daily_seed_30d_10properties.csv) — 30 days of daily rollups for 10 properties (300 rows). Load with `python manage.py load_metrics_daily_csv --file <path>` from the Api project to populate the metrics DB for pipeline testing.
- **Prometheus seed for Grafana:** [data/source/prometheus_property_metrics_seed_10properties.prom](data/source/prometheus_property_metrics_seed_10properties.prom) — Prometheus exposition format with portfolio and per-property gauges (10 properties, 30-day aggregates). [scripts/serve_property_metrics_seed.py](scripts/serve_property_metrics_seed.py) serves it at `/metrics` (default port 9091) so Prometheus can scrape it and Grafana can be tested without the full RealtyIQ collector.

#### Documentation
- **ROADMAP:** Section 21 — Property metrics for Prometheus (BI) added (planned).
- **Observability:** New [docs/developer-guide/observability/PROPERTY_METRICS_PROMETHEUS.md](docs/developer-guide/observability/PROPERTY_METRICS_PROMETHEUS.md) describing scope, scrape config, recommended metrics, implementation order, and **seed data for testing** (CSV + .prom + serve script). [Observability README](docs/developer-guide/observability/README.md) and [PROMETHEUS_METRICS.md](docs/developer-guide/observability/PROMETHEUS_METRICS.md) updated to reference it.

#### Removed - Prometheus .prom / .om simulated data
- Simulated property-metrics data is now **CSV + Grafana/Infinity only**. Removed: `.prom` and `.om` seed files, `scripts/serve_property_metrics_seed.py`, `scripts/generate_openmetrics_backfill.py`, `scripts/prometheus_batch_import.sh`, [PROMTOOL_INSTALL.md](docs/developer-guide/observability/PROMTOOL_INSTALL.md). Removed Prometheus scrape job `realtyiq-property-metrics-seed` and repo mount from Prometheus container. Docs updated (PROPERTY_METRICS_PROMETHEUS.md, observability README, ROADMAP) to describe CSV + Infinity for Grafana.

---

## [0.3.3] - 2026-03-03

### Added - BI Agent for BidHom Metrics (ROADMAP Task #20)

#### BI Agent
- **New agent `bi`**: BidHom property performance and metrics assistant
  - Registered in `agents.yaml`; config in `agents/bi/agent.py`; `agents/bi/__init__.py` and `agents/bi/SKILLS.md`
  - Instructions support Real Estate Specialists, Program Managers, Marketing/Outreach, and Leadership use-cases
  - Supports 20 prompt types: property-level performance, conversion/auction readiness, portfolio monitoring, operational monitoring, executive portfolio insights
- **Tools**: `get_metrics_property_summary`, `get_metrics_property_daily`, `get_metrics_top_properties`, `get_metrics_underperforming`, `get_metrics_properties_with_activity`; reuse of `list_properties`, `get_property_detail`, `auction_bidders`, `property_registration_graph`; DuckDuckGo web search; ThinkTool
- **Underperforming by interest metric**: Api and tool support `interest_metric=views|ifb_downloads|brochure_downloads` for “high IFB/brochure, low bidders”
- **Properties with activity**: New Api endpoint `GET /api/metrics/properties-with-activity` and tool for deriving “no activity” (active IDs not in set)
- **Token auth for metrics GET**: Api metrics read views accept `Authorization: Token` (staff user) in addition to session, so BI agent can call with `AUTH_TOKEN`
- **Tests**: `agent_app.tests.test_bi_agent` (9 tests); optional one-shot script `scripts/test_bi_agent.py "prompt"`

#### Documentation
- **ROADMAP**: Section 20 (BI Agent for BidHom Metrics) added and marked completed

---

## [0.3.2] - 2026-03-03

### Added - Workflow Version Control (ROADMAP Task #14)

#### Version Control Completion
- **View Version Files**: Version history page "View Files" button now opens a modal
  - Fetches file contents from `/api/workflows/<id>/versions/<n>/files/`
  - Tabs for each file: `metadata.yaml`, `workflow.py`, `diagram.mmd`, `README.md`
  - Scrollable read-only view of version snapshot contents
  - Replaces previous "coming soon" placeholder

#### Documentation
- **ROADMAP**: Section 14 (Workflow Version Control) marked ✅ Completed
  - Implemented: track changes, rollback, compare (diff), tag, version comments/changelog, view version files
  - Not implemented: branch/test environments, approval workflow for changes
  - Implementation details and technical notes added

### Technical Details

#### Modified Files
- `agent_ui/templates/workflows/versions.html` - View Files modal (markup, styles, JS)
- `docs/ROADMAP.md` - Workflow Version Control status and implementation details

---

## [0.3.1] - 2026-03-03

### Added - Favorite Workflows (ROADMAP Task #17)

#### Favorite Workflows Feature
- **Star/Favorite Workflows**: Click star icon on workflow cards to mark as favorites
  - Golden star for favorites, grey outline for non-favorites
  - Instant visual feedback and state persistence
  - Available to all users on `/workflows/` list page
- **Favorite Workflows Panel on Chat Homepage**
  - Collapsible panel showing all starred workflows
  - Quick-run button to navigate directly to workflow detail page
  - Displays workflow icon, name, description, category, and estimated duration
  - Panel collapse state persists via localStorage
  - Compact card design for easy scanning
- **API Endpoint**: `/api/workflows/<workflow_id>/favorite/`
  - Toggle favorite status with POST request
  - Returns success status and current favorite state
  - Session-based storage using UserPreference model

#### Workflow Export Enhancements
- **HTML Export Improvements**
  - Summary text now properly formatted with line breaks (was squished on one line)
  - Added "Initiated By" field showing user who started the workflow
  - Added "Task Approvals" section showing:
    - Task title and type
    - Task status (color-coded: green for completed, orange for in-progress)
    - User who completed each task
    - Completion timestamps
  - Better visual hierarchy and readability

#### Workflow Run Detail Page Enhancements
- **User Tracking**: Added "Initiated By" field to workflow run detail page
  - Shows user ID who started the workflow
  - Displayed in metadata table alongside Run ID and Workflow ID
  - Helps with accountability and audit trails

### Fixed

#### UI/UX Fixes
- **Favorite Cards Collapse**: Fixed panel not collapsing after manual resize
  - Added `!important` flags to override inline styles from resizer
  - Hide resizer bar when panel is collapsed
  - Proper height constraints for collapsed state
- **CSRF Token Issue**: Fixed workflow favorite toggle failing with CSRF error
  - Updated `getCsrfToken()` to read from cookie instead of form field
  - Consistent with other pages in the application

#### Database & Backend Fixes
- **Dashboard Error**: Fixed `FieldError` on `/dashboard/` page
  - Changed `Count("id")` to `Count("task_id")` in HumanTask queries
  - Applied fix in both `admin.py` and `metrics_collector.py`
  - HumanTask uses `task_id` as primary key, not `id`
- **Workflow Registry Import**: Fixed `ModuleNotFoundError` on workflow run detail page
  - Corrected import path from `.workflow_registry` to `agent_app.workflow_registry`
  - Applied fix in two locations in `workflows.py`

### Technical Details

#### Database Schema Changes
- Added `favorite_workflows` TextField to UserPreference model (migration 0024)
  - Stores JSON-encoded list of workflow IDs
  - Defaults to empty array "[]"
  - Nullable and blank allowed

#### New Files
- `agent_ui/agent_app/migrations/0024_add_favorite_workflows.py`

#### Modified Files
- `agent_ui/agent_app/models.py` - Added favorite_workflows field
- `agent_ui/agent_app/views/api_workflows.py` - New favorite API endpoint
- `agent_ui/agent_app/views/workflows.py` - Added tasks data, fixed imports
- `agent_ui/agent_app/views/chat.py` - Query and pass favorite workflows data
- `agent_ui/agent_app/views/admin.py` - Fixed Count("task_id") bug
- `agent_ui/agent_app/metrics_collector.py` - Fixed Count("task_id") bug
- `agent_ui/agent_app/urls.py` - Added workflow_favorite_api route
- `agent_ui/templates/chat.html` - Added Favorite Workflows panel (removed Recent Workflows)
- `agent_ui/templates/workflows/list.html` - Added star icons and toggle handler
- `agent_ui/templates/workflows/run_detail.html` - Added user_id, tasks data
- `agent_ui/static/js/chat.js` - Workflow panel rendering and toggle logic
- `agent_ui/static/js/workflow-execution.js` - Enhanced HTML export with user tracking
- `agent_ui/static/css/theme.css` - Styles for workflow panels and collapse behavior

---

## [0.3.0] - 2026-03-03

### Added - UI/UX Improvements

#### Agent Navigation Enhancements
- **"Prompt Agent" action** in agents list dropdown menu
  - Available to all users (not just admins)
  - Sets agent as default (for admins) and redirects to chat page
  - Enables quick agent switching with immediate chat access
  - Grey icon design consistent with new UI patterns

#### Workflow Runs User Tracking
- **User ID column** added to workflow runs list (`/workflows/runs/`)
  - Displays which user initiated each workflow run
  - Blue badge styling for visual distinction from Run ID
  - Helps with multi-user workflow accountability

#### Task List UI Modernization
- **Replaced colored buttons with grey icons** for cleaner interface
  - Grey icon buttons replace blue/red colored buttons
  - Hover effects with light grey background
  - Consistent with modern minimal design patterns
- **Distinct icons for different task actions**:
  - **View & Claim** (open tasks): User with checkmark icon
  - **Continue** (in-progress tasks): Play/arrow icon
  - **View** (completed tasks): Eye icon
  - **Delete** (admin only): Trash icon
- All icons maintain grey color scheme with tooltips for clarity

#### Product Roadmap
- **Created `docs/ROADMAP.md`** with 18 potential enhancements
  - Organized by: High-Impact Features, Analytics, UX, Developer/Admin, Quick Wins
  - Includes priority levels, effort estimates, and technical considerations
  - Top 3 priorities identified: User Authentication, Task Notifications, Global Search
  - Checkbox tracking for sub-features

#### Enhanced Task Statistics (ROADMAP Task #18) ⭐
- **Dashboard enhancements** with comprehensive task analytics
  - Tasks completed this week/month
  - Average, min, max task completion times
  - Overdue tasks count and highlighting
  - Tasks by type breakdown with visual progress bars
  - Human-readable duration formatting (s/m/h)
- **6 new Prometheus metrics** for monitoring and alerting
  - `realtyiq_workflow_tasks_completed_weekly` - 7-day completion count
  - `realtyiq_workflow_tasks_completed_monthly` - 30-day completion count
  - `realtyiq_workflow_tasks_overdue` - Past-due task count
  - `realtyiq_workflow_task_completion_duration_seconds` - Time-to-complete histogram
  - `realtyiq_workflow_tasks_by_type` - Distribution by task type
- **New dashboard section**: "Task Statistics" with detailed breakdown
  - Color-coded status indicators (open=blue, in-progress=orange, completed=green, overdue=red)
  - Task type icons (🔐 Approval, 👁️ Review, 📝 Data Collection, ✓ Verification)
  - Performance insights for optimization
- **Performance optimized** queries using indexed fields
- **Documentation**: Created implementation guide at `docs/developer-guide/implementation/TASK_STATISTICS_ENHANCEMENT.md`

### Fixed
- **Agent selection in chat page** now properly uses query parameter
  - Fixed: Chat page always selected default agent, ignoring `?agent=` parameter
  - Now correctly selects agent from URL when navigating from agent detail page
  - "New Chat with [Agent Name]" buttons now work as expected
  - Falls back to default agent only when no query parameter present

### Changed
- Updated agents list page to show action menu for all users (previously admin-only)
- Improved visual consistency across task management interfaces

---

## [0.2.0] - 2026-03-02

### Added - Workflow & Task Management with User Tracking

#### Comprehensive Test Suite
- **8 automated tests** for complete workflow lifecycle
- Test file: `agent_ui/agent_app/tests/test_workflow_commands.py`
- Tests: workflow list, execution, task claim/submit/delete, user filtering
- All tests passing: `Ran 8 tests in 33.826s - OK`

#### Enhanced Commands
- `/workflow runs` - View your workflow runs
- `/workflow runs all` - View all users' runs (admin only)
- `/workflow runs user <id>` - Filter by specific user (admin only)
- `/task list all` - Show all tasks including completed
- `/task delete <task_id>` - Delete completed/cancelled tasks

#### User Tracking Enhancement
- Added `completed_by_user_id` field to `HumanTask` model
- Migration: `0023_add_completed_by_user_id.py`
- Complete audit trail: tracks who claimed AND who completed tasks
- Updated all submission endpoints to record completing user

#### Bug Fixes
- Fixed `HumanTask.STATUS_PENDING` → `STATUS_OPEN` (correct constant)
- Fixed `task.claimed_by_user_id` → `task.assigned_to_user_id` (correct field)
- Fixed `task.response_data` → `task.output_data` (correct field)
- Task claim now properly sets status to `IN_PROGRESS`

#### Documentation Organization & Navbar Integration ⭐ MAJOR UPDATE

**Phase 1: Topic-Based Organization**
- **Project Root**: Cleaned from 10 files → 2 files (80% reduction)
- **Workflows Directory**: Organized from 17 files → 2 files + subdirs (88% reduction)
- **Docs Directory**: Reorganized from 65 files → 4 files + 10 topics (94% reduction)
- **Total Impact**: 92 scattered files → 8 essential files + 13 organized subdirectories

**Phase 2: User vs Developer Organization** ⭐ NEW
Reorganized from topic-based → audience-based structure for clarity:

- **User Guide** (`docs/user-guide/`) - 👤 How to USE the system (17 docs)
  - `workflow_management/` - Execute workflows and manage tasks
  - `features/` - How to use RAG, session context, etc.
  - `COMMANDS.md` - All slash commands
  - `TROUBLESHOOTING.md` - Common user issues

- **Developer Guide** (`docs/developer-guide/`) - 🔧 How to BUILD & EXTEND (69 docs)
  - `section508/` - Accessibility implementation and compliance
  - `setup/` - Development environment and infrastructure
  - `testing/` - Test strategy and execution (92 tests)
  - `observability/` - Monitoring, tracing, metrics, logging
  - `caching/` - Redis architecture and LLM caching
  - `reference/` - API and tool documentation
  - `implementation/` - Implementation details
  - `implementation_history/` - Historical development notes

**UI Integration & Design**:
- Added collapsible "Docs" section to left navbar
- **Collapsible "For Users" and "For Developers" subsections** with state persistence
- Created `docs_view()` function with security, markdown rendering, Mermaid support
- Added URL route: `docs/<path:path>`
- **Professional doc template with modern design**:
  - Clean header without icon clutter
  - Minimal text-based buttons (← Back, ↑ Back to Top)
  - Gradient divider between header and content
  - Beautiful typography with 1.75 line height
  - Dark gradient code blocks with colorful top border
  - Warm yellow gradient for inline code
  - Rounded tables with hover effects
  - Fixed HTML entity decoding (& instead of &amp;)
- All 92 docs accessible from UI with working internal links
- Clear audience targeting for better user experience

### Changed
- Updated `README.md` with new documentation structure
- Updated `docs/README.md` with workflow management section
- Server auto-reloads with updated commands

---

## [0.1.0] - 2026-02-21

### Added - Section 508 Accessibility Implementation

#### Core Features
- **Section 508 Toggle Mode** - System-wide toggle with user overrides
  - Environment variable: `SECTION_508_MODE` (default: false)
  - Per-user preference in database (nullable, uses env default)
  - Command: `/settings 508 <on|off>`
  - Settings UI toggle switch
  - Context processor makes status available to all templates

#### Accessibility Enhancements
- **Enhanced UI** when Section 508 mode is ON:
  - Larger base font (18px, up from 16px)
  - Increased line height (1.6, up from 1.5)
  - Enhanced focus indicators (3px solid outline with 2px offset)
  - Minimum touch targets (44x44px for all interactive elements)
  - Screen reader optimizations (ARIA live regions)
  - Better keyboard navigation (scroll-margin-top: 80px)

#### Text-to-Speech (TTS) Integration
- **On-Prem TTS** using Piper service (Docker):
  - Automatic audio generation for assistant responses
  - Background synthesis (non-blocking, 2-10s)
  - MP3 format for Safari compatibility
  - Native HTML5 audio controls (Play/Pause/Seek/Volume)
  - No autoplay (WCAG 2.1 compliant)
  - User-controlled playback
  - 24-hour audio caching
  - Graceful degradation if Piper unavailable

#### API Endpoints
- `GET /api/section508/` - Get Section 508 status
- `POST /api/section508/` - Update Section 508 preference
- `GET /api/messages/{id}/audio/` - Poll for TTS audio URL

#### Database Changes
- Added `UserPreference.section_508_enabled` (BooleanField, nullable)
- Added `ChatMessage.audio_url` (CharField, 512 max, nullable)
- Migrations: 0013, 0014, 0015

#### Frontend Components
- **New Files:**
  - `static/js/section508.js` - Section 508 mode management
  - Audio player rendering and polling logic in `chat.js`
  - Audio player styles in `theme.css`

- **Modified Files:**
  - `templates/base.html` - Initialize SECTION_508_ENABLED
  - `templates/settings.html` - Section 508 toggle UI
  - `static/js/chat.js` - Audio player integration
  - `static/css/theme.css` - Accessibility styles

#### Backend Components
- **New Files:**
  - `agent_app/tts_client.py` - TTS integration client
  - `agent_app/tests/test_section508.py` - Settings tests (7)
  - `agent_app/tests/test_tts_integration.py` - TTS tests (11)

- **Modified Files:**
  - `agent_app/views.py` - TTS trigger, section_508_api, message_audio_api
  - `agent_app/context_processors.py` - section_508_settings()
  - `agent_app/commands/settings.py` - /settings 508 handler
  - `agent_app/commands/help.py` - Updated help text
  - `agent_app/commands/context.py` - Fixed session_key bug

#### Documentation
- **New Files:**
  - `docs/SECTION_508_SUMMARY.md` - Quick start guide
  - `docs/SECTION_508_IMPLEMENTATION.md` - Complete technical guide
  - `docs/SECTION_508.md` - Features and configuration
  - `docs/TTS_INTEGRATION.md` - TTS architecture details

- **Updated Files:**
  - `docs/COMMANDS.md` - Added /settings 508 documentation
  - `README.md` - Added Section 508 features and config

#### Tests
- **Total: 92 tests passing** (up from 81)
  - 7 new Section 508 settings tests
  - 11 new TTS integration tests
  - All existing tests still passing

#### Environment Configuration
```bash
# New .env variables
SECTION_508_MODE=false
PIPER_BASE_URL=http://localhost:8088
PIPER_DEFAULT_VOICE=en_US-lessac-medium
```

### Fixed
- Bug in `/context` command handler (was using wrong parameter type)
- SKILLS.md files already existed from previous implementation

### Compliance
- ✅ WCAG 2.1 Level AA compliant
- ✅ Section 508 §1194.22 compliant
- ✅ All functionality keyboard-accessible
- ✅ Screen reader compatible
- ✅ No autoplay (user-controlled audio)
- ✅ Text always primary (audio supplementary)

### Performance
- **Text responses:** No impact (same speed as before)
- **Audio generation:** 2-10s in background (non-blocking)
- **Test suite:** 92 tests in 31s (parallel execution)

---

## Previous Versions

See git history for changes prior to v0.1.0.
