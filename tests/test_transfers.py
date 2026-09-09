"""Tests for transfers and transfer history."""

from __future__ import annotations

from decimal import Decimal

import httpx
import pytest
import respx

from angstrom_cyclos import CyclosClient, CyclosConfig, CyclosIdempotencyError, CyclosTransferError


@respx.mock
def test_successful_transfer(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/alice/payments").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "t1",
                "amount": "50000",
                "currency": "UGX",
                "description": "P2P transfer",
                "status": "processed",
                "kind": "payment",
            },
        )
    )
    transfer = client.transfers.create(
        transfer_type="walletTransfer",
        from_account="alice",
        to_account="bob",
        amount=Decimal("50000"),
        currency="UGX",
        description="P2P transfer",
        idempotency_key="TXN-20260909-000001",
    )
    assert transfer.amount == Decimal("50000")
    assert transfer.status == "SUCCESS"


@respx.mock
def test_failed_transfer_insufficient_balance(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/alice/payments").mock(
        return_value=httpx.Response(
            500,
            json={
                "exceptionType": "PaymentException",
                "exceptionMessage": "Insufficient balance",
            },
        )
    )
    with pytest.raises(CyclosTransferError) as exc_info:
        client.transfers.create(
            transfer_type="walletTransfer",
            from_account="alice",
            to_account="bob",
            amount=Decimal("50000"),
            currency="UGX",
        )
    assert exc_info.value.status_code == 500


@respx.mock
def test_duplicate_transfer_rejected(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.post("https://wallet.example.com/api/alice/payments").mock(
        return_value=httpx.Response(
            201,
            json={"id": "t1", "amount": "50000", "currency": "UGX", "status": "processed"},
        )
    )
    client.transfers.create(
        transfer_type="walletTransfer",
        from_account="alice",
        to_account="bob",
        amount=Decimal("50000"),
        currency="UGX",
        idempotency_key="DUP-1",
    )
    with pytest.raises(CyclosIdempotencyError):
        client.transfers.create(
            transfer_type="walletTransfer",
            from_account="alice",
            to_account="bob",
            amount=Decimal("50000"),
            currency="UGX",
            idempotency_key="DUP-1",
        )


@respx.mock
def test_transfer_history(config: CyclosConfig) -> None:
    client = CyclosClient(config)
    client._transport.session_token = "token"
    respx.get("https://wallet.example.com/api/m1/accounts/mobileWallet/history").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "h1",
                    "amount": "10000",
                    "date": "2026-09-09T00:00:00Z",
                    "transactionNumber": "TXN-1",
                }
            ],
        )
    )
    history = client.transfers.history(
        member_id="m1",
        account_type="mobileWallet",
        page=0,
        page_size=50,
    )
    assert len(history.items) == 1
    assert history.items[0].amount == Decimal("10000")
