"""Asynchronous organization client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from angstrom_cyclos.members.client_async import AsyncMembersClient
from angstrom_cyclos.members.models import Member as Organization
from angstrom_cyclos.members.models import MemberBase as OrganizationBase
from angstrom_cyclos.members.models import (
    MemberRegistrationResult as OrganizationRegistrationResult,
)
from angstrom_cyclos.models import PaginatedResult

if TYPE_CHECKING:
    from angstrom_cyclos.async_client import AsyncCyclosClient


class AsyncOrganizationsClient:
    """Async organization client."""

    def __init__(self, client: AsyncCyclosClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        group: str,
        name: str,
        username: str | None = None,
        email: str | None = None,
        mobile: str | None = None,
        custom_fields: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> OrganizationRegistrationResult:
        return await AsyncMembersClient(self._client).create(
            group=group,
            username=username or name,
            name=name,
            email=email,
            mobile=mobile,
            custom_fields=custom_fields,
            **kwargs,
        )

    async def get(self, organization_id: str) -> Organization:
        return await AsyncMembersClient(self._client).get(organization_id)

    async def update(
        self,
        organization_id: str,
        *,
        data: OrganizationBase | dict[str, Any],
    ) -> Organization:
        return await AsyncMembersClient(self._client).update(organization_id, data=data)

    async def search(
        self,
        *,
        query: str | None = None,
        groups: list[str] | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[Organization]:
        return await AsyncMembersClient(self._client).search(
            query=query,
            groups=groups,
            page=page,
            page_size=page_size,
        )
