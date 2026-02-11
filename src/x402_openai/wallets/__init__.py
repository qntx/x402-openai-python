"""Chain-specific wallet adapters for x402 payment.

Public API:

- :class:`Wallet` — protocol that all adapters implement.
- :class:`EvmWallet` — EVM / Ethereum adapter.
- :class:`SvmWallet` — Solana adapter.
"""

from __future__ import annotations

from x402_openai.wallets._base import Wallet
from x402_openai.wallets._evm import EvmWallet
from x402_openai.wallets._svm import SvmWallet

__all__ = [
    "EvmWallet",
    "SvmWallet",
    "Wallet",
]
