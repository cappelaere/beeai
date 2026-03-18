# User Story: BI Weekly Report Workflow

## Story ID

**US-003** – BI Weekly Report (Executive Brief)

## As a...

**Program Manager / Leadership / Real Estate Specialist**

## I want to...

Run a single workflow that produces a weekly executive brief for the BidHom property portfolio over a chosen date range (start date and end date)

## So that...

I get one consolidated report with portfolio totals, top performers, properties needing attention, conversion funnel, week-over-week trend, auction readiness, and recommended actions—without running multiple BI queries or copying data between tools

---

## Business Value

### Primary Benefits

- **One-click brief** – Single run produces the full executive brief for a date range.
- **Consistent structure** – Same sections and metrics every time (totals, funnel, trend, top/underperformers, readiness, actions).
- **Date range flexibility** – Use any start/end (e.g. last 7 days, custom week, or month).
- **Actionable output** – Recommended actions derived from underperformers, top performers, and auction readiness.
- **Audit trail** – Workflow run stores input (start_date, end_date) and full output for later reference.

### Success Metrics

- Workflow completes in under 60 seconds for typical portfolio size.
- Brief includes all 9 step outputs (totals, funnel, trend, top performers, underperformers, readiness, actions, markdown).
- Run detail page and API expose the same structured result.

---

## Acceptance Criteria

### Functional Requirements

#### 1. Input: start_date and end_date

- **Given** a user runs the BI Weekly Report workflow  
- **When** providing inputs  
- **Then** the workflow must accept:
  - **start_date** (required): YYYY-MM-DD, start of report period
  - **end_date** (required): YYYY-MM-DD, end of report period  
- And use this range for all metrics (portfolio, top, underperforming, trend).

#### 2. Get active properties

- **Given** valid start_date and end_date  
- **When** step 1 runs  
- **Then** the system must call the property API (e.g. front-property-listing), collect active property IDs, and store them for downstream steps.

#### 3. Collect portfolio metrics

- **Given** a list of active property IDs  
- **When** step 2 runs  
- **Then** the system must:
  - Call the metrics summary API per property for [start_date, end_date]
  - Aggregate totals (views, unique_sessions, brochure_downloads, ifb_downloads, bidder_registrations, subscriber_registrations, photo_clicks)
  - Store per-property metrics and portfolio_totals.

#### 4. Top performers and underperformers

- **Given** the same date range  
- **When** steps 3 and 4 run  
- **Then** the system must:
  - Call top-properties (e.g. by views, limit 10) for the date range
  - Call underperforming (e.g. min_views=50, max_bidder_registrations=2) for the date range
  - Store results as top_performers and properties_needing_attention.

#### 5. Conversion funnel and week-over-week trend

- **Given** portfolio_totals and date range  
- **When** steps 5 and 6 run  
- **Then** the system must:
  - Build funnel (views → brochure → IFB → bidders) and compute conversion rates
  - Compute prior period (same length ending day before start_date)
  - Compare this period vs prior period and compute % change for key metrics.

#### 6. Auction readiness and recommended actions

- **Given** active properties and their details  
- **When** steps 7 and 8 run  
- **Then** the system must:
  - Identify properties with auction date in the near term; fetch summary metrics; flag on_track / needs_attention
  - Generate recommended actions (e.g. follow up on underperformers, highlight top performers, outreach for low-readiness auctions).

#### 7. Executive brief output

- **Given** all prior step outputs  
- **When** step 9 runs  
- **Then** the system must produce a single executive_brief_markdown containing: headline, portfolio totals, funnel, week-over-week trend, top performers, properties needing attention, auction readiness, and recommended actions.

#### 8. Run result and UI

- **Given** the workflow completes successfully  
- **When** the user views the run  
- **Then** the run must expose: executive_brief_markdown, portfolio_totals, top_performers, properties_needing_attention, funnel, week_over_week_trend, auction_readiness, recommended_actions, workflow_steps.

### Non-Functional Requirements

- **Performance:** Target end-to-end time 30–60 seconds for typical portfolio.
- **Reliability:** Use asyncio.to_thread for sync API calls; validate start_date/end_date.
- **Integration:** Use same API base (API_URL, AUTH_TOKEN) as BI tools.

---

## User Flow

### Happy Path

1. User opens workflow list and selects “BI Weekly Report” (#3).
2. User enters start_date and end_date (e.g. 2025-02-01, 2025-02-07).
3. User starts the workflow (UI or Flo).
4. Workflow runs 9 steps; user sees step progress (optional).
5. Run completes; user sees executive brief and structured data on run detail page.
6. User copies or shares the brief or uses recommended actions.

---

## Technical Notes

- **Workflow id:** `bi_weekly_report`
- **Category:** BI
- **Executor:** `BiWeeklyReportWorkflow` in `workflows.bi_weekly_report`
- **API client:** `workflows.bi_weekly_report.api_client` (sync HTTP; used via asyncio.to_thread)
- **Metrics API:** Supports start/end for summary, top-properties, and underperforming.

---

## Definition of Done

- [x] metadata.yaml with start_date and end_date required
- [x] diagram.mmd vertical with Start and End
- [x] All 9 steps implemented and wired
- [x] Consumer maps bi_weekly_report result to result_dict
- [x] README, USER_STORY, and documentation.md added
