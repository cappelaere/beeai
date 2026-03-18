import os

import requests
from beeai_framework.tools import StringToolOutput, tool

API_BASE = os.environ["API_URL"].rstrip("/")
AUTH_TOKEN = os.environ["AUTH_TOKEN"]
DEFAULT_SITE_ID = int(os.getenv("SITE_ID", "3"))

# For quick dev parity with curl -k you can set REALTY_TLS_VERIFY=false (not recommended long term).
TLS_VERIFY = os.getenv("TLS_VERIFY", "true").lower() in ("1", "true", "yes")

session = requests.Session()
session.headers.update(
    {
        "Authorization": f"Token {AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
)


def _pick_agent_summary(item: dict) -> dict:
    # PII-SAFE: no email, no phone, no street address
    # Defensive: ensure item is a dict
    if not isinstance(item, dict):
        return {
            "user_id": None,
            "first_name": None,
            "last_name": None,
            "company_name": None,
            "property_count": 0,
            "state": None,
            "error": f"Invalid item type: {type(item).__name__}",
        }

    return {
        "user_id": item.get("user_id"),
        "first_name": item.get("first_name"),
        "last_name": item.get("last_name"),
        "company_name": item.get("company_name"),
        "property_count": item.get("property_count"),
        # optionally include state-only if it helps ops, but avoid street/postal:
        "state": (item.get("address") or [{}])[0].get("state")
        if isinstance(item.get("address"), list)
        else None,
    }


@tool
def list_agents_summary(
    site_id: int = DEFAULT_SITE_ID,
    page_size: int = 12,
    page: int = 1,
    search: str = "",
    filter: str = "",
    user_id: int | None = None,
) -> StringToolOutput:
    """
    Calls /api-users/agent-list/ and returns a PII-safe summary list of agents.
    """
    page_size = max(1, min(int(page_size), 50))
    page = max(1, int(page))

    payload = {
        "site_id": str(site_id),
        "page_size": page_size,
        "page": page,
        "search": search,
        "filter": filter,
        "user_id": user_id if user_id is not None else "",
    }

    url = f"{API_BASE}/api-users/agent-list/"
    r = session.post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()

    body = r.json()
    # Response structure: {"data": {"data": [...], "total": N}}
    data_obj = body.get("data") or {}
    items = data_obj.get("data") or []
    total = data_obj.get("total")

    out = {
        "site_id": site_id,
        "page": page,
        "page_size": page_size,
        "count_returned": len(items),
        "total": total,
        "agents": [_pick_agent_summary(x) for x in items],
    }
    return StringToolOutput(str(out))
