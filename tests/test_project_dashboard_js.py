from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_javascript_unit_suite() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is optional and unavailable")
    completed = subprocess.run(
        [node, "--test", str(ROOT / "tests/js/project_dashboard.test.mjs")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
