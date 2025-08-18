# Examples

- Basic: `examples/basic_usage.py`
- Tools: `examples/tools_demo.py`
- Tool recipes: see `Tool Recipes` for minimal examples you can paste into your codebase.
- Patterns:
  - Deterministic workflows: `examples/patterns/deterministic_workflows.py`
  - Commands as tools: `examples/patterns/commands_as_tools.py`
  - Triage routing: `examples/patterns/triage_routing.py`
  - DBC tool loop: `examples/patterns/dbc_tool_loop.py`
  - Advanced: Deep Agent (planning, subagents, filesystem): `examples/patterns/deep_agents.py`
- Streaming: `examples/basic/streaming_outputs.py`
- Modalities (sync/async/streaming): `examples/basic/modalities.py`
- Dynamic system prompts: `examples/basic/dynamic_system_prompts.py`
  (These map common orchestration ideas to Alloy’s simpler primitives.)

Run with `.env` loaded:

```
python examples/basic_usage.py
```

Optional: offline dev tip — set `ALLOY_BACKEND=fake` to run without network/keys.

Deep agent (real run):

```
python examples/patterns/deep_agents.py
```
