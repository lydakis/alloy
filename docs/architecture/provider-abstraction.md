# Provider Abstraction

How Alloy normalizes provider differences (~3 minutes).

---

- Request assembly: messages, tools, and schema built once; adapters map to provider requests.
- Streaming: adapters expose text streaming when supported; structured streaming preview assembles list elements.
- Structured outputs: JSON Schema sent via provider‑native mechanisms; primitives wrapped/unwrapped as needed.
- Error handling: normalize transient vs configuration vs parse errors.

## Provider Mapping

### OpenAI
- API: Responses API (`responses.create` / `responses.stream`)
- Tools: yes (function calling); parallel tool requests possible
- Structured outputs: yes (json_schema) with strict parse; primitives wrapped via `{value: ...}`
- Streaming: text‑only
- Finalization: one extra turn (no tools) to produce final structured answer when missing (auto‑finalize)
- Code: [src/alloy/models/openai.py](https://github.com/lydakis/alloy/blob/main/src/alloy/models/openai.py)

### Anthropic (Claude)
- API: `messages.create`
- Tools: yes (tool_use/tool_result)
- Structured outputs: yes (schema guidance + prefill)
- Streaming: text‑only
- Requirements: `max_tokens` required (defaults to 512 if unset)
- Code: [src/alloy/models/anthropic.py](https://github.com/lydakis/alloy/blob/main/src/alloy/models/anthropic.py)

### Google Gemini
- API: `google-genai` (responses + tool config)
- Tools: yes
- Structured outputs: yes (response_json_schema)
- Streaming: text‑only
- Requirements: `max_tool_turns` must be configured
- Code: [src/alloy/models/gemini.py](https://github.com/lydakis/alloy/blob/main/src/alloy/models/gemini.py)

### Ollama (local)
- API: `ollama.chat`
- Tools: not implemented in scaffold
- Structured outputs: limited (prompt steering for primitives)
- Streaming: not implemented in scaffold
- Code: [src/alloy/models/ollama.py](https://github.com/lydakis/alloy/blob/main/src/alloy/models/ollama.py)

### Fake (offline)
- Purpose: deterministic outputs for CI/examples
- Tools: no; Structured: yes (stubbed objects); Streaming: text chunks
- Code: [src/alloy/models/base.py](https://github.com/lydakis/alloy/blob/main/src/alloy/models/base.py) (inlined class)

---

## Shared Tool Loop & LoopState (for contributors)

All providers now share a single tool‑calling loop implemented in the base backend. This removes duplicated control flow and makes adding new providers straightforward.

- Shared logic: `ModelBackend.run_tool_loop()` and `ModelBackend.arun_tool_loop()` handle request/response iteration, turn‑limit enforcement, and parallel tool execution.
- Contract: Providers implement a `*LoopState(BaseLoopState)` that supplies only provider‑specific behavior.

BaseLoopState contract
- make_request(client): build and fire one model request using the state’s transcript/config.
- amake_request(client): async version of make_request.
- extract_text(response): return the assistant’s final text from this step (used when no tools are present).
- extract_tool_calls(response): return a list of normalized `ToolCall(id, name, args)`; return `[]` or `None` if there are no calls.
- add_tool_results(calls, results): append provider‑native tool‑result messages/parts to the transcript so the next request can use them.

Loop semantics
- Turn limit: increments only when tool calls are present; raises `ToolLoopLimitExceeded` if `turns > max_tool_turns`. The exception includes `partial_text` from the last assistant content.
- Parallel tools: serial for one call; otherwise bounded by `Config.parallel_tools_max` (default), using threads in sync and `asyncio.to_thread` in async.
- Streaming: text‑only. Provider front‑ends enforce this; streaming with tools or structured outputs raises a configuration error.

Provider responsibilities
- Message shaping: build initial transcript (system/user prompts), tools/functions declarations, and any provider extras (e.g., tool_choice).
- Tool extraction: parse provider responses into `ToolCall`s; where call IDs are unavailable (e.g., Gemini), rely on order.
- Tool result injection: map `ToolResult` values into provider‑native tool result blocks/messages for the next turn.
- Finalization (post‑loop): when structured outputs are requested and the primary turn produced no final JSON, issue a constrained follow‑up without tools to obtain the final object.

Adding a new provider
- Create `YourProviderLoopState(BaseLoopState)` implementing the methods above.
- In your backend, prepare the initial state (system/prompt/tools) and call `run_tool_loop` or `arun_tool_loop`.
- Implement provider‑specific finalize‑JSON if applicable.
