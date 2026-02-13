"""Multi-chain chat completion with payment policies.

Registers both EVM and SVM wallets, then uses policies to prefer Base
mainnet and cap the maximum payment amount.

Usage:
    EVM_PRIVATE_KEY="0x..." SVM_PRIVATE_KEY="base58..." \
        python examples/chat_multichain_policy.py
"""

import os

from x402_openai import X402OpenAI, max_amount, prefer_network, prefer_scheme
from x402_openai.wallets import EvmWallet, SvmWallet

client = X402OpenAI(
    wallets=[
        EvmWallet(private_key=os.environ["EVM_PRIVATE_KEY"]),
        SvmWallet(private_key=os.environ["SVM_PRIVATE_KEY"]),
    ],
    policies=[
        prefer_network("eip155:8453"),  # Prefer Base mainnet
        prefer_scheme("exact"),  # Prefer exact payment scheme
        max_amount(1_000_000),  # Cap at 1 USDC (6 decimals)
    ],
)

response = client.chat.completions.create(
    model=os.environ.get("MODEL", "openai/gpt-4o-mini"),
    messages=[{"role": "user", "content": "What is the x402 payment protocol?"}],
)
print(response.choices[0].message.content)
