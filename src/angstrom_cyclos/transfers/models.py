"""Transfer/payment models."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import Field

from angstrom_cyclos.models import (
    AccountReference,
    CyclosBaseModel,
    EntityReference,
    TransferStatus,
)


class TransferCreate(CyclosBaseModel):
    """Request to perform a Cyclos payment/transfer.

    Cyclos 4.16 creates transfers through ``POST /{owner}/payments``. This model
    maps the SDK's wallet-friendly fields to the Cyclos payload.
    """

    transfer_type: str = Field(alias="type")
    from_owner: str | None = Field(default=None, alias="owner")
    to_account: str | None = Field(default=None, alias="subject")
    amount: Decimal
    currency: str | None = None
    description: str | None = None
    custom_values: dict[str, str] | None = Field(default=None, alias="customValues")
    scheduling: str | None = None
    idempotency_key: str | None = Field(default=None, exclude=True)


class Transfer(CyclosBaseModel):
    """Result of a Cyclos payment/transfer."""

    id: str | None = None
    transaction_number: str | None = Field(default=None, alias="transactionNumber")
    date: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    description: str | None = None
    from_account: AccountReference | None = Field(default=None, alias="from")
    to_account: AccountReference | None = Field(default=None, alias="to")
    transfer_type: EntityReference | None = Field(default=None, alias="type")
    status: TransferStatus | None = None
    cyclos_status: str | None = None
    kind: str | None = None

    @classmethod
    def from_cyclos_transaction(cls, data: dict[str, Any]) -> Transfer:
        """Normalize a Cyclos transaction/transfer response."""
        status_value = data.get("status") or data.get("authorizationStatus") or ""
        normalized = str(status_value).upper()
        mapping = {"PROCESSED": "SUCCESS", "COMPLETED": "SUCCESS"}
        status_name = mapping.get(normalized, normalized)
        if status_name not in {"PENDING", "SUCCESS", "FAILED", "CANCELLED", "REVERSED"}:
            status_name = "PENDING"
        status = TransferStatus(status_name)
        return cls(
            id=data.get("id"),
            transaction_number=data.get("transactionNumber"),
            date=data.get("date"),
            amount=Decimal(data["amount"]) if data.get("amount") else None,
            currency=data.get("currency"),
            description=data.get("description"),
            from_account=data.get("from"),
            to_account=data.get("to"),
            transfer_type=data.get("type"),
            status=status,
            cyclos_status=str(status_value) if status_value else None,
            kind=data.get("kind"),
        )
