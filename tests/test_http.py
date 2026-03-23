"""Tests for the generic x402 httpx session factories."""

from __future__ import annotations

import httpx
import pytest

from x402_openai._http import create_async_x402_session, create_x402_session


# ---------------------------------------------------------------------------
# Fake x402 clients — no x402 SDK required.
# ---------------------------------------------------------------------------


class _FakeX402Sync:
    def handle_402_response(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[dict[str, str], dict[str, str]]:
        return {"x-payment": "signed"}, {}


class _FakeX402Async:
    async def handle_402_response(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[dict[str, str], dict[str, str]]:
        return {"x-payment": "signed"}, {}


# ---------------------------------------------------------------------------
# Fake inner transport helpers.
# ---------------------------------------------------------------------------


class _Pay402Transport(httpx.BaseTransport):
    """Returns 402 on first call, 200 on second (after payment header added)."""

    def __init__(self) -> None:
        self.calls = 0
        self.last_headers: dict[str, str] = {}

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        if self.calls == 1:
            return httpx.Response(402, headers={"x-402": "required"}, content=b"pay")
        self.last_headers = dict(request.headers)
        return httpx.Response(200, content=b"ok")


class _OkTransport(httpx.BaseTransport):
    def __init__(self) -> None:
        self.calls = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        return httpx.Response(200, content=b"ok")


class _Pay402AsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.calls = 0
        self.last_headers: dict[str, str] = {}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        if self.calls == 1:
            return httpx.Response(402, headers={"x-402": "required"}, content=b"pay")
        self.last_headers = dict(request.headers)
        return httpx.Response(200, content=b"ok")


class _OkAsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.calls = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        return httpx.Response(200, content=b"ok")


# ---------------------------------------------------------------------------
# Sync session tests.
# ---------------------------------------------------------------------------


def test_create_x402_session_requires_credential() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        create_x402_session()


def test_create_x402_session_returns_httpx_client() -> None:
    client = create_x402_session(x402_client=_FakeX402Sync())
    assert isinstance(client, httpx.Client)
    client.close()


def test_create_x402_session_retries_on_402() -> None:
    inner = _Pay402Transport()
    from x402_openai._transport import X402Transport

    client = httpx.Client(transport=X402Transport(_FakeX402Sync(), inner=inner))
    resp = client.get("https://example.com/resource")

    assert resp.status_code == 200
    assert inner.calls == 2
    assert inner.last_headers["x-payment"] == "signed"
    client.close()


def test_create_x402_session_passthrough_non_402() -> None:
    inner = _OkTransport()
    from x402_openai._transport import X402Transport

    client = httpx.Client(transport=X402Transport(_FakeX402Sync(), inner=inner))
    resp = client.get("https://example.com/resource")

    assert resp.status_code == 200
    assert inner.calls == 1
    client.close()


# ---------------------------------------------------------------------------
# Async session tests.
# ---------------------------------------------------------------------------


def test_create_async_x402_session_requires_credential() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        create_async_x402_session()


def test_create_async_x402_session_returns_httpx_async_client() -> None:
    client = create_async_x402_session(x402_client=_FakeX402Async())
    assert isinstance(client, httpx.AsyncClient)


@pytest.mark.asyncio
async def test_create_async_x402_session_retries_on_402() -> None:
    inner = _Pay402AsyncTransport()
    from x402_openai._transport import AsyncX402Transport

    client = httpx.AsyncClient(transport=AsyncX402Transport(_FakeX402Async(), inner=inner))
    resp = await client.get("https://example.com/resource")

    assert resp.status_code == 200
    assert inner.calls == 2
    assert inner.last_headers["x-payment"] == "signed"
    await client.aclose()


@pytest.mark.asyncio
async def test_create_async_x402_session_passthrough_non_402() -> None:
    inner = _OkAsyncTransport()
    from x402_openai._transport import AsyncX402Transport

    client = httpx.AsyncClient(transport=AsyncX402Transport(_FakeX402Async(), inner=inner))
    resp = await client.get("https://example.com/resource")

    assert resp.status_code == 200
    assert inner.calls == 1
    await client.aclose()
