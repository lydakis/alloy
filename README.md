# Alloy (Python)

Python for logic. English for intelligence.

[![CI](https://github.com/lydakis/alloy/actions/workflows/ci.yml/badge.svg)](https://github.com/lydakis/alloy/actions/workflows/ci.yml)
[![Docs](https://github.com/lydakis/alloy/actions/workflows/docs.yml/badge.svg)](https://docs.alloy.fyi/)
[![Docs Site](https://img.shields.io/badge/docs-website-blue)](https://docs.alloy.fyi/)
[![PyPI](https://img.shields.io/pypi/v/alloy-ai.svg)](https://pypi.org/project/alloy-ai/)
[![Downloads](https://pepy.tech/badge/alloy-ai)](https://pepy.tech/project/alloy-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

```python
from alloy import command

@command(output=float)
def extract_price(text: str) -> str:
    return f"Extract the price from: {text}"

print(extract_price("This costs $49.99"))  # 49.99
```

Write typed AI functions that feel like normal Python. No framework, no abstractions —
just functions that happen to use AI.

[Install](#install) • [Tutorial](https://docs.alloy.fyi/tutorial/) • [Examples](examples/) • [Docs](https://docs.alloy.fyi)

## Install

```bash
pip install alloy-ai                    # OpenAI only
pip install 'alloy-ai[anthropic]'       # With Anthropic
pip install 'alloy-ai[providers]'       # All providers
```

Quick start (OpenAI):

```bash
export OPENAI_API_KEY=sk-...
python -c "from alloy import ask; print(ask('Say hello'))"
```

## Why Alloy?

**🎯 Types you can trust**: Provider‑enforced structured outputs. Get a real `float`, not a string to parse.

**🐍 Just Python**: Commands are functions. Tools are functions. Everything composes.

**⚡ Production‑ready**: Retries, contracts, streaming, cross‑provider support — batteries included.

**🔍 Zero magic**: See what’s happening. Control what’s happening. No hidden state.

## Examples

**Exploration with `ask`** — Quick one‑offs and streaming

```python
from alloy import ask

# One‑liner exploration
print(ask("List 3 reasons Alloy is useful."))

# Stream text output (text‑only streaming)
for chunk in ask.stream("Write a two‑sentence pitch for Alloy."):
    print(chunk, end="")
```

**Typed outputs** — Get back real Python objects

```python
from dataclasses import dataclass
from alloy import command

@dataclass
class Analysis:
    sentiment: str
    score: float
    keywords: list[str]

@command(output=Analysis)
def analyze(text: str) -> str:
    return f"Analyze this text: {text}"

result = analyze("Alloy is amazing!")
print(result.score)  # 0.95
```

TypedDict outputs are supported too:

```python
from typing import TypedDict
from alloy import command

class Product(TypedDict):
    name: str
    price: float

@command(output=Product)
def make() -> str:
    return "Return a Product with name='Test' and price=9.99 (numeric literal)."

print(make()["price"])  # 9.99
```

**Tools + Contracts** — Safe multi‑step workflows

```python
from alloy import command, tool, ensure, require

@tool
@ensure(lambda x: x > 0, "Result must be positive")
def calculate(expression: str) -> float:
    return eval(expression)  # simplified example

@command(tools=[calculate])
def solve(problem: str) -> str:
    return f"Solve step by step: {problem}"
```

See more in [examples/](examples/) and the
[Examples guide](https://docs.alloy.fyi/examples/).

<details>
<summary>📦 More installation options</summary>

```bash
# Specific providers
pip install 'alloy-ai[anthropic]'
pip install 'alloy-ai[gemini]'
pip install 'alloy-ai[ollama]'

# Development
pip install -e '.[dev]'
```

</details>

<details>
<summary>🔧 Configuration</summary>

```bash
export ALLOY_MODEL=gpt-5-mini
export ALLOY_TEMPERATURE=0.2
export ALLOY_MAX_TOOL_TURNS=10
```

Or in Python:

```python
from alloy import configure
configure(model="gpt-5-mini", temperature=0.2)
```

</details>

<details>
<summary>🧪 Run examples offline</summary>

```bash
export ALLOY_BACKEND=fake
make examples-quick
```

</details>

## Providers

Works with major providers — same code, zero changes:

| Provider | Models (examples) | Setup |
|----------|--------------------|-------|
| OpenAI   | gpt‑5              | `export OPENAI_API_KEY=...` |
| Anthropic| claude‑4           | `export ANTHROPIC_API_KEY=...` |
| Google   | gemini             | `export GOOGLE_API_KEY=...` |
| Local    | ollama             | `ollama run <model>` + `ALLOY_MODEL=ollama:<model>` |

See the [full provider guide](https://docs.alloy.fyi/guide/providers/).

## Next Steps

New to Alloy? → [10‑minute tutorial](https://docs.alloy.fyi/tutorial/)

Ready to build? → [Browse examples](examples/)

Need details? → [Read the docs](https://docs.alloy.fyi)

## Contributing

We welcome contributions! See [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
