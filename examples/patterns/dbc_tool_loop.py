"""
Patterns: DBC (Design by Contract) tool loop.

Run:
  python examples/patterns/dbc_tool_loop.py

Notes:
- Tools expose pre/post conditions to guide the model without crashing the run.
- The model will receive messages like "run validate_data first" and can adapt.
"""

from __future__ import annotations

from dotenv import load_dotenv
from alloy import tool, require, ensure, command


@tool
@ensure(lambda d: isinstance(d, dict) and "validated_at" in d, "must add validated_at")
def validate_data(data: dict) -> dict:
    """Add validated_at to the payload if missing (idempotent)."""
    data = dict(data)
    data.setdefault("validated_at", "2025-01-01T00:00:00Z")
    return data


@tool
@require(
    lambda ba: isinstance(ba.arguments.get("data"), dict)
    and "validated_at" in ba.arguments["data"],
    "run validate_data first",
)
@ensure(lambda ok: ok is True, "save must succeed")
def save_to_production(data: dict) -> bool:
    """Pretend to save data; returns True on success."""
    return True


@command(output=str, tools=[validate_data, save_to_production])
def normalize_then_save(payload: dict) -> str:
    return """
        Normalize the payload using validate_data, then call save_to_production. If a step fails a
        contract (e.g., missing validated_at), read the message and correct your plan.
        Payload:
        {payload}
        """.strip().format(
        payload=payload
    )


def main() -> None:
    load_dotenv()
    # Example payload missing validated_at; model should call validate_data first, then save.
    out = normalize_then_save({"name": "Alice"})
    print(out)


if __name__ == "__main__":
    main()
