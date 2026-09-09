"""Transaction models."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import Field

from angstrom_cyclos.models import AccountReference, CyclosBaseModel, EntityReference


class Transaction(CyclosBaseModel):
    """Cyclos transaction result."""

    id: str | None = None
    transaction_number: str | None = Field(default=None, alias="transactionNumber")
    date: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    description: str | None = None
    kind: str | None = None
    status: str | None = None
    from_account: AccountReference | None = Field(default=None, alias="from")
    to_account: AccountReference | None = Field(default=None, alias="to")
    transfer_type: EntityReference | None = Field(default=None, alias="type")
    authorization_status: str | None = Field(default=None, alias="authorizationStatus")

    @classmethod
    def from_cyclos(cls, data: dict[str, Any]) -> Transaction:
        """Normalize a Cyclos transaction overview/detail response."""
        if not isinstance(data, dict):
            raise ValueError("Transaction data must be a dict")
        return cls.model_validate(data)
