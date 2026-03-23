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


class _FailingX402ClientSync:
    def handle_402_response(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[dict[str, str], dict[str, str]]:
        raise RuntimeError("signing failed")


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


class _PassthroughTransport(httpx.BaseTransport):
    def __init__(self) -> None:
        self.calls = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        return httpx.Response(200, content=b"ok")


class _CloseTracking402Transport(httpx.BaseTransport):
    def __init__(self) -> None:
        self.calls = 0
        self.first_response_closed = False

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        if self.calls == 1:
            response = httpx.Response(402, headers={"x-402": "required"}, content=b"challenge")
            original_close = response.close

            def tracked_close() -> None:
                self.first_response_closed = True
                original_close()

            response.close = tracked_close  # type: ignore[method-assign]
            return response
        return httpx.Response(200, content=b"ok")


class _CloseDelegatingTransport(httpx.BaseTransport):
    def __init__(self) -> None:
        self.closed = False

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"ok")

    def close(self) -> None:
        self.closed = True


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


def test_sync_transport_passes_through_non_402_response() -> None:
    inner = _PassthroughTransport()
    transport = X402Transport(_FakeX402ClientSync(), inner=inner)

    response = transport.handle_request(httpx.Request("GET", "https://example.com/v1/models"))

    assert response.status_code == 200
    assert inner.calls == 1


def test_sync_transport_returns_original_402_when_signing_fails() -> None:
    inner = _ShortCircuit402Transport()
    transport = X402Transport(_FailingX402ClientSync(), inner=inner)

    response = transport.handle_request(
        httpx.Request("POST", "https://example.com/v1/chat", content=_iter_json())
    )

    assert response.status_code == 402
    assert inner.calls == 1


def test_sync_transport_closes_original_402_before_retry() -> None:
    inner = _CloseTracking402Transport()
    transport = X402Transport(_FakeX402ClientSync(), inner=inner)

    response = transport.handle_request(
        httpx.Request("POST", "https://example.com/v1/chat", content=_iter_json())
    )

    assert response.status_code == 200
    assert inner.calls == 2
    assert inner.first_response_closed is True


def test_sync_transport_close_delegates_to_inner_transport() -> None:
    inner = _CloseDelegatingTransport()
    transport = X402Transport(_FakeX402ClientSync(), inner=inner)

    transport.close()

    assert inner.closed is True


class _FakeX402ClientAsync:
    async def handle_402_response(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[dict[str, str], dict[str, str]]:
        assert headers["x-402"] == "required"
        assert body == b"challenge"
        return {"x-payment": "signed"}, {}


class _FailingX402ClientAsync:
    async def handle_402_response(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[dict[str, str], dict[str, str]]:
        raise RuntimeError("signing failed")


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


class _PassthroughAsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.calls = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        return httpx.Response(200, content=b"ok")


class _CloseTracking402AsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.calls = 0
        self.first_response_closed = False

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        if self.calls == 1:
            response = httpx.Response(402, headers={"x-402": "required"}, content=b"challenge")
            original_aclose = response.aclose

            async def tracked_aclose() -> None:
                self.first_response_closed = True
                await original_aclose()

            response.aclose = tracked_aclose  # type: ignore[method-assign]
            return response
        return httpx.Response(200, content=b"ok")


class _CloseDelegatingAsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.closed = False

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"ok")

    async def aclose(self) -> None:
        self.closed = True


async def _aiter_json() -> AsyncIterator[bytes]:
    yield b'{"prompt":'
    yield b'"hi"}'


@pytest.mark.asyncio
async def test_async_transport_retries_even_if_402_response_short_circuits_body() -> None:
    inner = _ShortCircuit402AsyncTransport()
    transport = AsyncX402Transport(_FakeX402ClientAsync(), inner=inner)

    request = httpx.Request("POST", "https://example.com/v1/chat", content=_aiter_json())
    response = await transport.handle_async_request(request)

    assert response.status_code == 200
    assert inner.calls == 2
    assert inner.retry_headers["x-payment"] == "signed"
    assert inner.retry_body == b'{"prompt":"hi"}'


@pytest.mark.asyncio
async def test_async_transport_passes_through_non_402_response() -> None:
    inner = _PassthroughAsyncTransport()
    transport = AsyncX402Transport(_FakeX402ClientAsync(), inner=inner)

    response = await transport.handle_async_request(
        httpx.Request("GET", "https://example.com/v1/models")
    )

    assert response.status_code == 200
    assert inner.calls == 1


@pytest.mark.asyncio
async def test_async_transport_returns_original_402_when_signing_fails() -> None:
    inner = _ShortCircuit402AsyncTransport()
    transport = AsyncX402Transport(_FailingX402ClientAsync(), inner=inner)

    response = await transport.handle_async_request(
        httpx.Request("POST", "https://example.com/v1/chat", content=_aiter_json())
    )

    assert response.status_code == 402
    assert inner.calls == 1


@pytest.mark.asyncio
async def test_async_transport_closes_original_402_before_retry() -> None:
    inner = _CloseTracking402AsyncTransport()
    transport = AsyncX402Transport(_FakeX402ClientAsync(), inner=inner)

    response = await transport.handle_async_request(
        httpx.Request("POST", "https://example.com/v1/chat", content=_aiter_json())
    )

    assert response.status_code == 200
    assert inner.calls == 2
    assert inner.first_response_closed is True


@pytest.mark.asyncio
async def test_async_transport_aclose_delegates_to_inner_transport() -> None:
    inner = _CloseDelegatingAsyncTransport()
    transport = AsyncX402Transport(_FakeX402ClientAsync(), inner=inner)

    await transport.aclose()

    assert inner.closed is True
