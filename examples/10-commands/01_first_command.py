"""
Basic @command that returns text

Run:
  python examples/10-commands/01_first_command.py

Notes:
  - Commands are normal functions that return prompts
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import command, configure
from dotenv import load_dotenv


@command  # default typed output is str
def summarize(text: str) -> str:
    """Return a 3-bullet summary."""
    return f"Summarize in exactly 3 bullets:\n\n{text}"


def main():
    load_dotenv()
    configure(temperature=0.2)

    article = "REST APIs use HTTP methods, resources, and representations."
    summary = summarize(article)
    print(summary)


if __name__ == "__main__":
    main()

