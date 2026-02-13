"""EVM chat completion with payment policy (prefer Base network).

Demonstrates how to use policies to control which chain is used for payment
when multiple payment options are available.

Usage: EVM_PRIVATE_KEY="0x..." python examples/chat_evm_policy.py
"""

import os

from x402_openai import X402OpenAI, prefer_network
from x402_openai.wallets import EvmWallet

client = X402OpenAI(
    wallet=EvmWallet(private_key=os.environ["EVM_PRIVATE_KEY"]),
    policies=[prefer_network("eip155:143")],  # Prefer Monad mainnet
)

response = client.chat.completions.create(
    model=os.environ.get("MODEL", "openai/gpt-4o-mini"),
    messages=[{"role": "user", "content": "What is the x402 payment protocol?"}],
)
print(response.choices[0].message.content)
