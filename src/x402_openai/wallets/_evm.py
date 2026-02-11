"""EVM (Ethereum) wallet adapter for x402 payment.

Supports two credential sources:

- Raw hex private key (``"0x…"``).
- BIP-39 mnemonic phrase with optional derivation parameters.

All heavy dependencies (``eth_account``, ``x402.mechanisms.evm``) are imported
lazily so that users who only need SVM do not pay the import cost.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# BIP-44 standard derivation path template for Ethereum.
_BIP44_ETH_PATH = "m/44'/60'/0'/0/{index}"


class EvmWallet:
    """Wallet adapter for EVM-compatible chains.

    Provide **exactly one** of *private_key* or *mnemonic*.

    Parameters
    ----------
    private_key:
        Raw EVM hex key (``"0x…"``).
    mnemonic:
        BIP-39 phrase (12 or 24 words).
    account_index:
        BIP-44 account index (default ``0``).
    derivation_path:
        Custom BIP-44 derivation path.  Overrides *account_index*.
    passphrase:
        Optional BIP-39 passphrase.

    Examples
    --------
    ::

        wallet = EvmWallet(private_key="0x…")
        wallet = EvmWallet(mnemonic="word1 word2 … word12")
        wallet = EvmWallet(mnemonic="word1 …", account_index=2)
    """

    def __init__(
        self,
        *,
        private_key: str | None = None,
        mnemonic: str | None = None,
        account_index: int = 0,
        derivation_path: str | None = None,
        passphrase: str = "",
    ) -> None:
        sources = sum([private_key is not None, mnemonic is not None])
        if sources == 0:
            raise ValueError("EvmWallet requires 'private_key' or 'mnemonic'.")
        if sources > 1:
            raise ValueError("EvmWallet accepts only one of 'private_key' or 'mnemonic'.")
        if derivation_path is not None and mnemonic is None:
            raise ValueError("'derivation_path' requires 'mnemonic'.")

        self._private_key = private_key
        self._mnemonic = mnemonic
        self._account_index = account_index
        self._derivation_path = derivation_path
        self._passphrase = passphrase

    # -- Wallet protocol ---------------------------------------------------

    def register(self, client: Any) -> None:
        """Register the EVM exact payment scheme on *client*."""
        from x402.mechanisms.evm import EthAccountSigner
        from x402.mechanisms.evm.exact.register import register_exact_evm_client

        account = self._resolve_account()
        signer = EthAccountSigner(account)
        register_exact_evm_client(client, signer)

    # -- Internal helpers ---------------------------------------------------

    def _resolve_account(self) -> Any:
        """Lazily derive the ``eth_account.Account`` from stored credentials."""
        if self._mnemonic is not None:
            return self._account_from_mnemonic()
        return self._account_from_key()

    def _account_from_key(self) -> Any:
        """Derive an ``eth_account.Account`` from a raw hex private key."""
        from eth_account import Account

        account = Account.from_key(self._private_key)
        logger.debug("x402 evm wallet: %s", account.address)
        return account

    def _account_from_mnemonic(self) -> Any:
        """Derive an ``eth_account.Account`` from a BIP-39 mnemonic phrase."""
        from eth_account import Account

        Account.enable_unaudited_hdwallet_features()

        path = self._derivation_path or _BIP44_ETH_PATH.format(index=self._account_index)
        account = Account.from_mnemonic(
            self._mnemonic,
            account_path=path,
            passphrase=self._passphrase,
        )
        logger.debug("x402 evm wallet derived at %s: %s", path, account.address)
        return account
