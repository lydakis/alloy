"""
PII sanitize pattern (pre-processing guardrail)

Run:
  python examples/80-patterns/03_pii_sanitize.py

Notes:
  - Sanitize inputs using a tool before generation
  - Offline: export ALLOY_BACKEND=fake
"""

from __future__ import annotations

import re
from alloy import tool, command, configure
from dotenv import load_dotenv


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")


@tool
def sanitize_text(text: str) -> str:
    """Mask email and phone numbers."""
    out = EMAIL_RE.sub("[EMAIL]", text)
    out = PHONE_RE.sub("[PHONE]", out)
    return out


@command(tools=[sanitize_text])
def summarize_securely(text: str) -> str:
    return f"""
    First, call sanitize_text(text) to mask PII, then summarize in 2–3 bullets.
    Original text: {text}
    """


def main():
    load_dotenv()
    configure(temperature=0.2)
    sample = "Contact Jane at jane.doe@example.com or +1 (555) 123-4567 to schedule."
    print(summarize_securely(sample))


if __name__ == "__main__":
    main()

