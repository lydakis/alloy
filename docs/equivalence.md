# Equivalence Guide

This page maps common “agent SDK” patterns to Alloy’s simpler primitives. The
goal is the same functionality with less surface area and clearer types.

## Agents with tools → Command with tools

- SDK: Define an agent and attach tools the model can call.
- Alloy: Write Python tools with `@tool`, then declare a `@command(..., tools=[...])`.

See: `examples/patterns/commands_as_tools.py`.

## Deterministic workflows → Chain commands

- SDK: Orchestrate multiple agents (research → draft → edit).
- Alloy: Chain typed commands; pass outputs as inputs.

See: `examples/patterns/deterministic_workflows.py`.

## Parallel agents → asyncio.gather on .async_()

- SDK: Run agents in parallel.
- Alloy: Call `.async_()` on commands and `await asyncio.gather(...)`.

See: `examples/patterns/deterministic_workflows.py` (parallel section).

## Handoffs → Routing command

- SDK: Agent handoffs/transfer.
- Alloy: A small routing command decides and you call the specialized command.

See: `examples/patterns/triage_routing.py`.

## Dynamic system prompts → ask(..., system=...) or configure(...)

- SDK: Dynamic system messages.
- Alloy: Set `system` per call (`ask(..., system=...)`) or as a default via `configure(default_system=...)`.

See: `examples/basic/dynamic_system_prompts.py`.

## Streaming outputs → .stream() / ask.stream_async()

- SDK: Stream token deltas or high‑level events.
- Alloy: Stream text chunks (`Iterable[str]` or `AsyncIterable[str]`).

See: `examples/basic/streaming_outputs.py`.

## Lifecycle hooks → Wrap calls (optional)

Alloy doesn’t expose built‑in lifecycle hooks. If needed, wrap calls in your app
layer (e.g., log start/stop around calling a command) or introduce a tiny helper
decorator. This keeps the core library small and predictable.
