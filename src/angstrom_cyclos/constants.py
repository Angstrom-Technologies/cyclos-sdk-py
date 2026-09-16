"""Package constants and defaults."""

__version__ = "0.2.0"

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF = 0.5
DEFAULT_VERIFY_SSL = True

HTTP_READ_TIMEOUT = 60.0

# Header names
SESSION_TOKEN_HEADER = "Session-Token"
ACCESS_CLIENT_TOKEN_HEADER = "Access-Client-Token"
CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# Cyclos API status values observed for transfers/transactions.
# The SDK normalizes these into TransferStatus but preserves the raw value.
TRANSFER_STATUS_PENDING = "pending"
TRANSFER_STATUS_SUCCESS = "processed"
TRANSFER_STATUS_FAILED = "failed"
TRANSFER_STATUS_CANCELLED = "cancelled"
TRANSFER_STATUS_REVERSED = "reversed"

# Cyclos user statuses
USER_STATUS_ACTIVE = "active"
USER_STATUS_BLOCKED = "blocked"
USER_STATUS_DISABLED = "disabled"
USER_STATUS_PENDING = "pending"
USER_STATUS_REMOVED = "removed"
USER_STATUS_PURGED = "purged"
