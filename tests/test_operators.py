"""Tests for operator management."""

from __future__ import annotations

import httpx
import respx

from angstrom_cyclos import CyclosClient, CyclosConfig


@respx.mock
def test_create_operator(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/o1/operators").mock(
        return_value=httpx.Response(
            201,
            json={"user": {"id": "op1", "username": "operator001"}, "status": "active"},
        )
    )
    result = client.operators.create(
        organization_id="o1",
        username="operator001",
        first_name="Jane",
        last_name="Doe",
    )
    assert result.user.id == "op1"


@respx.mock
def test_assign_permissions(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.get("https://wallet.example.com/api/o1/operators/op1").mock(
        return_value=httpx.Response(
            200,
            json={"id": "op1", "group": {"id": "g1", "name": "operators"}},
        )
    )
    respx.put("https://wallet.example.com/api/o1/operator-groups/g1").mock(
        return_value=httpx.Response(200)
    )
    client.operators.assign_permissions(
        organization_id="o1",
        operator_id="op1",
        permissions=["VIEW_MEMBER", "PERFORM_TRANSFER"],
    )


@respx.mock
def test_activate_deactivate_operator(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/o1/operators/op1/status").mock(
        return_value=httpx.Response(200)
    )
    client.operators.activate("o1", "op1")
    respx.post("https://wallet.example.com/api/o1/operators/op1/status").mock(
        return_value=httpx.Response(200)
    )
    client.operators.deactivate("o1", "op1")
