"""Transfer/payment models."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import Field, field_validator

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
    transaction_id: str | None = None
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

    @field_validator("currency", mode="before")
    @classmethod
    def _normalize_currency(cls, value: Any) -> str | None:
        """Cyclos returns currency as either an internal name string or a full object."""
        if isinstance(value, dict):
            normalized = value.get("internalName") or value.get("symbol") or value.get("id")
            return str(normalized) if normalized is not None else None
        return str(value) if value is not None else None

    @classmethod
    def from_cyclos_transaction(cls, data: dict[str, Any]) -> Transfer:
        """Normalize a Cyclos transaction/transfer response."""
        nested = data.get("transfer")
        transfer = nested if isinstance(nested, dict) else data
        status_value = (
            transfer.get("status")
            or data.get("status")
            or data.get("authorizationStatus")
            or ""
        )
        normalized = str(status_value).upper()
        mapping = {"PROCESSED": "SUCCESS", "COMPLETED": "SUCCESS"}
        status_name = mapping.get(normalized, normalized)
        if status_name not in {"PENDING", "SUCCESS", "FAILED", "CANCELLED", "REVERSED"}:
            status_name = "PENDING"
        status = TransferStatus(status_name)
        return cls(
            id=transfer.get("id"),
            transaction_id=data.get("id") if transfer is not data else data.get("transactionId"),
            transaction_number=data.get("transactionNumber"),
            date=transfer.get("date") or data.get("date"),
            amount=Decimal(transfer["amount"]) if transfer.get("amount") else None,
            currency=transfer.get("currency") or data.get("currency"),
            description=transfer.get("description") or data.get("description"),
            from_account=transfer.get("from") or data.get("from"),
            to_account=transfer.get("to") or data.get("to"),
            transfer_type=transfer.get("type") or data.get("type"),
            status=status,
            cyclos_status=str(status_value) if status_value else None,
            kind=transfer.get("kind") or data.get("kind"),
        )
