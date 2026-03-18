# Business Intelligence Ideas for GSA Real Estate Sales

Ideas for extending RealtyIQ’s reporting and BI for the GSA Real Estate Sales auction platform. Use this as a backlog for new tools, prompts, or API support.

---

## 1. Funnel and conversion

- **Registration → bid conversion** per property or site (e.g. “What % of registered bidders placed a bid?”). Combine `auction_bidders` and `auction_total_bids`.
- **Watchers → bidders** – compare watcher count to bidder count per property (`auction_watchers` + `auction_bidders` / `auction_total_bids`).
- **Sold vs unsold** – count or list properties by status (e.g. status 9 = sold) using `list_properties` / `property_count_summary` with appropriate filters.

---

## 2. Time-based analytics

- **Bidding activity over time** – bids per day/week; requires API support for date-filtered bid or registration data.
- **Properties ending in next 7 / 14 / 30 days** – “ending soon” lists or counts via `list_properties` or `property_count_summary` with sort/filter.
- **Registration and bid trends** – extend usage of `property_registration_graph`; add similar endpoints for bid or registration volume if the API supports it.

---

## 3. Comparative and leaderboards

- **By site/domain** – compare properties, bidders, total bids, watchers across sites using existing tools and `get_site_detail`.
- **By agent** – “top agents” by listings, bidders, or bids; combine `list_agents_summary`, `list_properties`, `auction_bidders`, `auction_total_bids`.
- **By property/asset type** – which types get the most bids or watchers; use `list_property_types` / `list_asset_types` with bid and watcher tools.

---

## 4. Engagement and risk

- **Low-engagement alerts** – e.g. “Properties with 0 bidders ending in 14 days” (combine auction dashboard, bidders, count summary).
- **Watcher-to-bidder ratio** per property as a simple engagement signal.
- **Repeat bidders** – users bidding on multiple properties; requires user id in bid/registration data from the API.

---

## 5. Geographic

- **By state/region** – property counts, bid volume, or “hot” vs “cold” markets using city/state in property data.
- **Agent or bidder geography** – if the API exposes region/address for agents or bidders.

---

## 6. Revenue and valuation (if data exists)

- **Total bid volume** by period, site, or property type (sum bids from bid history/totals).
- **Reserve vs final bid** – e.g. “Properties that met or exceeded reserve” using `get_property_detail` if reserve is exposed.
- **Average bid or sale price** by asset type or region.

---

## 7. Operational and compliance

- **Bid and registration audit trail** – “Who bid what and when” for a property; use `bid_history` and optionally format for audit reports.
- **Admin metrics over time** – use `admin_dashboard` with date ranges for trend views.
- **Support/inquiries** – if the API has Contact Us or similar, add a tool for counts or summaries.

---

## 8. Exports and reporting

- **CSV/Excel export** – e.g. “Export current property list or bid summary for this site” (tool that calls existing APIs and returns or writes CSV).
- **Weekly/monthly digest** – “Summary of new listings, total bidders, top properties by bids this week” by orchestrating existing tools (scheduling could live outside the agent).

---

## 9. Alerts and thresholds

- **“Properties with no bidders”** (or &lt; N bidders) and ending within X days.
- **“Sites with no new registrations in 7 days”** if registration data is queryable.
- **Watcher or bid-count thresholds** – e.g. “List properties with &gt; 10 watchers.”

---

## 10. Natural-language BI summaries

- Prompts that tie several tools together, e.g.:  
  **“For site 3: how many properties are active, how many total bidders this month, and which 5 properties have the most watchers?”**  
  The agent uses `property_count_summary`, `auction_bidders` / `auction_total_bids`, and `auction_watchers` (or dashboard) and returns one narrative answer.
- Add such prompts to `prompts/README.md` and `prompts/examples.txt` as “BI summary” examples.

---

## Quick wins with current tools

- Add **example prompts** in `prompts/` that ask for: funnel-style questions (“How many bidders and watchers for property X?”), “ending soon” counts, and “admin dashboard for site 3 for last 30 days.”
- If the API supports **date filters** on bid/registration endpoints, add those parameters to the relevant tools so the agent can answer “bids in the last 30 days” or “registrations this week.”
- One **“BI summary”** prompt that asks the agent to combine several tools (counts, dashboard, top properties by watchers) into a short narrative for leadership.

---

## Related docs

- [Tools reference](tools.md) – existing tools and parameters.
- [Prompts](../prompts/README.md) – example prompts for demos.
