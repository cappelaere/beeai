import os

import requests
from beeai_framework.tools import StringToolOutput, tool

API_BASE = os.environ["API_URL"].rstrip("/")
AUTH_TOKEN = os.environ["AUTH_TOKEN"]
DEFAULT_SITE_ID = int(os.getenv("SITE_ID", "3"))

# Prefer fixing cert trust and using verify="/path/to/ca.pem" or system trust store.
# For quick dev parity with curl -k you *can* set REALTY_TLS_VERIFY=false (not recommended for prod).
TLS_VERIFY = os.getenv("TLS_VERIFY", "true").lower() in ("1", "true", "yes")

session = requests.Session()
session.headers.update(
    {
        "Authorization": f"Token {AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
)


def _pick_property_fields(item: dict) -> dict:
    # Keep it small and useful for reporting
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "status": item.get("status"),
        "auction_type": item.get("auction_type"),
        "bidding_start": item.get("bidding_start"),
        "bidding_end": item.get("bidding_end"),
        "city": item.get("city"),
        "state": item.get("state_name") or item.get("iso_state_name"),
        "postal_code": item.get("postal_code"),
        "asset_type": item.get("property_asset"),
        "list_price": item.get("property_price"),
        "current_price": item.get("property_current_price"),
        "is_featured": item.get("is_featured"),
        "latitude": item.get("latitude"),
        "longitude": item.get("longitude"),
    }


@tool
def list_properties(
    site_id: int = DEFAULT_SITE_ID,
    page_size: int = 12,
    page: int = 1,
    search: str = "",
    filter: str = "",
    sort_by: str = "ending_soonest",
    sort_order: str = "asc",
    agent_id: str = "",
    user_id: int | None = None,
) -> StringToolOutput:
    """
    Calls /api-property/front-property-listing/ and returns a trimmed list of properties.
    """
    # Hard caps so the tool can't dump huge payloads into the model
    page_size = max(1, min(int(page_size), 50))
    page = max(1, int(page))

    payload = {
        "site_id": str(site_id),
        "page_size": page_size,
        "page": page,
        "search": search,
        "filter": filter,
        "short_by": sort_by,  # endpoint appears to expect "short_by"
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

    items = (data.get("data") or {}).get("data") or []
    trimmed = [_pick_property_fields(x) for x in items]

    # return the basics plus paging hints if present
    out = {
        "site_id": site_id,
        "page": page,
        "page_size": page_size,
        "count_returned": len(trimmed),
        "properties": trimmed,
    }
    return StringToolOutput(str(out))
