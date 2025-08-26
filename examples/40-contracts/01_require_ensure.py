"""
Basic Design by Contract (DBC) with tools

Run:
  python examples/40-contracts/01_require_ensure.py

Notes:
  - @require checks inputs (receives BoundArguments)
  - @ensure checks outputs (receives tool result)
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import tool, command, require, ensure, configure
from dotenv import load_dotenv


@tool
@require(lambda ba: int(ba.arguments.get("n", 0)) % 2 == 0, "n must be even")
def half(n: int) -> int:
    """Return n/2, only defined for even n."""
    return int(n) // 2


@tool
@ensure(lambda result: result > 0, "result must be positive")
def absolute(n: int) -> int:
    """Return absolute value and ensure positivity."""
    return n if n >= 0 else -n


@command(tools=[half, absolute])
def process_number(n: int) -> str:
    return f"""
    You may call tools to process the number {n}:
    - If n is even, call half(n) once to reduce it.
    - Always produce a positive value via absolute(n).

    Provide a short explanation of what you did.
    """


def main():
    load_dotenv()
    configure(temperature=0.2)

    print(process_number(6))
    # For odd n, half(n) is disallowed by the contract; model should avoid it or recover.


if __name__ == "__main__":
    main()
