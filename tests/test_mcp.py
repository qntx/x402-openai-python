"""Tests for X402MCPClient and AsyncX402MCPClient."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from x402_openai._mcp import (
    AsyncX402MCPClient,
    X402MCPClient,
    _build_rpc_payload,
    _inject_payment,
)


# ---------------------------------------------------------------------------
# Helpers — no x402 SDK required.
# ---------------------------------------------------------------------------


class _FakeX402Sync:
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self._headers = headers or {"x-payment": "signed-payload"}
        self.calls = 0
        self.last_headers: dict[str, str] = {}
        self.last_body = b""

    def handle_402_response(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[dict[str, str], dict[str, str]]:
        self.calls += 1
        self.last_headers = headers
        self.last_body = body
        return self._headers, {}


class _FailingX402Sync:
    def handle_402_response(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[dict[str, str], dict[str, str]]:
        raise RuntimeError("signing failed")


class _FakeX402Async:
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self._headers = headers or {"x-payment": "signed-payload"}
        self.calls = 0

    async def handle_402_response(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[dict[str, str], dict[str, str]]:
        self.calls += 1
        return self._headers, {}


class _FailingX402Async:
    async def handle_402_response(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[dict[str, str], dict[str, str]]:
        raise RuntimeError("signing failed")


# ---------------------------------------------------------------------------
# Inner transports that return canned JSON-RPC responses.
# ---------------------------------------------------------------------------


def _rpc_ok(result: Any = {"status": "ok"}) -> bytes:  # noqa: B006
    return json.dumps({"jsonrpc": "2.0", "id": 1, "result": result}).encode()


def _rpc_payment_required(data: dict[str, Any] | None = None) -> bytes:
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32042,
                "message": "Payment Required",
                "data": data or {"x402Version": 1, "accepts": []},
            },
        }
    ).encode()


def _rpc_error(code: int = -32600, message: str = "bad request") -> bytes:
    return json.dumps(
        {"jsonrpc": "2.0", "id": 1, "error": {"code": code, "message": message}}
    ).encode()


class _SequentialTransport(httpx.BaseTransport):
    """Returns responses in the order they were provided."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = list(responses)
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._responses.pop(0)


class _SequentialAsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = list(responses)
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._responses.pop(0)


# ---------------------------------------------------------------------------
# Unit tests for pure helper functions.
# ---------------------------------------------------------------------------


def test_build_rpc_payload_includes_method_and_id() -> None:
    raw = _build_rpc_payload("tools/call", {"name": "weather"}, 42)
    payload = json.loads(raw)
    assert payload["jsonrpc"] == "2.0"
    assert payload["method"] == "tools/call"
    assert payload["id"] == 42
    assert payload["params"] == {"name": "weather"}


def test_build_rpc_payload_omits_params_when_none() -> None:
    raw = _build_rpc_payload("ping", None, 1)
    payload = json.loads(raw)
    assert "params" not in payload


def test_inject_payment_merges_into_meta() -> None:
    result = _inject_payment(
        {"name": "weather"},
        {"X-Payment": "signed", "X-Other": "val"},
    )
    assert result["name"] == "weather"
    assert result["_meta"]["x-payment"] == "signed"
    assert result["_meta"]["x-other"] == "val"


def test_inject_payment_preserves_existing_meta() -> None:
    result = _inject_payment(
        {"_meta": {"existing": "value"}},
        {"X-Payment": "signed"},
    )
    assert result["_meta"]["existing"] == "value"
    assert result["_meta"]["x-payment"] == "signed"


def test_inject_payment_handles_none_params() -> None:
    result = _inject_payment(None, {"X-Payment": "signed"})
    assert result["_meta"]["x-payment"] == "signed"


# ---------------------------------------------------------------------------
# X402MCPClient sync tests.
# ---------------------------------------------------------------------------


def _make_sync_client(
    x402: Any,
    responses: list[httpx.Response],
    base_url: str = "https://api.example.com",
) -> tuple[X402MCPClient, _SequentialTransport]:
    inner = _SequentialTransport(responses)
    client = X402MCPClient(x402_client=x402, base_url=base_url, _inner=inner)
    return client, inner


def test_mcp_sync_passthrough_success() -> None:
    client, inner = _make_sync_client(
        _FakeX402Sync(),
        [httpx.Response(200, content=_rpc_ok({"data": 42}))],
    )
    result = client.call("/mcp", "tools/call", params={"name": "weather"})
    assert result == {"data": 42}
    assert len(inner.requests) == 1
    client.close()


def test_mcp_sync_retries_on_32042() -> None:
    x402 = _FakeX402Sync()
    client, inner = _make_sync_client(
        x402,
        [
            httpx.Response(200, content=_rpc_payment_required()),
            httpx.Response(200, content=_rpc_ok()),
        ],
    )
    result = client.call("/mcp", "tools/call", params={"name": "weather"})
    assert result == {"status": "ok"}
    assert len(inner.requests) == 2
    assert x402.calls == 1
    client.close()


