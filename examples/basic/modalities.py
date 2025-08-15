"""Show sync commands, async commands, `.async_()`, and streaming.

Run:
  python examples/basic/modalities.py
"""

from __future__ import annotations

import asyncio

from dotenv import load_dotenv

from alloy import command


@command(output=str)
def greet() -> str:
    return "Say hi in one word."


@command(output=str)
async def greet_async() -> str:
    return "Say hi in one word."


async def main() -> None:
    load_dotenv()

    print("sync:", greet())
    print("async:", await greet_async())
    print("awaited sync via .async_():", await greet.async_())

    print("sync stream:", end=" ")
    for chunk in greet.stream():
        print(chunk, end="", flush=True)
    print()

    print("async stream:", end=" ")
    async for chunk in greet_async.stream():
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
