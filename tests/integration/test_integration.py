"""Optional integration tests.

Run only when ``CYCLOS_INTEGRATION_TESTS=true`` is set.
"""

from __future__ import annotations

import os

import pytest

from angstrom_cyclos import CyclosClient, CyclosConfig

pytestmark = pytest.mark.skipif(
    os.environ.get("CYCLOS_INTEGRATION_TESTS", "").lower() != "true",
    reason="Integration tests disabled. Set CYCLOS_INTEGRATION_TESTS=true to enable.",
)


@pytest.fixture
def live_client() -> CyclosClient:
    config = CyclosConfig(
        base_url=os.environ.get("CYCLOS_TEST_BASE_URL", ""),
        username=os.environ.get("CYCLOS_TEST_USERNAME", ""),
        password=os.environ.get("CYCLOS_TEST_PASSWORD", ""),
    )
    client = CyclosClient(config)
    client.auth.login(
        config.username or "",
        config.password.get_secret_value() if config.password else "",
    )
    return client


@pytest.mark.integration
def test_live_login(live_client: CyclosClient) -> None:
    assert live_client.auth.is_authenticated()
    user = live_client.auth.current_user()
    assert user.user is not None


@pytest.mark.integration
def test_live_list_accounts(live_client: CyclosClient) -> None:
    user = live_client.auth.current_user()
    assert user.user is not None
    user_id: str = user.user.id or ""
    accounts = live_client.accounts.list(member_id=user_id)
    assert accounts.items is not None
