"""Tests for authentication."""

from __future__ import annotations

import httpx
import pytest
import respx
from pydantic import SecretStr

from angstrom_cyclos import CyclosAuthenticationError, CyclosClient, CyclosConfig


@respx.mock
def test_login_success(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    route = respx.post("https://wallet.example.com/api/auth/session").mock(
        return_value=httpx.Response(
            200,
            json={
                "user": {"id": "u1", "display": "Admin"},
                "sessionToken": "abc123",
                "principal": "admin",
            },
        )
    )
    session = client.auth.login("admin", "secret")

    assert session.session_token == "abc123"
    assert client._transport.session_token == "abc123"
    assert route.called


@respx.mock
def test_login_invalid_credentials(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    respx.post("https://wallet.example.com/api/auth/session").mock(
        return_value=httpx.Response(
            401,
            json={"code": "login", "exceptionMessage": "Invalid credentials"},
        )
    )
    with pytest.raises(CyclosAuthenticationError) as exc_info:
        client.auth.login("admin", "wrong")
    assert exc_info.value.status_code == 401


@respx.mock
def test_logout(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "abc123"
    route = respx.delete("https://wallet.example.com/api/auth/session").mock(
        return_value=httpx.Response(200)
    )
    client.auth.logout()
    assert client._transport.session_token is None
    assert route.called


@respx.mock
def test_current_user(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "abc123"
    respx.get("https://wallet.example.com/api/auth").mock(
        return_value=httpx.Response(
            200,
            json={"user": {"id": "u1", "display": "Admin"}, "principal": "admin"},
        )
    )
    auth = client.auth.current_user()
    assert auth.user and auth.user.id == "u1"


@respx.mock
def test_is_authenticated(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    assert not client.auth.is_authenticated()
    client._transport.session_token = "x"
    assert client.auth.is_authenticated()


def test_access_client_token_from_config_is_used() -> None:
    config = CyclosConfig(
        base_url="https://wallet.example.com/api",
        access_client_token=SecretStr("activated-token"),
    )
    client = CyclosClient(config)

    assert client.auth.is_authenticated()
    headers = client._transport._build_headers()
    assert headers["Access-Client-Token"] == "activated-token"
