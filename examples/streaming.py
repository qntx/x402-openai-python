"""Streaming chat completion via x402 gateway.

Usage:
    EVM_PRIVATE_KEY="0x..." python examples/streaming.py
    MNEMONIC="word1 word2 ..." python examples/streaming.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from x402_openai import AsyncX402OpenAI

model = os.environ.get("MODEL", "gpt-4o-mini")


async def main() -> None:
    client = AsyncX402OpenAI(
        private_key=os.environ.get("EVM_PRIVATE_KEY"),
        mnemonic=os.environ.get("MNEMONIC"),
        account_index=int(os.environ.get("ACCOUNT_INDEX", "0")),
        base_url=os.environ.get("GATEWAY_URL"),  # defaults to https://llm.qntx.fun/v1
    )

    print(f"[request] model={model} stream=true\n")
    print("[Assistant]")

    stream = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "Explain the x402 payment protocol in detail."},
        ],
        stream=True,
    )

    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            sys.stdout.write(delta)
            sys.stdout.flush()

    print("\n\n[done]")


asyncio.run(main())
