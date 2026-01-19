"""
Smoke-run a curated subset of examples with the fake backend.

Usage:
  ALLOY_BACKEND=fake python scripts/smoke_examples.py

This avoids provider keys and network calls. It executes a small set of
examples that should remain stable over time.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


EXAMPLES: list[str] = [
    "examples/00-explore/01_ask_basic.py",
    "examples/10-commands/01_first_command.py",
    "examples/20-typed/02_dataclass_output.py",
    "examples/30-tools/01_simple_tool.py",
    "examples/40-contracts/01_require_ensure.py",
    "examples/50-composition/01_command_as_tool.py",
    "examples/60-integration/01_with_pandas.py",
    "examples/80-patterns/02_self_refine.py",
]


def run(cmd: list[str]) -> int:
    print("[smoke] $", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT), env=dict(os.environ, ALLOY_BACKEND="fake"))


def main() -> int:
    failures = 0
    for rel in EXAMPLES:
        path = ROOT / rel
        if not path.exists():
            print(f"[smoke] SKIP (missing): {rel}")
            continue
        rc = run([sys.executable, str(path)])
        if rc != 0:
            print(f"[smoke] FAIL: {rel} (exit {rc})")
            failures += 1
    print(f"[smoke] Completed with {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
