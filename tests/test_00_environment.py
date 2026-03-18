"""
First test: environment, API reachability, database connectivity.
Requires API and DB to be up (no mocks).
"""
import os

import pytest

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests


def test_api_url_is_set():
    api_url = os.environ.get("API_URL", "").strip()
    assert api_url, "API_URL must be set (e.g. in .env)"


def test_auth_token_is_set():
    auth_token = os.environ.get("AUTH_TOKEN", "").strip()
    assert auth_token, "AUTH_TOKEN must be set (e.g. in .env)"


def test_api_responds():
    api_base = os.environ.get("API_URL", "").rstrip("/")
    auth_token = os.environ.get("AUTH_TOKEN", "")
    if not api_base or not auth_token:
        pytest.skip("API_URL or AUTH_TOKEN not set")
    url = f"{api_base}/api-property/asset-listing/"
    headers = {
        "Authorization": f"Token {auth_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(
            url,
            json={},
            headers=headers,
            timeout=10,
            verify=os.environ.get("TLS_VERIFY", "true").lower() in ("1", "true", "yes"),
        )
    except requests.RequestException as e:
        pytest.fail(f"Cannot reach API at {url}: {e}")
    assert r.status_code in (200, 201), f"API returned {r.status_code}, expected 200 or 201"


def test_api_returns_valid_data_from_db():
    api_base = os.environ.get("API_URL", "").rstrip("/")
    auth_token = os.environ.get("AUTH_TOKEN", "")
    if not api_base or not auth_token:
        pytest.skip("API_URL or AUTH_TOKEN not set")
    url = f"{api_base}/api-property/asset-listing/"
    headers = {
        "Authorization": f"Token {auth_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(
            url,
            json={},
            headers=headers,
            timeout=10,
            verify=os.environ.get("TLS_VERIFY", "true").lower() in ("1", "true", "yes"),
        )
    except requests.RequestException as e:
        pytest.fail(f"Cannot reach API: {e}")
    assert r.status_code in (200, 201), f"API returned {r.status_code}"
    data = r.json()
    assert "error" in data
    assert data.get("error") in (0, "0", None), f"API error: {data}"
    assert "data" in data
