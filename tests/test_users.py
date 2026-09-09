"""Tests for low-level user client."""

from __future__ import annotations

import httpx
import respx

from angstrom_cyclos import CyclosClient, CyclosConfig


@respx.mock
def test_users_create_and_get(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/users").mock(
        return_value=httpx.Response(
            201,
            json={"user": {"id": "u1", "username": "alice"}, "status": "active"},
        )
    )
    result = client.users.create(group="individualCustomer", username="alice")
    assert result.user.id == "u1"

    respx.get("https://wallet.example.com/api/users/u1").mock(
        return_value=httpx.Response(
            200,
            json={"id": "u1", "username": "alice"},
        )
    )
    user = client.users.get("u1")
    assert user.id == "u1"
