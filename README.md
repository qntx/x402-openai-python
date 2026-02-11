# x402-openai

> Drop-in OpenAI Python client with transparent x402 payment support — **EVM, Solana, and beyond**.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT%20%7C%20Apache--2.0-green)](LICENSE)

## Install

```bash
# EVM only
pip install x402-openai[evm]

# Solana (SVM) only
pip install x402-openai[svm]

# Both chains
pip install x402-openai[all]
```

## Quick Start

### EVM (Ethereum / Base / …)

```python
from x402_openai import X402OpenAI
from x402_openai.wallets import EvmWallet

client = X402OpenAI(wallet=EvmWallet(private_key="0x…"))

# Use exactly like openai.OpenAI — everything just works!
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(completion.choices[0].message.content)
```

### SVM (Solana)

```python
from x402_openai import X402OpenAI
from x402_openai.wallets import SvmWallet

client = X402OpenAI(wallet=SvmWallet(private_key="base58…"))
```

### Multi-chain

Register multiple wallets — the x402 protocol automatically selects the right chain based on the server's payment requirements.

```python
from x402_openai import X402OpenAI
from x402_openai.wallets import EvmWallet, SvmWallet

client = X402OpenAI(wallets=[
    EvmWallet(private_key="0x…"),
    SvmWallet(private_key="base58…"),
])
```

### EVM mnemonic phrase

```python
from x402_openai.wallets import EvmWallet

wallet = EvmWallet(mnemonic="word1 word2 … word12")

# BIP-44 account #2: m/44'/60'/0'/0/2
wallet = EvmWallet(mnemonic="word1 word2 …", account_index=2)

# Ledger Live derivation path
wallet = EvmWallet(mnemonic="word1 word2 …", derivation_path="m/44'/60'/2'/0/0")
```

### Legacy EVM shortcut (backward compatible)

Existing code using `private_key=` / `mnemonic=` directly continues to work:

```python
client = X402OpenAI(private_key="0x…")
client = X402OpenAI(mnemonic="word1 word2 … word12")
```

### Async

```python
from x402_openai import AsyncX402OpenAI
from x402_openai.wallets import SvmWallet

client = AsyncX402OpenAI(wallet=SvmWallet(private_key="base58…"))

completion = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Streaming

```python
stream = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain x402"}],
    stream=True,
)
async for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Advanced: pre-built x402 client

```python
from x402 import x402ClientSync
from x402_openai import X402OpenAI

x402 = x402ClientSync()
# ... register custom payment schemes ...

client = X402OpenAI(x402_client=x402)
```

### Advanced: manual transport injection

```python
import httpx
from openai import AsyncOpenAI
from x402_openai import AsyncX402Transport

transport = AsyncX402Transport(x402_client=x402_http)
client = AsyncOpenAI(
    api_key="x402",
    http_client=httpx.AsyncClient(transport=transport),
)
```

## API

### `X402OpenAI(*, wallet=None, wallets=None, x402_client=None, **kwargs)`

Drop-in replacement for `openai.OpenAI`. Provide **exactly one** credential source:

| Parameter | Description |
| --- | --- |
| `wallet` | A single `Wallet` adapter (e.g. `EvmWallet`, `SvmWallet`) |
| `wallets` | List of `Wallet` adapters for multi-chain support |
| `private_key` | *(legacy)* EVM hex key (`"0x…"`) |
| `mnemonic` | *(legacy)* BIP-39 phrase (12/24 words) |
| `x402_client` | Pre-configured `x402HTTPClientSync` |

Legacy mnemonic companions: `account_index` (default `0`), `derivation_path`, `passphrase`.

Default `base_url` is `https://llm.qntx.fun/v1`. All kwargs (`base_url`, `timeout`, `max_retries`, …) forward to `openai.OpenAI`.

### `AsyncX402OpenAI(*, ...)`

Async version — identical parameters.

### Wallet adapters

| Class | Chain | Install extra |
| --- | --- | --- |
| `EvmWallet(private_key=…)` | EVM (Ethereum, Base, …) | `x402-openai[evm]` |
| `EvmWallet(mnemonic=…)` | EVM (BIP-39) | `x402-openai[evm]` |
| `SvmWallet(private_key=…)` | Solana | `x402-openai[svm]` |

All wallets implement the `Wallet` protocol. See [`wallets/_base.py`](src/x402_openai/wallets/_base.py) to add support for a new chain.

### `X402Transport(x402_client, *, inner=None)` / `AsyncX402Transport(x402_client, *, inner=None)`

Low-level httpx transports for manual wiring.

## Examples

```bash
# EVM chat completion
EVM_PRIVATE_KEY="0x..." python examples/chat.py

# SVM (Solana) chat completion
SOLANA_PRIVATE_KEY="base58..." python examples/chat_svm.py

# Multi-chain (EVM + SVM)
EVM_PRIVATE_KEY="0x..." SOLANA_PRIVATE_KEY="base58..." python examples/chat_multichain.py

# Streaming
EVM_PRIVATE_KEY="0x..." python examples/streaming.py

# List models
MNEMONIC="word1 word2 ..." python examples/models.py
```

## License

This project is licensed under either of the following licenses, at your option:

- Apache License, Version 2.0, ([LICENSE-APACHE](LICENSE-APACHE) or [https://www.apache.org/licenses/LICENSE-2.0](https://www.apache.org/licenses/LICENSE-2.0))
- MIT license ([LICENSE-MIT](LICENSE-MIT) or [https://opensource.org/licenses/MIT](https://opensource.org/licenses/MIT))

Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in this project by you, as defined in the Apache-2.0 license, shall be dually licensed as above, without any additional terms or conditions.
