import os

import requests
from beeai_framework.tools import StringToolOutput, tool

API_BASE = os.environ["API_URL"].rstrip("/")
AUTH_TOKEN = os.environ["AUTH_TOKEN"]
DEFAULT_SITE_ID = int(os.getenv("SITE_ID", "3"))
DEFAULT_USER_ID = os.getenv("USER_ID")
TLS_VERIFY = os.getenv("TLS_VERIFY", "true").lower() in ("1", "true", "yes")

session = requests.Session()
session.headers.update(
    {
        "Authorization": f"Token {AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
)

PAGE_SIZE_CAP = 50


@tool
def auction_dashboard(
    domain_id: int = DEFAULT_SITE_ID,
    user_id: int | None = None,
    page: int = 1,
    page_size: int = 12,
    status: int | None = None,
    agent_id: int | None = None,
    auction_id: int | None = None,
    asset_id: int | None = None,
    search: str = "",
) -> StringToolOutput:
    """
    Auction-focused dashboard: list auction properties with status, dates, and filters.
    Calls api-property/property-auction-dashboard/. Requires domain_id and user_id (or set USER_ID in env).
    Use for: Show auction dashboard for site 3, list active auctions for agent 5, upcoming auctions (status 17).
    """
    uid = user_id if user_id is not None else (int(DEFAULT_USER_ID) if DEFAULT_USER_ID else None)
    if uid is None:
        raise ValueError("user_id is required (or set USER_ID in environment)")
    page_size = max(1, min(int(page_size), PAGE_SIZE_CAP))
    page = max(1, int(page))
    payload = {
        "domain_id": domain_id,
        "user_id": uid,
        "page": page,
        "page_size": page_size,
        "search": search,
    }
    if status is not None:
        payload["status"] = status
    if agent_id is not None:
        payload["agent_id"] = agent_id
    if auction_id is not None:
        payload["auction_id"] = auction_id
    if asset_id is not None:
        payload["asset_id"] = asset_id
    url = f"{API_BASE}/api-property/property-auction-dashboard/"
    r = session.post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")
    return StringToolOutput(str(data.get("data") or {}))
