"""Tests for organization client."""

from __future__ import annotations

import httpx
import respx

from angstrom_cyclos import CyclosClient, CyclosConfig


@respx.mock
def test_create_organization(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/users").mock(
        return_value=httpx.Response(
            201,
            json={
                "user": {"id": "o1", "username": "abc_limited"},
                "status": "active",
            },
        )
    )
    result = client.organizations.create(
        group="corporate",
        username="abc_limited",
        name="ABC Limited",
        custom_fields={"businessRegistrationNumber": "800200012345"},
    )
    assert result.user.id == "o1"


@respx.mock
def test_get_organization(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.get("https://wallet.example.com/api/users/o1").mock(
        return_value=httpx.Response(
            200,
            json={"id": "o1", "username": "abc_limited", "name": "ABC Limited"},
        )
    )
    org = client.organizations.get("o1")
    assert org.id == "o1"
