"""Drop-in OpenAI client subclasses with built-in x402 payment support.

- :class:`X402OpenAI` — synchronous, replaces ``openai.OpenAI``.
- :class:`AsyncX402OpenAI` — asynchronous, replaces ``openai.AsyncOpenAI``.

All standard ``openai`` constructor parameters (``timeout``, ``max_retries``,
``base_url``, …) are forwarded transparently.
"""

from __future__ import annotations

from typing import Any

import httpx
import openai

from x402_openai._transport import AsyncX402Transport, X402Transport
from x402_openai._wallet import create_x402_http_client

# Default x402 LLM gateway URL.
_DEFAULT_BASE_URL = "https://llm.qntx.fun/v1"

# Match the OpenAI SDK default timeout (600 s overall, 10 s connect)
# instead of httpx's 5 s default which is too short for TLS handshake.
_DEFAULT_TIMEOUT = httpx.Timeout(600.0, connect=10.0)


class X402OpenAI(openai.OpenAI):
    """Synchronous OpenAI client with transparent x402 payment.

    Provide **exactly one** credential source:

    - ``private_key`` — raw EVM hex key (``"0x…"``).
    - ``mnemonic`` — BIP-39 phrase, optionally with ``account_index``,
      ``derivation_path``, or ``passphrase``.
    - ``x402_client`` — pre-configured ``x402HTTPClientSync``.

    All remaining keyword arguments are forwarded to ``openai.OpenAI()``.

    Examples
    --------
    ::

        client = X402OpenAI(private_key="0x…")
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello!"}],
        )
    """

    def __init__(
        self,
        *,
        private_key: str | None = None,
        mnemonic: str | None = None,
        account_index: int = 0,
        derivation_path: str | None = None,
        passphrase: str = "",
        x402_client: Any = None,
        base_url: str | httpx.URL | None = None,
        api_key: str | None = "x402",
        **kwargs: Any,
    ) -> None:
        x402_http = create_x402_http_client(
            private_key=private_key,
            mnemonic=mnemonic,
            account_index=account_index,
            derivation_path=derivation_path,
            passphrase=passphrase,
            x402_client=x402_client,
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

        client = AsyncX402OpenAI(mnemonic="word1 word2 … word12")
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello!"}],
        )
    """

    def __init__(
        self,
        *,
        private_key: str | None = None,
        mnemonic: str | None = None,
        account_index: int = 0,
        derivation_path: str | None = None,
        passphrase: str = "",
        x402_client: Any = None,
        base_url: str | httpx.URL | None = None,
        api_key: str | None = "x402",
        **kwargs: Any,
    ) -> None:
        x402_http = create_x402_http_client(
            private_key=private_key,
            mnemonic=mnemonic,
            account_index=account_index,
            derivation_path=derivation_path,
            passphrase=passphrase,
            x402_client=x402_client,
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
