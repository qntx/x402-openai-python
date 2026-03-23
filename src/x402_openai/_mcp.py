"""x402-aware MCP JSON-RPC client.

MCP servers signal payment requirements via JSON-RPC error code ``-32042``.
This client intercepts that error, signs the payment using the configured
wallet, and retries the request with credentials placed in ``params._meta``.

HTTP-level ``402`` responses are also handled transparently by the underlying
:class:`~x402_openai._transport.X402Transport`.

Examples
--------
Synchronous::

    from x402_openai import X402MCPClient
    from x402_openai.wallets import EvmWallet

    with X402MCPClient(
        wallet=EvmWallet(private_key="0x…"),
        base_url="https://apibase.pro",
    ) as client:
        result = client.call(
            "/mcp/v1",
            "tools/call",
            params={"name": "weather", "arguments": {"city": "Tokyo"}},
        )

Asynchronous::

    from x402_openai import AsyncX402MCPClient
    from x402_openai.wallets import EvmWallet

    async with AsyncX402MCPClient(
        wallet=EvmWallet(private_key="0x…"),
        base_url="https://apibase.pro",
    ) as client:
        result = await client.call(
            "/mcp/v1",
            "tools/call",
            params={"name": "weather", "arguments": {"city": "Tokyo"}},
        )
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import httpx

from x402_openai._transport import AsyncX402Transport, X402Transport
from x402_openai._wallet import create_x402_http_client

if TYPE_CHECKING:
    from x402_openai.wallets._base import Wallet

logger = logging.getLogger(__name__)

# MCP x402 payment required error code (mirrors HTTP 402).
_MCP_PAYMENT_REQUIRED = -32042


def _build_rpc_payload(
    method: str,
    params: dict[str, Any] | None,
    rpc_id: int | str,
) -> bytes:
    """Encode a JSON-RPC 2.0 request body."""
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "method": method,
    }
    if params is not None:
        payload["params"] = params
    return json.dumps(payload).encode()


def _inject_payment(
    params: dict[str, Any] | None,
    payment_headers: dict[str, str],
) -> dict[str, Any]:
    """Merge *payment_headers* into ``params._meta`` for the retry request.

    Header keys are lower-cased so ``X-Payment`` becomes ``x-payment``
    inside ``_meta``, matching common MCP server expectations.
    """
    base: dict[str, Any] = dict(params) if params else {}
    meta: dict[str, Any] = dict(base.get("_meta") or {})
    meta.update({k.lower(): v for k, v in payment_headers.items()})
    base["_meta"] = meta
    return base


class X402MCPClient:
    """Synchronous MCP JSON-RPC client with transparent x402 payment.

    Parameters
    ----------
    wallet / wallets / x402_client:
        Provide exactly one credential source (same semantics as
        :class:`~x402_openai.X402OpenAI`).
    policies:
        Optional x402 policy list.
    base_url:
        Default URL prefix; prepended to relative *url* arguments in
        :meth:`call`.
    """

    __slots__ = ("_x402", "_http", "_base_url")

    def __init__(
        self,
        *,
        wallet: Wallet | None = None,
        wallets: list[Wallet] | None = None,
        x402_client: Any = None,
        policies: list[Any] | None = None,
        base_url: str | None = None,
        _inner: httpx.BaseTransport | None = None,
    ) -> None:
        self._x402 = create_x402_http_client(
            wallet=wallet,
            wallets=wallets,
            x402_client=x402_client,
            policies=policies,
            sync=True,
        )
        self._http = httpx.Client(transport=X402Transport(self._x402, inner=_inner))
        self._base_url = base_url or ""

    def call(
        self,
        url: str,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        rpc_id: int | str = 1,
    ) -> dict[str, Any]:
        """Send a JSON-RPC request; on ``-32042`` pay and retry transparently.

        Parameters
        ----------
        url:
            Full URL or path appended to *base_url*.
        method:
            JSON-RPC method name (e.g. ``"tools/call"``).
        params:
            JSON-RPC params dict.
        rpc_id:
            JSON-RPC request id.

        Returns
        -------
        The ``result`` field from the JSON-RPC response dict.

        Raises
        ------
        ValueError
            When a non-payment JSON-RPC error is returned, or when payment
            signing fails.
        httpx.HTTPStatusError
            On non-2xx HTTP responses.
        """
        full_url = url if url.startswith(("http://", "https://")) else self._base_url + url
        body = _build_rpc_payload(method, params, rpc_id)

        response = self._http.post(
            full_url,
            content=body,
            headers={"content-type": "application/json"},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()

        error = data.get("error")
        if error and error.get("code") == _MCP_PAYMENT_REQUIRED:
            logger.debug("x402-mcp: received -32042 — signing payment")
            # Reconstruct headers expected by the x402 SDK: merge the
            # JSON-RPC error data as if it were the X-Payment-Required header.
            error_data = error.get("data") or {}
            fake_headers: dict[str, str] = {
                "x-payment-required": json.dumps(error_data),
                **{k.lower(): v for k, v in response.headers.items()},
            }
            try:
                payment_headers, _ = self._x402.handle_402_response(
                    fake_headers,
                    response.content,
                )
            except Exception:
                logger.exception("x402-mcp: payment signing failed")
                raise ValueError(f"x402 payment failed: {error}") from None

            retry_params = _inject_payment(params, payment_headers)
            retry_body = _build_rpc_payload(method, retry_params, rpc_id)
            retry_resp = self._http.post(
                full_url,
                content=retry_body,
                headers={"content-type": "application/json"},
            )
            retry_resp.raise_for_status()
            data = retry_resp.json()

        if "error" in data:
            raise ValueError(f"MCP error: {data['error']}")

        result = data.get("result")
        if result is None:
            raise ValueError(f"MCP response missing 'result' field: {data}")
        return dict(result)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> X402MCPClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class AsyncX402MCPClient:
    """Asynchronous MCP JSON-RPC client with transparent x402 payment.

    Same as :class:`X402MCPClient` but all methods are ``async``.

    Parameters
    ----------
    wallet / wallets / x402_client:
        Provide exactly one credential source.
    policies:
        Optional x402 policy list.
    base_url:
        Default URL prefix.
    """

    __slots__ = ("_x402", "_http", "_base_url")

    def __init__(
        self,
        *,
        wallet: Wallet | None = None,
        wallets: list[Wallet] | None = None,
        x402_client: Any = None,
        policies: list[Any] | None = None,
        base_url: str | None = None,
        _inner: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._x402 = create_x402_http_client(
            wallet=wallet,
            wallets=wallets,
            x402_client=x402_client,
            policies=policies,
            sync=False,
        )
        self._http = httpx.AsyncClient(
            transport=AsyncX402Transport(self._x402, inner=_inner)
        )
        self._base_url = base_url or ""

    async def call(
        self,
        url: str,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        rpc_id: int | str = 1,
    ) -> dict[str, Any]:
        """Send a JSON-RPC request; on ``-32042`` pay and retry transparently.

        Same contract as :meth:`X402MCPClient.call`.
        """
        full_url = url if url.startswith(("http://", "https://")) else self._base_url + url
        body = _build_rpc_payload(method, params, rpc_id)

        response = await self._http.post(
            full_url,
            content=body,
            headers={"content-type": "application/json"},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()

        error = data.get("error")
        if error and error.get("code") == _MCP_PAYMENT_REQUIRED:
            logger.debug("x402-mcp: received -32042 — signing payment")
            error_data = error.get("data") or {}
            fake_headers: dict[str, str] = {
                "x-payment-required": json.dumps(error_data),
                **{k.lower(): v for k, v in response.headers.items()},
            }
            try:
                payment_headers, _ = await self._x402.handle_402_response(
                    fake_headers,
                    response.content,
                )
            except Exception:
                logger.exception("x402-mcp: payment signing failed")
                raise ValueError(f"x402 payment failed: {error}") from None

            retry_params = _inject_payment(params, payment_headers)
            retry_body = _build_rpc_payload(method, retry_params, rpc_id)
            retry_resp = await self._http.post(
                full_url,
                content=retry_body,
                headers={"content-type": "application/json"},
            )
            retry_resp.raise_for_status()
            data = retry_resp.json()

        if "error" in data:
            raise ValueError(f"MCP error: {data['error']}")

        result = data.get("result")
        if result is None:
            raise ValueError(f"MCP response missing 'result' field: {data}")
        return dict(result)

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncX402MCPClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()
