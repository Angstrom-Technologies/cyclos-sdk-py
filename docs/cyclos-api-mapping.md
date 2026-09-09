# Cyclos 4.16 API Endpoint Mapping

This document maps the requested `angstrom-cyclos` SDK features to the actual Cyclos 4.16 REST API endpoints exposed by the OpenAPI specification (`openapi.yaml`, version `4.16.19`).

> **Base URL:** The OpenAPI spec reports `https://wallet.angstrom-technologies.ug/api`. The requirements ask for `https://wallet.angstrom-technologies.ug/uwallet/api`. The SDK makes the base URL fully configurable; no URL is hard-coded.

> **Authentication:** The spec supports HTTP Basic authentication (during login) and a `Session-Token` header for subsequent requests. Some endpoints also accept an `Access-Client-Token` header. The SDK uses `Session-Token` obtained from `POST /auth/session`.

## Mapping Table

| Feature | HTTP Method | Endpoint | Request Model | Response Model | Authentication |
|---------|-------------|----------|---------------|----------------|----------------|
| Login | POST | `/auth/session` | Basic auth + `LoginParams` (timeout, device, etc.) | `LoginAuth` (contains `sessionToken`) | Basic |
| Current User | GET | `/auth` | — | `Auth` | Session-Token |
| Logout | DELETE | `/auth/session` | `cookie` (query) | — | Session-Token |
| Replace Session | POST | `/auth/session/replace/{sessionToken}` | `sessionToken` path param | `LoginAuth` | Session-Token |
| Create Member / User | POST | `/users` | `UserNew` (group, name, username, email, customValues, phones, passwords, ...) | `UserRegistrationResult` | Basic or Session-Token |
| Search Members / Users | GET | `/users` | Query: `keywords`, `groups`, `page`, `pageSize`, ... | `UserResult[]` | Session-Token |
| Get Member / User | GET | `/users/{user}` | `user` path param | `UserView` | Session-Token |
| Update Member / User | PUT | `/users/{user}` | `UserEdit` / `UserNew` fields | `UserView` | Session-Token |
| Delete Pending Member | DELETE | `/users/{user}` | `user` path param | — | Session-Token |
| Change User Status | POST | `/{user}/status` | `UserStatusEnum` body | — | Session-Token |
| Create Operator | POST | `/{user}/operators` | `OperatorNew` (inherits name, username, email, customValues, group, phones, passwords) | `UserRegistrationResult` / `User` | Session-Token |
| Search Operators (of owner) | GET | `/{user}/operators` | Query: `keywords`, `page`, `pageSize`, ... | `UserResult[]` | Session-Token |
| Search All Operators | GET | `/operators` | Query: `keywords`, `page`, `pageSize`, ... | `UserResult[]` | Session-Token |
| Create Operator Group (permissions) | POST | `/{user}/operator-groups` | `OperatorGroupNew` / `OperatorGroupManage` | `OperatorGroupView` | Session-Token |
| Update Operator Group | PUT | `/{user}/operator-groups/{id}` | `OperatorGroupNew` / `OperatorGroupManage` | `OperatorGroupView` | Session-Token |
| List Operator Groups | GET | `/{user}/operator-groups` | Query params | `OperatorGroupView[]` | Session-Token |
| Get Operator Group | GET | `/operator-groups/{id}` | `id` path param | `OperatorGroupView` | Session-Token |
| Send Access Client Activation Code | POST | `/clients/send-activaction-code` | `SendOtp` | — | Session-Token |
| Create & Activate Access Client | POST | `/clients/{type}` | `CreateClientParams` (code, name, prefix) | `ActivateClientResult` (contains `token`) | Session-Token |
| Activate Access Client (code) | POST | `/clients/activate` | `code` query param | `ActivateClientResult` | Session-Token |
| Get Access Client | GET | `/clients/{key}` | `key` path param | `ClientView` | Session-Token |
| Unassign Access Client | POST | `/clients/{key}/unassign` | `key` path param | — | Session-Token |
| Disconnect Current Access Client | DELETE | `/auth/access-client` | — | — | Access-Client-Token |
| List Access Client Types for User | GET | `/{user}/client-types` | `user` path param | `ClientType[]` | Session-Token |
| List Accounts by Owner | GET | `/{owner}/accounts` | `owner` path param | `AccountWithStatus[]` | Session-Token |
| Get Account / Balance | GET | `/{owner}/accounts/{accountType}` | `owner`, `accountType` path params; history query filters | `AccountWithHistoryStatus` (includes `status.balance`) | Session-Token |
| Search Account History (transfers) | GET | `/{owner}/accounts/{accountType}/history` | `datePeriod`, `amountRange`, `page`, `pageSize`, `statuses`, `transferTypes`, ... | `AccountHistoryResult[]` | Session-Token |
| Perform Payment (creates transfer) | POST | `/{owner}/payments` | `PerformPayment` (`amount`, `type`, `subject`, `description`, `customValues`, scheduling, ...) | `Transaction` | Session-Token |
| Preview Payment | POST | `/{owner}/payments/preview` | `PerformPayment` | `Transaction` | Session-Token |
| Search Owner Transactions | GET | `/{owner}/transactions` | Query: `page`, `pageSize`, `datePeriod`, `amountRange`, `transferTypes`, ... | `TransactionResult[]` | Session-Token |
| Search All Transactions | GET | `/transactions` | Query: `page`, `pageSize`, `datePeriod`, `amountRange`, `transferTypes`, `transactionNumber`, ... | `TransactionOverviewResult[]` | Session-Token |
| Get Transaction | GET | `/transactions/{key}` | `key` path param | `TransactionView` | Session-Token |
| Search Transfers | GET | `/transfers` | Query: `page`, `pageSize`, `datePeriod`, `amountRange`, `statuses`, ... | `TransferResult[]` | Session-Token |
| Get Transfer | GET | `/transfers/{key}` | `key` path param | `TransferView` | Session-Token |
| Chargeback Transfer | POST | `/transfers/{key}/chargeback` | `key` path param | — | Session-Token |

