"""List available models using EVM mnemonic phrase.

Usage: MNEMONIC="word1 word2 ..." python examples/models_mnemonic.py
"""

import os

from x402_openai import X402OpenAI
from x402_openai.wallets import EvmWallet

client = X402OpenAI(
    wallet=EvmWallet(
        mnemonic=os.environ["MNEMONIC"],
        account_index=int(os.environ.get("ACCOUNT_INDEX", "0")),
    ),
)

for m in client.models.list():
    print(m.id)
