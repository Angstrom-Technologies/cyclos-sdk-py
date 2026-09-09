"""Shared Pydantic models for the Cyclos SDK."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CyclosBaseModel(BaseModel):
    """Base model with common configuration for all SDK models."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        extra="allow",
        json_encoders={Decimal: str},
    )


class EntityReference(CyclosBaseModel):
    """Lightweight reference to a Cyclos entity."""

    id: str | None = None
    name: str | None = None
    internal_name: str | None = Field(default=None, alias="internalName")


class UserReference(CyclosBaseModel):
    """Minimal user reference returned by the API."""

    id: str | None = None
    display: str | None = None


class Currency(CyclosBaseModel):
    """Currency reference."""

    id: str | None = None
    name: str | None = None
    internal_name: str | None = Field(default=None, alias="internalName")
    symbol: str | None = None
    prefix: str | None = None
    suffix: str | None = None
    decimal_digits: int | None = Field(default=None, alias="decimalDigits")


class AccountReference(CyclosBaseModel):
    """Account reference as returned inside transaction/transfer payloads."""

    id: str | None = None
    number: str | None = None
    type: EntityReference | None = None
    user: UserReference | None = None
    kind: str | None = None


class CustomFieldValue(CyclosBaseModel):
    """Custom field value as returned by the API."""

    field: EntityReference | None = None
    value: Any = None
    internal_name: str | None = Field(default=None, alias="internalName")


class Phone(CyclosBaseModel):
    """Phone number used when registering users/operators."""

    number: str
    name: str | None = None
    hidden: bool | None = None
    kind: str | None = None

    @field_validator("number")
    @classmethod
    def _mask_log(cls, value: str) -> str:
        # Validation only ensures the value is kept as-is.
        return value.strip()


class Address(CyclosBaseModel):
    """Address used when registering users/operators."""

    name: str | None = None
    address_line_1: str | None = Field(default=None, alias="addressLine1")
    address_line_2: str | None = Field(default=None, alias="addressLine2")
    city: str | None = None
    region: str | None = None
    country: str | None = None
    zip_code: str | None = Field(default=None, alias="zip")
    default: bool | None = None


class PasswordRegistration(CyclosBaseModel):
    """Initial password when registering a user/operator."""

    type: str | None = None
    value: str | None = Field(default=None, repr=False)
    check_confirmation: bool | None = Field(default=None, alias="checkConfirmation")
    confirmation_value: str | None = Field(default=None, repr=False, alias="confirmationValue")
    force_change: bool | None = Field(default=None, alias="forceChange")


class TransferStatus(StrEnum):
    """Normalized transfer/transaction status."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REVERSED = "REVERSED"


class UserStatus(StrEnum):
    """Cyclos user statuses exposed through ``POST /{user}/status``."""

    ACTIVE = "active"
    BLOCKED = "blocked"
    DISABLED = "disabled"
    PENDING = "pending"
    REMOVED = "removed"
    PURGED = "purged"


class MemberType(StrEnum):
    """Convenience enum for common member group *concepts*.

    The actual ``group`` identifier passed to Cyclos must be the configured
    internal name or id for the corresponding group.
    """

    INDIVIDUAL = "INDIVIDUAL"
    MERCHANT = "MERCHANT"
    ORGANIZATION = "ORGANIZATION"
    BUSINESS = "BUSINESS"
    AGENT = "AGENT"
    CORPORATE = "CORPORATE"


T = TypeVar("T")


class PaginatedResult(CyclosBaseModel, Generic[T]):
    """Generic pagination wrapper for Cyclos list responses.

    Cyclos returns arrays directly with ``page`` and ``pageSize`` query
    parameters. ``total_count`` is populated when the caller provides an
    explicit value or the response contains a ``totalCount`` field.
    ``has_next`` is derived from whether a full page of results was returned.
    """

    items: list[T]
    page: int
    page_size: int
    total_count: int | None = None
    has_next: bool | None = None

    @model_validator(mode="after")
    def _derive_has_next(self) -> "PaginatedResult[T]":
        if self.has_next is None:
            self.has_next = bool(self.page_size and len(self.items) >= self.page_size)
        return self


class AccountBalance(CyclosBaseModel):
    """Strongly typed account balance."""

    account_id: str
    account_type: str
    currency: str | None = None
    balance: Decimal
    available_balance: Decimal | None = None
    credit_limit: Decimal | None = None
    reserved_amount: Decimal | None = None


class DateRange(CyclosBaseModel):
    """Date range used by search filters."""

    begin: datetime | date | None = None
    end: datetime | date | None = None
