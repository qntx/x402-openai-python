"""Unit tests for the chain-agnostic wallet factory (_wallet.py)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from x402_openai._wallet import _resolve_wallets
from x402_openai.wallets._evm import EvmWallet
from x402_openai.wallets._svm import SvmWallet

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULTS: dict[str, Any] = dict(
    wallet=None,
    wallets=None,
    x402_client=None,
)


def _resolve(**overrides: Any) -> Any:
    """Call _resolve_wallets with defaults merged with *overrides*."""
    return _resolve_wallets(**{**_DEFAULTS, **overrides})


# ---------------------------------------------------------------------------
# Credential resolution
# ---------------------------------------------------------------------------


class TestResolveWallets:
    """Test credential source selection logic."""

    def test_no_credentials_raises(self) -> None:
        with pytest.raises(ValueError, match="exactly one"):
            _resolve()

    def test_multiple_sources_raises(self) -> None:
        w = EvmWallet(private_key="0xdead")
        with pytest.raises(ValueError, match="only one"):
            _resolve(wallet=w, x402_client=object())

    def test_prebuilt_client_returned_as_is(self) -> None:
        sentinel = object()
        result = _resolve(x402_client=sentinel)
        assert result is sentinel

    def test_single_wallet_wrapped_in_list(self) -> None:
        w = EvmWallet(private_key="0xdead")
        result = _resolve(wallet=w)
        assert result == [w]

    def test_wallets_list_preserved(self) -> None:
        w1 = EvmWallet(private_key="0xdead")
        w2 = SvmWallet(private_key="base58key")
        result = _resolve(wallets=[w1, w2])
        assert result == [w1, w2]

    def test_empty_wallets_treated_as_missing(self) -> None:
        with pytest.raises(ValueError, match="exactly one"):
            _resolve(wallets=[])


# ---------------------------------------------------------------------------
# Build client (mocked — no x402 SDK needed)
# ---------------------------------------------------------------------------


class TestBuildClient:
    """Test create_x402_http_client end-to-end with mocked x402 SDK."""

    @patch("x402_openai._wallet._build_client")
    def test_wallet_forwarded_to_build(self, mock_build: MagicMock) -> None:
        from x402_openai._wallet import create_x402_http_client

        mock_build.return_value = "fake_http_client"
        w = EvmWallet(private_key="0xdead")

        result = create_x402_http_client(wallet=w, sync=True)

        mock_build.assert_called_once_with([w], policies=None, sync=True)
        assert result == "fake_http_client"

    @patch("x402_openai._wallet._build_client")
    def test_multi_wallet_forwarded(self, mock_build: MagicMock) -> None:
        from x402_openai._wallet import create_x402_http_client

        mock_build.return_value = "fake_http_client"
        w1 = EvmWallet(private_key="0xdead")
        w2 = SvmWallet(private_key="base58key")

        result = create_x402_http_client(wallets=[w1, w2], sync=False)

        mock_build.assert_called_once_with([w1, w2], policies=None, sync=False)
        assert result == "fake_http_client"

    def test_prebuilt_client_bypasses_build(self) -> None:
        from x402_openai._wallet import create_x402_http_client

        sentinel = object()
        result = create_x402_http_client(x402_client=sentinel, sync=True)
        assert result is sentinel

    @patch("x402_openai._wallet._build_client")
    def test_policies_forwarded_to_build(self, mock_build: MagicMock) -> None:
        from x402_openai._wallet import create_x402_http_client

        mock_build.return_value = "fake_http_client"
        w = EvmWallet(private_key="0xdead")
        fake_policies = ["policy_a", "policy_b"]

        result = create_x402_http_client(wallet=w, policies=fake_policies, sync=True)

        mock_build.assert_called_once_with([w], policies=fake_policies, sync=True)
        assert result == "fake_http_client"

    def test_policies_ignored_with_prebuilt_client(self, caplog: Any) -> None:
        from x402_openai._wallet import create_x402_http_client

        sentinel = object()
        import logging

        with caplog.at_level(logging.WARNING):
            result = create_x402_http_client(
                x402_client=sentinel, policies=["policy_a"], sync=True
            )
        assert result is sentinel
        assert "policies" in caplog.text.lower()
