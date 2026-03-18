"""
GRES Agent Configuration (Default Agent)
GSA Real Estate Sales Auctions
"""

import sys
from pathlib import Path

# Add tools directory to path so we can import GRES tools
_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from admin_dashboard import admin_dashboard
from auction_bidders import auction_bidders
from auction_dashboard import auction_dashboard
from auction_total_bids import auction_total_bids
from auction_watchers import auction_watchers
from beeai_framework.tools.think import ThinkTool
from bid_history import bid_history
from chart_choropleth import chart_choropleth
from chart_map import chart_map
from get_auction_types import get_auction_types
from get_property_detail import get_property_detail
from get_site_detail import get_site_detail
from list_agents import list_agents_summary
from list_asset_types import list_asset_types

# Import all GRES tools from /tools directory
from list_properties import list_properties
from list_property_types import list_property_types
from list_tools import list_available_tools
from property_count_summary import property_count_summary
from property_registration_graph import property_registration_graph

from agents.base import AgentConfig

GRES_AGENT_CONFIG = AgentConfig(
    name="GRES Agent",
    description="GSA Real Estate Sales (GRES) Auction assistant - DEFAULT agent",
    instructions=(
        "You are the GRES Agent, a read-only assistant for GSA Real Estate Sales (GRES) Auctions. "
        "You help users query property data, auction information, bidding details, and agent performance. "
        "Use tools to fetch data about properties, auctions, bids, and agents. "
        "Do not request or output PII unless explicitly asked. "
        "When the user says 'density' (e.g. 'active properties density', 'property density'): always use chart_choropleth to show counts by state—do not use chart_map. chart_map plots individual property locations as points; chart_choropleth shades states by property count (density). (1) Call list_properties (e.g. page_size=100 or more). (2) Aggregate by state: count how many properties per state (use the 'state' field). (3) Build a JSON array of objects with keys 'state' (state name, e.g. Kansas) and 'count'. (4) Call chart_choropleth with that array as data_json, title e.g. 'Property density by state', location_column='state', value_column='count', locationmode='USA-states'. (5) Include the choropleth image in your reply. "
        "When the user asks to show properties on a map or display active properties on a map (and does not say 'density'): (1) Call list_properties (e.g. page_size=50). (2) Filter to only properties with non-empty latitude and longitude. (3) Call chart_map with that filtered list as data_json (title e.g. 'Active properties', label_column='name', scope='usa'). (4) Include the map image returned by chart_map in your reply—do not respond with only a table of coordinates. If no properties have coordinates, say so."
    ),
    tools=[
        ThinkTool(),
        list_available_tools,
        list_properties,
        list_agents_summary,
        get_property_detail,
        list_property_types,
        list_asset_types,
        get_auction_types,
        get_site_detail,
        property_count_summary,
        auction_dashboard,
        auction_bidders,
        auction_total_bids,
        bid_history,
        auction_watchers,
        admin_dashboard,
        property_registration_graph,
        chart_map,
        chart_choropleth,
    ],
    icon="🏢",
)
