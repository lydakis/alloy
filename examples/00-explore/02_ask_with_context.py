"""
ask() with explicit context

Run:
  python examples/00-explore/02_ask_with_context.py

Notes:
  - Context dict is prefixed by Alloy to the prompt
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import ask, configure
from dotenv import load_dotenv


def main():
    load_dotenv()
    configure(temperature=0.2)

    article = (
        "Python emphasizes code readability with significant indentation. "
        "It supports multiple paradigms and has a vast ecosystem."
    )

    outline = ask(
        "Create a concise outline with 3–5 headings",
        context={"text": article, "domain": "programming"},
    )
    print(outline)


if __name__ == "__main__":
    main()
