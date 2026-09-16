"""Fetch accounts for a Cyclos user using an OpenID client-credentials token.

Configure the environment, then run:

    python scripts/openid_fetch_accounts.py

Required environment variables:
    CYCLOS_OPENID_CLIENT_ID
    CYCLOS_OPENID_CLIENT_SECRET

Optional environment variables:
    CYCLOS_BASE_URL     (default: https://wallet.angstrom-technologies.ug/uwallet/api)
    CYCLOS_OWNER        (default: angstromUg)
"""

from __future__ import annotations

import os
import sys

import httpx

BASE_URL = os.environ.get(
    "CYCLOS_BASE_URL",
    "https://wallet.angstrom-technologies.ug/uwallet/api",
).rstrip("/")
CLIENT_ID = os.environ.get("CYCLOS_OPENID_CLIENT_ID")
CLIENT_SECRET = os.environ.get("CYCLOS_OPENID_CLIENT_SECRET")
OWNER = os.environ.get("CYCLOS_OWNER", "angstromUg")


def discover_token_endpoint(client: httpx.Client, base_url: str) -> str:
    """Return the OIDC token endpoint, trying discovery first."""
    well_known = f"{base_url}/.well-known/openid-configuration"
    try:
        response = client.get(well_known, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        token_endpoint = data.get("token_endpoint")
        if token_endpoint:
            print(f"Discovered token endpoint: {token_endpoint}")
            return token_endpoint
    except Exception as exc:  # noqa: BLE001
        print(f"OIDC discovery failed ({well_known}): {exc}")

    # Fallback to the common Cyclos OAuth2 token endpoint path.
    fallback = f"{base_url}/oauth/token"
    print(f"Falling back to token endpoint: {fallback}")
    return fallback


def fetch_token(client: httpx.Client, token_endpoint: str) -> str:
    """Obtain an access token using the client_credentials grant."""
    response = client.post(
        token_endpoint,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Accept": "application/json"},
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()
    token = data.get("access_token") or data.get("id_token")
    if not token:
        print("Token response did not contain access_token or id_token")
        print(data)
        sys.exit(1)
    print(f"Got token (expires_in={data.get('expires_in')})")
    return token


def fetch_accounts(client: httpx.Client, base_url: str, token: str, owner: str) -> list[dict]:
    """Fetch the accounts for the given owner using a Bearer token."""
    url = f"{base_url}/{owner}/accounts"
    response = client.get(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        },
        timeout=30.0,
    )
    print(f"GET {url} -> {response.status_code}")
    print(response.text)
    response.raise_for_status()
    return response.json()


def main() -> int:
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Set CYCLOS_OPENID_CLIENT_ID and CYCLOS_OPENID_CLIENT_SECRET")
        return 1

    with httpx.Client() as client:
        token_endpoint = discover_token_endpoint(client, BASE_URL)
        token = fetch_token(client, token_endpoint)
        accounts = fetch_accounts(client, BASE_URL, token, OWNER)
        print(f"\nFound {len(accounts)} account(s) for {OWNER}")
        for account in accounts:
            print(f"  - {account}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
