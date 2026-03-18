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
def get_metrics_event_types() -> StringToolOutput:
    """
    Get the list of property metric event types (id, event_type, description).
    Use when the user asks what metrics are tracked, what an event type or event number means,
    or for the canonical list of event types.
    """
    url = f"{API_BASE}/api/metrics/event-types"
    r = session.get(url, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    return StringToolOutput(str(r.json()))
