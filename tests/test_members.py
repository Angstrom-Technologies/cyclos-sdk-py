"""Tests for member management."""

from __future__ import annotations

import httpx
import pytest
import respx

from angstrom_cyclos import CyclosClient, CyclosConfig, CyclosValidationError


@respx.mock
def test_create_individual(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/users").mock(
        return_value=httpx.Response(
            201,
            json={"user": {"id": "m1", "username": "256772123456"}, "status": "active"},
        )
    )
    result = client.members.create_individual(
        username="256772123456",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        mobile="256772123456",
        custom_fields={"kycStatus": "VERIFIED"},
    )
    assert result.user.id == "m1"


@respx.mock
def test_create_merchant(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/users").mock(
        return_value=httpx.Response(
            201,
            json={"user": {"id": "m2", "username": "merchant001"}, "status": "active"},
        )
    )
    result = client.members.create_merchant(
        username="merchant001",
        name="Merchant One",
        group="merchant",
    )
    assert result.user.id == "m2"


@respx.mock
def test_get_member(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.get("https://wallet.example.com/api/users/m1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "m1",
                "username": "256772123456",
                "group": {"id": "g1", "name": "individual"},
            },
        )
    )
    member = client.members.get("m1")
    assert member.id == "m1"


@respx.mock
def test_get_member_status_as_string(config: CyclosConfig) -> None:
    """Cyclos sometimes returns status as a plain string (e.g. 'active')."""
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.get("https://wallet.example.com/api/users/m1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "m1",
                "username": "256772123456",
                "status": "active",
            },
        )
    )
    member = client.members.get("m1")
    assert member.status == "active"


@respx.mock
def test_search_members(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.get("https://wallet.example.com/api/users").mock(
        return_value=httpx.Response(
            200,
            json=[{"id": "m1", "username": "256772123456"}],
        )
    )
    result = client.members.search(query="256772123456")
    assert len(result.items) == 1


@respx.mock
def test_activate_deactivate_member(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/m1/status").mock(return_value=httpx.Response(200))
    client.members.activate("m1")
    respx.post("https://wallet.example.com/api/m1/status").mock(return_value=httpx.Response(200))
    client.members.deactivate("m1")


@respx.mock
def test_duplicate_member_validation_error(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/users").mock(
        return_value=httpx.Response(
            422,
            json={
                "code": "validation",
                "propertyErrors": {"username": ["Already in use"]},
            },
        )
    )
    with pytest.raises(CyclosValidationError) as exc_info:
        client.members.create(
            group="individualCustomer",
            username="256772123456",
        )
    assert "username" in exc_info.value.property_errors
