"""Permissions module.

Cyclos 4.16 exposes permissions in several places:

* ``GET /auth`` returns the permissions of the currently authenticated user.
* Operator permissions are managed through operator groups under
  ``/{user}/operator-groups``.

This module normalizes both sources into a simple list/search API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from angstrom_cyclos.models import PaginatedResult
from angstrom_cyclos.permissions.models import PermissionGroup

if TYPE_CHECKING:
    from angstrom_cyclos.client import CyclosClient


class PermissionsClient:
    """Inspect Cyclos permissions."""

    def __init__(self, client: CyclosClient) -> None:
        self._client = client

    def list(self) -> list[str]:
        """Return the permissions of the currently authenticated user."""
        response = self._client._transport.get("/auth")
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

    def get(self, group_id: str) -> PermissionGroup:
        """Return details of an operator group including its permissions."""
        response = self._client._transport.get(f"/operator-groups/{group_id}")
        data = response.json()
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
            if data.get(key):
                permissions.append(mapped)
        return PermissionGroup(
            id=data.get("id", group_id),
            name=data.get("name", group_id),
            permissions=permissions,
        )

    def search(
        self,
        owner_id: str,
        *,
        query: str | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[PermissionGroup]:
        """Search operator groups (permission groups) of an owner."""
        params: dict[str, Any] = {
            "keywords": query,
            "page": page,
            "pageSize": page_size,
        }
        response = self._client._transport.get(f"/{owner_id}/operator-groups", params=params)
        items = [
            PermissionGroup(
                id=g.get("id"),
                name=g.get("name"),
                permissions=[
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
                    if g.get(key)
                ],
            )
            for g in response.json()
        ]
        return PaginatedResult[PermissionGroup](
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(items) >= page_size,
        )
