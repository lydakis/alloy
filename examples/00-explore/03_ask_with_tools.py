"""
ask() with ad-hoc tools

Run:
  python examples/00-explore/03_ask_with_tools.py

Notes:
  - Tools are optional with ask(); streaming is text-only
  - Offline: export ALLOY_BACKEND=fake (tools still execute locally)
"""

from alloy import ask, tool, configure
from dotenv import load_dotenv


@tool
def list_languages(min_len: int = 4) -> list[str]:
    """Return a few popular languages longer than min_len."""
    langs = ["Python", "Rust", "Go", "JavaScript", "TypeScript", "Java"]
    return [x for x in langs if len(x) >= int(min_len)]


def main():
    load_dotenv()
    configure(temperature=0.2)

    response = ask(
        "Pick one language from the tool list and explain when to use it.",
        tools=[list_languages],
    )
    print(response)


if __name__ == "__main__":
    main()

