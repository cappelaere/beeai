# GRES Agent Documentation

## Overview

**Agent Name:** GRES Agent 🏢  
**Purpose:** GSA Real Estate Sales (GRES) Auction assistant - DEFAULT agent  
**Type:** Read-only data query agent

The GRES Agent provides comprehensive access to GSA Real Estate Sales auction data, including property listings, bidding information, agent performance metrics, and auction analytics.

## When to Use This Agent

Use the GRES Agent when you need to:
- Search and browse properties in GSA auctions
- Get detailed information about specific properties
- Track bidding activity and auction status
- Analyze agent performance and auction metrics
- View property registration trends
- Access auction dashboards and summaries

## Quick Start

### Selecting the Agent
1. Open the RealtyIQ interface
2. Use the agent selector dropdown in the top bar
3. Select "🏢 GRES" (this is the default agent)

### Basic Usage Examples

**Find properties:**
```
Show me properties ending soon
List all properties in California
Find properties with a list price under $500,000
```

**Get property details:**
```
Tell me about property ID 12345
What's the status of the auction for property 67890?
Show me bidding history for property ID 45678
```

**Analyze auctions:**
```
What's the auction dashboard summary?
Show me agent performance statistics
How many properties are currently active?
```

## Available Tools

### Property Search & Information

#### list_properties
**Purpose:** Search and list properties with filtering and sorting options

**Key Parameters:**
- `site_id` (int): Site identifier (default: 3)
- `page_size` (int): Results per page (1-50, default: 12)
- `page` (int): Page number (default: 1)
- `search` (str): Search term
- `filter` (str): Filter criteria
- `sort_by` (str): Sort field (default: "ending_soonest")
- `sort_order` (str): "asc" or "desc"
- `agent_id` (str): Filter by agent
- `user_id` (int): Filter by user

**Example:**
```
list_properties(search="California", page_size=20, sort_by="list_price")
```

#### get_property_detail
**Purpose:** Get comprehensive details for a specific property

**Key Parameters:**
- `property_id` (int): Property identifier

**Example:**
```
get_property_detail(property_id=12345)
```

### Property Metadata

#### list_property_types
**Purpose:** List all available property types in the system

**Example:**
```
list_property_types()
```

#### list_asset_types
**Purpose:** List all asset type categories

**Example:**
```
list_asset_types()
```

#### get_auction_types
**Purpose:** Get all auction type configurations

**Example:**
```
get_auction_types()
```

### Site Information

#### get_site_detail
**Purpose:** Get configuration and details for a specific site

**Key Parameters:**
- `site_id` (int): Site identifier

**Example:**
```
get_site_detail(site_id=3)
```

### Analytics & Dashboards

#### property_count_summary
**Purpose:** Get summary counts of properties by status

**Key Parameters:**
- `site_id` (int): Site identifier

**Example:**
```
property_count_summary(site_id=3)
```

#### auction_dashboard
**Purpose:** Get comprehensive auction dashboard metrics

**Key Parameters:**
- `site_id` (int): Site identifier
- `auction_id` (int): Specific auction identifier

**Example:**
```
auction_dashboard(site_id=3, auction_id=100)
```

#### admin_dashboard
**Purpose:** Get administrative dashboard with system-wide metrics

**Key Parameters:**
- `site_id` (int): Site identifier

**Example:**
```
admin_dashboard(site_id=3)
```

#### property_registration_graph
**Purpose:** Get property registration data over time for graphing

**Key Parameters:**
- `site_id` (int): Site identifier
- `days` (int): Number of days to include (default: 30)

**Example:**
```
property_registration_graph(site_id=3, days=60)
```

### Bidding Information

#### auction_bidders
**Purpose:** List all bidders for a specific auction

**Key Parameters:**
- `auction_id` (int): Auction identifier

**Example:**
```
auction_bidders(auction_id=100)
```

#### auction_total_bids
**Purpose:** Get total bid count for an auction

**Key Parameters:**
- `auction_id` (int): Auction identifier

**Example:**
```
auction_total_bids(auction_id=100)
```

#### bid_history
**Purpose:** Get complete bidding history for an auction

**Key Parameters:**
- `auction_id` (int): Auction identifier

**Example:**
```
bid_history(auction_id=100)
```

#### auction_watchers
**Purpose:** List users watching a specific auction

**Key Parameters:**
- `auction_id` (int): Auction identifier

**Example:**
```
auction_watchers(auction_id=100)
```

### Agent Performance

#### list_agents_summary
**Purpose:** Get performance summary for all agents

**Key Parameters:**
- `site_id` (int): Site identifier

**Example:**
```
list_agents_summary(site_id=3)
```

### System Tools

#### list_available_tools
**Purpose:** List all available tools and their descriptions

**Example:**
```
list_available_tools()
```

## Common Workflows

### Finding and Evaluating Properties

1. **Search for properties:**
   ```
   list_properties(search="commercial", sort_by="list_price", sort_order="asc")
   ```

2. **Get detailed information:**
   ```
   get_property_detail(property_id=12345)
   ```

3. **Check bidding activity:**
   ```
   bid_history(auction_id=100)
   auction_total_bids(auction_id=100)
   ```

### Monitoring Auction Performance

1. **View dashboard:**
   ```
   auction_dashboard(site_id=3)
   ```

2. **Check property counts:**
   ```
   property_count_summary(site_id=3)
   ```

3. **Analyze trends:**
   ```
   property_registration_graph(site_id=3, days=90)
   ```

### Agent Analysis

1. **Get agent summary:**
   ```
   list_agents_summary(site_id=3)
   ```

2. **View properties by agent:**
   ```
   list_properties(agent_id="12345")
   ```

## Technical Details

### API Integration
- **Base URL:** Configured via `API_URL` environment variable
- **Authentication:** Token-based (configured via `AUTH_TOKEN` environment variable)
- **Default Site ID:** 3 (configurable via `SITE_ID` environment variable)
- **TLS Verification:** Configurable via `TLS_VERIFY` environment variable

### Data Sources
- GSA Real Estate Sales API
- Property listing database
- Auction bidding system
- Agent performance tracking system

### Response Format
All tools return data as formatted strings (StringToolOutput) containing:
- JSON-formatted data structures
- Property metadata
- Auction statistics
- Agent performance metrics

### Rate Limiting
- Page size capped at 50 results per request
- Timeout set to 30 seconds per API call

## Example Use Cases

### For Property Investors
- "Show me all residential properties under $300,000"
- "Find properties ending in the next 7 days"
- "What's the bidding history for property 12345?"

### For Real Estate Agents
- "Show agent performance metrics for site 3"
- "List all my properties"
- "How many watchers does auction 100 have?"

### For Administrators
- "Show me the admin dashboard"
- "What's the property registration trend over 90 days?"
- "Get property count summary by status"

### For Data Analysts
- "Export property registration graph data"
- "Show auction dashboard for multiple auctions"
- "List all property types and asset categories"

## Privacy & Compliance

The GRES Agent is read-only and does not:
- Modify property data
- Create or update auctions
- Place bids
- Access or display PII unless explicitly requested

All queries are logged for audit purposes.

## Related Agents

- **SAM.gov Agent** - For exclusions and federal contractor verification
- **Identity Verification Agent** - For user identity validation
- **Library Agent** - For searching documentation and PDFs

## Support

For API access issues, check:
1. `API_URL` environment variable is set correctly
2. `AUTH_TOKEN` is valid and not expired
3. Network connectivity to the GRES API endpoint
4. TLS certificate trust (or set `TLS_VERIFY=false` for development)
