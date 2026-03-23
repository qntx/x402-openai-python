"""CLI: generate an x402 EVM wallet keypair.

Creates a new keypair, saves it to ``~/.x402/wallet.json``, and prints the
funding address.  Permissions are set to ``0o600`` so only the owner can
read the private key.

Usage::

    create-x402-wallet        # via installed entry-point
    python -m x402_openai     # directly from the package
"""

from __future__ import annotations

import json
import pathlib
import sys


def main() -> None:
    """Entry-point for the ``create-x402-wallet`` command."""
    try:
        from eth_account import Account  # type: ignore[import-untyped]
    except ImportError:
        print(
            "eth-account is required. Install with:\n"
            "  pip install x402-openai[evm]",
            file=sys.stderr,
        )
        sys.exit(1)

    wallet_dir = pathlib.Path.home() / ".x402"
    wallet_dir.mkdir(parents=True, exist_ok=True)
    wallet_file = wallet_dir / "wallet.json"

    if wallet_file.exists():
        print(
            f"Wallet already exists at {wallet_file}\n"
            "Delete it manually before generating a new one.",
            file=sys.stderr,
        )
        sys.exit(1)

    account = Account.create()
    data = {
        "address": account.address,
        "private_key": account.key.hex(),
        "chain": "eip155",
    }
    wallet_file.write_text(json.dumps(data, indent=2))
    wallet_file.chmod(0o600)

    print(f"Wallet created : {wallet_file}")
    print(f"Address        : {account.address}")
    print()
    print("Fund this address with USDC on Base (chain ID 8453) to use x402.")
    print("Minimum recommended balance: 1 USDC")


if __name__ == "__main__":
    main()
