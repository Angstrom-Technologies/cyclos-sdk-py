# Changelog

## 0.2.1 (Unreleased)

### Fixed
- `Member.status` now accepts both `EntityReference` and plain strings such as
  `"active"`, matching the live Cyclos `/users/{user}` response format.

## 0.2.0

### Added
- Automatic HTTP Basic authentication fallback on every request when
  `username`/`password` are configured and no session or access-client token is
  active. This enables admin/service accounts to call Cyclos endpoints such as
  `POST /users` and `POST /system/payments` without an explicit login step.

## 0.1.0

### Added
- Initial production-grade Python SDK for Cyclos 4.16 REST API.
- Synchronous `CyclosClient` and asynchronous `AsyncCyclosClient`.
- Environment-based configuration via `CyclosConfig` / `pydantic-settings`.
- Modular sub-clients: `auth`, `members`, `users`, `organizations`, `operators`, `permissions`, `webservices`, `accounts`, `transfers`, `transactions`.
- Pydantic v2 request/response models for members, operators, accounts, payments, transfers, and transactions.
- Structured, secret-safe logging with MSISDN masking.
- HTTP transport layer with retries, correlation IDs, timeouts, and connection pooling.
- Tenacity-based retry policy for transient errors only.
- Idempotency guard for financial `POST` operations.
- Generic `PaginatedResult[T]` pagination model.
- Comprehensive error hierarchy mapping Cyclos HTTP status codes.
- Unit tests using `pytest`, `pytest-asyncio`, and `respx`.
- Optional integration tests gated by `CYCLOS_INTEGRATION_TESTS`.
- `mypy` and `ruff` configuration in `pyproject.toml`.
