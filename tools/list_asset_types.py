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
def list_asset_types() -> StringToolOutput:
    """
    Get asset type reference data. Calls api-property/asset-listing/.
    Use for filtering and reporting.
    """
    url = f"{API_BASE}/api-property/asset-listing/"
    r = session.post(url, json={}, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")
    result = data.get("data") or []
    return StringToolOutput(str(result))
