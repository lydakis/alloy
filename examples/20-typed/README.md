# 20 — Typed Outputs

- Purpose: Provider-enforced typing (primitives, dataclasses, lists).
- When to use: You need structured results without manual parsing.
- Notes: Use `@dataclass` for objects; nested lists and dataclasses are supported.

Files:
- `01_extract_primitive.py` — float/int outputs
- `02_dataclass_output.py` — `@dataclass` result
- `03_list_output.py` — list of dataclasses
- `04_csv_to_api.py` — map CSV rows to API payloads
