# RealtyIQ Product Roadmap

This document outlines potential features and improvements for the RealtyIQ platform, organized by priority and impact.

---

## High-Impact, User-Facing Features

### 1. User Authentication & Multi-User Support
**Status:** Not Started  
**Priority:** High  
**Effort:** Large

Currently, user_id is set via environment variable with no login system.

**Proposed Features:**
- [ ] Proper authentication system (login/logout)
- [ ] User profiles with names, emails, roles
- [ ] Per-user session history and preferences
- [ ] Team/organization support
- [ ] Role-based access control (RBAC)
- [ ] User management admin interface

**Why:** Foundation for proper multi-user deployment. Currently tracking user_id but no way to manage users.

**Technical Considerations:**
- Django authentication system vs. external OAuth providers
- User model design
- Migration strategy for existing user_id references
- Session management

---

### 2. Task Notifications & Alerts
**Status:** Implemented (0.3.5)  
**Priority:** High  
**Effort:** Medium

In-app notification center with bell icon in the top bar.

**Implemented:**
- [x] Task assignment notifications (when you claim a task: "Task assigned to you")
- [x] Task deadline/expiration warnings (due within 24h; created when loading notifications)
- [x] Workflow completion/failure alerts (when a run completes or fails)
- [x] In-app notification center (bell dropdown: list, mark read, mark all read, link to My Tasks)
- [ ] Browser push notifications
- [ ] Email notifications (optional)
- [ ] Notification preferences per user

**Why:** Users no longer need to poll `/workflows/tasks/` to discover new work; notifications surface in the header.

**Technical notes:** Notification model; create on task claim, workflow complete/fail, and task cancel; due-soon created on demand in list API. See CHANGELOG 0.3.5.

---

### 3. Global Search
**Status:** Not Started  
**Priority:** High  
**Effort:** Medium

No search functionality across the platform.

**Proposed Features:**
- [ ] Search chat history (find previous conversations)
- [ ] Search workflow runs (by input parameters or results)
- [ ] Search tasks (by title, type, workflow, status)
- [ ] Search documents (beyond RAG semantic search)
- [ ] Unified search bar in navigation
- [ ] Search filters and advanced query syntax
- [ ] Search result relevance ranking
- [ ] Recent searches

**Why:** As data grows, finding specific items becomes increasingly difficult.

**Technical Considerations:**
- Full-text search implementation (PostgreSQL, Elasticsearch)
- Search indexing strategy
- Query performance optimization
- Faceted search for filtering

---

### 4. Bulk Task Operations
**Status:** Not Started  
**Priority:** Medium  
**Effort:** Small

Tasks page shows individual tasks but no batch operations.

**Proposed Features:**
- [ ] Multi-select checkboxes for tasks
- [ ] Batch claim tasks
- [ ] Batch reassign tasks
- [ ] Batch cancel/delete tasks
- [ ] Export tasks to CSV/Excel
- [ ] Advanced filtering (multiple criteria simultaneously)
- [ ] Saved filter presets

**Why:** Managing many tasks requires repetitive individual actions.

**Technical Considerations:**
- Bulk update API endpoints
- Transaction handling for batch operations
- UI state management for selection
- Export format options

---

## Analytics & Reporting

### 5. Enhanced Dashboard Analytics
**Status:** Not Started  
**Priority:** Medium  
**Effort:** Large

Current dashboard shows basic metrics only.

**Proposed Features:**
- [ ] Time-series charts (usage over time)
- [ ] Agent usage breakdown (which agents are most popular)
- [ ] Workflow success/failure trends
- [ ] Token usage by agent/user/time period
- [ ] Cost tracking and projections
- [ ] Peak usage time analysis
- [ ] Interactive charts with drill-down
- [ ] Custom date range selection
- [ ] Export analytics to PDF/CSV

**Why:** Better understanding of system usage patterns and optimization opportunities.

**Technical Considerations:**
- Chart library selection (Chart.js, D3.js, Plotly)
- Data aggregation queries
- Caching strategy for analytics
- Real-time vs. batch processing

---

### 6. Workflow Analytics Page
**Status:** Not Started  
**Priority:** Medium  
**Effort:** Medium

Dedicated page for workflow performance insights.

**Proposed Features:**
- [ ] Average completion times per workflow
- [ ] Success rate trends over time
- [ ] Common failure points identification
- [ ] Task bottleneck analysis (which tasks take longest)
- [ ] User efficiency metrics
- [ ] Workflow comparison tool
- [ ] Optimization recommendations

