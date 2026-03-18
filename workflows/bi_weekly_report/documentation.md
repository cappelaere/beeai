# BI Weekly Report Workflow – Documentation

This document describes the BI Weekly Report workflow: purpose, diagram, and step-by-step behavior.

## Workflow Overview

The **BI Weekly Report** workflow produces a single executive brief for the BidHom property portfolio over a user-defined date range. It runs nine steps in sequence: load active properties, aggregate metrics, identify top performers and underperformers, build the conversion funnel, compute week-over-week trend, snapshot auction readiness, generate recommended actions, and assemble the final Markdown brief.

**Inputs:** `start_date`, `end_date` (YYYY-MM-DD, required)  
**Outputs:** Executive brief (Markdown) plus structured data (totals, top performers, underperformers, funnel, trend, auction readiness, recommended actions).

## Step Descriptions

### 1. Get active properties

- **Purpose:** Load the list of active listings that will be included in the report.
- **Action:** Calls the property API (e.g. `front-property-listing`) with paging; collects property IDs and optional full records.
- **Output:** `active_property_ids`, `active_properties`.

### 2. Collect portfolio metrics

- **Purpose:** Aggregate metrics for the report period for every active property.
- **Action:** For each active property ID, calls the metrics summary endpoint with `start` and `end`; sums views, unique_sessions, brochure_downloads, ifb_downloads, bidder_registrations, subscriber_registrations, photo_clicks across the portfolio.
- **Output:** `portfolio_metrics` (per-property), `portfolio_totals` (aggregate).

### 3. Identify top performing properties

- **Purpose:** Rank properties by engagement for the “top performers” section.
- **Action:** Calls the top-properties API for the same date range (e.g. metric=views, limit=10).
- **Output:** `top_performers`.

### 4. Identify properties needing attention

- **Purpose:** List properties with high interest but low bidder registrations.
- **Action:** Calls the underperforming API for the same date range (e.g. min_views=50, max_bidder_registrations=2).
- **Output:** `properties_needing_attention`.

### 5. Conversion funnel analysis

- **Purpose:** Show portfolio-level funnel and conversion rates.
- **Action:** Uses `portfolio_totals` to build views → brochure_downloads → ifb_downloads → bidder_registrations and computes conversion percentages (e.g. brochure/views, ifb/brochure, bidders/ifb).
- **Output:** `funnel` (counts and conversion rates).

### 6. Week-over-week trend analysis

- **Purpose:** Compare this period to the prior period of the same length.
- **Action:** Computes prior period as [prior_start, prior_end] where prior_end = start_date - 1 day and the length matches (end_date - start_date + 1). Fetches aggregated metrics for both windows (e.g. for a sample of properties or portfolio-level) and computes percentage change for key metrics.
- **Output:** `week_over_week_trend` (this period, prior period, pct_change).

### 7. Auction readiness snapshot

- **Purpose:** Flag properties with upcoming auctions as on track or needing attention.
- **Action:** For active properties, fetches property detail (for auction/bidding end date) and metrics summary; for those with auctions in the near term (e.g. 7–14 days), applies simple rules (e.g. views ≥ 20 and bidder_registrations ≥ 1 → on_track, else needs_attention).
- **Output:** `auction_readiness` (property_id, bidding_end, views, bidder_registrations, readiness).

### 8. Generate recommended actions

- **Purpose:** Turn step outputs into a short list of suggested next steps.
- **Action:** Rule-based: e.g. “Follow up on underperformers: [IDs]”, “Highlight top performers: [IDs]”, “Outreach for low-readiness auctions: [IDs]”. If none apply, “No specific actions; monitor portfolio metrics.”
- **Output:** `recommended_actions` (list of strings).

### 9. Produce executive brief output

- **Purpose:** Assemble the final deliverable.
- **Action:** Builds a single Markdown string from: headline (date range), active property count, portfolio totals, conversion funnel, week-over-week trend, top performers list, properties needing attention list, auction readiness list, and recommended actions.
- **Output:** `executive_brief_markdown`. Step returns **End**; workflow completes.

## API Dependencies

- **Property listing:** POST to front-property-listing (or equivalent) for active properties.
- **Property detail:** POST to property-detail for auction/bidding dates.
- **Metrics summary:** GET properties/{id}/summary?start=&end=
- **Top properties:** GET top-properties?start=&end=&metric=&limit=
- **Underperforming:** GET underperforming?start=&end=&min_views=&max_bidder_registrations=&limit=

All use the same base URL and token (API_URL, AUTH_TOKEN).

## Run Result (UI / API)

On successful completion, the workflow run stores:

- **executive_brief_markdown** – Full brief text (Markdown)
- **portfolio_totals** – Aggregate metrics
- **top_performers** – List of {property_id, views, …}
- **properties_needing_attention** – List of underperformers
- **funnel** – Funnel counts and conversion rates
- **week_over_week_trend** – This/prior totals and % change
- **auction_readiness** – List of {property_id, readiness, …}
- **recommended_actions** – List of action strings
- **workflow_steps** – List of step names executed

## Related Documentation

- [README.md](./README.md) – Quick reference and file list
- [USER_STORY.md](./USER_STORY.md) – User story and acceptance criteria
- [metadata.yaml](./metadata.yaml) – Workflow registration and input schema
