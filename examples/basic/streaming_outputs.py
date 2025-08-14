"""
Alloy equivalent: streaming outputs (chunked text).

Run:
  python examples/basic/streaming_outputs.py

Notes:
- Alloy streams text chunks; it does not expose low-level token delta events.
"""

from __future__ import annotations

from dotenv import load_dotenv
from alloy import command, ask


@command(output=str)
def generate_jokes() -> str:
    return "Tell me 5 one-line jokes about databases. Keep them short."


def stream_raw() -> None:
    # Stream chunks from a command
    for chunk in generate_jokes.stream():
        print(chunk, end="", flush=True)
    print()


def stream_ask() -> None:
    for chunk in ask.stream("Explain vector databases in 3 short bullets."):
        print(chunk, end="", flush=True)
    print()


def main() -> None:
    load_dotenv()
    stream_raw()
    stream_ask()


if __name__ == "__main__":
    main()
