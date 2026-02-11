"""SVM (Solana) wallet adapter for x402 payment.

Supports a single credential source:

- Base58-encoded private key (Solana keypair secret).

All heavy dependencies (``solders``, ``x402.mechanisms.svm``) are imported
lazily so that users who only need EVM do not pay the import cost.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SvmWallet:
    """Wallet adapter for Solana (SVM) chains.

    Parameters
    ----------
    private_key:
        Base58-encoded Solana keypair secret key.

    Examples
    --------
    ::

        wallet = SvmWallet(private_key="base58…")
    """

    def __init__(self, *, private_key: str) -> None:
        if not private_key:
            raise ValueError("SvmWallet requires a non-empty 'private_key'.")
        self._private_key = private_key

    # -- Wallet protocol ---------------------------------------------------

    def register(self, client: Any) -> None:
        """Register the SVM exact payment scheme on *client*."""
        from solders.keypair import Keypair
        from x402.mechanisms.svm import KeypairSigner
        from x402.mechanisms.svm.exact.register import register_exact_svm_client

        keypair = Keypair.from_base58_string(self._private_key)
        signer = KeypairSigner(keypair)
        register_exact_svm_client(client, signer)
        logger.debug("x402 svm wallet: %s", keypair.pubkey())
