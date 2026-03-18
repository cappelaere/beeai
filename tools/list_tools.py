"""
List all available tools and their descriptions. Exposed as a tool so the agent can answer
"What tools do you have?" or "List your capabilities."
"""

import sys
from pathlib import Path

from beeai_framework.tools import StringToolOutput, tool

# Add tools directory to sys.path for absolute imports
_TOOLS_DIR = Path(__file__).parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

# Import all tool functions from their modules
from admin_dashboard import admin_dashboard
from auction_bidders import auction_bidders
from auction_dashboard import auction_dashboard
from auction_total_bids import auction_total_bids
from auction_watchers import auction_watchers
from bid_history import bid_history
from chart_choropleth import chart_choropleth
from chart_map import chart_map
from get_auction_types import get_auction_types
from get_property_detail import get_property_detail
from get_site_detail import get_site_detail
from list_agents import list_agents_summary
from list_asset_types import list_asset_types
from list_properties import list_properties
from list_property_types import list_property_types
from property_count_summary import property_count_summary
from property_registration_graph import property_registration_graph

# Single source of truth for "all tools that are listable" (excludes this meta-tool until we add it)
_ALL_TOOL_FUNCTIONS = [
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
]

# Agent-specific tool mappings (matches agent configs in agents/*/agent.py)
# Note: list_available_tools is excluded as it's a meta-tool
_AGENT_TOOLS = {
    "gres": [
        # All GRES property/auction tools
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
    "sam": [
        # SAM.gov exclusions tools only (no RAG tools)
    ],
}

# Static tool descriptions for SAM.gov tools (avoids complex imports)
_SAM_TOOLS_STATIC = [
    (
        "search_exclusions",
        "Search SAM.gov exclusions database by name, agency, type, classification, or country",
    ),
    (
        "get_exclusion_detail",
        "Get detailed information about a specific exclusion record by its unique identifier",
    ),
    (
        "check_entity_status",
        "Check if an individual or entity is currently excluded from federal contracts",
    ),
    (
        "list_excluding_agencies",
        "List all federal agencies that have issued exclusions in the database",
    ),
    (
        "exclusion_statistics",
        "Get statistics and summary counts for exclusions by agency, type, and classification",
    ),
]

# Static tool descriptions for Identity Verification tools
_IDV_TOOLS_STATIC = [
    (
        "verify_new_user",
        "Verify a new user's identity (name, city, state, street address, ID documents)",
    ),
    ("lookup_user_verification", "Lookup verification by exact match of all user information"),
    ("search_user", "Search for verifications by name, city, and/or state (no sensitive data)"),
    ("list_all_verifications", "List all verification records with filters and pagination"),
    ("extend_verification_expiration", "Extend the expiration date of an existing verification"),
]

# Static tool descriptions for Library agent tools
_LIBRARY_TOOLS_STATIC = [
    (
        "search_documents",
        "Search indexed PDF documents using semantic similarity and natural language queries",
    ),
    ("reindex_all_documents", "Rebuild the FAISS index from all PDF documents in the library"),
    ("list_documents", "List all PDF documents in the library with metadata (size, dates)"),
    (
        "get_document_info",
        "Get detailed information about a specific document (pages, index status, etc.)",
    ),
    ("library_statistics", "Get comprehensive statistics about the library and search index"),
]

# Static tool descriptions for Section 508 agent tools
_508_TOOLS_STATIC = [
    (
        "list_voices",
        "List all available text-to-speech voices with language, gender, and quality metadata",
    ),
    (
        "synthesize_speech",
        "Convert text or SSML to natural-sounding speech audio with customizable voice and parameters",
    ),
    (
        "tts_health_check",
        "Check the health and status of the Piper TTS service for troubleshooting",
    ),
]

# Static tool descriptions for OFAC agent tools
_OFAC_TOOLS_STATIC = [
    (
        "search_sdn_list",
        "Search OFAC SDN list with fuzzy name matching, filter by program or entity type",
    ),
    (
        "check_bidder_eligibility",
        "Check if a bidder is eligible to participate by screening against the OFAC SDN list",
    ),
    ("get_sdn_detail", "Get full details for a specific SDN list entry by entity ID"),
    (
        "sdn_statistics",
        "Get statistics about the OFAC SDN database (total entries, top programs, etc.)",
    ),
]

# Static tool descriptions for Bidder Verification agent tools (orchestration)
_BIDDER_VERIFICATION_TOOLS_STATIC = [
    (
        "verify_bidder_eligibility",
        "Orchestrate comprehensive bidder screening by running both SAM.gov and OFAC compliance checks",
    ),
]

_BPMN_EXPERT_TOOLS_STATIC = [
    ("get_workflow_context", "Load BPMN, bindings, and workflow.py context for a workflow"),
    ("analyze_bpmn_diagram", "Summarize BPMN structure, bindings, and likely sync issues"),
    ("explain_workflow_path", "Explain the execution path between BPMN elements"),
    ("validate_bpmn_bindings", "Validate service task ids, bindings, and handler names"),
    ("suggest_handler_stub", "Draft a workflow.py handler stub for a BPMN task"),
    ("update_bpmn_bindings", "Propose or apply updates to bpmn-bindings.yaml for a task"),
    ("update_workflow_bpmn", "Propose or apply focused BPMN XML edits such as renaming an element"),
    ("generate_workflow_handler", "Propose or apply a generated workflow.py handler stub"),
    ("sync_task_to_handler", "Align a BPMN task with both a binding entry and handler stub"),
]


def get_tools_list(agent_type: str = None) -> list[tuple[str, str]]:
    """
    Return a list of (tool_name, description) for available tools.
    If agent_type is provided, returns only tools for that agent.
    Otherwise returns all tools.

    Args:
        agent_type: Optional agent type (loaded from agents.yaml registry, or None for all)

    Uses the tool's .name and .description (set by the @tool decorator).
    """
    result = []

    # SAM agent - use static definitions to avoid complex imports
    # SAM agent does NOT include RAG tools (those are GRES-specific)
    if agent_type == "sam":
        # Add only SAM-specific tools
        result.extend(_SAM_TOOLS_STATIC)
        return result

    # IdV agent - use static definitions
    if agent_type == "idv":
        # Add only IdV-specific tools
        result.extend(_IDV_TOOLS_STATIC)
        return result

    # Library agent - use static definitions
    if agent_type == "library":
        # Add only Library-specific tools
        result.extend(_LIBRARY_TOOLS_STATIC)
        return result

    # Section 508 agent - use static definitions
    if agent_type == "508":
        # Add only Section 508-specific tools
        result.extend(_508_TOOLS_STATIC)
        return result

    # OFAC agent - use static definitions
    if agent_type == "ofac":
        # Add only OFAC-specific tools
        result.extend(_OFAC_TOOLS_STATIC)
        return result

    # Bidder Verification agent - use static definitions
    if agent_type == "bidder_verification":
        # Add only Bidder Verification orchestration tools
        result.extend(_BIDDER_VERIFICATION_TOOLS_STATIC)
        return result

    if agent_type == "bpmn_expert":
        result.extend(_BPMN_EXPERT_TOOLS_STATIC)
        return result

    # GRES agent or no agent specified
    if agent_type == "gres" or not agent_type:
        tools_to_list = _AGENT_TOOLS.get("gres", _ALL_TOOL_FUNCTIONS)

        # Extract tool info
        for t in tools_to_list:
            name = getattr(t, "name", None) or getattr(t, "__name__", "unknown")
            desc = (getattr(t, "description", None) or "").strip()
            if not desc:
                desc = "(No description)"
            result.append((name, desc))

    return result


@tool
def list_available_tools() -> StringToolOutput:
    """
    List all available tools and their short descriptions. Use when the user asks what tools you have, what you can do, or your capabilities.
    """
    tools_list = get_tools_list()
    lines = [f"- **{name}**: {desc}" for name, desc in tools_list]
    return StringToolOutput("Available tools:\n\n" + "\n".join(lines))
