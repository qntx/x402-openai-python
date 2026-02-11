"""Chain-agnostic wallet resolution and x402 HTTP client construction.

Provides a single entry point — :func:`create_x402_http_client` — that accepts
wallet adapters and returns a ready-to-use x402 HTTP client for the transport
layer.

Supported credential strategies:

1. **Wallet objects** — one or more :class:`~x402_openai.wallets.Wallet`
   instances (chain-agnostic).
2. **Pre-built x402 client** — an already-configured ``x402HTTPClientSync``
   or ``x402HTTPClient`` (returned as-is).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from x402_openai.wallets._base import Wallet

logger = logging.getLogger(__name__)


def create_x402_http_client(
    *,
    wallet: Wallet | None = None,
    wallets: list[Wallet] | None = None,
    x402_client: Any = None,
    sync: bool = True,
) -> Any:
    """Resolve credentials and return an x402 HTTP client.

    Credential sources (provide **exactly one**):

    - *wallet* — a single :class:`Wallet` adapter instance.
    - *wallets* — a list of :class:`Wallet` adapters (multi-chain).
    - *x402_client* — a pre-configured x402 HTTP client (returned as-is).

    Returns
    -------
    ``x402HTTPClientSync`` when *sync* is True, ``x402HTTPClient`` otherwise.
    """
    resolved = _resolve_wallets(
        wallet=wallet,
        wallets=wallets,
        x402_client=x402_client,
    )

    # Pre-built client — return as-is.
    if not isinstance(resolved, list):
        return resolved

    return _build_client(resolved, sync=sync)


def _resolve_wallets(
    *,
    wallet: Wallet | None,
    wallets: list[Wallet] | None,
    x402_client: Any,
) -> list[Wallet] | Any:
    """Return a list of :class:`Wallet` instances or a pre-built x402 client.

    Raises :class:`ValueError` on ambiguous or missing credentials.
    """
    has_wallet = wallet is not None
    has_wallets = wallets is not None and len(wallets) > 0
    has_prebuilt = x402_client is not None

    sources = sum([has_wallet, has_wallets, has_prebuilt])
    if sources == 0:
        raise ValueError(
            "Provide exactly one credential source: 'wallet', 'wallets', or 'x402_client'."
        )
    if sources > 1:
        raise ValueError(
            "Provide only one credential source — 'wallet', 'wallets', or 'x402_client'."
        )

    if has_prebuilt:
        return x402_client

    if has_wallet:
        return [wallet]

    return list(wallets)  # type: ignore[arg-type]


def _build_client(wallet_list: list[Wallet], *, sync: bool) -> Any:
    """Create an x402 HTTP client and register all wallets."""
    if sync:
        from x402 import x402ClientSync
        from x402.http import x402HTTPClientSync

        client = x402ClientSync()
        for w in wallet_list:
            w.register(client)
        return x402HTTPClientSync(client)

    from x402 import x402Client
    from x402.http import x402HTTPClient

    client = x402Client()
    for w in wallet_list:
        w.register(client)
    return x402HTTPClient(client)
