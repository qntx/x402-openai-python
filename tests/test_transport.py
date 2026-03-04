from __future__ import annotations

import httpx

from x402_openai._transport import _clone_request_with_headers


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
