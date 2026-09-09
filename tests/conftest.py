"""Shared test fixtures."""

from __future__ import annotations

import pytest

from angstrom_cyclos import CyclosConfig


@pytest.fixture
def config() -> CyclosConfig:
    return CyclosConfig(
        base_url="https://wallet.example.com/api",
        username="admin",
        password="secret",
        timeout=5.0,
        verify_ssl=True,
        max_retries=2,
        retry_backoff=0.1,
    )
