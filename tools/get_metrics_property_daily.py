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
def get_metrics_property_daily(
    property_id: int,
    start: str,
    end: str,
) -> StringToolOutput:
    """
    Get daily time series of metrics for a property. Calls api/metrics/properties/<id>/daily.
    Use for: How is interest trending as we approach close? Daily views and conversions for a property.
    start and end are YYYY-MM-DD (UTC).
    """
    params = {"start": start, "end": end}
    url = f"{API_BASE}/api/metrics/properties/{property_id}/daily"
    r = session.get(url, params=params, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    return StringToolOutput(str(r.json()))