## Important Cyclos-Specific Notes

1. **Members are Users:** Cyclos does not expose a separate `/members` endpoint. Individual members, merchants, organizations, and businesses are all created with `POST /users` using the appropriate `group` (internal name or id). The SDK provides a `members` module as a convenience wrapper over `/users`.

2. **Transfers are created via Payments:** There is no `POST /transfers` endpoint. The SDK's `transfers.create(...)` internally calls `POST /{owner}/payments` and returns the resulting `Transaction`/`Transfer`. Because payments are financial mutations, the SDK does not blindly retry `POST /{owner}/payments`; retries require an explicit `idempotency_key`.

3. **Operator permissions come from Operator Groups:** Cyclos does not expose a standalone `assign_permissions` endpoint for operators. Permissions are configured when creating/updating an `OperatorGroup` (`POST /{user}/operator-groups`, `PUT /{user}/operator-groups/{id}`), and operators are assigned to a group via `group` in `OperatorNew`. The SDK exposes `client.operators.assign_permissions(...)` as a helper that updates the operator's group permissions, and `client.permissions.list()` wraps `GET /{user}/operator-groups` and `GET /operator-groups/{id}`.

4. **Web Service / Access Clients require activation by code:** Creating an access client is a two-step process: `POST /clients/send-activaction-code` sends a code to the user, then `POST /clients/{type}` creates and activates the client using that code. The returned `token` must be used in the `Access-Client-Token` header. The SDK stores tokens securely and never logs them.

5. **Account history vs. transactions:**
   - `GET /{owner}/accounts/{accountType}/history` returns balance transfers from the account's point of view (debits negative, credits positive). Use this for transfer history.
   - `GET /transactions` and `GET /{owner}/transactions` return transaction-level records (payments, scheduled payments, etc.). Use this for transaction lookup.

6. **Status changes:** Activating/deactivating (or blocking/disabling/ removing/purging) a user is done via `POST /{user}/status` with the appropriate `UserStatusEnum` value (`active`, `blocked`, `disabled`, `pending`, `purged`, `removed`).

7. **Custom fields:** All custom fields are passed as `customValues: { "internalName": "value" }` in user/operator creation and as query params (`customFields`) in account/transaction searches. The SDK does not hard-code custom field IDs.

8. **Idempotency:** The Cyclos 4.16 spec does not expose an idempotency-key HTTP header for payments. The SDK therefore surfaces an `idempotency_key` parameter and an in-memory idempotency guard (configurable) so callers can prevent duplicate financial operations. Idempotency is **not** automatic retry; the SDK refuses to retry a payment unless an idempotency key is supplied.

9. **Decimal amounts:** All monetary fields in the Cyclos API are strings. The SDK serializes/deserializes these as Python `Decimal` objects to avoid floating-point errors.

10. **Pagination:** Cyclos returns arrays with `page` and `pageSize` query params. It does not always return a total count; the `PaginatedResult` model derives `has_next` from whether a full page of results was returned and supports an optional explicit `total_count`.
