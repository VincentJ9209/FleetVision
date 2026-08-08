from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "phase00_init_project.py"
CURRENT_WORKFLOW_GOVERNANCE = "docs/00_project_management/WORKFLOW_GOVERNANCE.md"


def test_validator_requires_current_workflow_governance_not_legacy_root(tmp_path: Path) -> None:
    governance_path = tmp_path / CURRENT_WORKFLOW_GOVERNANCE
    governance_path.parent.mkdir(parents=True)
    governance_path.write_text("# Current workflow governance\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--validate"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert CURRENT_WORKFLOW_GOVERNANCE in completed.stdout
    assert "CODEX_WORKFLOW.md" not in completed.stdout
