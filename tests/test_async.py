"""Tests for the asynchronous client."""

from __future__ import annotations

from decimal import Decimal

import httpx
import pytest
import respx

from angstrom_cyclos import AsyncCyclosClient, CyclosConfig


@respx.mock
@pytest.mark.asyncio
async def test_async_login_and_get_member(config: CyclosConfig) -> None:
    config = config
    respx.post("https://wallet.example.com/api/auth/session").mock(
        return_value=httpx.Response(
            200,
            json={"user": {"id": "u1"}, "sessionToken": "tok"},
        )
    )
    respx.get("https://wallet.example.com/api/users/u1").mock(
        return_value=httpx.Response(
            200,
            json={"id": "u1", "username": "alice"},
        )
    )

    async with AsyncCyclosClient(config) as client:
        session = await client.auth.login("admin", "secret")
        assert session.session_token == "tok"
        member = await client.members.get("u1")
        assert member.id == "u1"


@respx.mock
@pytest.mark.asyncio
async def test_async_transfer(config: CyclosConfig) -> None:
    respx.post("https://wallet.example.com/api/alice/payments").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "t1",
                "amount": "50000",
                "currency": "UGX",
                "status": "processed",
                "kind": "payment",
            },
        )
    )

    async with AsyncCyclosClient(config) as client:
        client._transport.session_token = "tok"
        transfer = await client.transfers.create(
            transfer_type="walletTransfer",
            from_account="alice",
            to_account="bob",
            amount=Decimal("50000"),
            currency="UGX",
        )
    assert transfer.amount == Decimal("50000")
    assert transfer.status == "SUCCESS"
