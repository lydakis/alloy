# Command Lifecycle

Understand how a command runs end‑to‑end (~4 minutes).

---

## Sequence (no tools)

```mermaid
sequenceDiagram
  participant U as Your code
  participant C as Command wrapper
  participant B as Backend adapter
  participant P as Provider API
  participant T as Type system

  U->>C: call my_cmd(args)
  C->>B: build request (config, schema)
  B->>P: create response
  P-->>B: final answer
  B->>T: parse/validate (if schema)
  T-->>C: Python object / str
  C-->>U: return value
```

## Sequence (with tools, strict output)

```mermaid
sequenceDiagram
  participant U as Your code
  participant C as Command wrapper
  participant B as Backend adapter
  participant P as Provider API
  participant L as Tools layer
  participant T as Type system

  U->>C: call my_cmd(args)
  C->>B: build request (tools+schema)
  loop tool calls (max_tool_turns)
    B->>P: respond (tool call)
    P-->>B: tool request
    B->>L: invoke @tool(args)
    L-->>B: tool result (or contract message)
    B->>P: tool_result
  end
  alt no final structured output
    B->>P: one final turn (no tools) to finalize
  end
  P-->>B: final answer
  B->>T: parse/validate
  T-->>C: typed object
  C-->>U: return value
```

## Notes

- Finalization: for providers that require it, Alloy may issue one final turn (without tools) to obtain a structured answer when tools were used and no final was returned.
- Limits: the tool loop is capped by `max_tool_turns` (default 10) to avoid runaway behavior.
- Errors: configuration errors surface immediately; parse failures raise `CommandError` with expected type/context.
