"""Member management client.

Cyclos 4.16 does not expose a separate ``/members`` endpoint; members,
merchants, organizations and operators are all managed through ``/users``.
This module is a convenience wrapper over the ``/users`` resource.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from angstrom_cyclos.members.models import (
    Member,
    MemberBase,
    MemberCreate,
    MemberRegistrationResult,
)
from angstrom_cyclos.models import PaginatedResult, UserStatus

if TYPE_CHECKING:
    from angstrom_cyclos.client import CyclosClient


class MembersClient:
    """Create, read, update and search Cyclos members."""

    def __init__(self, client: CyclosClient) -> None:
        self._client = client

    def create(
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
        """Create a new member/user in the given group.

        The ``group`` argument must be the Cyclos internal name or id for the
        desired member group (e.g. ``individualCustomer``).
        """
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
        response = self._client._transport.post(
            "/users", json=payload.model_dump(exclude_none=True, by_alias=True)
        )
        return MemberRegistrationResult.model_validate(response.json())

    def get(self, user_id: str) -> Member:
        """Retrieve a member by user id, login name, e-mail, phone, etc."""
        response = self._client._transport.get(f"/users/{user_id}")
        return Member.model_validate(response.json())

    def update(
        self,
        user_id: str,
        *,
        data: MemberBase | dict[str, Any],
    ) -> Member:
        """Update a member's profile fields."""
        if isinstance(data, MemberBase):
            payload = data.model_dump(exclude_none=True, by_alias=True)
        else:
            payload = data
        response = self._client._transport.put(f"/users/{user_id}", json=payload)
        return Member.model_validate(response.json())

    def delete(self, user_id: str) -> None:
        """Delete a pending member."""
        self._client._transport.delete(f"/users/{user_id}")

    def search(
        self,
        *,
        query: str | None = None,
        fields: dict[str, str] | None = None,
        groups: list[str] | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[Member]:
        """Search members/users.

        ``fields`` are sent as ``customValues`` query parameters where supported.
        Cyclos searches through the configured keyword principals, not arbitrary
        custom-field equality.
        """
        params: dict[str, Any] = {
            "keywords": query,
            "groups": groups,
            "page": page,
            "pageSize": page_size,
        }
        if fields:
            for key, value in fields.items():
                params[f"customValues.{key}"] = value
        response = self._client._transport.get("/users", params=params)
        items = [Member.model_validate(u) for u in response.json()]
        return PaginatedResult[Member](
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(items) >= page_size,
        )

    def _set_status(self, user_id: str, status: UserStatus) -> None:
        self._client._transport.post(
            f"/{user_id}/status",
            json={"status": status.value},
        )

    def activate(self, user_id: str) -> None:
        """Activate (or re-activate) a member."""
        self._set_status(user_id, UserStatus.ACTIVE)

    def deactivate(self, user_id: str) -> None:
        """Disable a member."""
        self._set_status(user_id, UserStatus.DISABLED)

    def block(self, user_id: str) -> None:
        """Block a member."""
        self._set_status(user_id, UserStatus.BLOCKED)

    def create_individual(
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
        """Convenience method to create an individual member."""
        return self.create(
            group=group,
            username=username,
            name=f"{first_name} {last_name}".strip(),
            first_name=first_name,
            last_name=last_name,
            email=email,
            mobile=mobile,
            **kwargs,
        )

    def create_merchant(
        self,
        *,
        username: str,
        name: str,
        email: str | None = None,
        mobile: str | None = None,
        group: str = "merchant",
        **kwargs: Any,
    ) -> MemberRegistrationResult:
        """Convenience method to create a merchant/business member."""
        return self.create(
            group=group,
            username=username,
            name=name,
            email=email,
            mobile=mobile,
            **kwargs,
        )

    def create_organization(
        self,
        *,
        username: str,
        name: str,
        email: str | None = None,
        mobile: str | None = None,
        group: str = "corporate",
        **kwargs: Any,
    ) -> MemberRegistrationResult:
        """Convenience method to create an organization member."""
        return self.create(
            group=group,
            username=username,
            name=name,
            email=email,
            mobile=mobile,
            **kwargs,
        )
