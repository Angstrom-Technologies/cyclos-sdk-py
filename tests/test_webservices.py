"""Tests for web service / access client management."""

from __future__ import annotations

import httpx
import respx

from angstrom_cyclos import CyclosClient, CyclosConfig


@respx.mock
def test_create_client(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/clients/default").mock(
        return_value=httpx.Response(
            200,
            json={
                "token": "secret-token",
                "accessClient": {"id": "c1", "name": "Angstrom Wallet API"},
                "accessClientType": {"id": "t1", "name": "default"},
            },
        )
    )
    ws_client = client.webservices.create_client(
        name="Angstrom Wallet API",
        activation_code="123456",
    )
    assert ws_client.id == "c1"
    assert client._transport.access_client_token == "secret-token"


@respx.mock
def test_get_client(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.get("https://wallet.example.com/api/clients/c1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "c1",
                "name": "Angstrom Wallet API",
                "status": "active",
                "user": {"id": "u1"},
            },
        )
    )
    ws_client = client.webservices.get_client("c1")
    assert ws_client.id == "c1"


@respx.mock
def test_delete_client(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/clients/c1/unassign").mock(
        return_value=httpx.Response(200)
    )
    client.webservices.delete_client("c1")
