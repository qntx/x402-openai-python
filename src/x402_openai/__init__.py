"""x402-openai — Drop-in OpenAI client with transparent x402 payment.

Quick start::

    from x402_openai import X402OpenAI

    client = X402OpenAI(
        private_key="0x…",
    )
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}],
    )

Public API:

- :class:`X402OpenAI` / :class:`AsyncX402OpenAI` — recommended client classes.
- :class:`X402Transport` / :class:`AsyncX402Transport` — low-level transports.
"""

from __future__ import annotations

from x402_openai._client import AsyncX402OpenAI, X402OpenAI
from x402_openai._transport import AsyncX402Transport, X402Transport

__all__ = [
    "AsyncX402OpenAI",
    "AsyncX402Transport",
    "X402OpenAI",
    "X402Transport",
]
