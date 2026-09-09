"""Core synchronous and asynchronous HTTP transport for Cyclos."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Mapping
from decimal import Decimal
from types import TracebackType
from typing import Any, Self

import httpx

from angstrom_cyclos.config import CyclosConfig
from angstrom_cyclos.constants import (
    ACCESS_CLIENT_TOKEN_HEADER,
    CORRELATION_ID_HEADER,
    DEFAULT_HEADERS,
    REQUEST_ID_HEADER,
    SESSION_TOKEN_HEADER,
    __version__,
)
from angstrom_cyclos.exceptions import (
    CyclosAuthenticationError,
    CyclosAuthorizationError,
    CyclosConflictError,
    CyclosConnectionError,
    CyclosError,
    CyclosNotFoundError,
    CyclosRateLimitError,
    CyclosServerError,
    CyclosTimeoutError,
    CyclosTransferError,
    CyclosValidationError,
)
from angstrom_cyclos.transport.retry import (
    make_async_retry,
    make_retry,
)

logger = logging.getLogger("cyclos")


def _mask_msisdn(value: str) -> str:
    """Mask an MSISDN by keeping the first 5 and last 2 digits."""
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) >= 8:
        return digits[:5] + "*****" + digits[-2:]
    return "***"


def _redact_url(url: httpx.URL) -> str:
    """Return the URL path without query fragments that could expose secrets."""
    return str(url.path)


def _make_log_safe_headers(headers: httpx.Headers) -> dict[str, str]:
    """Return a copy of headers with authorization tokens removed."""
    safe: dict[str, str] = {}
    for key, value in headers.items():
        lower = key.lower()
        if lower in {
            "authorization",
            SESSION_TOKEN_HEADER.lower(),
            ACCESS_CLIENT_TOKEN_HEADER.lower(),
        } or any(token in lower for token in ("token", "secret", "password", "pin")):
            safe[key] = "***"
        else:
            safe[key] = value
    return safe


def _encode_body(body: Any) -> Any:
    """Recursively encode body content for JSON serialization.

    Decimal values are converted to strings to avoid floating-point encoding.
    """
    if isinstance(body, Mapping):
        return {k: _encode_body(v) for k, v in body.items()}
    if isinstance(body, list):
        return [_encode_body(v) for v in body]
    if isinstance(body, Decimal):
        return str(body)
    return body


def _extract_cyclos_code(body: dict[str, Any] | None) -> str | None:
    if not body:
        return None
    if "code" in body:
        return str(body["code"])
    if "exceptionType" in body:
        return str(body["exceptionType"])
    return None


def _map_http_error(
    exc: httpx.HTTPStatusError,
    *,
    request_id: str | None,
    correlation_id: str | None,
    endpoint: str,
) -> CyclosError:
    status = exc.response.status_code
    try:
        body = exc.response.json()
    except Exception:
        body = None
    code = _extract_cyclos_code(body) if isinstance(body, dict) else None
    kwargs: dict[str, Any] = {
        "status_code": status,
        "cyclos_code": code,
        "request_id": request_id,
        "correlation_id": correlation_id,
        "endpoint": endpoint,
        "response_body": body if isinstance(body, dict) else None,
    }
    message = f"Cyclos API error {status}: {exc.response.reason_phrase}"
    if isinstance(body, dict) and body.get("exceptionMessage"):
        message = f"{message} - {body['exceptionMessage']}"

    if status == 401:
        return CyclosAuthenticationError(message, **kwargs)
    if status == 403:
        return CyclosAuthorizationError(message, **kwargs)
    if status == 404:
        return CyclosNotFoundError(message, **kwargs)
    if status == 409:
        return CyclosConflictError(message, **kwargs)
    if status == 422:
        err = CyclosValidationError(message, **kwargs)
        if isinstance(body, dict):
            err.property_errors = body.get("propertyErrors") or {}
            err.general_errors = body.get("generalErrors") or []
        return err
    if status == 429:
        return CyclosRateLimitError(message, **kwargs)
    if 500 <= status < 600:
        if "/payments" in endpoint or "/transfers" in endpoint:
            return CyclosTransferError(message, **kwargs)
        return CyclosServerError(message, **kwargs)
    return CyclosError(message, **kwargs)


class _BaseTransport:
    """Shared helpers for sync and async transports."""

    def __init__(self, config: CyclosConfig) -> None:
        self.config = config
        self.session_token: str | None = None
        self.access_client_token: str | None = None
        self.correlation_id: str | None = None
        self.base_url = str(config.base_url)
        self._idempotent_keys: set[str] = set()

    def _build_headers(
        self,
        *,
        extra_headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        headers: dict[str, str] = dict(DEFAULT_HEADERS)
        headers["User-Agent"] = f"angstrom-cyclos/{__version__}"
        cid = correlation_id or self.correlation_id or str(uuid.uuid4())
        headers[CORRELATION_ID_HEADER] = cid
        headers[REQUEST_ID_HEADER] = str(uuid.uuid4())
        if self.session_token:
            headers[SESSION_TOKEN_HEADER] = self.session_token
        if self.access_client_token:
            headers[ACCESS_CLIENT_TOKEN_HEADER] = self.access_client_token
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _check_idempotency(self, method: str, idempotency_key: str | None) -> None:
        if method.upper() != "POST" or not idempotency_key:
            return
        if idempotency_key in self._idempotent_keys:
            from angstrom_cyclos.exceptions import CyclosIdempotencyError

            raise CyclosIdempotencyError(
                f"Duplicate idempotency key detected: {idempotency_key}",
                cyclos_code="IDEMPOTENCY_VIOLATION",
            )

    def _record_idempotency(self, method: str, idempotency_key: str | None) -> None:
        if method.upper() == "POST" and idempotency_key:
            self._idempotent_keys.add(idempotency_key)

    def _safe_log_url(self, url: httpx.URL) -> str:
        return _redact_url(url)

    def _log_request_start(self, method: str, url: httpx.URL, headers: Mapping[str, str]) -> None:
        logger.info(
            "cyclos.request",
            extra={
                "method": method,
                "endpoint": self._safe_log_url(url),
                "correlation_id": headers.get(CORRELATION_ID_HEADER, "-"),
                "request_id": headers.get(REQUEST_ID_HEADER, "-"),
            },
        )

    def _log_request_end(
        self,
        method: str,
        url: httpx.URL,
        headers: Mapping[str, str],
        duration: float,
        status: int | None = None,
        exc: BaseException | None = None,
    ) -> None:
        extra = {
            "method": method,
            "endpoint": self._safe_log_url(url),
            "status": status,
            "duration_ms": round(duration * 1000, 2),
            "correlation_id": headers.get(CORRELATION_ID_HEADER, "-"),
            "request_id": headers.get(REQUEST_ID_HEADER, "-"),
        }
        if exc:
            logger.error("cyclos.error", extra=extra, exc_info=exc)
        elif status and status >= 400:
            logger.warning("cyclos.error", extra=extra)
        else:
            logger.info("cyclos.response", extra=extra)


class HTTPTransport(_BaseTransport):
    """Synchronous HTTP transport built on ``httpx.Client``."""

    def __init__(self, config: CyclosConfig) -> None:
        super().__init__(config)
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=config.timeout,
            verify=config.verify_ssl,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _prepare(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
        auth: tuple[str, str] | None = None,
    ) -> tuple[httpx.Request, dict[str, str], tuple[str, str] | None]:
        self._check_idempotency(method, idempotency_key)
        encoded = _encode_body(json) if json is not None else None
        req_headers = self._build_headers(extra_headers=headers, correlation_id=correlation_id)
        if idempotency_key:
            req_headers["Idempotency-Key"] = idempotency_key
        request = self._client.build_request(
            method,
            path,
            params=params,
            json=encoded,
            headers=req_headers,
        )
        return request, req_headers, auth

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
        auth: tuple[str, str] | None = None,
    ) -> httpx.Response:
        request, req_headers, auth = self._prepare(
            method,
            path,
            params=params,
            json=json,
            headers=headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            auth=auth,
        )
        self._log_request_start(method, request.url, req_headers)

        safe_methods = {"GET", "HEAD", "OPTIONS"}
        is_safe = method in safe_methods
        retry_network = is_safe or bool(idempotency_key)
        retry_server = bool(idempotency_key)
        retry = make_retry(
            self.config,
            retry_network_errors=retry_network,
            retry_server_errors=retry_server,
        )
        start = time.perf_counter()

        def do_request() -> httpx.Response:
            try:
                if auth:
                    response = self._client.request(
                        method,
                        path,
                        params=params,
                        json=_encode_body(json) if json is not None else None,
                        headers=req_headers,
                        auth=auth,
                    )
                else:
                    response = self._client.send(request)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                mapped = _map_http_error(
                    exc,
                    request_id=req_headers.get(REQUEST_ID_HEADER),
                    correlation_id=req_headers.get(CORRELATION_ID_HEADER),
                    endpoint=path,
                )
                self._log_request_end(
                    method,
                    exc.request.url,
                    req_headers,
                    time.perf_counter() - start,
                    status=exc.response.status_code,
                    exc=mapped,
                )
                raise mapped from exc
            except httpx.ConnectError as exc:
                err: CyclosError = CyclosConnectionError(
                    f"Connection error: {exc}",
                    endpoint=path,
                    request_id=req_headers.get(REQUEST_ID_HEADER),
                    correlation_id=req_headers.get(CORRELATION_ID_HEADER),
                )
                self._log_request_end(
                    method,
                    exc.request.url,
                    req_headers,
                    time.perf_counter() - start,
                    exc=err,
                )
                raise err from exc
            except httpx.TimeoutException as exc:
                err = CyclosTimeoutError(
                    f"Request timeout: {exc}",
                    endpoint=path,
                    request_id=req_headers.get(REQUEST_ID_HEADER),
                    correlation_id=req_headers.get(CORRELATION_ID_HEADER),
                )
                request_url = getattr(exc, "request", None) and exc.request.url
                self._log_request_end(
                    method,
                    request_url or request.url,
                    req_headers,
                    time.perf_counter() - start,
                    exc=err,
                )
                raise err from exc
            except httpx.HTTPError as exc:
                err = CyclosError(
                    f"HTTP error: {exc}",
                    endpoint=path,
                    request_id=req_headers.get(REQUEST_ID_HEADER),
                    correlation_id=req_headers.get(CORRELATION_ID_HEADER),
                )
                request_url = getattr(exc, "request", None) and exc.request.url
                self._log_request_end(
                    method,
                    request_url or request.url,
                    req_headers,
                    time.perf_counter() - start,
                    exc=err,
                )
                raise err from exc
            else:
                return response

        response: httpx.Response = retry(do_request)
        self._log_request_end(
            method,
            response.request.url,
            req_headers,
            time.perf_counter() - start,
            status=response.status_code,
        )
        self._record_idempotency(method, idempotency_key)
        return response

    def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
    ) -> httpx.Response:
        return self.request(
            "GET", path, params=params, headers=headers, correlation_id=correlation_id
        )

    def post(
        self,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
        auth: tuple[str, str] | None = None,
    ) -> httpx.Response:
        return self.request(
            "POST",
            path,
            params=params,
            json=json,
            headers=headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            auth=auth,
        )

    def put(
        self,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> httpx.Response:
        return self.request(
            "PUT",
            path,
            params=params,
            json=json,
            headers=headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
    ) -> httpx.Response:
        return self.request(
            "DELETE", path, params=params, headers=headers, correlation_id=correlation_id
        )


class AsyncHTTPTransport(_BaseTransport):
    """Asynchronous HTTP transport built on ``httpx.AsyncClient``."""

    def __init__(self, config: CyclosConfig) -> None:
        super().__init__(config)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=config.timeout,
            verify=config.verify_ssl,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    def _prepare(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
        auth: tuple[str, str] | None = None,
    ) -> tuple[httpx.Request, dict[str, str], tuple[str, str] | None]:
        self._check_idempotency(method, idempotency_key)
        encoded = _encode_body(json) if json is not None else None
        req_headers = self._build_headers(extra_headers=headers, correlation_id=correlation_id)
        if idempotency_key:
            req_headers["Idempotency-Key"] = idempotency_key
        request = self._client.build_request(
            method,
            path,
            params=params,
            json=encoded,
            headers=req_headers,
        )
        return request, req_headers, auth

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
        auth: tuple[str, str] | None = None,
    ) -> httpx.Response:
        request, req_headers, auth = self._prepare(
            method,
            path,
            params=params,
            json=json,
            headers=headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            auth=auth,
        )
        self._log_request_start(method, request.url, req_headers)

        safe_methods = {"GET", "HEAD", "OPTIONS"}
        is_safe = method in safe_methods
        retry_network = is_safe or bool(idempotency_key)
        retry_server = bool(idempotency_key)
        retry = make_async_retry(
            self.config,
            retry_network_errors=retry_network,
            retry_server_errors=retry_server,
        )
        start = time.perf_counter()

        async def async_do_request() -> httpx.Response:
            try:
                if auth:
                    response = await self._client.request(
                        method,
                        path,
                        params=params,
                        json=_encode_body(json) if json is not None else None,
                        headers=req_headers,
                        auth=auth,
                    )
                else:
                    response = await self._client.send(request)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                mapped = _map_http_error(
                    exc,
                    request_id=req_headers.get(REQUEST_ID_HEADER),
                    correlation_id=req_headers.get(CORRELATION_ID_HEADER),
                    endpoint=path,
                )
                self._log_request_end(
                    method,
                    exc.request.url,
                    req_headers,
                    time.perf_counter() - start,
                    status=exc.response.status_code,
                    exc=mapped,
                )
                raise mapped from exc
            except httpx.ConnectError as exc:
                err: CyclosError = CyclosConnectionError(
                    f"Connection error: {exc}",
                    endpoint=path,
                    request_id=req_headers.get(REQUEST_ID_HEADER),
                    correlation_id=req_headers.get(CORRELATION_ID_HEADER),
                )
                self._log_request_end(
                    method,
                    exc.request.url,
                    req_headers,
                    time.perf_counter() - start,
                    exc=err,
                )
                raise err from exc
            except httpx.TimeoutException as exc:
                err = CyclosTimeoutError(
                    f"Request timeout: {exc}",
                    endpoint=path,
                    request_id=req_headers.get(REQUEST_ID_HEADER),
                    correlation_id=req_headers.get(CORRELATION_ID_HEADER),
                )
                request_url = getattr(exc, "request", None) and exc.request.url
                self._log_request_end(
                    method,
                    request_url or request.url,
                    req_headers,
                    time.perf_counter() - start,
                    exc=err,
                )
                raise err from exc
            except httpx.HTTPError as exc:
                err = CyclosError(
                    f"HTTP error: {exc}",
                    endpoint=path,
                    request_id=req_headers.get(REQUEST_ID_HEADER),
                    correlation_id=req_headers.get(CORRELATION_ID_HEADER),
                )
                request_url = getattr(exc, "request", None) and exc.request.url
                self._log_request_end(
                    method,
                    request_url or request.url,
                    req_headers,
                    time.perf_counter() - start,
                    exc=err,
                )
                raise err from exc
            else:
                return response

        response: httpx.Response = await retry(async_do_request)
        self._log_request_end(
            method,
            response.request.url,
            req_headers,
            time.perf_counter() - start,
            status=response.status_code,
        )
        self._record_idempotency(method, idempotency_key)
        return response

    async def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
    ) -> httpx.Response:
        return await self.request(
            "GET", path, params=params, headers=headers, correlation_id=correlation_id
        )

    async def post(
        self,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
        auth: tuple[str, str] | None = None,
    ) -> httpx.Response:
        return await self.request(
            "POST",
            path,
            params=params,
            json=json,
            headers=headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            auth=auth,
        )

    async def put(
        self,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> httpx.Response:
        return await self.request(
            "PUT",
            path,
            params=params,
            json=json,
            headers=headers,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        correlation_id: str | None = None,
    ) -> httpx.Response:
        return await self.request(
            "DELETE", path, params=params, headers=headers, correlation_id=correlation_id
        )
