"""EVM async streaming chat completion with private key and payment policy.

Usage: EVM_PRIVATE_KEY="0x..." python examples/streaming_evm_policy.py
"""

import asyncio
import os

from x402_openai import AsyncX402OpenAI, prefer_network
from x402_openai.wallets import EvmWallet


async def main() -> None:
    client = AsyncX402OpenAI(
        wallet=EvmWallet(private_key=os.environ["EVM_PRIVATE_KEY"]),
        policies=[prefer_network("eip155:143")],
    )

    stream = await client.chat.completions.create(
        model=os.environ.get("MODEL", "openai/gpt-4o-mini"),
        messages=[{"role": "user", "content": "Explain the x402 payment protocol."}],
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()


asyncio.run(main())
