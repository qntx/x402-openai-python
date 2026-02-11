"""EVM async streaming chat completion with mnemonic phrase.

Usage: MNEMONIC="word1 word2 ..." python examples/streaming_evm_mnemonic.py
"""

import asyncio
import os

from x402_openai import AsyncX402OpenAI
from x402_openai.wallets import EvmWallet


async def main() -> None:
    client = AsyncX402OpenAI(
        wallet=EvmWallet(
            mnemonic=os.environ["MNEMONIC"],
            account_index=int(os.environ.get("ACCOUNT_INDEX", "0")),
        ),
    )

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
