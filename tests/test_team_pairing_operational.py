from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from team_pairing_audit_fixtures import create_rgb_image, create_test_project
try:
    from fleetvision.review.team_pairing_operational import (
        TeamPairingOperationalError,
        prepare_team_pairing_workspace,
    )
    _OPERATIONAL_IMPORT_ERROR: ModuleNotFoundError | None = None
except ModuleNotFoundError as exc:
    TeamPairingOperationalError = RuntimeError  # type: ignore[assignment]
    prepare_team_pairing_workspace = None  # type: ignore[assignment]
    _OPERATIONAL_IMPORT_ERROR = exc


def _require_operational_module() -> None:
    if _OPERATIONAL_IMPORT_ERROR is not None:
        pytest.fail(
            "missing fleetvision.review.team_pairing_operational: "
            f"{_OPERATIONAL_IMPORT_ERROR}"
        )


ROOT = Path(__file__).resolve().parents[1]
WRAPPERS = (
    "phase05s_prepare_team_pairing_audit.ps1",
    "phase05s_launch_team_pairing_review_app.ps1",
    "phase05s_export_team_pairing_review.ps1",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _project_with_four_images(tmp_path: Path) -> tuple[Path, Path, Path]:
    project_root, source_root, config_path = create_test_project(tmp_path)
    for index, minute in enumerate((0, 2, 4, 6), start=1):
        create_rgb_image(
            source_root / f"capture_{index}.jpg",
            color=(40 * index, 80, 120),
            exif_values={36867: f"2026:07:19 10:{minute:02d}:00"},
        )
    return project_root, source_root, config_path


def test_prepare_creates_candidate_contact_sheet_and_sqlite_workspace(
    tmp_path: Path,
) -> None:
    _require_operational_module()
    project_root, _, config_path = _project_with_four_images(tmp_path)
    workspace = (
        project_root
        / "outputs"
        / "phase05s"
        / "team_pairing_audit"
        / "team_pairing_audit_test"
    )

    result = prepare_team_pairing_workspace(
        config_path,
        project_root,
        workspace_root=workspace,
        created_at_utc="2026-07-19T10:30:00+00:00",
    )

    assert result.image_count == 4
    assert result.batch_count == 1
    assert result.candidate_manifest.is_file()
    assert result.review_database.is_file()
    assert len(list(result.contact_sheet_dir.glob("*.jpg"))) == 1
    assert (workspace / "source" / "source_snapshot_before.json").is_file()
    assert (workspace / "source" / "source_snapshot_after.json").is_file()
    assert (workspace / "source" / "source_snapshot_verification.json").is_file()


def test_prepare_preserves_source_bytes(tmp_path: Path) -> None:
    _require_operational_module()
    project_root, source_root, config_path = _project_with_four_images(tmp_path)
    before = {path.name: _sha256(path) for path in source_root.glob("*.jpg")}
    workspace = (
        project_root
        / "outputs"
        / "phase05s"
        / "team_pairing_audit"
        / "team_pairing_audit_source_safe"
    )

    prepare_team_pairing_workspace(
        config_path,
        project_root,
        workspace_root=workspace,
    )

    after = {path.name: _sha256(path) for path in source_root.glob("*.jpg")}
    assert after == before


def test_prepare_blocks_existing_workspace_without_overwrite(tmp_path: Path) -> None:
    _require_operational_module()
    project_root, _, config_path = _project_with_four_images(tmp_path)
    workspace = (
        project_root
        / "outputs"
        / "phase05s"
        / "team_pairing_audit"
        / "team_pairing_audit_existing"
    )
    workspace.mkdir(parents=True)
    marker = workspace / "keep.txt"
    marker.write_text("keep", encoding="utf-8")

    with pytest.raises(TeamPairingOperationalError, match="禁止覆蓋"):
        prepare_team_pairing_workspace(
            config_path,
            project_root,
            workspace_root=workspace,
        )

    assert marker.read_text(encoding="utf-8") == "keep"


def test_prepare_failure_cleans_partial_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_operational_module()
    project_root, _, config_path = _project_with_four_images(tmp_path)
    workspace = (
        project_root
        / "outputs"
        / "phase05s"
        / "team_pairing_audit"
        / "team_pairing_audit_failure"
    )

    def fail_contact_sheet(*args, **kwargs):
        raise RuntimeError("simulated contact-sheet failure")

    monkeypatch.setattr(
        "fleetvision.review.team_pairing_operational.create_batch_contact_sheet",
        fail_contact_sheet,
    )

    with pytest.raises(RuntimeError, match="simulated"):
        prepare_team_pairing_workspace(
            config_path,
            project_root,
            workspace_root=workspace,
        )

    assert not workspace.exists()


def test_prepare_cli_help_works_without_pythonpath() -> None:
    _require_operational_module()
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "phase05s_prepare_team_pairing_audit.py"),
            "--help",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "--workspace-root" in completed.stdout
    assert "--project-root" in completed.stdout
    assert "--config" in completed.stdout


def test_three_powershell_wrappers_have_safe_operational_contract() -> None:
    _require_operational_module()
    for name in WRAPPERS:
        text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert text.startswith("#requires -Version 5.1")
        assert "Set-StrictMode -Version Latest" in text
        assert '$ErrorActionPreference = "Stop"' in text
        assert "WRAPPER_OUTCOME=PASS" in text
        assert "WRAPPER_OUTCOME=BLOCKED" in text
        lowered = text.lower()
        assert "git add" not in lowered
        assert "git commit" not in lowered
        assert "git push" not in lowered
        assert "G:\\Project\\FleetVision\\.venv\\Scripts\\python.exe" in text

    review = (
        ROOT / "scripts" / "phase05s_launch_team_pairing_review_app.ps1"
    ).read_text(encoding="utf-8")
    assert "--server.address=127.0.0.1" in review
    assert "0.0.0.0" not in review


def test_operational_guide_documents_prepare_review_export_and_a3_boundary() -> None:
    _require_operational_module()
    guide = (
        ROOT
        / "docs"
        / "01_phase_guides"
        / "phase_05s_team_pairing_audit_operational_guide.md"
    ).read_text(encoding="utf-8")
    assert "### 1. Prepare" in guide
    assert "### 2. Review" in guide
    assert "### 3. Export" in guide
    assert "SQLite 是 live review state 的唯一來源" in guide
    assert "A3 只建立與驗證工具" in guide
    assert "pair comparison MVP" in guide
