import time
from typing import Any

import requests


def post_json_with_retry(
    *,
    url: str,
    payload: dict[str, Any],
    auth_token: str,
    tls_verify: bool,
    timeout_seconds: int = 30,
    max_attempts: int = 2,
    backoff_seconds: float = 0.25,
) -> dict[str, Any]:
    """
    POST JSON with explicit bounded retry and exponential backoff.

    Raises ValueError after retry budget is exhausted.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    headers = {
        "Authorization": f"Token {auth_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    for attempt in range(max_attempts):
        try:
            with requests.Session() as session:
                session.headers.update(headers)
                response = session.post(
                    url,
                    json=payload,
                    timeout=timeout_seconds,
                    verify=tls_verify,
                )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError(f"Expected JSON object, got {type(data).__name__}")
            return data
        except (requests.RequestException, ValueError) as exc:
            if attempt == max_attempts - 1:
                raise ValueError(f"Request failed after {max_attempts} attempt(s): {exc}") from exc
            time.sleep(backoff_seconds * (2**attempt))

    # Defensive: loop always returns or raises above.
    raise ValueError("Request failed without response")