**Why:** Optimize workflows based on real performance data rather than guesswork.

**Technical Considerations:**
- Performance metrics calculation
- Historical data retention policy
- Visualization design
- Automated insights generation

---

### 7. Export Capabilities
**Status:** Partial (Chat export exists)  
**Priority:** Medium  
**Effort:** Small

Expand beyond current chat export functionality.

**Proposed Features:**
- [ ] Export workflow run results to PDF
- [ ] Export workflow run results to CSV
- [ ] Export task lists with applied filters
- [ ] Batch export multiple chat sessions
- [ ] Scheduled/automated reports
- [ ] Custom export templates
- [ ] Email delivery of exports

**Why:** Users need to share results with stakeholders outside the system.

**Technical Considerations:**
- PDF generation library
- Template engine for custom exports
- Background job processing for large exports
- Export queue management

---

### 8. Property Metrics Events
**Status:** Not Started  
**Priority:** Medium  
**Effort:** Medium

Store daily user events on property pages and roll them up into an analytics table for business intelligence.

**Proposed Features:**
- [ ] Event table: store user events on property pages (e.g. view, click, time-on-page, workflow started)
- [ ] Event schema: property identifier, user/session, event type, timestamp (UTC), optional payload
- [ ] Daily roll-up table: pre-aggregated metrics per property per day (views, unique users, actions, etc.)
- [ ] Scheduled job (e.g. nightly) to aggregate raw events into daily roll-ups
- [ ] Retention policy for raw events (e.g. keep N days) with long-term storage of roll-ups only
- [ ] API or export for BI tools (query roll-ups by date range, property, segment)
- [ ] Optional: dashboard or report views on property engagement trends

**Why:** Enables business intelligence and product analytics (which properties get attention, user engagement patterns) without querying high-volume event data at report time.

**Technical Considerations:**
- Event ingestion: synchronous write vs. queue (e.g. Celery, Kafka) for high throughput
- Database: event table indexing (property_id, event_date, user_id); roll-up table keyed by (property_id, date)
- Idempotent roll-up job; handling late-arriving events (e.g. next-day correction window)
- Privacy and PII: avoid storing identifying data in events if required by policy
- UTC for all timestamps; date boundaries for roll-ups (e.g. by UTC day or configurable timezone)

---

## User Experience Enhancements

### 9. Chat History Search & Filtering
**Status:** Not Started  
**Priority:** Medium  
**Effort:** Small

Session sidebar lacks search and organization features.

**Proposed Features:**
- [ ] Search sessions by content/keywords
- [ ] Filter by agent type
- [ ] Filter by date range
- [ ] Tag/label sessions for organization
- [ ] Session folders/categories
- [ ] Pin important sessions to top
- [ ] Archive old sessions
- [ ] Bulk delete sessions

**Why:** Finding old conversations becomes difficult as chat history grows.

**Technical Considerations:**
- Search index for chat content
- Tag/folder data model
- UI for session organization
- Performance with large session counts

---

### 10. Workflow Templates & Cloning
**Status:** Not Started  
**Priority:** Medium  
**Effort:** Medium

Reusing workflow configurations is currently manual.

**Proposed Features:**
- [ ] Save workflow runs as templates
- [ ] Clone existing runs with modified inputs
- [ ] Template library/marketplace
- [ ] "Run again with different inputs" quick action
- [ ] Template sharing between users
- [ ] Template versioning
- [ ] Pre-populate form with previous values

**Why:** Repeated workflow patterns require tedious manual re-entry.

**Technical Considerations:**
- Template storage format
- Template sharing/permissions model
- Parameter validation for templates
- Template discovery UX

---

### 11. Task Assignment & Delegation
**Status:** Not Started  
**Priority:** Medium  
**Effort:** Medium

Tasks show assigned user but lack collaboration features.

**Proposed Features:**
- [ ] Reassign tasks to other users
- [ ] Add task watchers/collaborators
- [ ] Task priority levels (low/medium/high/urgent)
- [ ] Task comments/discussion threads
- [ ] Task history/activity log
- [ ] @mention notifications in comments
- [ ] Task attachments/supporting documents

**Why:** Team collaboration on tasks is currently very limited.

**Technical Considerations:**
- User picker/autocomplete UI
- Comment system implementation
- Activity feed design
- Permission model for task access

