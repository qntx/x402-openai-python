"""List available models from x402 gateway.

Usage:
    EVM_PRIVATE_KEY="0x..." python examples/models.py
    MNEMONIC="word1 word2 ..." python examples/models.py
"""

from __future__ import annotations

import os

from x402_openai import X402OpenAI

client = X402OpenAI(
    private_key=os.environ.get("EVM_PRIVATE_KEY"),
    mnemonic=os.environ.get("MNEMONIC"),
    account_index=int(os.environ.get("ACCOUNT_INDEX", "0")),
    base_url=os.environ.get("GATEWAY_URL"),  # defaults to https://llm.qntx.fun/v1
)

print("[gateway] %s\n" % client.base_url)
print("Available models:")

for m in client.models.list():
    print(f"  - {m.id}")
