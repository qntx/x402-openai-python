"""EVM chat completion using a BIP-39 mnemonic phrase.

Usage: MNEMONIC="word1 word2 ... word12" python examples/chat_mnemonic.py
"""

import os

from x402_openai import X402OpenAI
from x402_openai.wallets import EvmWallet

client = X402OpenAI(wallet=EvmWallet(mnemonic=os.environ["MNEMONIC"]))

response = client.chat.completions.create(
    model=os.environ.get("MODEL", "gpt-4o-mini"),
    messages=[{"role": "user", "content": "What is the x402 payment protocol?"}],
)
print(response.choices[0].message.content)
