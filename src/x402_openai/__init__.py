"""x402-openai — Drop-in OpenAI client with transparent x402 payment.

Quick start::

    from x402_openai import X402OpenAI, prefer_network
    from x402_openai.wallets import EvmWallet, SvmWallet

    # EVM
    client = X402OpenAI(wallet=EvmWallet(private_key="0x…"))

    # SVM (Solana)
    client = X402OpenAI(wallet=SvmWallet(private_key="base58…"))

    # Multi-chain with policy
    client = X402OpenAI(
        wallets=[
            EvmWallet(private_key="0x…"),
            SvmWallet(private_key="base58…"),
        ],
        policies=[prefer_network("eip155:8453")],
    )

Public API:

- :class:`X402OpenAI` / :class:`AsyncX402OpenAI` — recommended client classes.
- :class:`X402Transport` / :class:`AsyncX402Transport` — low-level transports.
- :func:`prefer_network` / :func:`prefer_scheme` / :func:`max_amount` — payment policies.
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
    # Lazily re-exported from x402 SDK.
    "max_amount",
    "prefer_network",
    "prefer_scheme",
]


# ---------------------------------------------------------------------------
# Lazy re-exports of x402 policy helpers.
# Avoids a hard import-time dependency on the x402 package so that
# ``import x402_openai`` never fails even if x402 is not installed yet.
# ---------------------------------------------------------------------------

_X402_POLICY_NAMES = {"prefer_network", "prefer_scheme", "max_amount"}


def __getattr__(name: str) -> object:
    if name in _X402_POLICY_NAMES:
        import x402 as _x402

        attr = getattr(_x402, name)
        # Cache on the module so __getattr__ is only called once per name.
        globals()[name] = attr
        return attr
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
