"""Generic x402-aware httpx client factories.

Drop-in replacements for ``httpx.Client`` / ``httpx.AsyncClient`` that
intercept HTTP 402 responses and automatically handle payment — framework
agnostic, works with any HTTP endpoint.

Examples
--------
Synchronous::

    from x402_openai import create_x402_session
    from x402_openai.wallets import EvmWallet

    client = create_x402_session(wallet=EvmWallet(private_key="0x…"))
    resp = client.post("https://apibase.pro/api/v1/tools/weather/call",
                       json={"city": "Tokyo"})

Asynchronous::

    from x402_openai import create_async_x402_session
    from x402_openai.wallets import EvmWallet

    async with create_async_x402_session(wallet=EvmWallet(private_key="0x…")) as client:
        resp = await client.post("https://apibase.pro/api/v1/tools/weather/call",
                                 json={"city": "Tokyo"})
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from x402_openai._transport import AsyncX402Transport, X402Transport
from x402_openai._wallet import create_x402_http_client

if TYPE_CHECKING:
    from x402_openai.wallets._base import Wallet


def create_x402_session(
    *,
    wallet: Wallet | None = None,
    wallets: list[Wallet] | None = None,
    x402_client: Any = None,
    policies: list[Any] | None = None,
    **httpx_kwargs: Any,
) -> httpx.Client:
    """Return a synchronous ``httpx.Client`` with automatic x402 payment handling.

    Any request that receives a ``402 Payment Required`` response is
    automatically paid and retried — the caller sees only the final 200.

    Parameters
    ----------
    wallet:
        Single chain wallet adapter.
    wallets:
        List of adapters for multi-chain support.
    x402_client:
        Pre-configured ``x402HTTPClientSync`` (takes precedence).
    policies:
        Optional x402 policy list (e.g. ``prefer_network``, ``max_amount``).
    **httpx_kwargs:
        Forwarded verbatim to ``httpx.Client()``.
    """
    x402 = create_x402_http_client(
        wallet=wallet,
        wallets=wallets,
        x402_client=x402_client,
        policies=policies,
        sync=True,
    )
    return httpx.Client(transport=X402Transport(x402), **httpx_kwargs)


def create_async_x402_session(
    *,
    wallet: Wallet | None = None,
    wallets: list[Wallet] | None = None,
    x402_client: Any = None,
    policies: list[Any] | None = None,
    **httpx_kwargs: Any,
) -> httpx.AsyncClient:
    """Return an asynchronous ``httpx.AsyncClient`` with automatic x402 payment handling.

    Same as :func:`create_x402_session` but async.

    Parameters
    ----------
    wallet:
        Single chain wallet adapter.
    wallets:
        List of adapters for multi-chain support.
    x402_client:
        Pre-configured ``x402HTTPClient`` (takes precedence).
    policies:
        Optional x402 policy list.
    **httpx_kwargs:
        Forwarded verbatim to ``httpx.AsyncClient()``.
    """
    x402 = create_x402_http_client(
        wallet=wallet,
        wallets=wallets,
        x402_client=x402_client,
        policies=policies,
        sync=False,
    )
    return httpx.AsyncClient(transport=AsyncX402Transport(x402), **httpx_kwargs)
