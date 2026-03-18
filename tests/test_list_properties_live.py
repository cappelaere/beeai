#!/usr/bin/env python3
"""Standalone script to test the property API directly (no agent, no LLM, no mocks)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import requests


def main():
    api_base = os.environ.get("API_URL", "").rstrip("/")
    auth_token = os.environ.get("AUTH_TOKEN")
    tls_verify = os.environ.get("TLS_VERIFY", "true").lower() in ("1", "true", "yes")

    if not api_base or not auth_token:
        print("Set API_URL and AUTH_TOKEN in .env")
        sys.exit(1)

    url = f"{api_base}/api-property/front-property-listing/"
    headers = {
        "Authorization": f"Token {auth_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "site_id": "3",
        "page_size": 5,
        "page": 1,
        "search": "",
        "filter": "",
        "short_by": "ending_soonest",
        "sort_order": "asc",
        "agent_id": "",
        "user_id": "",
    }

    print(f"Calling {url} ...")
    r = requests.post(url, json=payload, headers=headers, timeout=30, verify=tls_verify)
    print(f"Status: {r.status_code}")

    if r.ok:
        data = r.json()
        items = (data.get("data") or {}).get("data") or []
        print(f"Got {len(items)} properties")
        for i, p in enumerate(items[:3], 1):
            print(f"  {i}. {p.get('name', 'N/A')} - {p.get('city', '')}, {p.get('iso_state_name', '')}")
    else:
        print(r.text[:500])


if __name__ == "__main__":
    main()
