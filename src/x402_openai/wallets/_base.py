"""Abstract wallet protocol for chain-agnostic x402 payment registration.

Any chain adapter must implement the :class:`Wallet` protocol so that the
client layer can register payment schemes without knowing chain details.

To add support for a new blockchain:

1. Create a new module (e.g. ``_mychain.py``) in this package.
2. Implement the :class:`Wallet` protocol.
3. Re-export from ``wallets/__init__.py``.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Wallet(Protocol):
    """Protocol that all chain-specific wallet adapters must satisfy.

    Each wallet knows how to:
    - Derive or hold a signing key for its chain.
    - Register the appropriate x402 payment scheme on an ``x402ClientSync``
      or ``x402Client`` instance.
    """

    def register(self, client: Any) -> None:
        """Register this wallet's payment scheme(s) with *client*.

        Parameters
        ----------
        client:
            An ``x402ClientSync`` or ``x402Client`` instance.
        """
        ...
