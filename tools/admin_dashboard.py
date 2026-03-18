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
def admin_dashboard(
    site_id: int = DEFAULT_SITE_ID,
    start_date: str | None = None,
    end_date: str | None = None,
) -> StringToolOutput:
    """
    Admin dashboard counts and analytics for a site. Calls api-users/admin-dashboard/.
    Optional start_date and end_date (YYYY-MM-DD) to filter by date range.
    Use for: Show admin dashboard for site 3, key platform metrics.
    """
    payload = {"site_id": site_id}
    if start_date:
        payload["start_date"] = start_date
    if end_date:
        payload["end_date"] = end_date
    url = f"{API_BASE}/api-users/admin-dashboard/"
    r = session.post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")
    return StringToolOutput(str(data.get("data") or {}))
