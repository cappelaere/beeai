# RealtyIQ Example Prompts

Example prompts to demonstrate each tool when running the RealtyIQ agent (`python run_agent.py` or `python run_agent_ollama.py`). Copy and paste into the `RealtyIQ>` prompt.

---

## Meta / capabilities

| Tool | Example prompts |
|------|-----------------|
| `list_available_tools` | "What tools do you have?", "List your capabilities", "What can you do?" |

---

## Core listing

| Tool | Example prompts |
|------|-----------------|
| `list_properties` | "List active properties for site 3", "Show the first 20 properties ending soonest", "Properties for agent 5" |
| `list_agents_summary` | "List agents for site 3", "How many agents are there?", "Search agents by company name" |

---

## Tier 1 – Property & reference data

| Tool | Example prompts |
|------|-----------------|
| `get_property_detail` | "Show me full details for property 12345", "What's the status and reserve for property 500?", "Get property 100 details including bidding dates" |
| `list_property_types` | "What property types are available?", "List property types for asset 2" |
| `list_asset_types` | "What asset types exist in the system?", "List all asset types" |
| `get_auction_types` | "List all auction types", "What auction types are configured for site 3?" |
| `get_site_detail` | "Get site configuration for example.com", "What domains are configured?" |
| `property_count_summary` | "How many active properties are there for site 3?", "Count properties ending soon", "How many properties does agent 5 have?" |

---

## Tier 2 – Auctions & bids

| Tool | Example prompts |
|------|-----------------|
| `auction_dashboard` | "Show auction dashboard for site 3", "List active auctions for agent 5", "What auctions are upcoming (status 17)?" |
| `auction_bidders` | "How many bidders are registered for property 100?", "List bidders for auction property 500" |
| `auction_total_bids` | "Show bid summary for property 100", "Who has the highest bid on property 500?", "Bid activity for auction 100" |
| `bid_history` | "Show bid history for property 100", "List all bids on auction 500" |
| `auction_watchers` | "How many people are watching property 100?", "Watcher count for auction 500" |
| `admin_dashboard` | "Show admin dashboard for site 3", "What are the key metrics for the platform?", "Admin stats for last 30 days" |
| `property_registration_graph` | "Property registration trend for last 30 days", "Show property signup graph for site 3" |

---

## Quick copy-paste (one per line)

```
What tools do you have?
List active properties for site 3
List agents for site 3
Show me full details for property 100
What property types are available?
What asset types exist in the system?
List all auction types
How many active properties are there for site 3?
Show auction dashboard for site 3
How many bidders are registered for property 100?
Show bid summary for property 100
Show bid history for property 100
How many people are watching property 100?
Show admin dashboard for site 3
Property registration trend for last 30 days
```

---

## Notes

- Replace property IDs (e.g. 100, 500), site IDs (e.g. 3), and domains with your actual data.
- Tier 2 tools (`auction_dashboard`, `auction_bidders`, `auction_total_bids`, `auction_watchers`) require `USER_ID` in the environment if not passed in context.
- For date ranges (e.g. "last 30 days"), the agent may infer `start_date` and `end_date` (YYYY-MM-DD) from the prompt.
