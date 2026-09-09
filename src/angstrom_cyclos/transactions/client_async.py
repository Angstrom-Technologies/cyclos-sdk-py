"""Asynchronous transaction client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from angstrom_cyclos.models import PaginatedResult
from angstrom_cyclos.transactions.models import Transaction

if TYPE_CHECKING:
    from angstrom_cyclos.async_client import AsyncCyclosClient


class AsyncTransactionsClient:
    """Async transaction lookup client."""

    def __init__(self, client: AsyncCyclosClient) -> None:
        self._client = client

    async def get(self, transaction_id: str) -> Transaction:
        response = await self._client._transport.get(f"/transactions/{transaction_id}")
        return Transaction.from_cyclos(response.json())

    async def search(
        self,
        *,
        member_id: str | None = None,
        transaction_number: str | None = None,
        external_reference: str | None = None,
        provider_reference: str | None = None,
        transfer_id: str | None = None,
        page: int = 0,
        page_size: int = 20,
        **filters: Any,
    ) -> PaginatedResult[Transaction]:
        params: dict[str, Any] = {"page": page, "pageSize": page_size}
        if transaction_number:
            params["transactionNumber"] = transaction_number
        if external_reference:
            params["externalReference"] = external_reference
        if provider_reference:
            params["providerReference"] = provider_reference
        if transfer_id:
            params["transferId"] = transfer_id
        for key, value in filters.items():
            if value is not None:
                params[key] = value
        if member_id:
            response = await self._client._transport.get(
                f"/{member_id}/transactions", params=params
            )
        else:
            response = await self._client._transport.get("/transactions", params=params)
        items = [Transaction.from_cyclos(entry) for entry in response.json()]
        return PaginatedResult[Transaction](
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(items) >= page_size,
        )
