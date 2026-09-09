"""Web service / access client models."""

from __future__ import annotations

from pydantic import Field, model_validator

from angstrom_cyclos.models import CyclosBaseModel, EntityReference, UserReference


class WebServiceClientCreate(CyclosBaseModel):
    """Request to create/activate an access client.

    In Cyclos 4.16 an access client is created for the *authenticated user* via
    ``POST /clients/{type}`` after sending an activation code. The optional
    ``user_id`` is a wallet-middleware convenience identifier; the SDK will use
    that user's credentials where configured.
    """

    client_type: str = Field(alias="clientType")
    name: str | None = None
    prefix: str | None = None
    activation_code: str | None = Field(default=None, repr=False, alias="activationCode")
    user_id: str | None = Field(default=None, alias="userId")


class WebServiceClient(CyclosBaseModel):
    """Activated access client reference."""

    id: str | None = None
    name: str | None = None
    token: str | None = Field(default=None, repr=False)
    access_client: EntityReference | None = Field(default=None, alias="accessClient")
    access_client_type: EntityReference | None = Field(default=None, alias="accessClientType")
    user: UserReference | None = None
    status: str | None = None
    activation_date: str | None = Field(default=None, alias="activationDate")
    can_unassign: bool | None = Field(default=None, alias="canUnassign")

    @model_validator(mode="after")
    def _derive_id_from_access_client(self) -> "WebServiceClient":
        if not self.id and self.access_client and self.access_client.id:
            self.id = self.access_client.id
        if not self.name and self.access_client and self.access_client.name:
            self.name = self.access_client.name
        return self


class AccessClientActivationCodeRequest(CyclosBaseModel):
    """Request to send an access client activation code."""

    mobile_phone: str | None = Field(default=None, alias="mobilePhone")
    email: str | None = None
    principal: str | None = None
    principal_type: str | None = Field(default=None, alias="principalType")


__all__ = ["WebServiceClientCreate", "WebServiceClient", "AccessClientActivationCodeRequest"]
