"""List available models.

Usage: EVM_PRIVATE_KEY="0x..." python examples/models.py
"""

import os

from x402_openai import X402OpenAI
from x402_openai.wallets import EvmWallet

client = X402OpenAI(wallet=EvmWallet(private_key=os.environ["EVM_PRIVATE_KEY"]))

for m in client.models.list():
    print(m.id)
