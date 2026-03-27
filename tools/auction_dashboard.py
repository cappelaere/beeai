import os

from beeai_framework.tools import StringToolOutput, tool

from tools._auction_api import post_json_with_retry

API_BASE = os.environ["API_URL"].rstrip("/")
AUTH_TOKEN = os.environ["AUTH_TOKEN"]
DEFAULT_SITE_ID = int(os.getenv("SITE_ID", "3"))
DEFAULT_USER_ID = os.getenv("USER_ID")
TLS_VERIFY = os.getenv("TLS_VERIFY", "true").lower() in ("1", "true", "yes")

PAGE_SIZE_CAP = 50


def _is_invalid_user_error(data: dict) -> bool:
    code = str(data.get("code"))
    msg = str(data.get("msg", "")).lower()
    return code == "3" and ("active user" in msg or "user not exist" in msg)


@tool
def auction_dashboard(
    domain_id: int = DEFAULT_SITE_ID,
    user_id: int | None = None,
    page: int = 1,
    page_size: int = 12,
    status: int | None = None,
    agent_id: int | None = None,
    auction_id: int | None = None,
    asset_id: int | None = None,
    search: str = "",
) -> StringToolOutput:
    """
    Auction-focused dashboard: list auction properties with status, dates, and filters.
    Calls api-property/property-auction-dashboard/. Requires domain_id and user_id (or set USER_ID in env).
    Use for: Show auction dashboard for site 3, list active auctions for agent 5, upcoming auctions (status 17).
    """
    uid = user_id if user_id is not None else (int(DEFAULT_USER_ID) if DEFAULT_USER_ID else None)
    if uid is None:
        raise ValueError("user_id is required (or set USER_ID in environment)")
    page_size = max(1, min(int(page_size), PAGE_SIZE_CAP))
    page = max(1, int(page))
    payload = {
        "domain_id": domain_id,
        "user_id": uid,
        "page": page,
        "page_size": page_size,
        "search": search,
    }
    if status is not None:
        payload["status"] = status
    if agent_id is not None:
        payload["agent_id"] = agent_id
    if auction_id is not None:
        payload["auction_id"] = auction_id
    if asset_id is not None:
        payload["asset_id"] = asset_id
    url = f"{API_BASE}/api-property/property-auction-dashboard/"
    data = post_json_with_retry(
        url=url,
        payload=payload,
        auth_token=AUTH_TOKEN,
        tls_verify=TLS_VERIFY,
    )
    if data.get("error") not in (0, "0", None):
        if _is_invalid_user_error(data):
            return StringToolOutput(
                str(
                    {
                        "error": "inactive_user",
                        "message": "API rejected user_id as invalid/inactive.",
                        "hint": "Use an active USER_ID in .env or pass user_id explicitly when calling the tool.",
                        "user_id": uid,
                        "domain_id": domain_id,
                    }
                )
            )
        raise ValueError(f"API error: {data}")
    return StringToolOutput(str(data.get("data") or {}))
