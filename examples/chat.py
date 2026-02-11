"""Basic chat completion via x402 gateway.

Usage:
    EVM_PRIVATE_KEY="0x..." python examples/chat.py
    MNEMONIC="word1 word2 ..." python examples/chat.py
"""

from __future__ import annotations

import os

from x402_openai import X402OpenAI

model = os.environ.get("MODEL", "gpt-4o-mini")

client = X402OpenAI(
    private_key=os.environ.get("EVM_PRIVATE_KEY"),
    mnemonic=os.environ.get("MNEMONIC"),
    account_index=int(os.environ.get("ACCOUNT_INDEX", "0")),
    base_url=os.environ.get("GATEWAY_URL"),  # defaults to https://llm.qntx.fun/v1
)

print(f"[request] model={model}\n")

completion = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the x402 payment protocol? Answer in one paragraph."},
    ],
)

print("[Assistant]")
print(completion.choices[0].message.content)
print(f"\n[usage] {completion.usage}")
