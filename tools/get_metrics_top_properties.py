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

ALLOWED_METRICS = (
    "views",
    "unique_sessions",
    "brochure_downloads",
    "ifb_downloads",
    "subscriber_registrations",
    "bidder_registrations",
    "photo_clicks",
)


@tool
def get_metrics_top_properties(
    days: int = 7,
    metric: str = "views",
    limit: int = 20,
) -> StringToolOutput:
    """
    Rank properties by a metric over a period. Calls api/metrics/top-properties.
    Use for: Rank properties by IFB downloads / bidder registrations. Top performers. Which properties have strong interest?
    metric: one of views, unique_sessions, brochure_downloads, ifb_downloads, subscriber_registrations, bidder_registrations, photo_clicks.
    """
    if metric not in ALLOWED_METRICS:
        raise ValueError(f"metric must be one of {ALLOWED_METRICS}")
    days = max(1, min(int(days), 3660))
    limit = max(1, min(int(limit), 500))
    params = {"days": days, "metric": metric, "limit": limit}
    url = f"{API_BASE}/api/metrics/top-properties"
    r = session.get(url, params=params, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    return StringToolOutput(str(r.json()))
