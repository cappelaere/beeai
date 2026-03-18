"""
Identity Verification Agent Configuration
"""

import sys
from pathlib import Path

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from beeai_framework.tools.think import ThinkTool

from agents.base import AgentConfig
from agents.idv.tools import (
    extend_verification_expiration,
    list_all_verifications,
    lookup_user_verification,
    search_user,
    verify_new_user,
)

IDV_AGENT_CONFIG = AgentConfig(
    name="Identity Verification",
    description="Verify user identity and manage verification records",
    instructions=(
        "You are the Identity Verification Assistant. "
        "You help verify user identities by collecting required information "
        "and checking verification status. "
        "Required fields for new verification: name, city, state, street_address, and at least one ID "
        "(driver's license OR passport). "
        "You maintain audit trails without storing actual PII. "
        "All verifications expire after 1 year from the verification date. "
        "You can search for verifications by name, city, or state (non-sensitive fields only), "
        "list all records, and extend expiration dates as needed."
    ),
    tools=[
        ThinkTool(),
        verify_new_user,
        lookup_user_verification,
        search_user,
        list_all_verifications,
        extend_verification_expiration,
    ],
    icon="🔐",
)
