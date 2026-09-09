"""Operator management client.

Cyclos operators are a special kind of user created under a member.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from angstrom_cyclos.models import PaginatedResult, UserStatus
from angstrom_cyclos.operators.models import (
    Operator,
    OperatorBase,
    OperatorGroupPermissions,
    OperatorNew,
    OperatorRegistrationResult,
)

if TYPE_CHECKING:
    from angstrom_cyclos.client import CyclosClient


class OperatorsClient:
    """Create, manage and set permissions for organization operators."""

    def __init__(self, client: CyclosClient) -> None:
        self._client = client

    def _prepare_create_payload(
        self,
        organization_id: str,
        username: str,
        first_name: str | None = None,
        last_name: str | None = None,
        name: str | None = None,
        email: str | None = None,
        mobile: str | None = None,
        group: str | None = None,
        custom_fields: dict[str, str] | None = None,
        passwords: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload = OperatorNew(
            group=group,
            username=username,
            name=name or f"{first_name or ''} {last_name or ''}".strip(),
            first_name=first_name,
            last_name=last_name,
            email=email,
            mobile=mobile,
            custom_fields=custom_fields,
            passwords=passwords,
        )
        return payload.model_dump(exclude_none=True, by_alias=True)

    def create(
        self,
        organization_id: str,
        *,
        username: str,
        first_name: str | None = None,
        last_name: str | None = None,
        name: str | None = None,
        email: str | None = None,
        mobile: str | None = None,
        group: str | None = None,
        custom_fields: dict[str, str] | None = None,
        passwords: list[dict[str, Any]] | None = None,
    ) -> OperatorRegistrationResult:
        """Create an operator under an organization."""
        payload = self._prepare_create_payload(
            organization_id=organization_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            name=name,
            email=email,
            mobile=mobile,
            group=group,
            custom_fields=custom_fields,
            passwords=passwords,
        )
        response = self._client._transport.post(f"/{organization_id}/operators", json=payload)
        return OperatorRegistrationResult.model_validate(response.json())

    def get(self, organization_id: str, operator_id: str) -> Operator:
        """Retrieve an operator by id."""
        response = self._client._transport.get(f"/{organization_id}/operators/{operator_id}")
        return Operator.model_validate(response.json())

    def update(
        self,
        organization_id: str,
        operator_id: str,
        *,
        data: OperatorBase | dict[str, Any],
    ) -> Operator:
        """Update an operator's profile fields."""
        if isinstance(data, OperatorBase):
            payload = data.model_dump(exclude_none=True, by_alias=True)
        else:
            payload = data
        response = self._client._transport.put(
            f"/{organization_id}/operators/{operator_id}", json=payload
        )
        return Operator.model_validate(response.json())

    def delete(self, organization_id: str, operator_id: str) -> None:
        """Delete a pending operator."""
        self._client._transport.delete(f"/{organization_id}/operators/{operator_id}")

    def _set_status(self, organization_id: str, operator_id: str, status: UserStatus) -> None:
        self._client._transport.post(
            f"/{organization_id}/operators/{operator_id}/status",
            json={"status": status.value},
        )

    def activate(self, organization_id: str, operator_id: str) -> None:
        """Activate an operator."""
        self._set_status(organization_id, operator_id, UserStatus.ACTIVE)

    def deactivate(self, organization_id: str, operator_id: str) -> None:
        """Disable an operator."""
        self._set_status(organization_id, operator_id, UserStatus.DISABLED)

    def block(self, organization_id: str, operator_id: str) -> None:
        """Block an operator."""
        self._set_status(organization_id, operator_id, UserStatus.BLOCKED)

    def list_permissions(self, organization_id: str, operator_id: str) -> list[str]:
        """Return the permissions of the operator's group.

        Cyclos exposes operator permissions through the operator group. This
        method fetches the operator, then its operator group details.
        """
        operator = self.get(organization_id, operator_id)
        group_id = operator.group.id if operator.group else None
        if not group_id:
            return []
        response = self._client._transport.get(f"/operator-groups/{group_id}")
        group = response.json()
        # Collect enabled boolean permission flags from the operator group view.
        permissions: list[str] = []
        permission_map = {
            "chargebackPayments": "CHARGEBACK_PAYMENTS",
            "messages": "MESSAGES",
            "notifications": "NOTIFICATIONS",
            "receivePayments": "RECEIVE_PAYMENTS",
            "voucherTransactions": "VOUCHER_TRANSACTIONS",
            "requestPayments": "REQUEST_PAYMENTS",
            "viewAdvertisements": "VIEW_ADVERTISEMENTS",
            "manageAdvertisements": "MANAGE_ADVERTISEMENTS",
            "enableToken": "ENABLE_TOKEN",
            "cancelToken": "CANCEL_TOKEN",
            "blockToken": "BLOCK_TOKEN",
            "unblockToken": "UNBLOCK_TOKEN",
            "brokering": "BROKERING",
            "editOwnProfile": "EDIT_OWN_PROFILE",
        }
        for key, mapped in permission_map.items():
            if group.get(key):
                permissions.append(mapped)
        return permissions

    def assign_permissions(
        self,
        organization_id: str,
        operator_id: str,
        *,
        permissions: list[str] | None = None,
        operator_group: str | None = None,
        group_permissions: OperatorGroupPermissions | dict[str, Any] | None = None,
    ) -> None:
        """Assign permissions to an operator.

        Because Cyclos stores operator permissions in operator groups, this
        method either moves the operator to an existing group (when
        ``operator_group`` is given) or updates the operator's current group
        with the boolean flags provided in ``group_permissions``.

        Args:
            organization_id: Owner organization id.
            operator_id: Operator id.
            permissions: List of human-readable permission names (translated to
                booleans where possible). Prefer ``group_permissions`` for exact control.
            operator_group: Id or internal name of an existing operator group.
            group_permissions: Boolean flag dict or ``OperatorGroupPermissions``.
        """
        if operator_group:
            payload = {"group": operator_group}
            self._client._transport.put(
                f"/{organization_id}/operators/{operator_id}",
                json=payload,
            )
            return

        operator = self.get(organization_id, operator_id)
        group_id = operator.group.id if operator.group else None
        if not group_id:
            raise ValueError(
                "Operator has no operator group. Create a group first or pass operator_group."
            )

        if group_permissions is None and permissions:
            group_permissions = OperatorGroupPermissions()
            for perm in permissions:
                lowered = perm.lower().replace(" ", "_")
                if hasattr(group_permissions, lowered):
                    setattr(group_permissions, lowered, True)

        if isinstance(group_permissions, OperatorGroupPermissions):
            update_payload = group_permissions.model_dump(exclude_none=True, by_alias=True)
        else:
            update_payload = group_permissions or {}

        self._client._transport.put(
            f"/{organization_id}/operator-groups/{group_id}",
            json=update_payload,
        )

    def remove_permissions(
        self,
        organization_id: str,
        operator_id: str,
        *,
        permissions: list[str],
    ) -> None:
        """Disable a set of permissions for the operator's current group."""
        operator = self.get(organization_id, operator_id)
        group_id = operator.group.id if operator.group else None
        if not group_id:
            return
        current = self._client._transport.get(f"/operator-groups/{group_id}").json()
        flags = {
            key: current.get(key, False)
            for key in {
                "chargebackPayments",
                "messages",
                "notifications",
                "receivePayments",
                "voucherTransactions",
                "requestPayments",
                "viewAdvertisements",
                "manageAdvertisements",
                "enableToken",
                "cancelToken",
                "blockToken",
                "unblockToken",
                "brokering",
                "editOwnProfile",
            }
        }
        for perm in permissions:
            lowered = perm.lower().replace(" ", "_")
            mapping = {
                "chargeback_payments": "chargebackPayments",
                "messages": "messages",
                "notifications": "notifications",
                "receive_payments": "receivePayments",
                "voucher_transactions": "voucherTransactions",
                "request_payments": "requestPayments",
                "view_advertisements": "viewAdvertisements",
                "manage_advertisements": "manageAdvertisements",
                "enable_token": "enableToken",
                "cancel_token": "cancelToken",
                "block_token": "blockToken",
                "unblock_token": "unblockToken",
                "brokering": "brokering",
                "edit_own_profile": "editOwnProfile",
            }
            if lowered in mapping:
                flags[mapping[lowered]] = False
        self._client._transport.put(f"/{organization_id}/operator-groups/{group_id}", json=flags)

    def search(
        self,
        organization_id: str,
        *,
        query: str | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[Operator]:
        """Search operators of an organization."""
        params: dict[str, Any] = {
            "keywords": query,
            "page": page,
            "pageSize": page_size,
        }
        response = self._client._transport.get(f"/{organization_id}/operators", params=params)
        items = [Operator.model_validate(u) for u in response.json()]
        return PaginatedResult[Operator](
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(items) >= page_size,
        )
