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
def get_metrics_property_summary(
    property_id: int,
    days: int | None = None,
    start: str | None = None,
    end: str | None = None,
) -> StringToolOutput:
    """
    Get aggregated metrics for a single property over a period. Calls api/metrics/properties/<id>/summary.
    Use for: How is my property performing (last 7/30 days)? Is engagement normal? Why is my property not getting bidders?
    Provide either days (e.g. 7 or 30) or both start and end (YYYY-MM-DD).
    """
    if days is not None and start is None and end is None:
        params = {"days": max(1, min(int(days), 3660))}
    elif start and end:
        params = {"start": start, "end": end}
    else:
        raise ValueError("Provide either days=N or both start= and end= (YYYY-MM-DD)")
    url = f"{API_BASE}/api/metrics/properties/{property_id}/summary"
    r = session.get(url, params=params, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    return StringToolOutput(str(r.json()))
