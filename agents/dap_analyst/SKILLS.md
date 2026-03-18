# DAP Analyst Agent

GSA Digital Analytics Program (DAP) assistant for realestatesales.gov and other DAP-participating .gov domains.

## What this agent does

- Answers questions about web analytics for DAP domains using the GSA DAP API (api.gsa.gov/analytics/dap).
- Default domain: **realestatesales.gov** (one "s" in "sales"). Other GSA/DAP domains can be queried by overriding the domain parameter.
- Summarizes visits, page views, and trends; supports date-range queries and comparisons. Data is sampled and high-level; V2 data is available from Aug 2023 to present.
- Can **chart** time series: after fetching DAP data, use the chart tool to return an inline PNG (e.g. visits over time).
- Can **map** locations: use chart_map with data that has latitude/longitude (or lat/lon) to show points on a world or USA map.

## Tools

- **get_dap_domain_analytics(domain, report, after, before, limit)**  
  Fetches DAP report data for a domain. Parameters:
  - **domain**: DAP domain (default: realestatesales.gov).
  - **report**: Report type (e.g. `site` for site-level metrics; exact names may vary—see API docs).
  - **after**, **before**: Date range as YYYY-MM-DD.
  - **limit**: Optional row limit.
  Returns JSON from the DAP API or a clear error message if the key, domain, or report is invalid.

- **ThinkTool**: Used for reasoning before calling tools.

- **DuckDuckGo**: Optional web search for DAP/GSA documentation or report types when needed.

- **chart_time_series(data_json, title, date_column, value_columns, chart_type)**  
  Plots time series data as a line or bar chart. **Workflow:** (1) Call get_dap_domain_analytics to fetch data; (2) pass the raw response string as `data_json` to this tool; (3) include the tool output in your reply so the user sees the chart (image is shown in chat with a download option). Parameters:
  - **data_json**: JSON string (the stringified response from get_dap_domain_analytics).
  - **title**: Chart title (e.g. "realestatesales.gov visits, last 30 days").
  - **date_column**: Optional; key for x-axis (default: inferred, e.g. date, report_date).
  - **value_columns**: Optional; comma-separated numeric keys to plot (default: inferred, e.g. visits, pageviews). Use multiple for several lines/bars (e.g. "visits,pageviews").
  - **chart_type**: Optional; `"line"` (default) or `"bar"`.

- **chart_map(data_json, title, lat_column, lon_column, label_column, size_column, scope)**  
  Plots points on a map from latitude/longitude data. Use when the user asks to show locations, offices, or any geo-tagged data on a map. Include the tool output in your reply (map image appears in chat with a download option). Parameters:
  - **data_json**: JSON string — array of objects with latitude and longitude (or lat/lon, y/x).
  - **title**: Map title.
  - **lat_column**, **lon_column**: Optional; keys for lat/lon (default: inferred from latitude/longitude, lat/lon, y/x).
  - **label_column**: Optional; key for point labels/hover (e.g. name, address).
  - **size_column**: Optional; numeric key for marker size.
  - **scope**: `"world"` (default) or `"usa"`.

## Example prompts

### Traffic and visits (site report)

1. What were realestatesales.gov analytics for the last 30 days?
2. Show me realestatesales.gov site traffic for March 2024.
3. How many visits did realestatesales.gov get last month?
4. Compare realestatesales.gov traffic for January 2025 vs February 2025.
5. Summarize realestatesales.gov visits from August 2024 to October 2024.

### Trends and comparisons

6. Is traffic to realestatesales.gov going up or down over the last three months?
7. Compare realestatesales.gov analytics for Q1 2024 and Q2 2024.
8. What were the busiest weeks for realestatesales.gov in 2024?
9. Give me a high-level trend for realestatesales.gov for the past 90 days.
10. How did realestatesales.gov perform in December 2024 compared to November 2024?

### Downloads (download report)

11. What were the top downloads on realestatesales.gov in the last 30 days?
12. Show download activity for realestatesales.gov for October 2024.
13. Which files were downloaded most from realestatesales.gov last month?

### Domain and second-level (domain / second-level-domain reports)

14. Show realestatesales.gov domain report for the last 7 days.
15. Give me second-level-domain analytics for realestatesales.gov for September 2024.

### Other

16. What report types can I get for realestatesales.gov from the DAP API?
17. Get realestatesales.gov site metrics for the first week of 2025.
18. Summarize realestatesales.gov analytics from 2024-06-01 to 2024-06-30.
19. What does the DAP API say about realestatesales.gov traffic in the last 14 days?
20. Show realestatesales.gov site data with a limit of 50 rows for last month.

### Charting

21. Chart realestatesales.gov visits for the last 30 days.
22. Plot realestatesales.gov traffic over the past 90 days as a line chart.
23. Show me a bar chart of realestatesales.gov visits for March 2024.
24. Visualize realestatesales.gov site metrics (visits and pageviews) for the last 14 days.
25. Create a chart comparing realestatesales.gov traffic week over week for the last month.

### Map (when data has lat/lon)

26. Show these locations on a map: [JSON with latitude, longitude, and optional name].
27. Plot our office locations on a USA map.
