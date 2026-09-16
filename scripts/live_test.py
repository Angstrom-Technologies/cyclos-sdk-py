"""Live smoke test for cyclos-sdk-py.

Fill in the values in ``SETTINGS`` or provide their matching environment
variables, then run:

    python scripts/live_test.py

Read-only checks run by default. Mutating tests require ENABLE_WRITES=true.
The transfer test additionally requires ENABLE_TRANSFER=true.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, SecretStr

from angstrom_cyclos import CyclosClient, CyclosConfig, CyclosError

SETTINGS = {
    "base_url": os.getenv(
        "CYCLOS_BASE_URL",
        "https://wallet.angstrom-technologies.ug/uwallet/api",
    ),
    # Preferred authentication: paste the full token returned by /clients/activate.
    "access_client_token": os.getenv("CYCLOS_ACCESS_CLIENT_TOKEN", ""),
    # Only needed to test session login or activate an access client.
    "username": os.getenv("CYCLOS_USERNAME", ""),
    "password": os.getenv("CYCLOS_PASSWORD", ""),
    "activation_code": os.getenv("CYCLOS_ACTIVATION_CODE", ""),
    "activation_prefix": os.getenv("CYCLOS_ACTIVATION_PREFIX", ""),
    # Existing resources used by read-only tests.
    "member_id": os.getenv("CYCLOS_TEST_MEMBER_ID", ""),
    "organization_id": os.getenv("CYCLOS_TEST_ORGANIZATION_ID", ""),
    "operator_id": os.getenv("CYCLOS_TEST_OPERATOR_ID", ""),
    "operator_group_id": os.getenv("CYCLOS_TEST_OPERATOR_GROUP_ID", ""),
    "account_type": os.getenv("CYCLOS_TEST_ACCOUNT_TYPE", "mobileWallet"),
    "transfer_id": os.getenv("CYCLOS_TEST_TRANSFER_ID", ""),
    "transaction_id": os.getenv("CYCLOS_TEST_TRANSACTION_ID", ""),
    "access_client_id": os.getenv("CYCLOS_TEST_ACCESS_CLIENT_ID", ""),
    # Values used only when write tests are explicitly enabled.
    "new_member_group": os.getenv("CYCLOS_TEST_NEW_MEMBER_GROUP", ""),
    "new_member_username": os.getenv("CYCLOS_TEST_NEW_MEMBER_USERNAME", ""),
    "new_member_first_name": os.getenv("CYCLOS_TEST_NEW_MEMBER_FIRST_NAME", "SDK"),
    "new_member_last_name": os.getenv("CYCLOS_TEST_NEW_MEMBER_LAST_NAME", "Test"),
    "transfer_type": os.getenv("CYCLOS_TEST_TRANSFER_TYPE", ""),
    "transfer_from": os.getenv("CYCLOS_TEST_TRANSFER_FROM", ""),
    "transfer_to": os.getenv("CYCLOS_TEST_TRANSFER_TO", ""),
    "transfer_amount": os.getenv("CYCLOS_TEST_TRANSFER_AMOUNT", "1"),
    "transfer_currency": os.getenv("CYCLOS_TEST_TRANSFER_CURRENCY", "UGX"),
}

ENABLE_WRITES = os.getenv("ENABLE_WRITES", "false").lower() == "true"
ENABLE_TRANSFER = os.getenv("ENABLE_TRANSFER", "false").lower() == "true"


def compact(value: Any) -> Any:
    """Return a concise, serializable representation without exposing secrets."""
    if isinstance(value, BaseModel):
        data = value.model_dump(mode="json", exclude_none=True)
        for key in ("token", "sessionToken", "session_token", "access_client_token"):
            if key in data:
                data[key] = "***"
        return data
    if isinstance(value, list):
        return [compact(item) for item in value[:5]]
    return value


def run_check(name: str, callback: Callable[[], Any]) -> bool:
    """Run one check and report a useful result without stopping the suite."""
    try:
        result = callback()
    except CyclosError as exc:
        print(f"[FAIL] {name}: {type(exc).__name__}: {exc}")
        return False
    except Exception as exc:  # noqa: BLE001 - smoke runner must continue
        print(f"[FAIL] {name}: {type(exc).__name__}: {exc}")
        return False
    print(f"[PASS] {name}")
    if result is not None:
        print(f"       {compact(result)}")
    return True


def require(*keys: str) -> bool:
    """Return whether all named settings are populated."""
    return all(bool(SETTINGS[key]) for key in keys)


def main() -> int:
    token = SETTINGS["access_client_token"]
    config = CyclosConfig(
        base_url=SETTINGS["base_url"],
        username=SETTINGS["username"] or None,
        password=SecretStr(SETTINGS["password"]) if SETTINGS["password"] else None,
        access_client_token=SecretStr(token) if token else None,
    )

    if not token and not require("username", "password"):
        print("Set CYCLOS_ACCESS_CLIENT_TOKEN or CYCLOS_USERNAME and CYCLOS_PASSWORD.")
        return 2

    passed = 0
    failed = 0
    skipped = 0

    def check(name: str, callback: Callable[[], Any], enabled: bool = True) -> None:
        nonlocal passed, failed, skipped
        if not enabled:
            print(f"[SKIP] {name}")
            skipped += 1
        elif run_check(name, callback):
            passed += 1
        else:
            failed += 1

    with CyclosClient(config) as client:
        if not token:
            check(
                "Session login",
                lambda: client.auth.login(SETTINGS["username"], SETTINGS["password"]),
            )

        check(
            "Activate access client",
            lambda: client.webservices.activate_client(
                code=SETTINGS["activation_code"],
                prefix=SETTINGS["activation_prefix"] or None,
            ),
            enabled=bool(SETTINGS["activation_code"]),
        )
        check("Current authentication", client.auth.current_user)
        check("Current permissions", client.permissions.list)
        check("Search users", lambda: client.users.search(page_size=5))

        member_id = SETTINGS["member_id"]
        account_type = SETTINGS["account_type"]
        check("Get member", lambda: client.members.get(member_id), enabled=bool(member_id))
        check(
            "List member accounts",
            lambda: client.accounts.list(member_id, page_size=5),
            enabled=bool(member_id),
        )
        check(
            "Get account balance",
            lambda: client.accounts.get_balance(member_id, account_type=account_type),
            enabled=bool(member_id and account_type),
        )
        check(
            "Get account history",
            lambda: client.accounts.history(member_id, account_type, page_size=5),
            enabled=bool(member_id and account_type),
        )
        check(
            "Search owner transactions",
            lambda: client.transactions.search(member_id=member_id, page_size=5),
            enabled=bool(member_id),
        )
        check(
            "Search owner transfers",
            lambda: client.transfers.search(member_id=member_id, page_size=5),
            enabled=bool(member_id),
        )

        organization_id = SETTINGS["organization_id"]
        check(
            "Get organization",
            lambda: client.organizations.get(organization_id),
            enabled=bool(organization_id),
        )
        check(
            "Search organization operators",
            lambda: client.operators.search(organization_id, page_size=5),
            enabled=bool(organization_id),
        )
        check(
            "Search operator groups",
            lambda: client.permissions.search(organization_id, page_size=5),
            enabled=bool(organization_id),
        )

        check(
            "Get operator-group permissions",
            lambda: client.permissions.get(SETTINGS["operator_group_id"]),
            enabled=bool(SETTINGS["operator_group_id"]),
        )
        check(
            "Get access client",
            lambda: client.webservices.get_client(SETTINGS["access_client_id"]),
            enabled=bool(SETTINGS["access_client_id"]),
        )
        check(
            "Get transfer",
            lambda: client.transfers.get(SETTINGS["transfer_id"]),
            enabled=bool(SETTINGS["transfer_id"]),
        )
        check(
            "Get transaction",
            lambda: client.transactions.get(SETTINGS["transaction_id"]),
            enabled=bool(SETTINGS["transaction_id"]),
        )

        check(
            "Create test member",
            lambda: client.members.create_individual(
                group=SETTINGS["new_member_group"],
                username=SETTINGS["new_member_username"],
                first_name=SETTINGS["new_member_first_name"],
                last_name=SETTINGS["new_member_last_name"],
            ),
            enabled=ENABLE_WRITES and require("new_member_group", "new_member_username"),
        )

        check(
            "Create test transfer",
            lambda: client.transfers.create(
                transfer_type=SETTINGS["transfer_type"],
                from_account=SETTINGS["transfer_from"],
                to_account=SETTINGS["transfer_to"],
                amount=Decimal(SETTINGS["transfer_amount"]),
                currency=SETTINGS["transfer_currency"],
                description="cyclos-sdk-py live smoke test",
                idempotency_key=os.getenv("CYCLOS_TEST_IDEMPOTENCY_KEY"),
            ),
            enabled=(
                ENABLE_WRITES
                and ENABLE_TRANSFER
                and require("transfer_type", "transfer_from", "transfer_to")
            ),
        )

    print(f"\nSummary: {passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
