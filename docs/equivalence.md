# Equivalence Guide

This page maps common “agent SDK” patterns to Alloy’s simpler primitives. The
goal is the same functionality with less surface area and clearer types.

## Agents with tools → Command with tools

- SDK: Define an agent and attach tools the model can call.
- Alloy: Write Python tools with `@tool`, then declare a `@command(..., tools=[...])`.

See: `examples/30-tools/02_command_with_tools.py`.

## Deterministic workflows → Chain commands

- SDK: Orchestrate multiple agents (research → draft → edit).
- Alloy: Chain typed commands; pass outputs as inputs.

See: `examples/50-composition/03_recursive_analysis.py`.

## Parallel agents → asyncio.gather on .async_()

- SDK: Run agents in parallel.
- Alloy: Call `.async_()` on commands and `await asyncio.gather(...)`.

Tip: call `.async_()` and use `await asyncio.gather(...)` to run commands concurrently.

## Handoffs → Routing command

- SDK: Agent handoffs/transfer.
- Alloy: A small routing command decides and you call the specialized command.

See: `examples/50-composition/02_routing_triage.py`.

## Dynamic system prompts → ask(..., system=...) or configure(...)

- SDK: Dynamic system messages.
- Alloy: Set `system` per call (`ask(..., system=...)`) or as a default via `configure(default_system=...)`.

Tip: pass a `system` per call or set a default via `configure(default_system=...)`.

## Streaming outputs → .stream() / ask.stream_async()

- SDK: Stream token deltas or high‑level events.
- Alloy: Stream text chunks (`Iterable[str]` or `AsyncIterable[str]`).

See: `examples/80-patterns/04_streaming_updates.py` and `examples/80-patterns/08_streaming_limits.py`.

## Lifecycle hooks → Wrap calls (optional)

Alloy doesn’t expose built‑in lifecycle hooks. If needed, wrap calls in your app
layer (e.g., log start/stop around calling a command) or introduce a tiny helper
decorator. This keeps the core library small and predictable.
