"""Asynchronous operator client."""

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
    from angstrom_cyclos.async_client import AsyncCyclosClient


class AsyncOperatorsClient:
    """Async operator client."""

    def __init__(self, client: AsyncCyclosClient) -> None:
        self._client = client

    async def create(
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
        ).model_dump(exclude_none=True, by_alias=True)
        response = await self._client._transport.post(f"/{organization_id}/operators", json=payload)
        return OperatorRegistrationResult.model_validate(response.json())

    async def get(self, organization_id: str, operator_id: str) -> Operator:
        response = await self._client._transport.get(f"/{organization_id}/operators/{operator_id}")
        return Operator.model_validate(response.json())

    async def update(
        self,
        organization_id: str,
        operator_id: str,
        *,
        data: OperatorBase | dict[str, Any],
    ) -> Operator:
        if isinstance(data, OperatorBase):
            payload = data.model_dump(exclude_none=True, by_alias=True)
        else:
            payload = data
        response = await self._client._transport.put(
            f"/{organization_id}/operators/{operator_id}",
            json=payload,
        )
        return Operator.model_validate(response.json())

    async def delete(self, organization_id: str, operator_id: str) -> None:
        await self._client._transport.delete(f"/{organization_id}/operators/{operator_id}")

    async def _set_status(self, organization_id: str, operator_id: str, status: UserStatus) -> None:
        await self._client._transport.post(
            f"/{organization_id}/operators/{operator_id}/status",
            json={"status": status.value},
        )

    async def activate(self, organization_id: str, operator_id: str) -> None:
        await self._set_status(organization_id, operator_id, UserStatus.ACTIVE)

    async def deactivate(self, organization_id: str, operator_id: str) -> None:
        await self._set_status(organization_id, operator_id, UserStatus.DISABLED)

    async def block(self, organization_id: str, operator_id: str) -> None:
        await self._set_status(organization_id, operator_id, UserStatus.BLOCKED)

    async def list_permissions(self, organization_id: str, operator_id: str) -> list[str]:
        operator = await self.get(organization_id, operator_id)
        group_id = operator.group.id if operator.group else None
        if not group_id:
            return []
        response = await self._client._transport.get(f"/operator-groups/{group_id}")
        group = response.json()
        return [
            mapped
            for key, mapped in {
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
            }.items()
            if group.get(key)
        ]

    async def assign_permissions(
        self,
        organization_id: str,
        operator_id: str,
        *,
        permissions: list[str] | None = None,
        operator_group: str | None = None,
        group_permissions: OperatorGroupPermissions | dict[str, Any] | None = None,
    ) -> None:
        if operator_group:
            await self._client._transport.put(
                f"/{organization_id}/operators/{operator_id}",
                json={"group": operator_group},
            )
            return
        operator = await self.get(organization_id, operator_id)
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
        await self._client._transport.put(
            f"/{organization_id}/operator-groups/{group_id}",
            json=update_payload,
        )

    async def remove_permissions(
        self,
        organization_id: str,
        operator_id: str,
        *,
        permissions: list[str],
    ) -> None:
        operator = await self.get(organization_id, operator_id)
        group_id = operator.group.id if operator.group else None
        if not group_id:
            return
        current = (await self._client._transport.get(f"/operator-groups/{group_id}")).json()
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
        for perm in permissions:
            lowered = perm.lower().replace(" ", "_")
            if lowered in mapping:
                flags[mapping[lowered]] = False
        await self._client._transport.put(
            f"/{organization_id}/operator-groups/{group_id}",
            json=flags,
        )

    async def search(
        self,
        organization_id: str,
        *,
        query: str | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[Operator]:
        response = await self._client._transport.get(
            f"/{organization_id}/operators",
            params={"keywords": query, "page": page, "pageSize": page_size},
        )
        items = [Operator.model_validate(u) for u in response.json()]
        return PaginatedResult[Operator](
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(items) >= page_size,
        )
