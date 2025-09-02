# Models: Ollama

See also

- Guide → Providers: guide/providers.md
- Architecture → Provider Abstraction: architecture/provider-abstraction.md#provider-mapping

::: alloy.models.ollama
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      separate_signature: true

## Usage

```bash
export ALLOY_MODEL=ollama:<model>
# Ensure the model is running locally: ollama run <model>
```

### API strategy

Ollama supports two API strategies internally:

- `native` (default for most models): uses the Ollama Python SDK and `/api/chat`.
- `openai_chat`: uses the OpenAI SDK pointed at Ollama’s Chat Completions‑compatible endpoint (`base_url=http://localhost:11434/v1`, `api_key=ollama`).

Default is `native`. The config layer auto‑routes `ollama:*gpt-oss*` models to `openai_chat` unless you explicitly set `extra["ollama_api"]`. Override via `Config.extra["ollama_api"] = "native" | "openai_chat"` to control it.

Notes:

- Tools: both strategies support function tools; native path uses `role="tool"` messages; OpenAI Chat path uses `tool_calls` / `tool_call_id`.
- Structured outputs: native supports JSON Schema via `format={...}` (strict). OpenAI‑compat works with Chat Completions parsing; Alloy can add one final follow‑up (no tools) when `auto_finalize_missing_output` is enabled.

### Configuration extras

- Key: `ollama_api`
  - Values: `"native"` | `"openai_chat"`
  - Default: `"native"`

Example

```python
from alloy import configure

cfg = configure(extra={"ollama_api": "openai_chat"})
```

### Streaming

- Supports text‑only streaming (`ask.stream(...)` and `command.stream(...)`).
- Streaming with tools or typed outputs is not supported.

### Model compatibility (tools + structured outputs)

Tool calling requires a “tool‑capable” model. Structured outputs (strict JSON) are enforced by the API; larger instruction‑tuned models adhere best. Quick picks (see Providers guide for details):

- Llama 3.1 (8B/70B): tools + structured OK; prefer 70B for reliability.
- Qwen 2.5/3 (mid/large): strong tool following; works with both APIs.
- Mistral Nemo 12B, Mixtral: good balance; tool‑tagged variants recommended.
- Command‑R / Command‑R+: robust tool chains.
- Firefunction‑v2 (70B): purpose‑built for function calls.
- Gemma 2 IT: tools require careful prompting or fine‑tunes; not first choice.

### Caveats

- OpenAI‑compatible layer focuses on Chat Completions; it does not implement the OpenAI Responses API. Features tied to `/v1/responses` won’t work through the shim.
- Some Ollama options (e.g., `num_ctx`) aren’t exposed via the OpenAI shim; use the native API for full control.
