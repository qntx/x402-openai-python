"""EVM chat completion with mnemonic phrase.

Usage:
    MNEMONIC="word1 word2 ..." python examples/chat_evm_mnemonic.py
"""

import os

from x402_openai import X402OpenAI
from x402_openai.wallets import EvmWallet

wallet = EvmWallet(
    mnemonic=os.environ["MNEMONIC"],
)

client = X402OpenAI(wallet=wallet)

response = client.chat.completions.create(
    model=os.environ.get("MODEL", "openai/gpt-4o-mini"),
    messages=[{"role": "user", "content": "What is the x402 payment protocol?"}],
)
print(response.choices[0].message.content)
