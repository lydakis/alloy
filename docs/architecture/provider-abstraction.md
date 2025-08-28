# Provider Abstraction

- Audience: engineers interested in backend support and portability.
- Outcome: know how Alloy normalizes provider differences.
- Time: 3 minutes
- Prereqs: none.

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
