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
def get_property_detail(
    property_id: int,
    site_id: int = DEFAULT_SITE_ID,
) -> StringToolOutput:
    """
    Fetch full details for a single property by ID (status, bidding dates, reserve, images, etc.).
    Calls api-property/property-detail/. Use for deep dive on a property or to verify status and bidding window.
    """
    payload = {
        "site_id": str(site_id),
        "property_id": property_id,
    }
    url = f"{API_BASE}/api-property/property-detail/"
    r = session.post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")
    # API returns serializer.data in the "data" field of parsejson
    detail = data.get("data") or {}
    return StringToolOutput(str(detail))
