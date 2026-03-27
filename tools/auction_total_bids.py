import os

from beeai_framework.tools import StringToolOutput, tool

from tools._auction_api import post_json_with_retry

API_BASE = os.environ["API_URL"].rstrip("/")
AUTH_TOKEN = os.environ["AUTH_TOKEN"]
DEFAULT_SITE_ID = int(os.getenv("SITE_ID", "3"))
DEFAULT_USER_ID = os.getenv("USER_ID")
TLS_VERIFY = os.getenv("TLS_VERIFY", "true").lower() in ("1", "true", "yes")

PAGE_SIZE_CAP = 50


def _is_inactive_user_error(data: dict) -> bool:
    return str(data.get("code")) == "3" and "active user" in str(data.get("msg", "")).lower()


@tool
def auction_total_bids(
    property_id: int,
    site_id: int = DEFAULT_SITE_ID,
    user_id: int | None = None,
    page: int = 1,
    page_size: int = 12,
) -> StringToolOutput:
    """
    Bid activity summary per bidder for an auction property. Calls api-bid/auction-total-bids/.
    Use for: Show bid summary for property 100, who has the highest bid on property 500.
    """
    uid = user_id if user_id is not None else (int(DEFAULT_USER_ID) if DEFAULT_USER_ID else None)
    if uid is None:
        raise ValueError("user_id is required (or set USER_ID in environment)")
    page_size = max(1, min(int(page_size), PAGE_SIZE_CAP))
    page = max(1, int(page))
    payload = {
        "site_id": site_id,
        "property_id": property_id,
        "user_id": uid,
        "page": page,
        "page_size": page_size,
    }
    url = f"{API_BASE}/api-bid/auction-total-bids/"
    data = post_json_with_retry(
        url=url,
        payload=payload,
        auth_token=AUTH_TOKEN,
        tls_verify=TLS_VERIFY,
    )
    if data.get("error") not in (0, "0", None):
        if _is_inactive_user_error(data):
            return StringToolOutput(
                str(
                    {
                        "error": "inactive_user",
                        "message": "API rejected user_id as inactive.",
                        "hint": "Use an active USER_ID in .env or pass user_id explicitly when calling the tool.",
                        "user_id": uid,
                        "site_id": site_id,
                        "property_id": property_id,
                    }
                )
            )
        raise ValueError(f"API error: {data}")
    return StringToolOutput(str(data.get("data") or {}))
