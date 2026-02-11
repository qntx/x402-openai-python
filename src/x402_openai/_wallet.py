"""Chain-agnostic wallet resolution and x402 HTTP client construction.

Provides a single entry point — :func:`create_x402_http_client` — that accepts
wallet adapters (or legacy EVM credentials) and returns a ready-to-use x402
HTTP client for the transport layer.

Supported credential strategies:

1. **Wallet objects** — one or more :class:`~x402_openai.wallets.Wallet`
   instances (recommended, chain-agnostic).
2. **Legacy EVM shortcuts** — ``private_key`` / ``mnemonic`` (backward
   compatible, internally creates an :class:`~x402_openai.wallets.EvmWallet`).
3. **Pre-built x402 client** — an already-configured ``x402HTTPClientSync``
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
    # Legacy EVM-only shortcuts (backward compatible).
    private_key: str | None = None,
    mnemonic: str | None = None,
    account_index: int = 0,
    derivation_path: str | None = None,
    passphrase: str = "",
    x402_client: Any = None,
    sync: bool = True,
) -> Any:
    """Resolve credentials and return an x402 HTTP client.

    Credential sources (provide **exactly one**):

    - *wallet* — a single :class:`Wallet` adapter instance.
    - *wallets* — a list of :class:`Wallet` adapters (multi-chain).
    - *private_key* / *mnemonic* — legacy EVM shortcuts.
    - *x402_client* — a pre-configured x402 HTTP client (returned as-is).

    Returns
    -------
    ``x402HTTPClientSync`` when *sync* is True, ``x402HTTPClient`` otherwise.
    """
    resolved = _resolve_wallets(
        wallet=wallet,
        wallets=wallets,
        private_key=private_key,
        mnemonic=mnemonic,
        account_index=account_index,
        derivation_path=derivation_path,
        passphrase=passphrase,
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
    private_key: str | None,
    mnemonic: str | None,
    account_index: int,
    derivation_path: str | None,
    passphrase: str,
    x402_client: Any,
) -> list[Wallet] | Any:
    """Return a list of :class:`Wallet` instances or a pre-built x402 client.

    Raises :class:`ValueError` on ambiguous or missing credentials.
    """
    has_wallet = wallet is not None
    has_wallets = wallets is not None and len(wallets) > 0
    has_legacy = private_key is not None or mnemonic is not None
    has_prebuilt = x402_client is not None

    sources = sum([has_wallet, has_wallets, has_legacy, has_prebuilt])
    if sources == 0:
        raise ValueError(
            "Provide exactly one credential source: "
            "'wallet', 'wallets', 'private_key'/'mnemonic', or 'x402_client'."
        )
    if sources > 1:
        raise ValueError(
            "Provide only one credential source — "
            "'wallet', 'wallets', 'private_key'/'mnemonic', or 'x402_client'."
        )

    if has_prebuilt:
        return x402_client

    if has_wallet:
        return [wallet]

    if has_wallets:
        return list(wallets)  # type: ignore[arg-type]

    # Legacy EVM shortcut — delegate to EvmWallet.
    from x402_openai.wallets._evm import EvmWallet

    return [
        EvmWallet(
            private_key=private_key,
            mnemonic=mnemonic,
            account_index=account_index,
            derivation_path=derivation_path,
            passphrase=passphrase,
        )
    ]


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
