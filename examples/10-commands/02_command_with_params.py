"""
Command with parameters and light guidance

Run:
  python examples/10-commands/02_command_with_params.py

Notes:
  - Feels like normal Python; Alloy adds intelligence
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import command, configure
from dotenv import load_dotenv


@command
def write_intro(style: str, topic: str) -> str:
    """Write a short intro in a requested style."""
    return f"""
    Write a concise introduction (80–120 words).
    Style: {style}
    Topic: {topic}

    Keep it specific and avoid fluff.
    """


def main():
    load_dotenv()
    configure(temperature=0.2)

    text = write_intro("pragmatic, developer-focused", "type-safe AI functions in Python")
    print(text)


if __name__ == "__main__":
    main()

