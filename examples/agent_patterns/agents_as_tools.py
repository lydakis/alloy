"""
Alloy equivalent: turn specialist commands into callable tools.

Run:
  python examples/agent_patterns/agents_as_tools.py

Notes:
- Tools run locally in Python. Here they call ask() to delegate translation back to the model.
- The orchestrator command uses tools=[...] so the model can call them.
"""

from __future__ import annotations

from dotenv import load_dotenv
from alloy import command, tool, ask


@tool
def translate_to_spanish(text: str) -> str:
    return ask(f"Translate to Spanish, return only the translation: {text}")


@tool
def translate_to_french(text: str) -> str:
    return ask(f"Translate to French, return only the translation: {text}")


@command(output=str, tools=[translate_to_spanish, translate_to_french])
def translate(prompt: str) -> str:
    return """
        You translate using the provided tools. If multiple languages are requested, call the
        relevant tool(s). Return the final answer in plain text.
        Task:
        {prompt}
        """.strip().format(
        prompt=prompt
    )


def main() -> None:
    load_dotenv()
    # configure(model="gpt-5-mini")
    out = translate("Say 'Hello, how are you?' in Spanish and French.")
    print(out)


if __name__ == "__main__":
    main()
