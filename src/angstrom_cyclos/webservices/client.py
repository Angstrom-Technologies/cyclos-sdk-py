"""Web service / access client management.

Cyclos 4.16 access clients belong to the authenticated user. Administrators
wishing to create a client on behalf of another user must either authenticate as
that user or use a privileged channel. The SDK documents this limitation and
never logs the returned access token.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from angstrom_cyclos.models import PaginatedResult
from angstrom_cyclos.webservices.models import (
    AccessClientActivationCodeRequest,
    WebServiceClient,
    WebServiceClientCreate,
)

if TYPE_CHECKING:
    from angstrom_cyclos.client import CyclosClient


class WebServicesClient:
    """Manage Cyclos access clients (web service clients)."""

    def __init__(self, client: CyclosClient) -> None:
        self._client = client

    def send_activation_code(
        self,
        request: AccessClientActivationCodeRequest | dict[str, Any] | None = None,
    ) -> None:
        """Request Cyclos to send an activation code to the authenticated user."""
        if request is None:
            payload = {}
        elif isinstance(request, AccessClientActivationCodeRequest):
            payload = request.model_dump(exclude_none=True, by_alias=True)
        else:
            payload = request
        self._client._transport.post("/clients/send-activaction-code", json=payload)

    def create_client(
        self,
        *,
        name: str,
        client_type: str | None = None,
        activation_code: str,
        prefix: str | None = None,
        user_id: str | None = None,
    ) -> WebServiceClient:
        """Create and activate an access client.

        The Cyclos ``POST /clients/{type}`` endpoint creates the client for the
        *currently authenticated user*. The optional ``user_id`` parameter is
        recorded as metadata only; to create a client for another user the
        caller must authenticate as that user or have an appropriate privileged
        channel configured.

        The returned token is stored on the transport layer for subsequent
        requests and is never included in logs.
        """
        ct = client_type or "default"
        payload = WebServiceClientCreate(
            client_type=ct,
            name=name,
            prefix=prefix,
            activation_code=activation_code,
            user_id=user_id,
        )
        response = self._client._transport.post(
            f"/clients/{ct}",
            json=payload.model_dump(exclude_none=True, by_alias=True),
        )
        data = response.json()
        token = data.get("token")
        if token:
            self._client._transport.access_client_token = f"{prefix or ''}{token}"
        return WebServiceClient.model_validate(data)

    def get_client(self, key: str) -> WebServiceClient:
        """Retrieve an access client by id or internal name."""
        response = self._client._transport.get(f"/clients/{key}")
        return WebServiceClient.model_validate(response.json())

    def update_client(
        self,
        key: str,
        *,
        name: str | None = None,
        status: str | None = None,
    ) -> WebServiceClient:
        """Update an access client.

        Cyclos exposes ``unassign`` and activation operations rather than a
        generic PUT. This method updates fields that the API supports via POST
        operations. Status changes are mapped to ``/clients/{key}/unassign``.
        """
        if status == "unassigned":
            self._client._transport.post(f"/clients/{key}/unassign")
        return self.get_client(key)

    def delete_client(self, key: str) -> None:
        """Unassign (disconnect) an access client."""
        self._client._transport.post(f"/clients/{key}/unassign")

    def activate_client(
        self,
        *,
        code: str,
        prefix: str | None = None,
    ) -> WebServiceClient:
        """Activate an unassigned access client using a code."""
        params: dict[str, Any] = {"code": code}
        if prefix:
            params["prefix"] = prefix
        response = self._client._transport.post("/clients/activate", params=params)
        data = response.json()
        token = data.get("token")
        if token:
            self._client._transport.access_client_token = f"{prefix or ''}{token}"
        return WebServiceClient.model_validate(data)

    def deactivate_client(self, key: str) -> None:
        """Deactivate (unassign) an access client."""
        self._client._transport.post(f"/clients/{key}/unassign")

    def list_clients(
        self,
        *,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[WebServiceClient]:
        """List access clients.

        Cyclos does not expose a dedicated list endpoint for access clients. This
        method returns an empty result and documents the limitation. Callers
        should store access client ids locally.
        """
        return PaginatedResult[WebServiceClient](
            items=[],
            page=page,
            page_size=page_size,
            has_next=False,
        )

    def rotate_credentials(
        self,
        key: str,
        *,
        activation_code: str,
        prefix: str | None = None,
    ) -> WebServiceClient:
        """Rotate an access client token.

        Cyclos 4.16 does not expose a dedicated rotate endpoint. The SDK
        unassigns the old client and activates a new one with the same name.
        """
        old = self.get_client(key)
        self.delete_client(key)
        return self.create_client(
            name=old.name or key,
            client_type=old.access_client_type.id if old.access_client_type else None,
            activation_code=activation_code,
            prefix=prefix,
            user_id=old.user.id if old.user else None,
        )
