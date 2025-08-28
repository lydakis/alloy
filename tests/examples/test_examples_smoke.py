import os
import sys
import subprocess
import pytest
from pathlib import Path


pytestmark = pytest.mark.examples


def test_examples_smoke_runs():
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "smoke_examples.py"
    if not script.exists():
        pytest.skip("smoke_examples.py not found")
    env = dict(os.environ)
    env["ALLOY_BACKEND"] = "fake"
    rc = subprocess.call([sys.executable, str(script)], cwd=str(root), env=env)
    assert rc == 0

