"""Cyclos SDK exception hierarchy.

Exception messages must never contain passwords, access tokens, secrets, PINs,
or authorization headers.
"""

from __future__ import annotations

from typing import Any


class CyclosError(Exception):
    """Base class for all Cyclos SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        cyclos_code: str | None = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
        endpoint: str | None = None,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.cyclos_code = cyclos_code
        self.request_id = request_id
        self.correlation_id = correlation_id
        self.endpoint = endpoint
        self.response_body = response_body or {}

    def __str__(self) -> str:  # pragma: no cover
        parts = [self.message]
        if self.status_code:
            parts.append(f"status={self.status_code}")
        if self.cyclos_code:
            parts.append(f"cyclos_code={self.cyclos_code}")
        if self.request_id:
            parts.append(f"request_id={self.request_id}")
        if self.correlation_id:
            parts.append(f"correlation_id={self.correlation_id}")
        if self.endpoint:
            parts.append(f"endpoint={self.endpoint}")
        return " | ".join(parts)

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}({self})"


class CyclosAuthenticationError(CyclosError):
    """Invalid or missing credentials (HTTP 401)."""


class CyclosAuthorizationError(CyclosError):
    """Permission denied or illegal action (HTTP 403)."""


class CyclosValidationError(CyclosError):
    """Input validation failed (HTTP 422)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.property_errors: dict[str, list[str]] = kwargs.pop("property_errors", {})
        self.general_errors: list[str] = kwargs.pop("general_errors", [])
        super().__init__(*args, **kwargs)


class CyclosNotFoundError(CyclosError):
    """Expected entity was not found (HTTP 404)."""


class CyclosConflictError(CyclosError):
    """Entity state conflict (HTTP 409)."""


class CyclosRateLimitError(CyclosError):
    """Rate limit exceeded (HTTP 429)."""


class CyclosServerError(CyclosError):
    """Unexpected Cyclos server error (HTTP 5xx)."""


class CyclosTimeoutError(CyclosError):
    """Request timed out."""


class CyclosConnectionError(CyclosError):
    """Network-level connection error."""


class CyclosTransferError(CyclosError):
    """Payment/transfer operation failed after a successful HTTP response."""


class CyclosIdempotencyError(CyclosError):
    """A duplicate financial operation was detected by the SDK idempotency guard."""


class CyclosNotImplementedError(CyclosError):
    """Feature not exposed by the configured Cyclos installation."""
