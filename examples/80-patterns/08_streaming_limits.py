"""
Streaming limits: what works and what doesn't

Run:
  python examples/80-patterns/08_streaming_limits.py

Notes:
  - Streaming is text-only. No tools, no typed outputs.
  - This file demonstrates allowed and disallowed patterns.
"""

from alloy import command, ask, configure, ConfigurationError
from dotenv import load_dotenv


@command  # text output
def brainstorm(topic: str) -> str:
    return f"Write a short riff about: {topic}"


@command(output=float)
def extract_number(text: str) -> str:
    return f"Extract a number from: {text}"


def main():
    load_dotenv()
    configure(temperature=0.2)

    print("-- ask.stream (text-only) --")
    for chunk in ask.stream("Write a one-liner about cats"):
        print(chunk, end="")
    print("\n")

    print("-- command.stream (text-only) --")
    for chunk in brainstorm.stream("Alloy examples"):
        print(chunk, end="")
    print()

    print("-- typed output cannot stream --")
    try:
        # This will raise ConfigurationError because typed outputs don't stream
        _ = extract_number.stream("$49.99")
    except ConfigurationError as e:
        print("Expected error:", e)


if __name__ == "__main__":
    main()

