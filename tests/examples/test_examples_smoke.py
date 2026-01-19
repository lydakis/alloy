import os
import sys
import subprocess
import pytest
from pathlib import Path

pytestmark = pytest.mark.examples


def test_examples_smoke_runs():
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["ALLOY_BACKEND"] = "fake"

    # Curated subset that does not require optional deps like pandas
    subset = [
        "examples/00-explore/01_ask_basic.py",
        "examples/10-commands/01_first_command.py",
        "examples/20-typed/02_dataclass_output.py",
        "examples/30-tools/01_simple_tool.py",
        "examples/40-contracts/01_require_ensure.py",
        "examples/50-composition/01_command_as_tool.py",
        # intentionally skip examples/60-integration/01_with_pandas.py
        "examples/80-patterns/02_self_refine.py",
    ]

    failures = []
    for rel in subset:
        path = root / rel
        if not path.exists():
            continue
        rc = subprocess.call([sys.executable, str(path)], cwd=str(root), env=env)
        if rc != 0:
            failures.append((rel, rc))

    if failures:
        pytest.fail(f"example failures: {failures}")
