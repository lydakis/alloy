"""
Simple @tool usage

Run:
  python examples/30-tools/01_simple_tool.py

Notes:
  - Tools are normal Python functions marked with @tool
  - Offline: export ALLOY_BACKEND=fake (tools still run locally)
"""

from alloy import tool, command, configure
from dotenv import load_dotenv


@tool
def word_count(text: str) -> int:
    """Count words in text."""
    return len([w for w in text.split() if w.strip()])


@command(tools=[word_count])
def analyze(text: str) -> str:
    return f"""
    Use word_count(text) to compute length, then suggest one change to improve clarity.
    Text: {text}
    """


def main():
    load_dotenv()
    configure(temperature=0.2)
    result = analyze("Alloy makes typed AI functions feel like normal Python.")
    print(result)


if __name__ == "__main__":
    main()

