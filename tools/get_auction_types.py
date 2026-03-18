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
def get_auction_types(
    site_id: int = DEFAULT_SITE_ID,
) -> StringToolOutput:
    """
    Get auction type reference data (English, Dutch, Sealed, etc.) for a site.
    Calls api-cms/get-auction-type/. site_id is required by the API.
    """
    payload = {"site_id": str(site_id)}
    url = f"{API_BASE}/api-cms/get-auction-type/"
    r = session.post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")
    result = data.get("data") or {}
    return StringToolOutput(str(result))
