# Examples

Run curated, copy‑paste examples (5–15 minutes end‑to‑end). Requires Python 3.10+ and `pip install alloy-ai` (or `-e '.[dev]'` for the repo). Set a provider key; `ALLOY_BACKEND=fake` is optional for offline demos.

---

## Quick Decision Guide

"I want to…"
- Try Alloy interactively → [Exploration](exploration.md)
- Create reusable AI functions → [Commands](commands.md)
- Get structured data → [Commands](commands.md#typed-output-dataclass)
- Add local capabilities → [Tools](tools.md)
- Build multi-step workflows → [Workflows](workflows.md)
- Integrate with my app → [Integration](integration.md)

## Run

- Each example is a standalone script: `python examples/<category>/<file>.py`
- Offline mode: `export ALLOY_BACKEND=fake` for deterministic demo outputs.

## Browse by Category

- Exploration: `examples/00-explore/`
- Commands: `examples/10-commands/`
- Typed outputs: `examples/20-typed/`
- Tools: `examples/30-tools/`
- Contracts: `examples/40-contracts/`
- Composition: `examples/50-composition/`
- Integration: `examples/60-integration/`
- Providers: `examples/70-providers/`
- Patterns: `examples/80-patterns/`
- Advanced: `examples/90-advanced/`

## Selected Links (GitHub)

- [Hello world ask](https://github.com/lydakis/alloy/blob/main/examples/00-explore/00_hello.py)
- [First command](https://github.com/lydakis/alloy/blob/main/examples/10-commands/01_first_command.py)
- [Dataclass output](https://github.com/lydakis/alloy/blob/main/examples/20-typed/02_dataclass_output.py)
- [Simple tool](https://github.com/lydakis/alloy/blob/main/examples/30-tools/01_simple_tool.py)
- [Streaming limits](https://github.com/lydakis/alloy/blob/main/examples/80-patterns/08_streaming_limits.py)
- [Switch providers](https://github.com/lydakis/alloy/blob/main/examples/70-providers/00_switch_providers.py)

## Browse on GitHub

- [All examples](https://github.com/lydakis/alloy/tree/main/examples)
- [00-explore](https://github.com/lydakis/alloy/tree/main/examples/00-explore)
- [10-commands](https://github.com/lydakis/alloy/tree/main/examples/10-commands)
- [20-typed](https://github.com/lydakis/alloy/tree/main/examples/20-typed)
- [30-tools](https://github.com/lydakis/alloy/tree/main/examples/30-tools)
- [40-contracts](https://github.com/lydakis/alloy/tree/main/examples/40-contracts)
- [50-composition](https://github.com/lydakis/alloy/tree/main/examples/50-composition)
- [60-integration](https://github.com/lydakis/alloy/tree/main/examples/60-integration)
- [70-providers](https://github.com/lydakis/alloy/tree/main/examples/70-providers)
- [80-patterns](https://github.com/lydakis/alloy/tree/main/examples/80-patterns)
- [90-advanced](https://github.com/lydakis/alloy/tree/main/examples/90-advanced)

## Tips

- Read the [Common Pitfalls](../guide/pitfalls.md) for quick wins (streaming limits, typed outputs, tool loops).
