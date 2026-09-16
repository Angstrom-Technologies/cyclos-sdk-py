"""Authentication client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from angstrom_cyclos.auth.models import Auth, LoginAuth

if TYPE_CHECKING:
    from angstrom_cyclos.client import CyclosClient


class AuthClient:
    """Handles Cyclos login, logout, session refresh, and current user lookup."""

    def __init__(self, client: CyclosClient) -> None:
        self._client = client

    def login(self, username: str, password: str) -> LoginAuth:
        """Authenticate and store the returned session token.

        Args:
            username: Cyclos login name.
            password: Cyclos password. Never logged.

        Returns:
            Parsed login response including ``session_token``.
        """
        response = self._client._transport.post(
            "/auth/session",
            auth=(username, password),
        )
        data = LoginAuth.model_validate(response.json())
        if data.session_token:
            self._client._transport.session_token = data.session_token
        return data

    def logout(self) -> None:
        """Log out the current session and clear local authentication state."""
        self._client._transport.delete("/auth/session")
        self._client._transport.session_token = None
        self._client._transport.access_client_token = None

    def current_user(self) -> Auth:
        """Return information about the currently authenticated user."""
        response = self._client._transport.get("/auth")
        return Auth.model_validate(response.json())

    def is_authenticated(self) -> bool:
        """Return whether a session or access-client token is currently stored."""
        transport = self._client._transport
        return transport.session_token is not None or transport.access_client_token is not None

    def set_access_client_token(self, token: str) -> None:
        """Set a token returned by ``POST /clients/activate`` for subsequent requests."""
        self._client._transport.access_client_token = token

    def refresh(self) -> LoginAuth:
        """Refresh the current session if supported.

        Cyclos 4.16 does not expose a dedicated refresh endpoint. This method
        re-authenticates using the credentials stored in the configuration
        (if available). Prefer explicit ``login`` calls if credentials are not
        configured.
        """
        config = self._client._config
        if not config.username or not config.password:
            raise RuntimeError("Cannot refresh session: no credentials configured")
        return self.login(config.username, config.password.get_secret_value())

    def set_session_token(self, token: str) -> None:
        """Manually set the session token for subsequent requests."""
        self._client._transport.session_token = token
