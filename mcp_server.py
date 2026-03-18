#!/usr/bin/env python3
"""
RealtyIQ MCP Server
Exposes all tools for property, agent, auction, bidding data, document search, and identity verification via MCP protocol.
"""
from beeai_framework.adapters.mcp.serve.server import MCPServer, MCPServerConfig, MCPSettings
from dotenv import load_dotenv

# Import all available tools
from tools import (
    # Core tools
    list_properties,
    list_agents_summary,
    
    # Tier 1 - Property & reference data
    get_property_detail,
    list_property_types,
    list_asset_types,
    get_auction_types,
    get_site_detail,
    property_count_summary,
    
    # Tier 2 - Auctions & bids
    auction_dashboard,
    auction_bidders,
    auction_total_bids,
    bid_history,
    auction_watchers,
    admin_dashboard,
    property_registration_graph,
    
    # Charting
    chart_map,
    chart_choropleth,
    
    # Utility
    list_available_tools,
)

# Import IdV tools
from agents.idv.tools import (
    verify_new_user,
    lookup_user_verification,
    search_user,
    list_all_verifications,
    extend_verification_expiration
)

# Import Library tools
from agents.library.tools import (
    search_documents,
    reindex_all_documents,
    list_documents,
    get_document_info,
    library_statistics
)

# Load environment variables
load_dotenv()


def main() -> None:
    """Initialize and start the MCP server with all tools registered."""
    # Configure server
    config = MCPServerConfig(
        transport="streamable-http",
        settings=MCPSettings(
            port=8001,
            host="0.0.0.0",  # Allow external connections
        )
    )
    
    # Create server instance
    server = MCPServer(config=config)
    
    # Register all tools
    all_tools = [
        # Core
        list_properties,
        list_agents_summary,
        
        # Tier 1
        get_property_detail,
        list_property_types,
        list_asset_types,
        get_auction_types,
        get_site_detail,
        property_count_summary,
        
        # Tier 2
        auction_dashboard,
        auction_bidders,
        auction_total_bids,
        bid_history,
        auction_watchers,
        admin_dashboard,
        property_registration_graph,
        
        # Charting / Maps
        chart_map,
        chart_choropleth,
        
        # Identity Verification
        verify_new_user,
        lookup_user_verification,
        search_user,
        list_all_verifications,
        extend_verification_expiration,
        
        # Library / Document Management
        search_documents,
        reindex_all_documents,
        list_documents,
        get_document_info,
        library_statistics,
        
        # Utility
        list_available_tools,
    ]
    
    server.register_many(all_tools)
    
    print(f"🚀 RealtyIQ MCP Server starting on port 8001")
    print(f"📊 Registered {len(all_tools)} tools:")
    print()
    
    # Print tool categories
    print("  Core Tools:")
    print("    • list_properties")
    print("    • list_agents_summary")
    print()
    
    print("  Tier 1 - Property & Reference Data:")
    print("    • get_property_detail")
    print("    • list_property_types")
    print("    • list_asset_types")
    print("    • get_auction_types")
    print("    • get_site_detail")
    print("    • property_count_summary")
    print()
    
    print("  Tier 2 - Auctions & Bids:")
    print("    • auction_dashboard")
    print("    • auction_bidders")
    print("    • auction_total_bids")
    print("    • bid_history")
    print("    • auction_watchers")
    print("    • admin_dashboard")
    print("    • property_registration_graph")
    print()
    
    print("  Charts / Maps:")
    print("    • chart_map")
    print("    • chart_choropleth")
    print()
    
    print("  RAG / Document Search:")
    print("    • search_documents")
    print("    • reindex_all_documents")
    print()
    
    print("  Identity Verification:")
    print("    • verify_new_user")
    print("    • lookup_user_verification")
    print("    • search_user")
    print("    • list_all_verifications")
    print("    • extend_verification_expiration")
    print()
    
    print("  Utility:")
    print("    • list_available_tools")
    print()
    
    print("📖 See docs/tools.md for detailed documentation")
    print()
    
    # Start server
    server.serve()


if __name__ == "__main__":
    main()