---

## Developer/Admin Features

### 12. Audit Trail & Activity Log
**Status:** Not Started  
**Priority:** Medium  
**Effort:** Medium

No tracking of system changes and user actions.

**Proposed Features:**
- [ ] Track configuration changes (agents, workflows)
- [ ] Track task status changes
- [ ] Track user actions (login, exports, etc.)
- [ ] Track API usage
- [ ] Audit log viewer with search/filter
- [ ] Export audit logs
- [ ] Compliance reporting
- [ ] Retention policy configuration

**Why:** Accountability, debugging, and compliance requirements.

**Technical Considerations:**
- Audit log storage strategy
- What to log vs. privacy concerns
- Log rotation and archival
- Query performance on large logs

---

### 13. API Documentation Page
**Status:** Not Started  
**Priority:** Low  
**Effort:** Small

API endpoints exist but are undocumented for external use.

**Proposed Features:**
- [ ] Interactive API documentation (OpenAPI/Swagger)
- [ ] All REST endpoints documented
- [ ] Request/response examples
- [ ] Authentication requirements
- [ ] Rate limits (if implemented)
- [ ] Code samples in multiple languages
- [ ] Try-it-out functionality
- [ ] Webhook documentation

**Why:** Enable external integrations and third-party development.

**Technical Considerations:**
- OpenAPI/Swagger spec generation
- Documentation hosting approach
- API versioning strategy
- Authentication documentation

---

### 14. Scheduled/Automated Workflows
**Status:** Partially Implemented  
**Priority:** High  
**Effort:** Large

Workflows can be scheduled to run at a specific time or on a recurring interval.

**Implemented:**
- [x] Schedule workflows to run at a specific time (once)
- [x] Recurring workflows (interval in minutes)
- [x] Run name and input variables per schedule
- [x] /schedule command: list, add, show, edit, delete
- [x] UI: schedule list, create/edit form, Schedule button on workflow detail
- [x] API: list, create, get, update, delete, run now
- [x] DB-backed schedule + management command `run_scheduled_workflows` (run via cron every 1–5 minutes)

**Proposed (not yet):**
- [ ] Event-based workflow triggers
- [ ] Workflow queuing and prioritization
- [ ] Rate limiting and throttling
- [ ] Retry logic for failed runs
- [ ] Workflow dependencies (run A, then B)
- [ ] Conditional workflow execution

**Why:** Manual triggering limits automation potential for routine processes.

**Technical notes:** Run `python manage.py run_scheduled_workflows` every 1–5 minutes (cron or systemd timer). See also `expire_tasks` for a similar pattern.

---

### 15. Workflow Version Control
**Status:** ✅ Completed  
**Priority:** Medium  
**Effort:** Medium

Workflow definition history with folder-based snapshots and version management UI.

**Proposed Features:**
- [x] Track workflow definition changes over time
- [x] Rollback to previous versions (restore creates new version)
- [x] Compare versions (diff view)
- [x] Tag stable releases
- [x] Version comments/changelog
- [ ] Branch/test environments for workflows
- [ ] Approval workflow for changes

**Why:** No way to track or revert workflow modifications made in studio.

**Technical Considerations:**
- Version storage format ✓ (folder-based `.versions/vN_timestamp/`)
- Diff algorithm for workflow definitions ✓ (unified diff)
- Migration path for existing workflows ✓ (`create_initial_versions` management command)
- Version management UI ✓

**Implementation Details:**
- `WorkflowVersion` model; `VersionManager` (create_version, restore_version, compare_versions, tag_version, get_version_files, changelog)
- Edit page: "Save as new version" with comment/tag; versions list page with restore, compare, view files
- Version compare page (unified diff per file); View Files modal (tabs for metadata.yaml, workflow.py, diagram.mmd, README.md)
- APIs: save (create version), restore, tag, version files (GET)
- Per-workflow CHANGELOG.md generation

---

## Quick Wins (Low Effort, High Value)

### 16. Keyboard Shortcuts
**Status:** Not Started  
**Priority:** Low  
**Effort:** Small

Add shortcuts for common actions.

**Proposed Features:**
- [ ] `Ctrl+K` / `Cmd+K` for command palette
- [ ] `Ctrl+N` / `Cmd+N` for new chat
- [ ] `Ctrl+/` / `Cmd+/` for global search
- [ ] `Esc` to close modals/dialogs
- [ ] Arrow keys for navigation in lists
- [ ] Keyboard shortcut help modal (`?`)
- [ ] Customizable shortcuts

