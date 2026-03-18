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
def property_registration_graph(
    site_id: int = DEFAULT_SITE_ID,
    start_date: str | None = None,
    end_date: str | None = None,
) -> StringToolOutput:
    """
    Property registration over time (graph data). Calls api-users/property-registration-graph/.
    Optional start_date and end_date (YYYY-MM-DD). Use for: Registration trend last 30 days, signup graph for site 3.
    """
    payload = {"site_id": site_id}
    if start_date:
        payload["start_date"] = start_date
    if end_date:
        payload["end_date"] = end_date
    url = f"{API_BASE}/api-users/property-registration-graph/"
    r = session.post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")
    return StringToolOutput(str(data.get("data") or {}))
