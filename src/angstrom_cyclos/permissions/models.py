"""Permission models."""

from __future__ import annotations

from pydantic import Field

from angstrom_cyclos.models import CyclosBaseModel


class Permissions(CyclosBaseModel):
    """Cyclos permission structure returned by ``GET /auth``."""

    user_operations: list[str] | None = Field(default=None, alias="userOperations")
    user_records: list[str] | None = Field(default=None, alias="userRecords")
    system_records: list[str] | None = Field(default=None, alias="systemRecords")
    user_profile_fields: list[str] | None = Field(default=None, alias="userProfileFields")
    own_profile_fields: list[str] | None = Field(default=None, alias="ownProfileFields")
    contact_profile_fields: list[str] | None = Field(default=None, alias="contactProfileFields")
    operations: list[str] | None = None
    user_advertisements: list[str] | None = Field(default=None, alias="userAdvertisements")


class PermissionGroup(CyclosBaseModel):
    """Normalized permission group representation."""

    id: str
    name: str
    permissions: list[str]


__all__ = ["Permissions", "PermissionGroup"]
