"""Organization management client.

Cyclos 4.16 does not expose a separate organization resource. Organizations are
users in a specific group (e.g. ``corporate``). This module wraps the
``MembersClient`` with organization-oriented defaults.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from angstrom_cyclos.members.client import MembersClient
from angstrom_cyclos.members.models import Member as Organization
from angstrom_cyclos.members.models import MemberBase as OrganizationBase
from angstrom_cyclos.members.models import (
    MemberRegistrationResult as OrganizationRegistrationResult,
)
from angstrom_cyclos.models import PaginatedResult

if TYPE_CHECKING:
    from angstrom_cyclos.client import CyclosClient


class OrganizationsClient:
    """Create and search organizations/businesses in Cyclos."""

    def __init__(self, client: CyclosClient) -> None:
        self._client = client
        self._members = MembersClient(client)

    def create(
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
        """Create an organization/business user.

        Args:
            group: Cyclos internal name or id of the organization group.
            name: Organization name. Also used as username if not supplied.
            username: Optional login name; defaults to ``name``.
            email: Optional e-mail address.
            mobile: Optional mobile phone number.
            custom_fields: Optional custom field values keyed by internal name.
            **kwargs: Additional fields forwarded to the underlying member create.
        """
        return self._members.create(
            group=group,
            username=username or name,
            name=name,
            email=email,
            mobile=mobile,
            custom_fields=custom_fields,
            **kwargs,
        )

    def get(self, organization_id: str) -> Organization:
        """Retrieve an organization by id or principal."""
        return self._members.get(organization_id)

    def update(
        self,
        organization_id: str,
        *,
        data: OrganizationBase | dict[str, Any],
    ) -> Organization:
        """Update an organization's profile fields."""
        return self._members.update(organization_id, data=data)

    def search(
        self,
        *,
        query: str | None = None,
        groups: list[str] | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[Organization]:
        """Search organizations by query and/or organization groups."""
        return self._members.search(
            query=query,
            groups=groups,
            page=page,
            page_size=page_size,
        )
