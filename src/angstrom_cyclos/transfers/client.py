"""Transfer client.

Cyclos 4.16 does not expose a standalone ``POST /transfers`` endpoint.
Transfers are created by performing payments: ``POST /{owner}/payments``.
This module normalizes that behavior behind a wallet-friendly API.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from angstrom_cyclos.models import PaginatedResult
from angstrom_cyclos.transfers.models import Transfer, TransferCreate

if TYPE_CHECKING:
    from angstrom_cyclos.client import CyclosClient


class TransfersClient:
    """Create and inspect transfers/payments."""

    def __init__(self, client: CyclosClient) -> None:
        self._client = client

    def create(
        self,
        *,
        transfer_type: str,
        from_account: str,
        to_account: str,
        amount: Decimal | str | float | int,
        currency: str | None = None,
        description: str | None = None,
        idempotency_key: str | None = None,
        custom_fields: dict[str, str] | None = None,
        owner: str | None = None,
        **kwargs: Any,
    ) -> Transfer:
        """Perform a payment/transfer from one account to another.

        ``from_account`` is used as the Cyclos ``owner`` path parameter. The
        actual debited account is determined by the ``transfer_type``
        configuration in Cyclos.

        Args:
            transfer_type: Cyclos payment/transfer type id or qualified internal
                name (e.g. ``fromAccountType.paymentType``).
            from_account: Owner/payer identifier (login, id, etc.).
            to_account: Recipient identifier (login, id, etc.).
            amount: Transfer amount. Converted to ``Decimal``.
            currency: Optional currency id or internal name.
            description: Optional transfer description.
            idempotency_key: Optional key used by the SDK idempotency guard.
            custom_fields: Optional custom field values for the transfer.
            owner: Optional override for the path ``owner``.
            **kwargs: Extra fields forwarded to Cyclos (e.g. scheduling).
        """
        payer = owner or from_account
        amount_decimal = Decimal(str(amount)) if not isinstance(amount, Decimal) else amount
        payload = TransferCreate(
            type=transfer_type,
            subject=to_account,
            amount=amount_decimal,
            currency=currency,
            description=description,
            customValues=custom_fields or {},
            **kwargs,
        )
        response = self._client._transport.post(
            f"/{payer}/payments",
            json=payload.model_dump(exclude_none=True, exclude={"idempotency_key"}, by_alias=True),
            idempotency_key=idempotency_key,
        )
        return Transfer.from_cyclos_transaction(response.json())

    def get(self, transfer_id: str) -> Transfer:
        """Retrieve a transfer by id."""
        response = self._client._transport.get(f"/transfers/{transfer_id}")
        return Transfer.from_cyclos_transaction(response.json())

    def search(
        self,
        *,
        member_id: str | None = None,
        account_type: str | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[Transfer]:
        """Search transfers.

        If ``member_id`` and ``account_type`` are supplied, the account history
        endpoint is used. Otherwise the global ``/transfers`` endpoint is used.
        """
        params: dict[str, Any] = {"page": page, "pageSize": page_size}
        if member_id and account_type:
            response = self._client._transport.get(
                f"/{member_id}/accounts/{account_type}/history",
                params=params,
            )
        else:
            response = self._client._transport.get("/transfers", params=params)
        items = [Transfer.from_cyclos_transaction(entry) for entry in response.json()]
        return PaginatedResult[Transfer](
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(items) >= page_size,
        )

    def history(
        self,
        *,
        member_id: str,
        account_type: str,
        page: int = 0,
        page_size: int = 20,
        date_from: str | None = None,
        date_to: str | None = None,
        amount_min: Decimal | str | float | int | None = None,
        amount_max: Decimal | str | float | int | None = None,
        status: str | None = None,
        transfer_type: str | None = None,
        currency: str | None = None,
        direction: str | None = None,
    ) -> PaginatedResult[Transfer]:
        """Fetch paginated transfer history for a member/account."""
        params: dict[str, Any] = {"page": page, "pageSize": page_size}
        if date_from:
            params["datePeriod.begin"] = date_from
        if date_to:
            params["datePeriod.end"] = date_to
        if amount_min is not None:
            params["amountRange.min"] = str(amount_min)
        if amount_max is not None:
            params["amountRange.max"] = str(amount_max)
        if status:
            params["statuses"] = status
        if transfer_type:
            params["transferTypes"] = transfer_type
        if currency:
            params["currency"] = currency
        if direction:
            params["direction"] = direction
        response = self._client._transport.get(
            f"/{member_id}/accounts/{account_type}/history",
            params=params,
        )
        items = [Transfer.from_cyclos_transaction(entry) for entry in response.json()]
        return PaginatedResult[Transfer](
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(items) >= page_size,
        )

    def cancel(self, transfer_id: str, *, member_id: str) -> Transfer:
        """Cancel a transfer/payment if supported by Cyclos."""
        response = self._client._transport.post(f"/{member_id}/payments/{transfer_id}/cancel")
        return Transfer.from_cyclos_transaction(response.json())

    def reverse(self, transfer_id: str, *, description: str | None = None) -> Transfer:
        """Reverse (chargeback) a transfer if supported by Cyclos."""
        payload = {"description": description} if description else {}
        response = self._client._transport.post(
            f"/transfers/{transfer_id}/chargeback", json=payload
        )
        return Transfer.from_cyclos_transaction(response.json())
