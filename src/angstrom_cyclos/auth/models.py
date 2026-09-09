"""Authentication-related Pydantic models."""

from __future__ import annotations

from pydantic import Field

from angstrom_cyclos.models import CyclosBaseModel, EntityReference, UserReference


class LoginAuth(CyclosBaseModel):
    """Response from ``POST /auth/session``."""

    user: UserReference | None = None
    session_token: str | None = Field(default=None, alias="sessionToken")
    principal: str | None = None
    expired_password: bool | None = Field(default=None, alias="expiredPassword")
    pending_agreements: bool | None = Field(default=None, alias="pendingAgreements")


class Auth(CyclosBaseModel):
    """Response from ``GET /auth``."""

    user: UserReference | None = None
    principal: str | None = None
    access_client: EntityReference | None = Field(default=None, alias="accessClient")
    expired_password: bool | None = Field(default=None, alias="expiredPassword")
    pending_agreements: bool | None = Field(default=None, alias="pendingAgreements")
