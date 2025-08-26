"""
Async command example

Run:
  python examples/10-commands/03_async_command.py

Notes:
  - Use `.async_()` to await results from async commands
  - Offline: export ALLOY_BACKEND=fake
"""

import asyncio
from alloy import command, configure
from dotenv import load_dotenv


@command
async def generate_title(topic: str) -> str:
    """Generate a catchy but clear title."""
    return f"Generate a concise, descriptive title about: {topic}"


async def run_async():
    title = await generate_title.async_("Alloy: Python-first AI functions")
    print(title)


def main():
    load_dotenv()
    configure(temperature=0.2)
    asyncio.run(run_async())


if __name__ == "__main__":
    main()

