"""Tests for transaction lookup."""

from __future__ import annotations

import httpx
import respx

from angstrom_cyclos import CyclosClient, CyclosConfig


@respx.mock
def test_get_transaction(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.get("https://wallet.example.com/api/transactions/t1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "t1",
                "amount": "10000",
                "currency": "UGX",
                "kind": "payment",
            },
        )
    )
    transaction = client.transactions.get("t1")
    assert transaction.id == "t1"


@respx.mock
def test_search_transactions(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.get("https://wallet.example.com/api/transactions").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "t1",
                    "amount": "10000",
                    "currency": "UGX",
                    "transactionNumber": "TXN-1",
                }
            ],
        )
    )
    result = client.transactions.search(transaction_number="TXN-1")
    assert len(result.items) == 1
    assert result.items[0].transaction_number == "TXN-1"
