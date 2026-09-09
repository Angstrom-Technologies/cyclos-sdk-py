"""Asynchronous account client."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from angstrom_cyclos.accounts.models import Account, AccountHistoryEntry, AccountStatus
from angstrom_cyclos.models import AccountBalance, PaginatedResult

if TYPE_CHECKING:
    from angstrom_cyclos.async_client import AsyncCyclosClient


class AsyncAccountsClient:
    """Async account client."""

    def __init__(self, client: AsyncCyclosClient) -> None:
        self._client = client

    async def list(
        self,
        member_id: str,
        *,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[Account]:
        response = await self._client._transport.get(
            f"/{member_id}/accounts",
            params={"page": page, "pageSize": page_size},
        )
        items = [Account.model_validate(a) for a in response.json()]
        return PaginatedResult[Account](
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(items) >= page_size,
        )

    async def get(self, member_id: str, account_type: str) -> Account:
        response = await self._client._transport.get(f"/{member_id}/accounts/{account_type}")
        return Account.model_validate(response.json())

    async def get_balance(
        self,
        member_id: str,
        *,
        account_type: str = "mobileWallet",
    ) -> AccountBalance:
        account = await self.get(member_id, account_type)
        status = account.status or AccountStatus()
        return AccountBalance(
            account_id=account.id or member_id,
            account_type=account_type,
            currency=account.currency.name if account.currency else None,
            balance=status.balance or Decimal("0"),
            available_balance=status.available_balance,
            credit_limit=status.credit_limit,
            reserved_amount=status.reserved_amount,
        )

    async def history(
        self,
        member_id: str,
        account_type: str,
        *,
        page: int = 0,
        page_size: int = 20,
        date_from: str | None = None,
        date_to: str | None = None,
        amount_min: Decimal | None = None,
        amount_max: Decimal | None = None,
        status: str | None = None,
        transfer_type: str | None = None,
        direction: str | None = None,
    ) -> PaginatedResult[AccountHistoryEntry]:
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
        if direction:
            params["direction"] = direction
        response = await self._client._transport.get(
            f"/{member_id}/accounts/{account_type}/history",
            params=params,
        )
        items = [AccountHistoryEntry.model_validate(entry) for entry in response.json()]
        return PaginatedResult[AccountHistoryEntry](
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(items) >= page_size,
        )
