# Examples

- Basic: `examples/basic_usage.py`
- Tools: `examples/tools_demo.py`
- Built-in tools: use `file_search`, `py_eval`, `py_exec` directly or include in `tools=[...]`.
- Agent patterns:
  - Deterministic workflows: `examples/agent_patterns/deterministic_workflows.py`
  - Agents as tools: `examples/agent_patterns/agents_as_tools.py`
- Streaming: `examples/basic/streaming_outputs.py`
- Dynamic system prompts: `examples/basic/dynamic_system_prompts.py`
- Handoffs: `examples/handoffs/triage_pattern.py`

Run with `.env` loaded:

```
python examples/basic_usage.py
```

Offline demo:

```
ALLOY_BACKEND=fake python examples/basic_usage.py
```
