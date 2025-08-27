# Examples

All examples live under the `examples/` folder and are runnable scripts. Each is small (50–150 lines) and shows a specific Alloy pattern.

## Quick Start

- Install extras used by some examples: `pip install -r examples/requirements.txt`
- Set a model (e.g., `export ALLOY_MODEL=gpt-5-mini`) and provider key
- Load keys from `.env` or export directly
- Run any file, e.g.: `python examples/00-explore/01_ask_basic.py`
- Offline: `export ALLOY_BACKEND=fake` to run without network/keys

## Streaming Policy

Streaming is text-only. For details and constraints, see:
- Commands → Streaming constraints: https://docs.alloy.fyi/commands/#sync-async-and-streaming

## 00 — Explore

- `examples/00-explore/01_ask_basic.py` — simplest `ask()`
- `examples/00-explore/02_ask_with_context.py` — ask() with context dict
- `examples/00-explore/03_ask_with_tools.py` — ask() with ad-hoc tools

## 10 — Commands

- `examples/10-commands/01_first_command.py` — basic `@command`
- `examples/10-commands/02_command_with_params.py` — parameters + guidance
- `examples/10-commands/03_async_command.py` — async command + `.async_()`

## 20 — Typed Outputs

- `examples/20-typed/01_extract_primitive.py` — output=float/int
- `examples/20-typed/02_dataclass_output.py` — dataclass result
- `examples/20-typed/03_list_output.py` — list[dataclass]
- `examples/20-typed/04_csv_to_api.py` — CSV → API payloads

## 30 — Tools

- `examples/30-tools/01_simple_tool.py` — basic `@tool`
- `examples/30-tools/02_command_with_tools.py` — `@command(tools=[...])`
- `examples/30-tools/03_parallel_tools.py` — multiple tools in a call
- `examples/30-tools/04_tool_recipes.py` — HTTP, file, SQL minimal tools

## 40 — Contracts (DBC)

- `examples/40-contracts/01_require_ensure.py` — pre/post conditions
- `examples/40-contracts/02_workflow_contracts.py` — validate → save pipeline
- `examples/40-contracts/03_self_correcting.py` — recover from contract failures
- `examples/40-contracts/04_payment_pipeline.py` — real-world payment flow

## 50 — Composition

- `examples/50-composition/01_command_as_tool.py` — command calling another
- `examples/50-composition/02_routing_triage.py` — route to specialists
- `examples/50-composition/03_recursive_analysis.py` — coordinator loop
- `examples/50-composition/04_translator_network.py` — multi-stage translation

## 60 — Integration

- `examples/60-integration/01_with_pandas.py` — pandas + one command
- `examples/60-integration/02_flask_endpoint.py` — Flask JSON endpoint
- `examples/60-integration/03_batch_processor.py` — ThreadPool batch processing
- `examples/60-integration/04_pytest_generator.py` — generate pytest tests

## 70 — Providers

- Same invoice task across OpenAI, Anthropic, Gemini, and Ollama
- Setup guide: `examples/70-providers/README.md`

## 80 — Patterns

- `examples/80-patterns/01_rag_citations.py` — RAG with typed citations
- `examples/80-patterns/02_self_refine.py` — iterative improvement loop
- `examples/80-patterns/03_pii_sanitize.py` — PII guardrail via tool
- `examples/80-patterns/04_streaming_updates.py` — streaming text-only
- `examples/80-patterns/05_retry_strategies.py` — retry patterns
- `examples/80-patterns/06_stateful_assistant.py` — file-backed memory (facts + summary)
- `examples/80-patterns/07_conversation_history.py` — rolling chat history between turns

## 90 — Advanced

- `examples/90-advanced/01_deep_agents.py` — dynamic deep-agents (planning, subagents, workspace)
- `examples/90-advanced/02_deep_research.py` — minimal plan/execute
- `examples/90-advanced/03_multi_modal.py` — OCR an image, then summarize
- `examples/90-advanced/04_observability.py` — timing wrapper
- `examples/90-advanced/05_eval_simple.py` — tiny exact-match eval

## Provider Setup

- OpenAI: `ALLOY_MODEL=gpt-5-mini` and `OPENAI_API_KEY`
- Anthropic: `ALLOY_MODEL=claude-sonnet-4-20250514` and `ANTHROPIC_API_KEY`
- Gemini: `ALLOY_MODEL=gemini-2.5-flash` and `GOOGLE_API_KEY`
- Ollama: `ALLOY_MODEL=ollama:<model>` with a local model running (`ollama run <model>`)

## Tips

- Use these as copy‑paste starting points in your own codebase.
