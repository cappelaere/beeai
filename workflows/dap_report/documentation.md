# DAP Report Workflow – Documentation

This document describes the **DAP Report** workflow: purpose, diagram, and step-by-step behavior.

## Workflow Overview

The **DAP Report** workflow generates a Daily Activity Performance (DAP) report for a user-specified date. It retrieves DAP data via the GRES Agent, builds time-series data for trend analysis, runs a performance analysis, and flags any issues that require analyst attention (including optional analyst tasks and user toast notifications).

**Inputs:** `report_date` (required, YYYY-MM-DD). Optional: `user_id`, `include_comparison`, `lookback_days` (default 30, 1–365).

**Outputs:** Report data (DAP metrics, time-series, analysis summary, risk level, highlights, concerns, recommendations) and, when issues are detected, analyst tasks and a user toast notification.

## Step Descriptions

### 1. Retrieve data (`retrieve_data`)

- **Purpose:** Load Daily Activity Performance data for the specified report date.
- **Action:** Validates input (report_date format and range). Calls the GRES Agent to retrieve DAP metrics for the date. Structures the response into categories: auctions (active, new, closed), bidding (total_bids, new_bidders, average_bid), engagement (property_views, unique_visitors), revenue (total), compliance (checks_performed, checks_failed), and system (uptime, response_time).
- **Output:** `dap_data` (date, metrics, raw_data). On failure returns an error; workflow stops.

### 2. Create time series (`create_time_series`)

- **Purpose:** Build time-series data for trend analysis over a lookback window.
- **Action:** Uses the GRES Agent to request daily metrics from `report_date - lookback_days` through `report_date`. If historical data is unavailable, falls back to a single data point using the current day’s DAP data. Computes trends (e.g. auctions_change, bids_change, revenue_change, compliance_failures_change) between first and last period.
- **Output:** `time_series_data` (list of date/metrics entries), `trends` (percentage changes and direction). On failure returns an error; workflow stops.

### 3. Create analysis (`create_analysis`)

- **Purpose:** Produce a performance analysis and risk assessment from DAP and time-series data.
- **Action:** Sends the GRES Agent a structured analysis query with current metrics and time-series context. Requests: overall performance assessment, highlights, concerns, anomalies, recommendations, historical comparison, and risk factors. Parses the response into summary, performance_score, highlights, concerns, anomalies, recommendations, risk_level, and detailed_analysis.
- **Output:** `analysis_results`. On failure returns an error; workflow stops.

### Post-steps (issue handling)

After the three steps above, the workflow checks analysis results (risk_level, concerns, anomalies). If risk is high/critical or concerns/anomalies exist, it compiles an issues list, optionally creates an analyst task (e.g. “Review DAP Report Issues – &lt;date&gt;”), and creates a user toast notifying the analyst. The final run output includes report data and any tasks created.

## Dependencies

- **GRES Agent:** Used for data retrieval, time-series data, and analysis. The workflow fails or degrades (e.g. time-series fallback) if the agent is unavailable or returns errors.
- **Input validation:** Report date must be YYYY-MM-DD, not in the future; optional lookback_days clamped to 1–365.

## Run result

The workflow run stores input (`report_date`, etc.) and output (report data, analysis, issues, tasks_created). The run detail page and API expose this structured result for viewing and audit.