**Why:** Power users appreciate faster navigation and reduced mouse usage.

**Technical Considerations:**
- Keyboard event handling
- Shortcut conflicts with browser defaults
- Accessibility considerations
- Shortcut customization storage

---

### 17. Dark Mode Improvements
**Status:** Partial (Theme switching exists)  
**Priority:** Low  
**Effort:** Small

Theme switching exists but may need refinement.

**Proposed Features:**
- [ ] Ensure all pages respect dark mode
- [ ] Syntax highlighting respects theme
- [ ] High contrast mode option
- [ ] Custom theme colors
- [ ] Theme preview before applying
- [ ] Auto-switch based on time of day

**Why:** Complete dark mode coverage improves user experience.

**Technical Considerations:**
- CSS variable consistency
- Chart/visualization theming
- Code block syntax highlighting themes
- Image/icon contrast in dark mode

---

### 18. Favorite Workflows
**Status:** ✅ Completed (Partial - Features 1-2)  
**Priority:** Low  
**Effort:** Small

Like favorite cards, add workflow favorites.

**Proposed Features:**
- [x] Star/favorite workflows for quick access
- [x] Favorite workflows panel on chat homepage (collapsible)
- [ ] Pinned workflows in navigation
- [ ] Quick-run favorites from any page
- [ ] Organize favorites into folders

**Why:** Users likely run the same workflows repeatedly.

**Technical Considerations:**
- Favorites storage (user preferences) ✓
- UI placement for favorites ✓
- Sync with other quick-access features

**Implementation Details:**
- Added `favorite_workflows` JSON field to UserPreference model
- Created `/api/workflows/<workflow_id>/favorite/` API endpoint
- Added star icons to workflow cards in workflows list
- Implemented collapsible "Favorite Workflows" panel on chat homepage
- State persists via localStorage for collapsed state

---

### 19. Task Statistics on Dashboard
**Status:** ✅ Completed  
**Priority:** Low  
**Effort:** Small

Expand task metrics on dashboard.

**Proposed Features:**
- [x] Tasks completed this week/month
- [x] Average task completion time
- [x] Tasks by type breakdown chart
- [x] Overdue tasks count and list
- [ ] Tasks completed by user (future enhancement)
- [ ] Task velocity trends (future enhancement)
- [ ] SLA compliance metrics (future enhancement)

**Why:** Dashboard shows basic task count but lacks trend analysis.

**Technical Considerations:**
- Aggregation queries for statistics ✓
- Date range selection (week/month implemented)
- Chart visualization (progress bars implemented)
- Performance optimization ✓

**Implementation Details:**
- Enhanced `_calculate_workflow_stats()` function in `admin.py`
- Added 6 new Prometheus metrics for task statistics
- New "Task Statistics" section on dashboard with:
  - Weekly/monthly completion counts
  - Average, min, max completion times
  - Overdue tasks count
  - Tasks by type breakdown with visual progress bars
- Metrics exported to Prometheus for monitoring and alerting

---

### 20. BI Agent for BidHom Metrics
**Status:** ✅ Completed  
**Priority:** Medium  
**Effort:** Medium

Agent that answers role-based questions about BidHom property performance using metrics and property APIs.

**Proposed Features:**
- [x] BI Agent registered in agents.yaml (agent id: `bi`)
- [x] Tools: property summary, daily series, top properties, underperforming (by views/IFB/brochure), properties-with-activity
- [x] Reuse: list_properties, get_property_detail, auction_bidders, property_registration_graph
- [x] Web search (DuckDuckGo) for benchmarks and regional context
- [x] Role-based instructions: Real Estate Specialists, Program Managers, Marketing/Outreach, Leadership
- [x] Support for 20 prompt types (property-level, conversion/readiness, portfolio, operational, executive)
- [x] Api: Token auth for metrics GET endpoints (staff or Token); underperforming by interest_metric; properties-with-activity endpoint
- [x] Tests: `agent_app.tests.test_bi_agent`; script `scripts/test_bi_agent.py` for one-shot prompts
- [x] SKILLS.md and agents/bi/__init__.py

**Why:** Enables stakeholders to ask natural-language questions about listing performance, underperformers, and portfolio trends without writing reports by hand.

