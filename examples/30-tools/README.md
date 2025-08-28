# 30 — Tools

- Purpose: Call local Python functions from the model (`@tool`).
- When to use: Retrieval, calculations, validation, external I/O.
- Notes: Add DBC with `@require/@ensure` for safer behavior.

Files:
- `01_simple_tool.py` — basic tool + command
- `02_command_with_tools.py` — command with two tools
- `03_parallel_tools.py` — multiple tools in one call
- `04_tool_recipes.py` — HTTP, file, and SQL mini-recipes
