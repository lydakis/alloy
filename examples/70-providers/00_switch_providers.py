"""
Same code, different providers — zero changes needed

Run with different models:
  ALLOY_MODEL=gpt-5-mini python examples/70-providers/00_switch_providers.py
  ALLOY_MODEL=claude-sonnet-4-20250514 python examples/70-providers/00_switch_providers.py
  ALLOY_MODEL=gemini-2.5-flash python examples/70-providers/00_switch_providers.py
  ALLOY_MODEL=ollama:<model> python examples/70-providers/00_switch_providers.py

Offline:
  ALLOY_BACKEND=fake python examples/70-providers/00_switch_providers.py
"""

from dataclasses import dataclass
from alloy import command, configure
from dotenv import load_dotenv


@dataclass
class Summary:
    title: str
    bullets: list[str]


@command(output=Summary)
def summarize(text: str) -> str:
    return f"Summarize with a title and 3 bullets: {text}"


def main():
    load_dotenv()
    configure(temperature=0.2)
    res = summarize("Alloy lets you write typed AI functions in Python.")
    print(res)


if __name__ == "__main__":
    main()

