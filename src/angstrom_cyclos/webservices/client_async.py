"""Asynchronous web service / access client module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from angstrom_cyclos.models import PaginatedResult
from angstrom_cyclos.webservices.models import (
    AccessClientActivationCodeRequest,
    WebServiceClient,
    WebServiceClientCreate,
)

if TYPE_CHECKING:
    from angstrom_cyclos.async_client import AsyncCyclosClient


class AsyncWebServicesClient:
    """Async web service client."""

    def __init__(self, client: AsyncCyclosClient) -> None:
        self._client = client

    async def send_activation_code(
        self,
        request: AccessClientActivationCodeRequest | dict[str, Any] | None = None,
    ) -> None:
        if request is None:
            payload = {}
        elif isinstance(request, AccessClientActivationCodeRequest):
            payload = request.model_dump(exclude_none=True, by_alias=True)
        else:
            payload = request
        await self._client._transport.post("/clients/send-activaction-code", json=payload)

    async def create_client(
        self,
        *,
        name: str,
        client_type: str | None = None,
        activation_code: str,
        prefix: str | None = None,
        user_id: str | None = None,
    ) -> WebServiceClient:
        ct = client_type or "default"
        payload = WebServiceClientCreate(
            client_type=ct,
            name=name,
            prefix=prefix,
            activation_code=activation_code,
            user_id=user_id,
        )
        response = await self._client._transport.post(
            f"/clients/{ct}",
            json=payload.model_dump(exclude_none=True, by_alias=True),
        )
        data = response.json()
        token = data.get("token")
        if token:
            self._client._transport.access_client_token = token
        return WebServiceClient.model_validate(data)

    async def get_client(self, key: str) -> WebServiceClient:
        response = await self._client._transport.get(f"/clients/{key}")
        return WebServiceClient.model_validate(response.json())

    async def update_client(
        self,
        key: str,
        *,
        name: str | None = None,
        status: str | None = None,
    ) -> WebServiceClient:
        if status == "unassigned":
            await self._client._transport.post(f"/clients/{key}/unassign")
        return await self.get_client(key)

    async def delete_client(self, key: str) -> None:
        await self._client._transport.post(f"/clients/{key}/unassign")

    async def activate_client(
        self,
        *,
        code: str,
        prefix: str | None = None,
    ) -> WebServiceClient:
        params: dict[str, Any] = {"code": code}
        if prefix:
            params["prefix"] = prefix
        response = await self._client._transport.post("/clients/activate", params=params)
        data = response.json()
        token = data.get("token")
        if token:
            self._client._transport.access_client_token = token
        return WebServiceClient.model_validate(data)

    async def deactivate_client(self, key: str) -> None:
        await self._client._transport.post(f"/clients/{key}/unassign")

    async def list_clients(
        self,
        *,
        page: int = 0,
        page_size: int = 20,
    ) -> PaginatedResult[WebServiceClient]:
        return PaginatedResult[WebServiceClient](
            items=[],
            page=page,
            page_size=page_size,
            has_next=False,
        )

    async def rotate_credentials(
        self,
        key: str,
        *,
        activation_code: str,
        prefix: str | None = None,
    ) -> WebServiceClient:
        old = await self.get_client(key)
        await self.delete_client(key)
        return await self.create_client(
            name=old.name or key,
            client_type=old.access_client_type.id if old.access_client_type else None,
            activation_code=activation_code,
            prefix=prefix,
            user_id=old.user.id if old.user else None,
        )
