"""Asynchronous permissions client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from angstrom_cyclos.models import PaginatedResult
from angstrom_cyclos.permissions.models import PermissionGroup

if TYPE_CHECKING:
    from angstrom_cyclos.async_client import AsyncCyclosClient


class AsyncPermissionsClient:
    """Async permissions inspection client."""

    def __init__(self, client: AsyncCyclosClient) -> None:
        self._client = client

    async def list(self) -> list[str]:
        response = await self._client._transport.get("/auth")
        auth = response.json()
        perms = auth.get("permissions") or {}
        result: list[str] = []
        for key, value in perms.items():
            if isinstance(value, list):
                for item in value:
                    result.append(f"{key}:{item}")
            elif isinstance(value, dict):
                for sub, subval in value.items():
                    if subval:
                        result.append(f"{key}:{sub}")
            elif value is True:
                result.append(key)
        return sorted(set(result))

    async def get(self, group_id: str) -> PermissionGroup:
        response = await self._client._transport.get(f"/operator-groups/{group_id}")
        data = response.json()
        permissions = [
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
            if data.get(key)
        ]
        return PermissionGroup(
            id=data.get("id", group_id),
            name=data.get("name", group_id),
            permissions=permissions,
        )

    async def search(
        self,
        owner_id: str,
        *,
        query: str | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[PermissionGroup]:
        response = await self._client._transport.get(
            f"/{owner_id}/operator-groups",
            params={"keywords": query, "page": page, "pageSize": page_size},
        )
        mapping = {
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
        items = [
            PermissionGroup(
                id=g.get("id"),
                name=g.get("name"),
                permissions=[mapped for key, mapped in mapping.items() if g.get(key)],
            )
            for g in response.json()
        ]
        return PaginatedResult[PermissionGroup](
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(items) >= page_size,
        )
