"""Unit tests for wallet adapters and the Wallet protocol."""

from __future__ import annotations

import pytest

from x402_openai.wallets._base import Wallet
from x402_openai.wallets._evm import EvmWallet
from x402_openai.wallets._svm import SvmWallet

# ---------------------------------------------------------------------------
# Wallet protocol conformance
# ---------------------------------------------------------------------------


class TestWalletProtocol:
    """Verify that wallet classes satisfy the Wallet protocol."""

    def test_evm_wallet_is_wallet(self) -> None:
        w = EvmWallet(private_key="0xdead")
        assert isinstance(w, Wallet)

    def test_svm_wallet_is_wallet(self) -> None:
        w = SvmWallet(private_key="abc123")
        assert isinstance(w, Wallet)


# ---------------------------------------------------------------------------
# EvmWallet validation
# ---------------------------------------------------------------------------


class TestEvmWallet:
    """Test EvmWallet __init__ validation logic."""

    def test_requires_credential(self) -> None:
        with pytest.raises(ValueError, match="requires"):
            EvmWallet()

    def test_rejects_both_credentials(self) -> None:
        with pytest.raises(ValueError, match="only one"):
            EvmWallet(private_key="0xdead", mnemonic="word1 word2")

    def test_derivation_path_requires_mnemonic(self) -> None:
        with pytest.raises(ValueError, match="derivation_path"):
            EvmWallet(private_key="0xdead", derivation_path="m/44'/60'/0'/0/0")

    def test_accepts_private_key(self) -> None:
        w = EvmWallet(private_key="0xdead")
        assert w._private_key == "0xdead"
        assert w._mnemonic is None

    def test_accepts_mnemonic(self) -> None:
        w = EvmWallet(mnemonic="word1 word2 word3")
        assert w._mnemonic == "word1 word2 word3"
        assert w._private_key is None

    def test_default_account_index(self) -> None:
        w = EvmWallet(mnemonic="word1 word2 word3")
        assert w._account_index == 0

    def test_custom_account_index(self) -> None:
        w = EvmWallet(mnemonic="word1 word2 word3", account_index=5)
        assert w._account_index == 5

    def test_custom_derivation_path(self) -> None:
        w = EvmWallet(mnemonic="word1 word2 word3", derivation_path="m/44'/60'/2'/0/0")
        assert w._derivation_path == "m/44'/60'/2'/0/0"


# ---------------------------------------------------------------------------
# SvmWallet validation
# ---------------------------------------------------------------------------


class TestSvmWallet:
    """Test SvmWallet __init__ validation logic."""

    def test_requires_non_empty_key(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            SvmWallet(private_key="")

    def test_accepts_private_key(self) -> None:
        w = SvmWallet(private_key="base58key")
        assert w._private_key == "base58key"
