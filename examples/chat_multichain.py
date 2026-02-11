"""Multi-chain (EVM + SVM) chat completion.

Usage: EVM_PRIVATE_KEY="0x..." SOLANA_PRIVATE_KEY="base58..." python examples/chat_multichain.py
"""

import os

from x402_openai import X402OpenAI
from x402_openai.wallets import EvmWallet, SvmWallet

client = X402OpenAI(
    wallets=[
        EvmWallet(private_key=os.environ["EVM_PRIVATE_KEY"]),
        SvmWallet(private_key=os.environ["SOLANA_PRIVATE_KEY"]),
    ],
)

response = client.chat.completions.create(
    model=os.environ.get("MODEL", "gpt-4o-mini"),
    messages=[{"role": "user", "content": "What is the x402 payment protocol?"}],
)
print(response.choices[0].message.content)
