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
def get_metrics_properties_with_activity(
    days: int = 7,
    limit: int = 500,
) -> StringToolOutput:
    """
    List property_ids that have at least one metrics record in the period. Calls api/metrics/properties-with-activity.
    Use for: Which properties had any activity; to compute 'no activity' combine with list_properties (active IDs not in this set = no activity in the period).
    """
    params = {
        "days": max(1, min(int(days), 3660)),
        "limit": max(1, min(int(limit), 5000)),
    }
    url = f"{API_BASE}/api/metrics/properties-with-activity"
    r = session.get(url, params=params, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    return StringToolOutput(str(r.json()))
