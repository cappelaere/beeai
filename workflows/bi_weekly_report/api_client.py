"""
Sync HTTP client for metrics and property API. Used by BiWeeklyReportWorkflow via asyncio.to_thread.
Uses API_URL and AUTH_TOKEN from environment (same as tools).
"""
import os
from typing import Any

import requests

API_BASE = os.environ.get("API_URL", "").rstrip("/")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")
TLS_VERIFY = os.getenv("TLS_VERIFY", "true").lower() in ("1", "true", "yes")
DEFAULT_SITE_ID = int(os.getenv("SITE_ID", "3"))


def _session():
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Token {AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    return s


def list_properties(page_size: int = 50, page: int = 1, site_id: int = DEFAULT_SITE_ID) -> dict:
    """POST api-property/front-property-listing/; returns { data: { data: [ {id, name, status, ...} ] } }."""
    url = f"{API_BASE}/api-property/front-property-listing/"
    payload = {
        "site_id": str(site_id),
        "page_size": page_size,
        "page": page,
        "search": "",
        "filter": "",
        "short_by": "ending_soonest",
        "sort_order": "asc",
        "agent_id": "",
        "user_id": "",
    }
    r = _session().post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")
    return data


def property_summary(property_id: int, start_date: str, end_date: str) -> dict:
    """GET api/metrics/properties/<id>/summary?start=&end=; returns { property_id, range, totals }."""
    url = f"{API_BASE}/api/metrics/properties/{property_id}/summary"
    params = {"start": start_date, "end": end_date}
    r = _session().get(url, params=params, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    return r.json()


def top_properties(start_date: str, end_date: str, metric: str = "views", limit: int = 10) -> dict:
    """GET api/metrics/top-properties?start=&end=&metric=&limit=; returns { items: [ {property_id, views, ...} ] }."""
    url = f"{API_BASE}/api/metrics/top-properties"
    params = {"start": start_date, "end": end_date, "metric": metric, "limit": limit}
    r = _session().get(url, params=params, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    return r.json()


def underperforming(
    start_date: str,
    end_date: str,
    min_views: int = 50,
    max_bidder_registrations: int = 2,
    limit: int = 50,
) -> dict:
    """GET api/metrics/underperforming?start=&end=&min_views=&max_bidder_registrations=&limit=."""
    url = f"{API_BASE}/api/metrics/underperforming"
    params = {
        "start": start_date,
        "end": end_date,
        "min_views": min_views,
        "max_bidder_registrations": max_bidder_registrations,
        "limit": limit,
    }
    r = _session().get(url, params=params, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    return r.json()


def property_detail(property_id: int, site_id: int = DEFAULT_SITE_ID) -> dict:
    """POST api-property/property-detail/; returns { data: { ... } }."""
    url = f"{API_BASE}/api-property/property-detail/"
    payload = {"site_id": str(site_id), "property_id": property_id}
    r = _session().post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")
    return data.get("data") or {}