def test_mcp_sync_payment_injected_into_meta() -> None:
    x402 = _FakeX402Sync(headers={"x-payment": "signed-abc"})
    client, inner = _make_sync_client(
        x402,
        [
            httpx.Response(200, content=_rpc_payment_required()),
            httpx.Response(200, content=_rpc_ok()),
        ],
    )
    client.call("/mcp", "tools/call", params={"name": "weather"})

    retry_body = json.loads(inner.requests[1].content)
    assert retry_body["params"]["_meta"]["x-payment"] == "signed-abc"
    client.close()


def test_mcp_sync_raises_on_signing_failure() -> None:
    client, _ = _make_sync_client(
        _FailingX402Sync(),
        [httpx.Response(200, content=_rpc_payment_required())],
    )
    with pytest.raises(ValueError, match="x402 payment failed"):
        client.call("/mcp", "tools/call")
    client.close()


def test_mcp_sync_raises_on_non_payment_rpc_error() -> None:
    client, _ = _make_sync_client(
        _FakeX402Sync(),
        [httpx.Response(200, content=_rpc_error(-32600, "invalid request"))],
    )
    with pytest.raises(ValueError, match="MCP error"):
        client.call("/mcp", "tools/call")
    client.close()


def test_mcp_sync_context_manager() -> None:
    inner = _SequentialTransport([httpx.Response(200, content=_rpc_ok())])
    with X402MCPClient(x402_client=_FakeX402Sync(), _inner=inner) as client:
        result = client.call("https://example.com/mcp", "ping")
    assert result == {"status": "ok"}


def test_mcp_sync_absolute_url_not_prefixed() -> None:
    inner = _SequentialTransport([httpx.Response(200, content=_rpc_ok())])
    client = X402MCPClient(
        x402_client=_FakeX402Sync(),
        base_url="https://should-not-appear.example.com",
        _inner=inner,
    )
    client.call("https://actual.example.com/mcp", "ping")
    assert str(inner.requests[0].url) == "https://actual.example.com/mcp"
    client.close()


# ---------------------------------------------------------------------------
# AsyncX402MCPClient tests.
# ---------------------------------------------------------------------------


def _make_async_client(
    x402: Any,
    responses: list[httpx.Response],
    base_url: str = "https://api.example.com",
) -> tuple[AsyncX402MCPClient, _SequentialAsyncTransport]:
    inner = _SequentialAsyncTransport(responses)
    client = AsyncX402MCPClient(x402_client=x402, base_url=base_url, _inner=inner)
    return client, inner


@pytest.mark.asyncio
async def test_mcp_async_passthrough_success() -> None:
    client, inner = _make_async_client(
        _FakeX402Async(),
        [httpx.Response(200, content=_rpc_ok({"answer": 7}))],
    )
    result = await client.call("/mcp", "tools/call", params={"name": "weather"})
    assert result == {"answer": 7}
    assert len(inner.requests) == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_mcp_async_retries_on_32042() -> None:
    x402 = _FakeX402Async()
    client, inner = _make_async_client(
        x402,
        [
            httpx.Response(200, content=_rpc_payment_required()),
            httpx.Response(200, content=_rpc_ok()),
        ],
    )
    result = await client.call("/mcp", "tools/call", params={"name": "weather"})
    assert result == {"status": "ok"}
    assert len(inner.requests) == 2
    assert x402.calls == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_mcp_async_payment_injected_into_meta() -> None:
    x402 = _FakeX402Async(headers={"x-payment": "async-signed"})
    client, inner = _make_async_client(
        x402,
        [
            httpx.Response(200, content=_rpc_payment_required()),
            httpx.Response(200, content=_rpc_ok()),
        ],
    )
    await client.call("/mcp", "tools/call", params={"name": "weather"})

    retry_body = json.loads(inner.requests[1].content)
    assert retry_body["params"]["_meta"]["x-payment"] == "async-signed"
    await client.aclose()


@pytest.mark.asyncio
async def test_mcp_async_raises_on_signing_failure() -> None:
    client, _ = _make_async_client(
        _FailingX402Async(),
        [httpx.Response(200, content=_rpc_payment_required())],
    )
    with pytest.raises(ValueError, match="x402 payment failed"):
        await client.call("/mcp", "tools/call")
    await client.aclose()


@pytest.mark.asyncio
async def test_mcp_async_raises_on_non_payment_rpc_error() -> None:
    client, _ = _make_async_client(
        _FakeX402Async(),
        [httpx.Response(200, content=_rpc_error())],
    )
    with pytest.raises(ValueError, match="MCP error"):
        await client.call("/mcp", "tools/call")
    await client.aclose()


@pytest.mark.asyncio
async def test_mcp_async_context_manager() -> None:
    inner = _SequentialAsyncTransport([httpx.Response(200, content=_rpc_ok())])
    async with AsyncX402MCPClient(x402_client=_FakeX402Async(), _inner=inner) as client:
        result = await client.call("https://example.com/mcp", "ping")
    assert result == {"status": "ok"}
