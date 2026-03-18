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
def auction_total_bids(
    property_id: int,
    site_id: int = DEFAULT_SITE_ID,
    user_id: int | None = None,
    page: int = 1,
    page_size: int = 12,
) -> StringToolOutput:
    """
    Bid activity summary per bidder for an auction property. Calls api-bid/auction-total-bids/.
    Use for: Show bid summary for property 100, who has the highest bid on property 500.
    """
    uid = user_id if user_id is not None else (int(DEFAULT_USER_ID) if DEFAULT_USER_ID else None)
    if uid is None:
        raise ValueError("user_id is required (or set USER_ID in environment)")
    page_size = max(1, min(int(page_size), PAGE_SIZE_CAP))
    page = max(1, int(page))
    payload = {
        "site_id": site_id,
        "property_id": property_id,
        "user_id": uid,
        "page": page,
        "page_size": page_size,
    }
    url = f"{API_BASE}/api-bid/auction-total-bids/"
    r = session.post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")
    return StringToolOutput(str(data.get("data") or {}))
