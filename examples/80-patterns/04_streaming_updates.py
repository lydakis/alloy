"""
Streaming updates (text-only)

Run:
  python examples/80-patterns/04_streaming_updates.py

Notes:
  - Streaming supports text-only output; tools stream only when the backend supports it (OpenAI Responses today)
  - Offline: export ALLOY_BACKEND=fake (emits a single 'demo' chunk)
"""

from alloy import command, ask, configure
from dotenv import load_dotenv


@command  # text-only
def brainstorm(topic: str) -> str:
    return f"Brainstorm concise ideas about: {topic}"


def main():
    load_dotenv()
    configure(temperature=0.2)

    print("-- ask.stream --")
    for chunk in ask.stream("Explain the benefits of typed AI functions."):
        print(chunk, end="", flush=True)
    print("\n")

    print("-- command.stream --")
    for chunk in brainstorm.stream("Alloy examples"):  # text-only command
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
