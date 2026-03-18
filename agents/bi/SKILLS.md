# BI Agent

BidHom property performance and business intelligence assistant.

## What this agent does

- Answers role-based questions about BidHom property performance using:
  - **Telemetry metrics:** views, unique sessions, brochure/IFB downloads, subscriber and bidder registrations, photo clicks (from the metrics API).
  - **Property context:** title, address, region, status, auction dates (from the property API).
  - **Web search:** when useful for benchmarks, regional trends, or market context (e.g. “is this engagement normal?”, “which regions have strongest growth?”).
- Supports **Real Estate Specialists**, **Program Managers**, **Marketing/Outreach** (no campaign attribution), and **Leadership**.
- Uses tools to call the Api (metrics, property, and bid endpoints). Does not expose PII unless the user explicitly asks.

## Tools

- **Metrics:** property summary (totals over a period), property daily (time series), top properties (rank by any metric), underperforming (high interest but low bidders; by views, IFB, or brochure), properties with activity (to derive “no activity” with list_properties), **event types** (canonical list of tracked event types with id, slug, and description—use when the user asks what metrics are tracked or what an event type or event number means).
- **Property & bid:** list properties, property detail, auction bidders, property registration graph.
- **ThinkTool:** Use for multi-step reasoning when the question is complex.
- **Charting:** chart_time_series — use after get_metrics_property_daily to visualize time series. **Workflow:** (1) Call get_metrics_property_daily(property_id, start, end) to get daily data; (2) pass the response string as `data_json` to chart_time_series with a title and optional `value_columns` (e.g. views, unique_sessions); (3) include the tool output in your reply (chart appears in chat with a download option). Supports line or bar charts; multiple value columns show as multiple series.
- **Map:** chart_map — plot points on a world or USA map from data with latitude/longitude (or lat/lon). Use when the user asks to show properties or locations on a map. Pass `data_json` with lat/lon; optional `label_column` (e.g. title, address), `size_column` (e.g. views), `scope='usa'` or `'world'`. Include the tool output in your reply (map appears in chat with a download option).
- **Web search:** DuckDuckGo for research and context when answering performance questions.

## Example prompts

Replace `{property_id}` with a real property ID (e.g. from your listing or metrics data).

### Property-level (Real Estate Specialist)

1. Show the performance summary for property {property_id} for the last 30 days.
2. How is property {property_id} performing compared to the previous 30 days?
3. Show the engagement funnel for property {property_id} (views → brochure downloads → IFB downloads → bidder registrations).
4. Is interest in property {property_id} increasing or decreasing over the last 14 days?
5. How many unique visitors viewed property {property_id} this month?

### Conversion and auction readiness

6. Is property {property_id} attracting enough bidder registrations relative to its views?
7. Show properties with high IFB downloads but low bidder registrations.
8. Which properties have strong interest signals but weak bidder conversion?
9. Show a pre-auction readiness check for property {property_id}.
10. Which properties are likely to struggle attracting bidders?

### Portfolio (Program Managers)

11. Show the top 10 properties by views in the last 7 days.
12. Show the top 10 properties by IFB downloads in the last 30 days.
13. Which properties received the most bidder registrations this month?
14. Show underperforming listings with high views but few bidders.
15. Rank all active properties by engagement.

### Operational

16. Which properties are seeing rapid increases in interest this week?
17. Which properties had no activity in the last 7 days?
18. Which listings generated the most brochure downloads recently?

### Executive

19. Provide a portfolio summary for all active properties for the last 30 days.
20. What are the top opportunities and risks across the current property portfolio?

### Reference (event types)

21. What property metrics do you track?
22. What does event type 3 mean? (or any event number 1–6)

### Charting

23. Chart daily views for property {property_id} over the last 30 days.
24. Plot interest (views and unique sessions) for property {property_id} for the past 14 days.
25. Show me a line chart of property {property_id} metrics (views, brochure downloads) for last month.
26. Visualize how engagement changed for property {property_id} week by week as a bar chart.

### Map (when property/location data has lat/lon)

27. Show these properties on a map: [data with latitude, longitude, and optional title].
28. Plot our portfolio locations on a USA map with marker size by views.
