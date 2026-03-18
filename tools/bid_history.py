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
def bid_history(
    property_id: int,
    domain_id: int | None = None,
    site_id: int | None = None,
) -> StringToolOutput:
    """
    Full bid history for a property (summary per user). Calls api-bid/bid-history/.
    Pass domain_id (or site_id, used as domain_id). Use for: Show bid history for property 100.
    """
    did = domain_id if domain_id is not None else site_id
    if did is None:
        did = DEFAULT_SITE_ID
    payload = {
        "domain_id": int(did),
        "property_id": property_id,
    }
    url = f"{API_BASE}/api-bid/bid-history/"
    r = session.post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")
    return StringToolOutput(str(data.get("data") or {}))
