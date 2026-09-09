"""Account models."""

from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from angstrom_cyclos.models import (
    AccountReference,
    Currency,
    CyclosBaseModel,
    EntityReference,
    UserReference,
)


class AccountStatus(CyclosBaseModel):
    """Account status including balances."""

    balance: Decimal | None = None
    credit_limit: Decimal | None = Field(default=None, alias="creditLimit")
    upper_credit_limit: Decimal | None = Field(default=None, alias="upperCreditLimit")
    reserved_amount: Decimal | None = Field(default=None, alias="reservedAmount")
    available_balance: Decimal | None = Field(default=None, alias="availableBalance")
    negative_since: str | None = Field(default=None, alias="negativeSince")
    begin_date: str | None = Field(default=None, alias="beginDate")
    end_date: str | None = Field(default=None, alias="endDate")
    balance_at_begin: Decimal | None = Field(default=None, alias="balanceAtBegin")
    balance_at_end: Decimal | None = Field(default=None, alias="balanceAtEnd")


class Account(CyclosBaseModel):
    """Cyclos account with owner and currency."""

    id: str | None = None
    type: EntityReference | None = None
    user: UserReference | None = None
    kind: str | None = None
    currency: Currency | None = None
    status: AccountStatus | None = None


class AccountHistoryEntry(CyclosBaseModel):
    """Single entry from an account history."""

    id: str | None = None
    date: str | None = None
    amount: Decimal | None = None
    description: str | None = None
    transaction_number: str | None = Field(default=None, alias="transactionNumber")
    related_account: AccountReference | None = Field(default=None, alias="relatedAccount")
    related_name: str | None = Field(default=None, alias="relatedName")
    statuses: dict[str, str] | None = None


__all__ = ["Account", "AccountStatus", "AccountHistoryEntry", "AccountReference", "Currency"]
