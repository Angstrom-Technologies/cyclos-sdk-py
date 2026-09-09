"""Configuration management for the Cyclos SDK."""

from __future__ import annotations

from pydantic import Field, HttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from angstrom_cyclos.constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_BACKOFF,
    DEFAULT_TIMEOUT,
    DEFAULT_VERIFY_SSL,
)


class CyclosConfig(BaseSettings):
    """Configuration object for connecting to a Cyclos 4.16 installation.

    Values may be provided directly or loaded from environment variables.
    Sensitive fields are stored as ``SecretStr`` and are never exposed in
    string representations or logs.
    """

    model_config = SettingsConfigDict(
        env_prefix="CYCLOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_assignment=True,
    )

    base_url: str = Field(
        default="https://wallet.angstrom-technologies.ug/uwallet/api",
        description="Base URL of the Cyclos REST API.",
    )
    username: str | None = Field(
        default=None,
        description="Cyclos login name used for HTTP Basic authentication during login.",
    )
    password: SecretStr | None = Field(
        default=None,
        description="Cyclos password used for HTTP Basic authentication during login.",
    )
    timeout: float = Field(
        default=DEFAULT_TIMEOUT,
        ge=1.0,
        description="Default HTTP request timeout in seconds.",
    )
    verify_ssl: bool = Field(
        default=DEFAULT_VERIFY_SSL,
        description="Whether to verify SSL certificates.",
    )
    max_retries: int = Field(
        default=DEFAULT_MAX_RETRIES,
        ge=0,
        le=10,
        description="Maximum number of retries for transient failures.",
    )
    retry_backoff: float = Field(
        default=DEFAULT_RETRY_BACKOFF,
        ge=0.0,
        description="Initial exponential backoff in seconds.",
    )

    @field_validator("base_url", mode="before")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/") if isinstance(value, str) else value

    @field_validator("base_url", mode="after")
    @classmethod
    def _ensure_valid_url(cls, value: str) -> str:
        HttpUrl(value)
        return value

    @classmethod
    def from_env(cls) -> "CyclosConfig":
        """Instantiate configuration from environment variables."""
        return cls()

    def __str__(self) -> str:  # pragma: no cover
        return f"CyclosConfig(base_url={self.base_url}, username={self.username!r})"

    def __repr__(self) -> str:  # pragma: no cover
        return self.__str__()
