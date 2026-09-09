"""Retry configuration using tenacity.

Financial POSTs are never automatically retried. Retries are only applied to
transport-level failures and safe HTTP methods unless explicitly opted-in.
"""

from __future__ import annotations

from typing import Any

from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from angstrom_cyclos.exceptions import CyclosConnectionError, CyclosServerError, CyclosTimeoutError

RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


def _is_retryable_status_code(exc: CyclosServerError) -> bool:
    return exc.status_code in RETRYABLE_STATUS_CODES if exc.status_code else False


def make_retry(
    config: Any,
    *,
    retry_network_errors: bool = True,
    retry_server_errors: bool = False,
) -> Retrying:
    """Build a tenacity retry object from a ``CyclosConfig`` instance.

    Financial ``POST`` operations are only retried when the caller supplies an
    idempotency key. Safe/read-only requests may be retried on transient
    network failures.

    Args:
        config: A ``CyclosConfig`` instance.
        retry_network_errors: Retry connection and timeout errors.
        retry_server_errors: Retry retryable 5xx responses.
    """
    retry_exceptions: tuple[type[Exception], ...] = ()
    if retry_network_errors:
        retry_exceptions += (CyclosConnectionError, CyclosTimeoutError)
    if retry_server_errors:
        retry_exceptions += (CyclosServerError,)

    if retry_exceptions:
        max_attempts = max(1, config.max_retries + 1)
        retry_cond = retry_if_exception_type(retry_exceptions)
    else:
        max_attempts = 1
        retry_cond = retry_if_exception_type(Exception)

    return Retrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(
            initial=config.retry_backoff,
            exp_base=2.0,
            jitter=0.5,
        ),
        retry=retry_cond,
        reraise=True,
    )


def make_async_retry(
    config: Any,
    *,
    retry_network_errors: bool = True,
    retry_server_errors: bool = False,
) -> AsyncRetrying:
    """Async variant of ``make_retry``."""
    retry_exceptions: tuple[type[Exception], ...] = ()
    if retry_network_errors:
        retry_exceptions += (CyclosConnectionError, CyclosTimeoutError)
    if retry_server_errors:
        retry_exceptions += (CyclosServerError,)

    if retry_exceptions:
        max_attempts = max(1, config.max_retries + 1)
        retry_cond = retry_if_exception_type(retry_exceptions)
    else:
        max_attempts = 1
        retry_cond = retry_if_exception_type(Exception)

    return AsyncRetrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(
            initial=config.retry_backoff,
            exp_base=2.0,
            jitter=0.5,
        ),
        retry=retry_cond,
        reraise=True,
    )
