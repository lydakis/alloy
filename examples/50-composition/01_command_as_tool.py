"""
Command calling another command (composition)

Run:
  python examples/50-composition/01_command_as_tool.py

Notes:
  - Commands compose naturally: call one command inside another
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import command, configure
from dotenv import load_dotenv


@command
def outline(topic: str) -> str:
    """Create a 3–5 bullet outline for a topic."""
    return f"Write a compact outline with 3–5 bullets for: {topic}"


@command
def write_section(topic: str, bullet: str) -> str:
    """Write a short section expanding one bullet."""
    return f"Expand this bullet into 3–4 sentences about {topic}: {bullet}"


def write_article(topic: str) -> str:
    """Python function composing commands to produce an article-like output."""
    bullets = outline(topic)
    sections = []
    for b in bullets.splitlines():
        b = b.strip("- • ")
        if not b:
            continue
        sections.append(write_section(topic, b))
    return f"# {topic}\n\n" + "\n\n".join(sections[:4])


def main():
    load_dotenv()
    configure(temperature=0.2)
    article = write_article("Type-safe AI functions in Python")
    print(article)


if __name__ == "__main__":
    main()
