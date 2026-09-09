"""Asynchronous member management client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from angstrom_cyclos.members.models import (
    Member,
    MemberCreate,
    MemberRegistrationResult,
)
from angstrom_cyclos.models import PaginatedResult, UserStatus

if TYPE_CHECKING:
    from angstrom_cyclos.async_client import AsyncCyclosClient


class AsyncMembersClient:
    """Async member management client."""

    def __init__(self, client: AsyncCyclosClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        group: str,
        username: str,
        name: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        mobile: str | None = None,
        custom_fields: dict[str, str] | None = None,
        mobile_phones: list[dict[str, Any]] | None = None,
        land_line_phones: list[dict[str, Any]] | None = None,
        addresses: list[dict[str, Any]] | None = None,
        passwords: list[dict[str, Any]] | None = None,
        skip_activation_email: bool | None = None,
        broker: str | None = None,
    ) -> MemberRegistrationResult:
        payload = MemberCreate(
            group=group,
            username=username,
            name=name,
            first_name=first_name,
            last_name=last_name,
            email=email,
            mobile=mobile,
            custom_fields=custom_fields,
            mobile_phones=mobile_phones,
            land_line_phones=land_line_phones,
            addresses=addresses,
            passwords=passwords,
            skip_activation_email=skip_activation_email,
            broker=broker,
        )
        response = await self._client._transport.post(
            "/users",
            json=payload.model_dump(exclude_none=True, by_alias=True),
        )
        return MemberRegistrationResult.model_validate(response.json())

    async def get(self, user_id: str) -> Member:
        response = await self._client._transport.get(f"/users/{user_id}")
        return Member.model_validate(response.json())

    async def update(
        self,
        user_id: str,
        *,
        data: Any,
    ) -> Member:
        from angstrom_cyclos.members.models import MemberBase

        if isinstance(data, MemberBase):
            payload = data.model_dump(exclude_none=True, by_alias=True)
        else:
            payload = data
        response = await self._client._transport.put(f"/users/{user_id}", json=payload)
        return Member.model_validate(response.json())

    async def delete(self, user_id: str) -> None:
        await self._client._transport.delete(f"/users/{user_id}")

    async def search(
        self,
        *,
        query: str | None = None,
        fields: dict[str, str] | None = None,
        groups: list[str] | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[Member]:
        params: dict[str, Any] = {
            "keywords": query,
            "groups": groups,
            "page": page,
            "pageSize": page_size,
        }
        if fields:
            for key, value in fields.items():
                params[f"customValues.{key}"] = value
        response = await self._client._transport.get("/users", params=params)
        items = [Member.model_validate(u) for u in response.json()]
        return PaginatedResult[Member](
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(items) >= page_size,
        )

    async def _set_status(self, user_id: str, status: UserStatus) -> None:
        await self._client._transport.post(f"/{user_id}/status", json={"status": status.value})

    async def activate(self, user_id: str) -> None:
        await self._set_status(user_id, UserStatus.ACTIVE)

    async def deactivate(self, user_id: str) -> None:
        await self._set_status(user_id, UserStatus.DISABLED)

    async def block(self, user_id: str) -> None:
        await self._set_status(user_id, UserStatus.BLOCKED)

    async def create_individual(
        self,
        *,
        username: str,
        first_name: str,
        last_name: str,
        email: str | None = None,
        mobile: str | None = None,
        group: str = "individualCustomer",
        **kwargs: Any,
    ) -> MemberRegistrationResult:
        return await self.create(
            group=group,
            username=username,
            name=f"{first_name} {last_name}".strip(),
            first_name=first_name,
            last_name=last_name,
            email=email,
            mobile=mobile,
            **kwargs,
        )

    async def create_merchant(
        self,
        *,
        username: str,
        name: str,
        email: str | None = None,
        mobile: str | None = None,
        group: str = "merchant",
        **kwargs: Any,
    ) -> MemberRegistrationResult:
        return await self.create(
            group=group,
            username=username,
            name=name,
            email=email,
            mobile=mobile,
            **kwargs,
        )

    async def create_organization(
        self,
        *,
        username: str,
        name: str,
        email: str | None = None,
        mobile: str | None = None,
        group: str = "corporate",
        **kwargs: Any,
    ) -> MemberRegistrationResult:
        return await self.create(
            group=group,
            username=username,
            name=name,
            email=email,
            mobile=mobile,
            **kwargs,
        )
