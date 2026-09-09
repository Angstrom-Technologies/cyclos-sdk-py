"""Low-level user client wrapping ``/users``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from angstrom_cyclos.members.client import MembersClient
from angstrom_cyclos.members.models import Member as User
from angstrom_cyclos.members.models import MemberBase as UserBase
from angstrom_cyclos.members.models import MemberRegistrationResult as UserRegistrationResult
from angstrom_cyclos.models import PaginatedResult

if TYPE_CHECKING:
    from angstrom_cyclos.client import CyclosClient


class UsersClient:
    """Low-level user client.

    Provides the same functionality as ``MembersClient`` under the ``users``
    namespace for callers that prefer Cyclos terminology.
    """

    def __init__(self, client: CyclosClient) -> None:
        self._client = client
        self._members = MembersClient(client)

    def create(
        self,
        *,
        group: str,
        username: str,
        **kwargs: Any,
    ) -> UserRegistrationResult:
        """Create a new Cyclos user."""
        return self._members.create(group=group, username=username, **kwargs)

    def get(self, user_id: str) -> User:
        """Retrieve a user by id or principal."""
        return self._members.get(user_id)

    def update(
        self,
        user_id: str,
        *,
        data: UserBase | dict[str, Any],
    ) -> User:
        """Update a user's profile fields."""
        return self._members.update(user_id, data=data)

    def search(
        self,
        *,
        query: str | None = None,
        fields: dict[str, str] | None = None,
        groups: list[str] | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[User]:
        """Search users."""
        return self._members.search(
            query=query,
            fields=fields,
            groups=groups,
            page=page,
            page_size=page_size,
        )
