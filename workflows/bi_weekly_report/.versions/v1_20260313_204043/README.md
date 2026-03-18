# BI Weekly Report Workflow

## Overview

Produces a weekly executive brief for the BidHom property portfolio. The workflow fetches active properties, aggregates metrics (views, brochure/IFB downloads, bidder and subscriber registrations), identifies top performers and properties needing attention, analyzes the conversion funnel and week-over-week trends, and summarizes auction readiness. It then generates recommended actions and a single executive brief (narrative + tables) suitable for leadership.

## Files

- **`USER_STORY.md`** – User story with business value and acceptance criteria
- **`workflow.py`** – Main workflow implementation (`BiWeeklyReportWorkflow` class)
- **`api_client.py`** – Sync HTTP client for metrics and property API
- **`metadata.yaml`** – Workflow configuration: name, icon, input schema (YAML)
- **`diagram.mmd`** – Mermaid diagram (vertical, Start → 9 steps → End)
- **`documentation.md`** – Detailed documentation with diagram and step descriptions
- **`__init__.py`** – Package init, exports workflow classes
- **`README.md`** – This file

## Quick Start

### Input Schema

Required fields:

- **`start_date`** (string, YYYY-MM-DD) – Start of the report period (UTC)
- **`end_date`** (string, YYYY-MM-DD) – End of the report period (UTC)

### Running the Workflow

- **UI:** Run workflow #3 (BI Weekly Report) with JSON body:  
  `{"start_date": "2025-02-01", "end_date": "2025-02-07"}`
- **Flo:** e.g. “Run workflow 3 for start date 2025-02-01 and end date 2025-02-07”

### Output

The run produces:

- **executive_brief_markdown** – Full brief (headline, totals, funnel, trend, top/underperformers, auction readiness, recommended actions)
- **portfolio_totals** – Aggregate views, sessions, brochure/IFB, bidders, etc.
- **top_performers** – Top properties by views (or selected metric)
- **properties_needing_attention** – Underperformers (high interest, low bidders)
- **funnel** – Conversion funnel and rates
- **week_over_week_trend** – This period vs prior period % change
- **auction_readiness** – Upcoming auctions with on_track / needs_attention
- **recommended_actions** – List of suggested next steps

## Steps (9)

1. **Get active properties** – Load active listings from the property API.
2. **Collect portfolio metrics** – Fetch metrics per property for [start_date, end_date]; aggregate totals.
3. **Identify top performers** – Rank by views (or metric), top N.
4. **Identify properties needing attention** – Underperforming endpoint (high views, low bidders).
5. **Conversion funnel analysis** – Portfolio funnel and conversion rates.
6. **Week-over-week trend** – Compare to prior period of same length; % change.
7. **Auction readiness snapshot** – Properties with auctions soon; flag on track / needs attention.
8. **Generate recommended actions** – Rule-based actions from underperformers, top performers, readiness.
9. **Produce executive brief** – Assemble Markdown brief and set as output.

## Technical Details

- **Execution time:** ~30–60 seconds
- **Category:** BI
- **Workflow number:** #3
- **System name:** `bi_weekly_report`
- **Dependencies:** API_URL, AUTH_TOKEN (metrics and property API)

## Documentation

For the full diagram and step-by-step description, see [documentation.md](./documentation.md).
