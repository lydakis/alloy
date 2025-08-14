"""
Alloy equivalent: simple handoff (triage -> specialized commands).

Run:
  python examples/handoffs/triage_pattern.py

Notes:
- Triage picks a target based on the message; we then invoke the specialized command.
"""

from __future__ import annotations

from dotenv import load_dotenv
from alloy import command


@command(output=str)
def triage_route(message: str) -> str:
    return """
        Decide the correct destination for this request: 'billing' or 'refund'. Return exactly one
        word: billing or refund. Consider the user intent carefully.
        Message:
        {message}
        """.strip().format(
        message=message
    )


@command(output=str)
def billing_handler(message: str) -> str:
    return """
        Handle billing questions only. Answer concisely with next steps and required info. If the
        question is out of scope, say so.
        Message:
        {message}
        """.strip().format(
        message=message
    )


@command(output=str)
def refund_handler(message: str) -> str:
    return """
        Handle refund requests only. Ask for the minimum details needed and provide clear next
        steps. If the request is out of scope, say so.
        Message:
        {message}
        """.strip().format(
        message=message
    )


def main() -> None:
    load_dotenv()
    message = "I was charged twice for order #123; please fix it."
    route = triage_route(message).strip().lower()
    if route == "billing":
        print(billing_handler(message))
    else:
        print(refund_handler(message))


if __name__ == "__main__":
    main()
