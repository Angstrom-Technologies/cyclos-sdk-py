"""Operator models."""

from __future__ import annotations

from pydantic import Field

from angstrom_cyclos.members.models import Member as Operator
from angstrom_cyclos.members.models import MemberBase as OperatorBase
from angstrom_cyclos.members.models import (
    MemberRegistrationResult as OperatorRegistrationResult,
)
from angstrom_cyclos.models import CyclosBaseModel


class OperatorNew(OperatorBase):
    """Create an operator under an organization.

    The ``group`` field refers to an operator group. If omitted the operator
    becomes an alias of the owner organization.
    """

    group: str | None = None


class OperatorPermissions(CyclosBaseModel):
    """Normalized operator permission assignment request.

    In Cyclos 4.16 permissions are granted through operator groups. This model
    represents the boolean/permission set the caller wants to apply.
    """

    permissions: list[str] | None = None
    operator_group: str | None = Field(default=None, alias="operatorGroup")


class OperatorGroupPermissions(CyclosBaseModel):
    """Permission/operation names the caller wants to enable for an operator."""

    view_member: bool | None = None
    view_account: bool | None = None
    perform_transfer: bool | None = None
    receive_payments: bool | None = None
    request_payments: bool | None = None
    chargeback_payments: bool | None = None
    messages: bool | None = None
    notifications: bool | None = None
    edit_own_profile: bool | None = None
    brokering: bool | None = None


class OperatorGroupCreate(CyclosBaseModel):
    """Create or update an operator group."""

    name: str
    description: str | None = None
    permissions: OperatorGroupPermissions | None = None


__all__ = [
    "Operator",
    "OperatorBase",
    "OperatorNew",
    "OperatorRegistrationResult",
    "OperatorPermissions",
    "OperatorGroupPermissions",
    "OperatorGroupCreate",
]
