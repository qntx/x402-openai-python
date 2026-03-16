from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

from x402_openai._transport import (
    AsyncX402Transport,
    X402Transport,
    _clone_request_with_headers,
)


def test_clone_request_merges_headers() -> None:
    original = httpx.Request(
        "POST",
        "https://example.com/v1/chat",
        headers={"authorization": "Bearer old-token", "x-trace": "abc"},
        content=b'{"prompt":"hello"}',
    )

    cloned = _clone_request_with_headers(
        original,
        {
            "authorization": "Bearer new-token",
            "x-payment": "signed",
        },
    )

    assert cloned.headers["authorization"] == "Bearer new-token"
    assert cloned.headers["x-trace"] == "abc"
    assert cloned.headers["x-payment"] == "signed"
    assert cloned.content == original.content


def test_clone_request_preserves_extensions() -> None:
    original = httpx.Request(
        "GET",
        "https://example.com/v1/models",
        extensions={"timeout": {"connect": 1.0, "read": 2.0}},
    )

    cloned = _clone_request_with_headers(original, {"x-payment": "signed"})

    assert cloned.extensions == original.extensions


class _FakeX402ClientSync:
    def handle_402_response(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[dict[str, str], dict[str, str]]:
        assert headers["x-402"] == "required"
        assert body == b"challenge"
        return {"x-payment": "signed"}, {}


class _ShortCircuit402Transport(httpx.BaseTransport):
    def __init__(self) -> None:
        self.calls = 0
        self.retry_body = b""
        self.retry_headers: dict[str, str] = {}

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        if self.calls == 1:
            # Intentionally do not consume request body.
            return httpx.Response(402, headers={"x-402": "required"}, content=b"challenge")

        self.retry_body = request.read()
        self.retry_headers = dict(request.headers)
        return httpx.Response(200, content=b"ok")


def _iter_json() -> Iterator[bytes]:
    yield b'{"prompt":'
    yield b'"hi"}'


def test_sync_transport_retries_even_if_402_response_short_circuits_body() -> None:
    inner = _ShortCircuit402Transport()
    transport = X402Transport(_FakeX402ClientSync(), inner=inner)

    request = httpx.Request("POST", "https://example.com/v1/chat", content=_iter_json())
    response = transport.handle_request(request)

    assert response.status_code == 200
    assert inner.calls == 2
    assert inner.retry_headers["x-payment"] == "signed"
    assert inner.retry_body == b'{"prompt":"hi"}'


class _FakeX402ClientAsync:
    async def handle_402_response(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[dict[str, str], dict[str, str]]:
        assert headers["x-402"] == "required"
        assert body == b"challenge"
        return {"x-payment": "signed"}, {}


class _ShortCircuit402AsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.calls = 0
        self.retry_body = b""
        self.retry_headers: dict[str, str] = {}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        if self.calls == 1:
            # Intentionally do not consume request body.
            return httpx.Response(402, headers={"x-402": "required"}, content=b"challenge")

        self.retry_body = await request.aread()
        self.retry_headers = dict(request.headers)
        return httpx.Response(200, content=b"ok")


async def _aiter_json() -> AsyncIterator[bytes]:
    yield b'{"prompt":'
    yield b'"hi"}'


@pytest.mark.anyio
async def test_async_transport_retries_even_if_402_response_short_circuits_body() -> None:
    inner = _ShortCircuit402AsyncTransport()
    transport = AsyncX402Transport(_FakeX402ClientAsync(), inner=inner)

    request = httpx.Request("POST", "https://example.com/v1/chat", content=_aiter_json())
    response = await transport.handle_async_request(request)

    assert response.status_code == 200
    assert inner.calls == 2
    assert inner.retry_headers["x-payment"] == "signed"
    assert inner.retry_body == b'{"prompt":"hi"}'
