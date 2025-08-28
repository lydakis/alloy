# 10 — Commands

- Purpose: First-class, typed AI functions via `@command`.
- When to use: You want reusable functions returning text or typed results.
- Notes: Annotate as `-> str`; the decorator controls the actual return type.

Files:
- `01_first_command.py` — basic text command
- `02_command_with_params.py` — params + guidance
- `03_async_command.py` — async command + `.async_()`
