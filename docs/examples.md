# Examples

All examples live under the `examples/` folder and are runnable scripts. Each page in the suite demonstrates a specific Alloy pattern with minimal Python code.

Quick start
- Install extras used by some examples: `pip install -r examples/requirements.txt`
- Set a provider model via env, for example: `export ALLOY_MODEL=gpt-5-mini`
- Load keys in `.env` (e.g., `OPENAI_API_KEY`) or export directly
- Run any file, for example: `python examples/00-explore/01_ask_basic.py`
- Offline tip: `export ALLOY_BACKEND=fake` to run without network/keys

Streaming policy
- Streaming is text-only across providers. Commands with tools or non-string outputs do not stream; call them normally to get typed results.

Index (progressive path)
- Explore: `examples/00-explore/`
  - `01_ask_basic.py` — simplest `ask()`
  - `02_ask_with_context.py` — ask() with context dict
  - `03_ask_with_tools.py` — ask() with ad-hoc tools
- Commands: `examples/10-commands/`
  - `01_first_command.py` — basic `@command`
  - `02_command_with_params.py` — parameters + guidance
  - `03_async_command.py` — async command + `.async_()`
- Typed: `examples/20-typed/`
  - `01_extract_primitive.py` — output=float/int
  - `02_dataclass_output.py` — dataclass result
  - `03_list_output.py` — list[dataclass]
  - `04_csv_to_api.py` — CSV → API payloads
- Tools: `examples/30-tools/`
  - `01_simple_tool.py` — basic `@tool`
  - `02_command_with_tools.py` — `@command(tools=[...])`
  - `03_parallel_tools.py` — multiple tools in a call
  - `04_tool_recipes.py` — HTTP, file, SQL minimal tools
- Contracts: `examples/40-contracts/`
  - `01_require_ensure.py` — pre/post conditions
  - `02_workflow_contracts.py` — validate → save pipeline
  - `03_self_correcting.py` — model recovers from contract failures
  - `04_payment_pipeline.py` — real-world payment flow
- Composition: `examples/50-composition/`
  - `01_command_as_tool.py` — command calling another
  - `02_routing_triage.py` — route to specialists
  - `03_recursive_analysis.py` — coordinator loop
  - `04_translator_network.py` — multi-stage translation
- Integration: `examples/60-integration/`
  - `01_with_pandas.py` — pandas + one command
  - `02_flask_endpoint.py` — Flask JSON endpoint
  - `03_batch_processor.py` — ThreadPool batch processing
  - `04_pytest_generator.py` — generate pytest tests
- Providers: `examples/70-providers/`
  - Same invoice task across OpenAI, Anthropic, Gemini, and Ollama
  - Setup guide: `examples/70-providers/README.md`
- Patterns: `examples/80-patterns/`
  - `01_rag_citations.py` — RAG with typed citations
  - `02_self_refine.py` — iterative improvement loop
  - `03_pii_sanitize.py` — PII guardrail via tool
  - `04_streaming_updates.py` — streaming text-only
  - `05_retry_strategies.py` — retry patterns
  - `06_stateful_assistant.py` — file-backed memory (facts + summary)
  - `07_conversation_history.py` — rolling chat history between turns
- Advanced: `examples/90-advanced/`
  - `01_deep_agents.py` — dynamic deep-agents (planning, subagents, workspace)
  - `02_deep_research.py` — minimal plan/execute
  - `03_multi_modal.py` — OCR an image, then summarize
  - `04_observability.py` — timing wrapper
  - `05_eval_simple.py` — tiny exact-match eval

Provider setup
- OpenAI: `ALLOY_MODEL=gpt-5-mini` and `OPENAI_API_KEY`
- Anthropic: `ALLOY_MODEL=claude-sonnet-4-20250514` and `ANTHROPIC_API_KEY`
- Gemini: `ALLOY_MODEL=gemini-2.5-flash` and `GOOGLE_API_KEY`
- Ollama: `ALLOY_MODEL=ollama:<model>` with a local model running (`ollama run <model>`)

Tip
- Examples are intentionally small (50–150 lines) and Python-first. Use them as copy-paste starting points in your own codebase.
