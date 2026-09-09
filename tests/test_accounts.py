"""Tests for account management."""

from __future__ import annotations

from decimal import Decimal

import httpx
import respx

from angstrom_cyclos import CyclosClient, CyclosConfig


@respx.mock
def test_get_balance(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.get("https://wallet.example.com/api/m1/accounts/mobileWallet").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "a1",
                "type": {"id": "mobileWallet"},
                "currency": {"id": "UGX", "name": "Uganda Shilling"},
                "status": {
                    "balance": "150000",
                    "availableBalance": "150000",
                    "reservedAmount": "0",
                },
            },
        )
    )
    balance = client.accounts.get_balance(member_id="m1", account_type="mobileWallet")
    assert balance.balance == Decimal("150000")
    assert balance.currency == "Uganda Shilling"


@respx.mock
def test_list_accounts(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.get("https://wallet.example.com/api/m1/accounts").mock(
        return_value=httpx.Response(
            200,
            json=[{"id": "a1", "type": {"id": "mobileWallet"}}],
        )
    )
    result = client.accounts.list(member_id="m1")
    assert len(result.items) == 1
