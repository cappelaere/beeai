import os

import requests
from beeai_framework.tools import StringToolOutput, tool

API_BASE = os.environ["API_URL"].rstrip("/")
AUTH_TOKEN = os.environ["AUTH_TOKEN"]
DEFAULT_SITE_ID = int(os.getenv("SITE_ID", "3"))
TLS_VERIFY = os.getenv("TLS_VERIFY", "true").lower() in ("1", "true", "yes")

session = requests.Session()
session.headers.update(
    {
        "Authorization": f"Token {AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
)


@tool
def property_count_summary(
    site_id: int = DEFAULT_SITE_ID,
    filter: str = "",
    search: str = "",
    sort_by: str = "ending_soonest",
    sort_order: str = "asc",
    agent_id: str = "",
    user_id: int | None = None,
) -> StringToolOutput:
    """
    Get property count/total for the given filters without fetching full listings.
    Uses api-property/front-property-listing/ with page_size=1 and returns total.
    Use for: How many active properties? Count properties ending soon? How many for agent X?
    """
    payload = {
        "site_id": str(site_id),
        "page_size": 1,
        "page": 1,
        "search": search,
        "filter": filter,
        "short_by": sort_by,
        "sort_order": sort_order,
        "agent_id": agent_id,
        "user_id": user_id if user_id is not None else "",
    }
    url = f"{API_BASE}/api-property/front-property-listing/"
    r = session.post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")

    # Navigate to the nested data structure
    outer_data = data.get("data") or {}
    inner = outer_data.get("data")

    # Handle different response structures
    if isinstance(inner, dict):
        # If inner is a dict, get total from it
        total = inner.get("total")
    elif isinstance(inner, list):
        # If inner is a list, check if total is in outer_data
        total = outer_data.get("total")
        if total is None:
            # Fallback: use the length of the list
            total = len(inner)
    else:
        # Fallback to outer level or 0
        total = outer_data.get("total", 0)

    out = {
        "site_id": site_id,
        "total": total,
        "filters": {"filter": filter, "search": search, "agent_id": agent_id},
    }
    return StringToolOutput(str(out))
