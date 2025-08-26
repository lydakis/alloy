"""
Structured dataclass output

Run:
  python examples/20-typed/02_dataclass_output.py

Notes:
  - Shows provider-enforced structured output via a @dataclass
  - Offline: export ALLOY_BACKEND=fake
"""

from dataclasses import dataclass
from alloy import command, configure
from dotenv import load_dotenv


@dataclass
class ArticleSummary:
    title: str
    key_points: list[str]
    reading_time_minutes: int


@command(output=ArticleSummary)
def summarize_article(text: str) -> str:
    """Summarize an article into a structured JSON object."""
    return f"""
    Read the article and produce:
    - title: concise title
    - key_points: 3–5 short bullets
    - reading_time_minutes: integer estimate

    Article:
    {text}
    """


def main():
    load_dotenv()
    configure(temperature=0.2)

    article = (
        "Python emphasizes code readability, supports multiple paradigms, and has a vast library ecosystem. "
        "It is widely used in data science, web development, and scripting."
    )
    res = summarize_article(article)
    print("Title:", res.title)
    print("Reading time:", res.reading_time_minutes)
    for i, p in enumerate(res.key_points, 1):
        print(f"{i}. {p}")


if __name__ == "__main__":
    main()
