import os

import requests
from beeai_framework.tools import StringToolOutput, tool

API_BASE = os.environ["API_URL"].rstrip("/")
AUTH_TOKEN = os.environ["AUTH_TOKEN"]
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
def list_property_types(
    asset_id: int | None = None,
) -> StringToolOutput:
    """
    Get property type reference data for filtering and reporting.
    Calls api-property/property-type-listing/. Optionally filter by asset_id.
    """
    payload = {}
    if asset_id is not None:
        payload["asset_id"] = asset_id
    url = f"{API_BASE}/api-property/property-type-listing/"
    r = session.post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")
    result = data.get("data") or []
    return StringToolOutput(str(result))
