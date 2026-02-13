"""Drop-in OpenAI client subclasses with built-in x402 payment support.

- :class:`X402OpenAI` — synchronous, replaces ``openai.OpenAI``.
- :class:`AsyncX402OpenAI` — asynchronous, replaces ``openai.AsyncOpenAI``.

All standard ``openai`` constructor parameters (``timeout``, ``max_retries``,
``base_url``, …) are forwarded transparently.

Supports multiple blockchain backends via wallet adapters::

    from x402_openai import X402OpenAI
    from x402_openai.wallets import EvmWallet, SvmWallet

    # Single chain
    client = X402OpenAI(wallet=EvmWallet(private_key="0x…"))

    # Multi-chain
    client = X402OpenAI(wallets=[
        EvmWallet(private_key="0x…"),
        SvmWallet(private_key="base58…"),
    ])
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import openai

from x402_openai._transport import AsyncX402Transport, X402Transport
from x402_openai._wallet import create_x402_http_client

if TYPE_CHECKING:
    from x402_openai.wallets._base import Wallet

# Default x402 LLM gateway URL.
_DEFAULT_BASE_URL = "https://llm.qntx.fun/v1"

# Match the OpenAI SDK default timeout (600 s overall, 10 s connect)
# instead of httpx's 5 s default which is too short for TLS handshake.
_DEFAULT_TIMEOUT = httpx.Timeout(600.0, connect=10.0)


class X402OpenAI(openai.OpenAI):
    """Synchronous OpenAI client with transparent x402 payment.

    Provide **exactly one** credential source:

    - ``wallet`` — a :class:`~x402_openai.wallets.Wallet` adapter.
    - ``wallets`` — a list of adapters for multi-chain support.
    - ``x402_client`` — pre-configured ``x402HTTPClientSync``.

    All remaining keyword arguments are forwarded to ``openai.OpenAI()``.

    Examples
    --------
    ::

        from x402_openai import X402OpenAI, prefer_network
        from x402_openai.wallets import EvmWallet, SvmWallet

        # Single chain
        client = X402OpenAI(wallet=EvmWallet(private_key="0x…"))

        # Multi-chain with policy
        client = X402OpenAI(
            wallets=[
                EvmWallet(private_key="0x…"),
                SvmWallet(private_key="base58…"),
            ],
            policies=[prefer_network("eip155:8453")],
        )
    """

    def __init__(
        self,
        *,
        wallet: Wallet | None = None,
        wallets: list[Wallet] | None = None,
        x402_client: Any = None,
        policies: list[Any] | None = None,
        base_url: str | httpx.URL | None = None,
        api_key: str | None = "x402",
        **kwargs: Any,
    ) -> None:
        x402_http = create_x402_http_client(
            wallet=wallet,
            wallets=wallets,
            x402_client=x402_client,
            policies=policies,
            sync=True,
        )
        http_client = httpx.Client(
            transport=X402Transport(x402_http),
            timeout=_DEFAULT_TIMEOUT,
        )
        super().__init__(
            api_key=api_key,
            base_url=base_url or _DEFAULT_BASE_URL,
            http_client=http_client,
            **kwargs,
        )


class AsyncX402OpenAI(openai.AsyncOpenAI):
    """Asynchronous OpenAI client with transparent x402 payment.

    Same parameters as :class:`X402OpenAI` — the only difference is that
    all methods are ``async``.

    Examples
    --------
    ::

        from x402_openai import AsyncX402OpenAI, prefer_network
        from x402_openai.wallets import SvmWallet

        client = AsyncX402OpenAI(
            wallet=SvmWallet(private_key="base58…"),
            policies=[prefer_network("solana:*")],
        )
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello!"}],
        )
    """

    def __init__(
        self,
        *,
        wallet: Wallet | None = None,
        wallets: list[Wallet] | None = None,
        x402_client: Any = None,
        policies: list[Any] | None = None,
        base_url: str | httpx.URL | None = None,
        api_key: str | None = "x402",
        **kwargs: Any,
    ) -> None:
        x402_http = create_x402_http_client(
            wallet=wallet,
            wallets=wallets,
            x402_client=x402_client,
            policies=policies,
            sync=False,
        )
        http_client = httpx.AsyncClient(
            transport=AsyncX402Transport(x402_http),
            timeout=_DEFAULT_TIMEOUT,
        )
        super().__init__(
            api_key=api_key,
            base_url=base_url or _DEFAULT_BASE_URL,
            http_client=http_client,
            **kwargs,
        )
