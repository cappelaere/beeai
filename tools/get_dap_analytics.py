"""
GSA Digital Analytics Program (DAP) API tools.
Fetches web analytics for DAP-participating .gov domains (e.g. realestatesales.gov).
Auth: x-api-key header. API key from api.data.gov / DAP_API_KEY in env.
"""

import os

import requests
from beeai_framework.tools import StringToolOutput, tool

DAP_API_BASE = os.environ.get("DAP_API_BASE", "https://api.gsa.gov/analytics/dap").rstrip("/")
DAP_API_KEY = os.environ.get("DAP_API_KEY", "")
TLS_VERIFY = os.getenv("TLS_VERIFY", "true").lower() in ("1", "true", "yes")

session = requests.Session()
session.headers.update(
    {
        "x-api-key": DAP_API_KEY,
        "Accept": "application/json",
    }
)


@tool
def get_dap_domain_analytics(
    domain: str = "realestatesales.gov",
    report: str = "site",
    after: str | None = None,
    before: str | None = None,
    limit: int | None = None,
) -> StringToolOutput:
    """
    Get DAP (Digital Analytics Program) analytics for a .gov domain.
    Default domain: realestatesales.gov. Use for weekly/monthly traffic, page views, and trends.
    Provide after and before as YYYY-MM-DD (e.g. after=2024-03-01, before=2024-03-31).
    V2 data is available from Aug 2023 to present. Data is sampled and high-level.
    """
    if not DAP_API_KEY:
        return StringToolOutput("Error: DAP_API_KEY is not set. Set it in .env to use the DAP API.")
    params = {}
    if after:
        params["after"] = after
    if before:
        params["before"] = before
    if limit is not None:
        params["limit"] = max(1, min(int(limit), 1000))
    url = f"{DAP_API_BASE}/v2/domain/{domain}/reports/{report}/data"
    try:
        r = session.get(url, params=params or None, timeout=30, verify=TLS_VERIFY)
        r.raise_for_status()
        return StringToolOutput(str(r.json()))
    except requests.exceptions.HTTPError as e:
        return StringToolOutput(
            f"DAP API error: {e.response.status_code} - {e.response.text[:500]}"
        )
    except requests.exceptions.RequestException as e:
        return StringToolOutput(f"DAP API request failed: {e!s}")
