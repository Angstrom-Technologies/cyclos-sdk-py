"""Synchronous Cyclos SDK client."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from angstrom_cyclos.accounts.client import AccountsClient
from angstrom_cyclos.auth.client import AuthClient
from angstrom_cyclos.config import CyclosConfig
from angstrom_cyclos.members.client import MembersClient
from angstrom_cyclos.operators.client import OperatorsClient
from angstrom_cyclos.organizations.client import OrganizationsClient
from angstrom_cyclos.permissions.client import PermissionsClient
from angstrom_cyclos.transactions.client import TransactionsClient
from angstrom_cyclos.transfers.client import TransfersClient
from angstrom_cyclos.transport import HTTPTransport
from angstrom_cyclos.users.client import UsersClient
from angstrom_cyclos.webservices.client import WebServicesClient


class CyclosClient:
    """Main synchronous client for the Cyclos 4.16 REST API.

    The client exposes domain-specific sub-clients for authentication, members,
    organizations, operators, permissions, web-service/access clients, accounts,
    transfers and transactions.

    Example:
        >>> from angstrom_cyclos import CyclosClient, CyclosConfig
        >>> config = CyclosConfig.from_env()
        >>> with CyclosClient(config) as client:
        ...     client.auth.login("username", "password")
        ...     client.members.get("alice")
    """

    def __init__(self, config: CyclosConfig | None = None) -> None:
        self._config = config or CyclosConfig.from_env()
        self._transport = HTTPTransport(self._config)
        self.auth = AuthClient(self)
        self.members = MembersClient(self)
        self.users = UsersClient(self)
        self.organizations = OrganizationsClient(self)
        self.operators = OperatorsClient(self)
        self.permissions = PermissionsClient(self)
        self.webservices = WebServicesClient(self)
        self.accounts = AccountsClient(self)
        self.transfers = TransfersClient(self)
        self.transactions = TransactionsClient(self)

    @property
    def config(self) -> CyclosConfig:
        """Return the client configuration."""
        return self._config

    @property
    def _transport(self) -> HTTPTransport:
        return self.__transport

    @_transport.setter
    def _transport(self, value: HTTPTransport) -> None:
        self.__transport = value

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP transport."""
        self._transport.close()
