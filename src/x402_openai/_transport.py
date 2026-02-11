"""Custom httpx transports that intercept HTTP 402 and handle x402 payment.

When the upstream server returns ``402 Payment Required``, the transport
delegates to the x402 SDK to parse payment headers, sign a payment payload,
and transparently retry the original request.

Two flavours:

- :class:`X402Transport` — synchronous (``httpx.Client``).
- :class:`AsyncX402Transport` — asynchronous (``httpx.AsyncClient``).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------


def _clone_request_with_headers(
    original: httpx.Request,
    extra_headers: dict[str, str],
) -> httpx.Request:
    """Clone *original* and merge *extra_headers* into the copy."""
    headers = dict(original.headers)
    headers.update(extra_headers)
    return httpx.Request(
        method=original.method,
        url=original.url,
        headers=headers,
        content=original.content,
    )


# ---------------------------------------------------------------------------
# Synchronous transport
# ---------------------------------------------------------------------------


class X402Transport(httpx.BaseTransport):
    """Synchronous httpx transport with automatic x402 payment handling.

    Parameters
    ----------
    x402_client:
        A configured ``x402HTTPClientSync`` with registered payment schemes.
    inner:
        Underlying transport to delegate to.  Defaults to ``httpx.HTTPTransport()``.
    """

    __slots__ = ("_inner", "_x402")

    def __init__(
        self,
        x402_client: Any,
        *,
        inner: httpx.BaseTransport | None = None,
    ) -> None:
        self._x402 = x402_client
        self._inner = inner or httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Send *request*; on 402 sign payment and retry transparently."""
        logger.debug("x402: %s %s", request.method, request.url)
        response = self._inner.handle_request(request)

        if response.status_code != 402:
            return response

        logger.debug("x402: received 402 — signing payment")
        response.read()

        try:
            payment_headers, _ = self._x402.handle_402_response(
                dict(response.headers),
                response.content,
            )
        except Exception:
            logger.exception("x402: payment signing failed")
            return response

        retry = _clone_request_with_headers(request, payment_headers)
        return self._inner.handle_request(retry)

    def close(self) -> None:
        """Shut down the underlying transport."""
        self._inner.close()


# ---------------------------------------------------------------------------
# Asynchronous transport
# ---------------------------------------------------------------------------


class AsyncX402Transport(httpx.AsyncBaseTransport):
    """Asynchronous httpx transport with automatic x402 payment handling.

    Parameters
    ----------
    x402_client:
        A configured ``x402HTTPClient`` with registered payment schemes.
    inner:
        Underlying transport to delegate to.  Defaults to ``httpx.AsyncHTTPTransport()``.
    """

    __slots__ = ("_inner", "_x402")

    def __init__(
        self,
        x402_client: Any,
        *,
        inner: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._x402 = x402_client
        self._inner = inner or httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Send *request*; on 402 sign payment and retry transparently."""
        logger.debug("x402: %s %s", request.method, request.url)
        response = await self._inner.handle_async_request(request)

        if response.status_code != 402:
            return response

        logger.debug("x402: received 402 — signing payment")
        await response.aread()

        try:
            payment_headers, _ = await self._x402.handle_402_response(
                dict(response.headers),
                response.content,
            )
        except Exception:
            logger.exception("x402: payment signing failed")
            return response

        retry = _clone_request_with_headers(request, payment_headers)
        return await self._inner.handle_async_request(retry)

    async def aclose(self) -> None:
        """Shut down the underlying transport."""
        await self._inner.aclose()
