"""x402-openai — Drop-in OpenAI client with transparent x402 payment.

Quick start::

    from x402_openai import X402OpenAI
    from x402_openai.wallets import EvmWallet, SvmWallet

    # EVM
    client = X402OpenAI(wallet=EvmWallet(private_key="0x…"))

    # SVM (Solana)
    client = X402OpenAI(wallet=SvmWallet(private_key="base58…"))

    # Multi-chain
    client = X402OpenAI(wallets=[
        EvmWallet(private_key="0x…"),
        SvmWallet(private_key="base58…"),
    ])

Public API:

- :class:`X402OpenAI` / :class:`AsyncX402OpenAI` — recommended client classes.
- :class:`X402Transport` / :class:`AsyncX402Transport` — low-level transports.
- :mod:`x402_openai.wallets` — chain-specific wallet adapters.
"""

from __future__ import annotations

from x402_openai._client import AsyncX402OpenAI, X402OpenAI
from x402_openai._transport import AsyncX402Transport, X402Transport
from x402_openai.wallets import EvmWallet, SvmWallet, Wallet

__all__ = [
    "AsyncX402OpenAI",
    "AsyncX402Transport",
    "EvmWallet",
    "SvmWallet",
    "Wallet",
    "X402OpenAI",
    "X402Transport",
]
