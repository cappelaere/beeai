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
def get_metrics_underperforming(
    days: int = 30,
    min_views: int = 200,
    max_bidder_registrations: int = 2,
    limit: int = 50,
    interest_metric: str = "views",
    min_ifb_downloads: int | None = None,
    min_brochure_downloads: int | None = None,
) -> StringToolOutput:
    """
    List properties with high interest but low bidder registrations. Calls api/metrics/underperforming.
    Use for: Underperformers (high views, low bidders); high IFB downloads but low bidders; high brochure downloads but low bidders; which listings need attention; which may struggle attracting bidders.
    interest_metric: views (default), ifb_downloads, or brochure_downloads. When ifb_downloads use min_ifb_downloads; when brochure_downloads use min_brochure_downloads.
    """
    params = {
        "days": max(1, min(int(days), 3660)),
        "min_views": max(0, int(min_views)),
        "max_bidder_registrations": max(0, int(max_bidder_registrations)),
        "limit": max(1, min(int(limit), 500)),
        "interest_metric": interest_metric.strip().lower(),
    }
    if interest_metric == "ifb_downloads" and min_ifb_downloads is not None:
        params["min_ifb_downloads"] = max(0, int(min_ifb_downloads))
    if interest_metric == "brochure_downloads" and min_brochure_downloads is not None:
        params["min_brochure_downloads"] = max(0, int(min_brochure_downloads))
    url = f"{API_BASE}/api/metrics/underperforming"
    r = session.get(url, params=params, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    return StringToolOutput(str(r.json()))
