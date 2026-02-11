"""Async streaming chat completion.

Usage: EVM_PRIVATE_KEY="0x..." python examples/streaming.py
"""

import asyncio
import os

from x402_openai import AsyncX402OpenAI
from x402_openai.wallets import EvmWallet


async def main() -> None:
    client = AsyncX402OpenAI(wallet=EvmWallet(private_key=os.environ["EVM_PRIVATE_KEY"]))

    stream = await client.chat.completions.create(
        model=os.environ.get("MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": "Explain the x402 payment protocol."}],
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()


asyncio.run(main())
