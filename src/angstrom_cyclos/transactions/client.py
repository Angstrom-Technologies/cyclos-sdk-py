"""Transaction lookup client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from angstrom_cyclos.models import PaginatedResult
from angstrom_cyclos.transactions.models import Transaction

if TYPE_CHECKING:
    from angstrom_cyclos.client import CyclosClient


class TransactionsClient:
    """Retrieve transactions by id, number or search criteria."""

    def __init__(self, client: CyclosClient) -> None:
        self._client = client

    def get(self, transaction_id: str) -> Transaction:
        """Retrieve a transaction by id or transaction number."""
        response = self._client._transport.get(f"/transactions/{transaction_id}")
        return Transaction.from_cyclos(response.json())

    def search(
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
        """Search transactions.

        Cyclos exposes ``GET /transactions`` for global search and
        ``GET /{owner}/transactions`` for owner-scoped search. Custom field
        filters (e.g. external reference) are passed as query params when the
        Cyclos configuration exposes those fields.
        """
        params: dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
        }
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
            response = self._client._transport.get(f"/{member_id}/transactions", params=params)
        else:
            response = self._client._transport.get("/transactions", params=params)
        items = [Transaction.from_cyclos(entry) for entry in response.json()]
        return PaginatedResult[Transaction](
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(items) >= page_size,
        )