**Technical Considerations:**
- Metrics API (Api project) must be deployed with staff Token for BI tool calls
- Agent uses same AUTH_TOKEN as other agents; metrics read views accept Token or session staff
- Underperforming endpoint supports interest_metric=views|ifb_downloads|brochure_downloads for “high interest, low bidders”

**Implementation Details:**
- `agents/bi/agent.py` (BI_AGENT_CONFIG), `agents/bi/SKILLS.md`, `agents/bi/__init__.py`
- Tools: `get_metrics_property_summary`, `get_metrics_property_daily`, `get_metrics_top_properties`, `get_metrics_underperforming`, `get_metrics_properties_with_activity`
- Api: `api/metrics/` views use `@staff_or_token_required`; `GET underperforming?interest_metric=...`; `GET properties-with-activity`
- Run: `python run_agent.py --agent bi` or `python scripts/test_bi_agent.py "prompt"`

---

### 21. Property metrics for Prometheus (BI)
**Status:** Completed  
**Priority:** Medium  
**Effort:** Small–Medium

Expose property-related Prometheus metrics from **RealtyIQ only** (no Api monitoring). Metrics are for **business intelligence**: alerting and Grafana dashboards so RS, SDA, and Management can discuss property auctions and marketing efficiency.

**Proposed Features:**
- [x] RealtyIQ exposes portfolio-level gauges: `property_metrics_properties_with_activity_24h`, `_7d`, `property_metrics_funnel_last_7d`
- [x] RealtyIQ exposes per-property gauges (only for **active properties**): `property_metrics_num_viewers`, `property_metrics_num_bidders`, `property_metrics_num_subscribers` (and optionally brochure_downloads, ifb_downloads, unique_sessions) with label `property_id`
- [x] Data source: Api read APIs (`properties-with-activity`, `properties/<id>/summary`); RealtyIQ calls them on each scrape (every 5m)
- [x] Prometheus scrape job `realtyiq-property-metrics` targeting RealtyIQ with **scrape_interval: 5m**
- [x] Grafana dashboards: portfolio funnel, auction readiness, per-property viewers/bidders/subscribers; BI-oriented alerts
- [x] Seed data for testing: (1) CSV `property_metric_daily_seed_30d_10properties.csv` (30 days × 10 properties) for Api; (2) Grafana: same CSV via Infinity (Property metrics (CSV) dashboard)

**Why:** Enables BI alerting and visualization for property engagement and auction readiness without monitoring the Api (PostgreSQL) service.

**Technical Considerations:**
- Only **active properties** (from `properties-with-activity?days=7`) are included to bound cardinality
- Api is not scraped and has no `/metrics` endpoint for this; RealtyIQ fetches via existing read APIs
- See [Property metrics for Prometheus (observability doc)](developer-guide/observability/PROPERTY_METRICS_PROMETHEUS.md) for full plan

---

## Top 3 Priorities

Based on impact and foundational importance:

1. **User Authentication System** - Enables proper multi-user support, foundational for many other features
2. **Task Notifications** - Immediate productivity boost, ensures users don't miss important work
3. **Global Search** - Makes the system usable at scale as data accumulates

---

## Implementation Notes

### General Technical Considerations
- **Performance:** Consider caching strategies for all analytics features
- **Scalability:** Design for multi-tenant architecture from the start
- **Security:** Implement proper authorization checks for all new endpoints
- **Testing:** Maintain test coverage for new features
- **Documentation:** Update user documentation alongside feature development
- **Migration:** Plan data migration strategy for schema changes

### Feature Dependencies
- Many features depend on User Authentication being implemented first
- Notifications require real-time infrastructure (WebSockets)
- Analytics features benefit from time-series database or aggregation tables
- Search features may require dedicated search infrastructure

### Deployment Considerations
- Feature flags for gradual rollout
- Backward compatibility for API changes
- Database migration strategy
- Monitoring and alerting for new features

---

## How to Use This Document

- **Priority** indicates business/user value
- **Effort** is a rough estimate (Small: < 1 week, Medium: 1-3 weeks, Large: > 3 weeks)
- **Status** tracks implementation progress
- Check boxes ([ ]) track individual sub-features
- Update this document as features are completed or priorities change

---

*Last Updated: 2026-03-03* — Property metrics for Prometheus (BI) (#21) implemented (v0.3.4). BI Agent for BidHom Metrics (#20) marked completed (v0.3.3).
