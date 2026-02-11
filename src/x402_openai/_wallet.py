"""Wallet credential resolution and x402 HTTP client construction.

Provides a single entry point — :func:`create_x402_http_client` — that accepts
one of three credential sources (private key, mnemonic, or pre-built client)
and returns a ready-to-use x402 HTTP client for the transport layer.

All x402 SDK imports are lazy so that users who inject a pre-built client
do not need ``eth-account`` or ``x402[evm]`` installed.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# BIP-44 standard derivation path template for Ethereum.
_BIP44_ETH_PATH = "m/44'/60'/0'/0/{index}"


def create_x402_http_client(
    *,
    private_key: str | None = None,
    mnemonic: str | None = None,
    account_index: int = 0,
    derivation_path: str | None = None,
    passphrase: str = "",
    x402_client: Any = None,
    sync: bool = True,
) -> Any:
    """Resolve credentials and return an x402 HTTP client.

    Exactly one credential source must be provided:

    - *private_key* — raw EVM hex key (``"0x…"``).
    - *mnemonic* — BIP-39 phrase.  Optionally combined with
      *account_index*, *derivation_path*, or *passphrase*.
    - *x402_client* — a pre-configured ``x402HTTPClientSync`` or
      ``x402HTTPClient`` instance (returned as-is).

    Returns
    -------
    ``x402HTTPClientSync`` when *sync* is True, ``x402HTTPClient`` otherwise.

    Raises
    ------
    ValueError
        If zero or more than one credential source is provided, or if
        mnemonic-only parameters are used without a mnemonic.
    """
    sources = sum([private_key is not None, mnemonic is not None, x402_client is not None])
    if sources == 0:
        raise ValueError(
            "Provide exactly one credential: 'private_key', 'mnemonic', or 'x402_client'."
        )
    if sources > 1:
        raise ValueError(
            "Provide only one credential — 'private_key', 'mnemonic', or 'x402_client'."
        )
    if derivation_path is not None and mnemonic is None:
        raise ValueError("'derivation_path' requires 'mnemonic'.")

    if x402_client is not None:
        return x402_client

    account = (
        _account_from_mnemonic(mnemonic, account_index, derivation_path, passphrase)
        if mnemonic is not None
        else _account_from_key(private_key)  # type: ignore[arg-type]
    )
    return _wrap_account(account, sync=sync)


def _account_from_key(private_key: str) -> Any:
    """Derive an ``eth_account.Account`` from a raw hex private key."""
    from eth_account import Account

    account = Account.from_key(private_key)
    logger.debug("x402 wallet: %s", account.address)
    return account


def _account_from_mnemonic(
    mnemonic: str,
    account_index: int,
    derivation_path: str | None,
    passphrase: str,
) -> Any:
    """Derive an ``eth_account.Account`` from a BIP-39 mnemonic phrase."""
    from eth_account import Account

    Account.enable_unaudited_hdwallet_features()

    path = derivation_path or _BIP44_ETH_PATH.format(index=account_index)
    account = Account.from_mnemonic(mnemonic, account_path=path, passphrase=passphrase)
    logger.debug("x402 wallet derived at %s: %s", path, account.address)
    return account


def _wrap_account(account: Any, *, sync: bool) -> Any:
    """Register *account* with the x402 SDK and return the HTTP wrapper."""
    from x402.mechanisms.evm import EthAccountSigner
    from x402.mechanisms.evm.exact.register import register_exact_evm_client

    signer = EthAccountSigner(account)

    if sync:
        from x402 import x402ClientSync
        from x402.http import x402HTTPClientSync

        sync_client = x402ClientSync()
        register_exact_evm_client(sync_client, signer)
        return x402HTTPClientSync(sync_client)

    from x402 import x402Client
    from x402.http import x402HTTPClient

    async_client = x402Client()
    register_exact_evm_client(async_client, signer)
    return x402HTTPClient(async_client)
