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
def get_site_detail(
    domain: str,
) -> StringToolOutput:
    """
    Get site/domain configuration and metadata. Calls api-users/get-site-detail/.
    Pass the domain name (e.g. example.com, without https://). Use for multi-tenant reporting.
    """
    domain_clean = domain.strip().lower()
    if domain_clean.startswith("http://"):
        domain_clean = domain_clean[7:]
    if domain_clean.startswith("https://"):
        domain_clean = domain_clean[8:]
    payload = {"domain_name": domain_clean}
    url = f"{API_BASE}/api-users/get-site-detail/"
    r = session.post(url, json=payload, timeout=30, verify=TLS_VERIFY)
    r.raise_for_status()
    data = r.json()
    if data.get("error") not in (0, "0", None):
        raise ValueError(f"API error: {data}")
    result = data.get("data") or {}
    return StringToolOutput(str(result))
