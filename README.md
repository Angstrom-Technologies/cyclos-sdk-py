# cyclos-sdk-py

Production-grade Python SDK for the Cyclos 4.16 REST API.

Published on PyPI as `cyclos-sdk-py`, imported as `angstrom_cyclos`.

## Installation

```bash
pip install cyclos-sdk-py
```

For development:

```bash
git clone https://github.com/Angstrom-Technologies/cyclos-sdk-py.git
cd cyclos-sdk-py
pip install -e ".[dev]"
```

## Configuration

Set environment variables or pass a `CyclosConfig` object:

```python
from angstrom_cyclos import CyclosClient, CyclosConfig

config = CyclosConfig(
    base_url="https://wallet.angstrom-technologies.ug/uwallet/api",
    username="service_client",
    password="...",
)

client = CyclosClient(config)
```

### Environment variables

```env
CYCLOS_BASE_URL=https://wallet.angstrom-technologies.ug/uwallet/api
CYCLOS_USERNAME=service_client
CYCLOS_PASSWORD=...
CYCLOS_TIMEOUT=30
CYCLOS_VERIFY_SSL=true
CYCLOS_MAX_RETRIES=3
CYCLOS_RETRY_BACKOFF=0.5
```

## Authentication

```python
from angstrom_cyclos import CyclosClient, CyclosConfig

config = CyclosConfig.from_env()
client = CyclosClient(config)

client.auth.login("customer", "password")
print(client.auth.is_authenticated())

client.auth.logout()
```

## Creating members

### Individual

```python
customer = client.members.create_individual(
    username="256772123456",
    first_name="John",
    last_name="Doe",
    email="john@example.com",
    mobile="256772123456",
    custom_fields={"kycStatus": "VERIFIED"},
)
```

### Merchant

```python
merchant = client.members.create_merchant(
    username="merchant001",
    name="Merchant One",
    email="merchant@example.com",
    mobile="256772123456",
    group="merchant",
)
```

### Organization

```python
organization = client.organizations.create(
    group="corporate",
    username="abc_limited",
    name="ABC Limited",
    custom_fields={"businessRegistrationNumber": "800200012345"},
)
```

## Operators

```python
operator = client.operators.create(
    organization_id=organization.user.id,
    username="operator001",
    first_name="Jane",
    last_name="Doe",
)

client.operators.assign_permissions(
    organization_id=organization.user.id,
    operator_id=operator.user.id,
    permissions=["VIEW_MEMBER", "PERFORM_TRANSFER"],
)
```

## Web service client

```python
client.webservices.send_activation_code(
    {"mobilePhone": "256772123456"}
)
ws_client = client.webservices.create_client(
    name="Angstrom Wallet API",
    activation_code="123456",
)
```

## Accounts and balances

```python
accounts = client.accounts.list(member_id="alice")
account = client.accounts.get(member_id="alice", account_type="mobileWallet")
balance = client.accounts.get_balance(member_id="alice", account_type="mobileWallet")
print(balance.balance)
```

## Transfers

```python
from decimal import Decimal

transfer = client.transfers.create(
    transfer_type="walletTransfer",
    from_account="alice",
    to_account="bob",
    amount=Decimal("50000"),
    currency="UGX",
    description="P2P transfer",
    idempotency_key="TXN-20260909-000001",
)
```

## Transfer history

```python
history = client.transfers.history(
    member_id="alice",
    account_type="mobileWallet",
    page=0,
    page_size=50,
)
```

## Transaction lookup

```python
transaction = client.transactions.get("transaction-id")
```

## Error handling

```python
from angstrom_cyclos import CyclosAuthenticationError, CyclosValidationError, CyclosNotFoundError

try:
    client.auth.login("user", "wrong")
except CyclosAuthenticationError as exc:
    print(exc.status_code)
except CyclosValidationError as exc:
    print(exc.property_errors)
except CyclosNotFoundError as exc:
    print(exc.endpoint)
```

## Async usage

```python
import asyncio
from angstrom_cyclos import AsyncCyclosClient, CyclosConfig

async def main() -> None:
    config = CyclosConfig.from_env()
    async with AsyncCyclosClient(config) as client:
        await client.auth.login("user", "pass")
        member = await client.members.get("alice")
        print(member)

asyncio.run(main())
```

## CLI

```bash
cyclos --help
cyclos members get <id>
cyclos members search <query>
cyclos accounts balance <member>
cyclos transfers get <id>
cyclos transfers history <member>
```

## Architecture

```
Mobile App
     |
Web App
     |
SMS / USSD
     |
Wallet API
     |
Angstrom Cyclos SDK  <-- this package
     |
Cyclos
     |
PostgreSQL
```

This SDK is only an API client. Mobile money integrations (MTN/Airtel) belong
in the wallet middleware, not in this package.

## Testing

```bash
pytest
mypy src
ruff check src
ruff format src
```

## License

MIT License - see [LICENSE](LICENSE).
