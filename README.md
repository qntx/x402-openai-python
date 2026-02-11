# x402-openai

> Drop-in OpenAI Python client with transparent x402 payment support.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT%20%7C%20Apache--2.0-green)](LICENSE)

## Install

```bash
pip install x402-openai "x402[evm]" eth-account
```

## Quick Start

### Private key

```python
from x402_openai import X402OpenAI

client = X402OpenAI(private_key="0x…")

# Use exactly like openai.OpenAI — everything just works!
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(completion.choices[0].message.content)
```

### Mnemonic phrase

```python
client = X402OpenAI(mnemonic="word1 word2 … word12")
```

### Custom account index / derivation path

```python
# BIP-44 account #2: m/44'/60'/0'/0/2
client = X402OpenAI(mnemonic="word1 word2 …", account_index=2)

# Ledger Live derivation path
client = X402OpenAI(mnemonic="word1 word2 …", derivation_path="m/44'/60'/2'/0/0")
```

### Async

```python
from x402_openai import AsyncX402OpenAI

client = AsyncX402OpenAI(private_key="0x…")

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

### `X402OpenAI(*, private_key=None, mnemonic=None, x402_client=None, **kwargs)`

Drop-in replacement for `openai.OpenAI`. Provide **exactly one** credential:

| Parameter | Description |
| --- | --- |
| `private_key` | EVM hex key (`"0x…"`) |
| `mnemonic` | BIP-39 phrase (12/24 words) |
| `x402_client` | Pre-configured `x402HTTPClientSync` |

Mnemonic companions: `account_index` (default `0`), `derivation_path`, `passphrase`.

Default `base_url` is `https://llm.qntx.fun/v1`. All kwargs (`base_url`, `timeout`, `max_retries`, …) forward to `openai.OpenAI`.

### `AsyncX402OpenAI(*, ...)`

Async version — identical parameters.

### `X402Transport(x402_client, *, inner=None)` / `AsyncX402Transport(x402_client, *, inner=None)`

Low-level httpx transports for manual wiring.

## Examples

```bash
# Chat completion
EVM_PRIVATE_KEY="0x..." python examples/chat.py

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
