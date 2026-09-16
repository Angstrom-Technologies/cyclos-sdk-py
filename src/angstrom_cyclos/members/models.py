"""Member/user models for the Cyclos SDK."""

from __future__ import annotations

from pydantic import Field

from angstrom_cyclos.models import (
    Address,
    CyclosBaseModel,
    EntityReference,
    PasswordRegistration,
    Phone,
    UserReference,
)


class MemberBase(CyclosBaseModel):
    """Common fields for member/user creation."""

    group: str | None = None
    username: str | None = None
    name: str | None = None
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    email: str | None = None
    mobile: str | None = None
    custom_fields: dict[str, str] | None = Field(default=None, alias="customValues")
    mobile_phones: list[Phone] | None = Field(default=None, alias="mobilePhones")
    land_line_phones: list[Phone] | None = Field(default=None, alias="landLinePhones")
    addresses: list[Address] | None = None
    passwords: list[PasswordRegistration] | None = None
    skip_activation_email: bool | None = Field(default=None, alias="skipActivationEmail")
    accept_agreements: list[str] | None = Field(default=None, alias="acceptAgreements")
    broker: str | None = None


class IndividualMemberCreate(MemberBase):
    """Create an individual member."""


class MerchantMemberCreate(MemberBase):
    """Create a merchant/business member."""


class OrganizationMemberCreate(MemberBase):
    """Create an organization/corporate member."""


class AgentMemberCreate(MemberBase):
    """Create an agent member."""


class MemberCreate(MemberBase):
    """Generic member creation model."""


class Member(UserReference):
    """Member/user result returned by Cyclos."""

    username: str | None = None
    email: str | None = None
    group: EntityReference | None = None
    status: str | EntityReference | None = None
    custom_values: dict[str, str] | None = Field(default=None, alias="customValues")


class MemberRegistrationResult(CyclosBaseModel):
    """Result of a user/member registration."""

    user: Member
    generated_passwords: list[EntityReference] | None = Field(
        default=None, alias="generatedPasswords"
    )
    status: str | None = None
    root_url: str | None = Field(default=None, alias="rootUrl")
