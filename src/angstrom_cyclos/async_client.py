"""Asynchronous Cyclos SDK client."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from angstrom_cyclos.accounts.client_async import AsyncAccountsClient
from angstrom_cyclos.auth.client_async import AsyncAuthClient
from angstrom_cyclos.config import CyclosConfig
from angstrom_cyclos.members.client_async import AsyncMembersClient
from angstrom_cyclos.operators.client_async import AsyncOperatorsClient
from angstrom_cyclos.organizations.client_async import AsyncOrganizationsClient
from angstrom_cyclos.permissions.client_async import AsyncPermissionsClient
from angstrom_cyclos.transactions.client_async import AsyncTransactionsClient
from angstrom_cyclos.transfers.client_async import AsyncTransfersClient
from angstrom_cyclos.transport import AsyncHTTPTransport
from angstrom_cyclos.users.client_async import AsyncUsersClient
from angstrom_cyclos.webservices.client_async import AsyncWebServicesClient


class AsyncCyclosClient:
    """Asynchronous client for the Cyclos 4.16 REST API.

    Example:
        >>> import asyncio
        >>> from angstrom_cyclos import AsyncCyclosClient, CyclosConfig
        >>> config = CyclosConfig.from_env()
        >>> async def main() -> None:
        ...     async with AsyncCyclosClient(config) as client:
        ...         await client.auth.login("username", "password")
        ...         await client.members.get("alice")
        >>> asyncio.run(main())
    """

    def __init__(self, config: CyclosConfig | None = None) -> None:
        self._config = config or CyclosConfig.from_env()
        self._transport = AsyncHTTPTransport(self._config)
        self.auth = AsyncAuthClient(self)
        self.members = AsyncMembersClient(self)
        self.users = AsyncUsersClient(self)
        self.organizations = AsyncOrganizationsClient(self)
        self.operators = AsyncOperatorsClient(self)
        self.permissions = AsyncPermissionsClient(self)
        self.webservices = AsyncWebServicesClient(self)
        self.accounts = AsyncAccountsClient(self)
        self.transfers = AsyncTransfersClient(self)
        self.transactions = AsyncTransactionsClient(self)

    @property
    def config(self) -> CyclosConfig:
        return self._config

    @property
    def _transport(self) -> AsyncHTTPTransport:
        return self.__transport

    @_transport.setter
    def _transport(self, value: AsyncHTTPTransport) -> None:
        self.__transport = value

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self._transport.close()
