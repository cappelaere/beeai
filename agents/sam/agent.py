"""
SAM.gov Exclusions Agent Configuration
"""

import sys
from pathlib import Path

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

# Add tools directory to path for RAG tools
_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from beeai_framework.tools.think import ThinkTool

from agents.base import AgentConfig
from agents.sam.tools import (
    check_entity_status,
    exclusion_statistics,
    get_exclusion_detail,
    list_excluding_agencies,
    search_exclusions,
)

SAM_AGENT_CONFIG = AgentConfig(
    name="SAM.gov Exclusions",
    description="Query federal contract exclusions from SAM.gov database",
    instructions=(
        "You are SAM.gov Assistant, a specialized agent for querying the "
        "System for Award Management (SAM) Exclusions database. "
        "You help users check if individuals or entities are excluded from "
        "receiving federal contracts. Use tools to search and retrieve exclusion data. "
        "Be clear and factual when reporting exclusion status. "
        "The database contains 138,885 exclusion records from various federal agencies "
        "including HHS, TREAS-OFAC, OPM, DOJ, and EPA."
    ),
    tools=[
        ThinkTool(),
        search_exclusions,
        get_exclusion_detail,
        check_entity_status,
        list_excluding_agencies,
        exclusion_statistics,
    ],
    icon="🚫",
)
