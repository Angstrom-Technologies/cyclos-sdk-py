"""Asynchronous authentication client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from angstrom_cyclos.auth.models import Auth, LoginAuth

if TYPE_CHECKING:
    from angstrom_cyclos.async_client import AsyncCyclosClient


class AsyncAuthClient:
    """Async authentication client."""

    def __init__(self, client: AsyncCyclosClient) -> None:
        self._client = client

    async def login(self, username: str, password: str) -> LoginAuth:
        response = await self._client._transport.post(
            "/auth/session",
            auth=(username, password),
        )
        data = LoginAuth.model_validate(response.json())
        if data.session_token:
            self._client._transport.session_token = data.session_token
        return data

    async def logout(self) -> None:
        await self._client._transport.delete("/auth/session")
        self._client._transport.session_token = None
        self._client._transport.access_client_token = None

    async def current_user(self) -> Auth:
        response = await self._client._transport.get("/auth")
        return Auth.model_validate(response.json())

    async def is_authenticated(self) -> bool:
        transport = self._client._transport
        return transport.session_token is not None or transport.access_client_token is not None

    async def set_access_client_token(self, token: str) -> None:
        self._client._transport.access_client_token = token

    async def refresh(self) -> LoginAuth:
        config = self._client._config
        if not config.username or not config.password:
            raise RuntimeError("Cannot refresh session: no credentials configured")
        return await self.login(config.username, config.password.get_secret_value())

    async def set_session_token(self, token: str) -> None:
        self._client._transport.session_token = token
