"""Tests for transport layer behavior: retries, redaction, and pagination."""

from __future__ import annotations

import logging

import httpx
import pytest
import respx

from angstrom_cyclos import CyclosClient, CyclosConfig, CyclosConnectionError


@respx.mock
def test_safe_retry_on_connection_error(
    config: CyclosConfig,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Read operations are retried when the server returns transient errors."""
    config.max_retries = 3
    config.retry_backoff = 0.01
    client = CyclosClient(config)
    client._transport.session_token = "token"

    route = respx.get("https://wallet.example.com/api/users/u1").mock(
        side_effect=[
            httpx.ConnectError("connection refused"),
            httpx.Response(200, json={"id": "u1", "username": "alice"}),
        ]
    )

    caplog.set_level(logging.DEBUG, logger="cyclos")
    member = client.members.get("u1")
    assert member.id == "u1"
    assert route.call_count == 2
    assert "connection refused" in caplog.text or "Retry" in caplog.text


@respx.mock
def test_financial_writes_not_retried(config: CyclosConfig) -> None:
    """Financial POSTs are not blindly retried."""
    config.max_retries = 3
    config.retry_backoff = 0.01
    client = CyclosClient(config)
    client._transport.session_token = "token"

    route = respx.post("https://wallet.example.com/api/alice/payments").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    with pytest.raises(CyclosConnectionError):
        client.transfers.create(
            transfer_type="walletTransfer",
            from_account="alice",
            to_account="bob",
            amount=10_000,
            currency="UGX",
        )
    assert route.call_count == 1


@respx.mock
def test_header_redaction(config: CyclosConfig, caplog: pytest.LogCaptureFixture) -> None:
    """Session token and password must not leak into request/response logs."""
    caplog.set_level(logging.DEBUG, logger="cyclos")
    client = CyclosClient(config)
    client._transport.session_token = "super-secret-token"

    respx.get("https://wallet.example.com/api/users/u1").mock(
        return_value=httpx.Response(200, json={"id": "u1", "username": "alice"})
    )
    client.members.get("u1")

    assert "super-secret-token" not in caplog.text


def test_pagination_next_page_indicator(config: CyclosConfig) -> None:
    """PaginatedResult reports has_next_page based on page_size."""
    from angstrom_cyclos.models import PaginatedResult

    page = PaginatedResult[
        dict[str, str]
    ](
        items=[{"id": "1"}, {"id": "2"}],
        page=0,
        page_size=2,
        total_count=None,
    )
    assert page.has_next is True


@respx.mock
def test_basic_auth_fallback_when_no_token(config: CyclosConfig) -> None:
    """Configured credentials are sent as Basic auth when no token is active."""
    client = CyclosClient(config)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"id": "u1", "username": "alice"})

    respx.get("https://wallet.example.com/api/users/u1").mock(side_effect=handler)
    client.members.get("u1")

    assert len(requests) == 1
    authorization = requests[0].headers.get("Authorization")
    assert authorization is not None
    assert authorization.startswith("Basic ")
