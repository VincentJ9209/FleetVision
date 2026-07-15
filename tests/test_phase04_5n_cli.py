from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from annotation_correction_promotion_fixtures import build_phase04_5n_fixture
from fleetvision.review.annotation_correction_promotion_contract import (
    load_phase04_5n_config,
    sha256_file,
)
from fleetvision.review.annotation_correction_staging import (
    prepare_staged_correction_workspace,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SCRIPT = REPO_ROOT / "scripts/phase04_5_stage_annotation_corrections.py"
POWERSHELL_WRAPPER = REPO_ROOT / "scripts/phase04_5_stage_annotation_corrections.ps1"
RUNBOOK = REPO_ROOT / "docs/01_phase_guides/phase_04_5_annotation_correction_promotion.md"
PROMOTION_PYTHON_SCRIPT = REPO_ROOT / "scripts/phase04_5_promote_annotation_corrections.py"
PROMOTION_POWERSHELL_WRAPPER = REPO_ROOT / "scripts/phase04_5_promote_annotation_corrections.ps1"


def _python_env() -> dict[str, str]:
    env = os.environ.copy()
    source_root = str(REPO_ROOT / "src")
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = source_root if not current else source_root + os.pathsep + current
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _last_json_line(text: str) -> dict[str, object]:
    lines = [line for line in text.splitlines() if line.strip()]
    assert lines, "expected a JSON output line"
    return json.loads(lines[-1])


def test_n1_python_cli_returns_structured_pass_json(tmp_path: Path) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(PYTHON_SCRIPT),
            "--project-root",
            str(fixture.project_root),
            "--config",
            str(fixture.config_path),
            "--completed-review-workspace",
            str(fixture.completed_review_root),
            "--timestamp",
            "20260715_031000000",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=_python_env(),
    )
    assert result.returncode == 0, result.stderr
    assert len([line for line in result.stdout.splitlines() if line.strip()]) == 1
    payload = _last_json_line(result.stdout)
    assert payload["outcome"] == "PASS"
    assert payload["classification"] == (
        "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED"
    )
    assert payload["proposal_count"] == 2
    assert payload["canonical_source_modified"] is False
    assert payload["test_split_read"] is False


def test_n1_python_cli_returns_structured_blocked_json_on_rerun(
    tmp_path: Path,
) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    command = [
        sys.executable,
        str(PYTHON_SCRIPT),
        "--project-root",
        str(fixture.project_root),
        "--config",
        str(fixture.config_path),
        "--completed-review-workspace",
        str(fixture.completed_review_root),
        "--timestamp",
        "20260715_031000010",
    ]
    first = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=_python_env(),
    )
    assert first.returncode == 0, first.stderr

    second = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=_python_env(),
    )
    assert second.returncode == 1
    assert second.stdout.strip() == ""
    assert len([line for line in second.stderr.splitlines() if line.strip()]) == 1
    payload = _last_json_line(second.stderr)
    assert payload["outcome"] == "BLOCKED"
    assert payload["classification"] == (
        "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_BLOCKED"
    )
    assert payload["canonical_source_modified"] is False
    assert payload["n1_executed"] is False
    assert payload["n2_executed"] is False


def test_python_adapter_is_thin_and_imports_domain_main() -> None:
    text = PYTHON_SCRIPT.read_text(encoding="utf-8")
    assert "from fleetvision.review.annotation_correction_staging import main" in text
    assert "raise SystemExit(main())" in text
    assert "argparse" not in text


def test_powershell_wrapper_sets_location_and_forwards_all_required_arguments() -> None:
    text = POWERSHELL_WRAPPER.read_text(encoding="utf-8-sig")
    assert "Set-Location -LiteralPath $ProjectRoot" in text
    assert "--project-root" in text
    assert "--config" in text
    assert "--completed-review-workspace" in text
    assert "--timestamp" in text
    assert "ConvertFrom-Json" not in text


@pytest.mark.skipif(
    shutil.which("powershell.exe") is None,
    reason="Windows PowerShell unavailable",
)
def test_n1_powershell_wrapper_forwards_every_required_parameter(
    tmp_path: Path,
) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    fixture_script = fixture.project_root / "scripts/phase04_5_stage_annotation_corrections.py"
    fixture_script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PYTHON_SCRIPT, fixture_script)

    env = _python_env()
    env["FLEETVISION_PYTHON"] = sys.executable
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(POWERSHELL_WRAPPER),
            "-ProjectRoot",
            str(fixture.project_root),
            "-Config",
            str(fixture.config_path),
            "-CompletedReviewWorkspace",
            str(fixture.completed_review_root),
            "-Timestamp",
            "20260715_031000001",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = _last_json_line(result.stdout)
    assert payload["classification"] == (
        "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED"
    )


@pytest.mark.skipif(
    shutil.which("powershell.exe") is None,
    reason="Windows PowerShell unavailable",
)
def test_n1_powershell_wrapper_parses_with_windows_powershell() -> None:
    command = (
        "$Errors = $null; "
        "[System.Management.Automation.Language.Parser]::ParseFile("
        f"'{str(POWERSHELL_WRAPPER).replace("'", "''")}',"
        "[ref]$null,[ref]$Errors) | Out-Null; "
        "if ($Errors.Count -ne 0) { $Errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_runbook_marks_production_n1_command_not_authorized() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "NOT AUTHORIZED BY IMPLEMENTATION PLAN" in text
    assert "phase04_5_stage_annotation_corrections.ps1" in text
    assert "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED" in text
    assert "N1 PASS does not authorize N2" in text


@dataclass(frozen=True)
class _CliPromotionFixture:
    project_root: Path
    config_path: Path
    n1_workspace_root: Path
    canonical_path: Path
    source_sha256: str
    staged_sha256: str
    repository_head: str
    authorization_phrase: str


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, (
        f"git {' '.join(args)} failed ({result.returncode})\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    return result.stdout.strip()


def _initialize_cli_git_repository(project_root: Path, remote_root: Path) -> str:
    test_sentinel = (
        project_root
        / "dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1"
        / "canonical_coco/test/_annotations.coco.json"
    )
    if test_sentinel.exists():
        test_sentinel.unlink()
        parent = test_sentinel.parent
        while parent != project_root and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent

    _run_git(project_root, "init")
    _run_git(project_root, "config", "user.email", "fleetvision-cli-tests@example.invalid")
    _run_git(project_root, "config", "user.name", "FleetVision CLI Tests")
    _run_git(project_root, "checkout", "-b", "main")
    _run_git(project_root, "add", "configs", "dataset")
    _run_git(project_root, "commit", "-m", "fixture baseline")
    subprocess.run(
        ["git", "init", "--bare", str(remote_root)],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    _run_git(project_root, "remote", "add", "origin", str(remote_root))
    _run_git(project_root, "push", "-u", "origin", "main")
    return _run_git(project_root, "rev-parse", "HEAD")


def _build_cli_promotion_fixture(
    tmp_path: Path,
    *,
    n1_timestamp: str,
) -> _CliPromotionFixture:
    fixture = build_phase04_5n_fixture(tmp_path)
    config = load_phase04_5n_config(fixture.config_path, fixture.project_root)
    staged = prepare_staged_correction_workspace(
        config,
        fixture.completed_review_root,
        timestamp=n1_timestamp,
    )
    repository_head = _initialize_cli_git_repository(
        fixture.project_root,
        tmp_path / "origin.git",
    )
    return _CliPromotionFixture(
        project_root=fixture.project_root,
        config_path=fixture.config_path,
        n1_workspace_root=staged.workspace_root,
        canonical_path=fixture.canonical_valid_coco,
        source_sha256=staged.source_coco_sha256,
        staged_sha256=staged.staged_coco_sha256,
        repository_head=repository_head,
        authorization_phrase=config.n2_authorization_phrase,
    )


def _promotion_cli_command(
    fixture: _CliPromotionFixture,
    *,
    timestamp: str,
    execute: bool,
    authorization_phrase: str | None = None,
) -> list[str]:
    command = [
        sys.executable,
        str(PROMOTION_PYTHON_SCRIPT),
        "--project-root",
        str(fixture.project_root),
        "--config",
        str(fixture.config_path),
        "--n1-workspace",
        str(fixture.n1_workspace_root),
        "--expected-repository-head",
        fixture.repository_head,
        "--expected-canonical-sha256",
        fixture.source_sha256,
        "--expected-staged-sha256",
        fixture.staged_sha256,
        "--authorization-phrase",
        fixture.authorization_phrase if authorization_phrase is None else authorization_phrase,
        "--timestamp",
        timestamp,
    ]
    command.append("--execute" if execute else "--dry-run")
    return command


def test_n2_python_cli_dry_run_is_read_only_and_structured(tmp_path: Path) -> None:
    fixture = _build_cli_promotion_fixture(
        tmp_path,
        n1_timestamp="20260715_050000000",
    )
    before = fixture.canonical_path.read_bytes()
    result = subprocess.run(
        _promotion_cli_command(
            fixture,
            timestamp="20260715_051000000",
            execute=False,
        ),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=_python_env(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert len([line for line in result.stdout.splitlines() if line.strip()]) == 1
    payload = _last_json_line(result.stdout)
    assert payload["outcome"] == "PASS"
    assert payload["classification"] == "PHASE_04_5N_PROMOTION_PREFLIGHT_VALIDATED"
    assert payload["execute"] is False
    assert payload["canonical_before_sha256"] == fixture.source_sha256
    assert payload["staged_coco_sha256"] == fixture.staged_sha256
    assert fixture.canonical_path.read_bytes() == before
    assert not Path(str(payload["evidence_workspace_root"])).exists()


def test_n2_python_cli_defaults_to_dry_run(tmp_path: Path) -> None:
    fixture = _build_cli_promotion_fixture(
        tmp_path,
        n1_timestamp="20260715_050000010",
    )
    command = _promotion_cli_command(
        fixture,
        timestamp="20260715_051000010",
        execute=False,
    )
    command.remove("--dry-run")
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=_python_env(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = _last_json_line(result.stdout)
    assert payload["classification"] == "PHASE_04_5N_PROMOTION_PREFLIGHT_VALIDATED"
    assert payload["execute"] is False


def test_n2_python_cli_execute_promotes_only_fixture_canonical(tmp_path: Path) -> None:
    fixture = _build_cli_promotion_fixture(
        tmp_path,
        n1_timestamp="20260715_050000020",
    )
    result = subprocess.run(
        _promotion_cli_command(
            fixture,
            timestamp="20260715_051000020",
            execute=True,
        ),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=_python_env(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert len([line for line in result.stdout.splitlines() if line.strip()]) == 1
    payload = _last_json_line(result.stdout)
    assert payload["OUTCOME"] == "PASS"
    assert payload["CLASSIFICATION"] == "PHASE_04_5N_ANNOTATION_CORRECTIONS_PROMOTED"
    assert payload["PROMOTED_ANNOTATION_COUNT"] == 2
    assert sha256_file(fixture.canonical_path) == fixture.staged_sha256
    backup_path = Path(str(payload["backup_path"]))
    assert backup_path.is_file()
    assert sha256_file(backup_path) == fixture.source_sha256


def test_n2_python_cli_returns_one_structured_blocked_json(tmp_path: Path) -> None:
    fixture = _build_cli_promotion_fixture(
        tmp_path,
        n1_timestamp="20260715_050000030",
    )
    result = subprocess.run(
        _promotion_cli_command(
            fixture,
            timestamp="20260715_051000030",
            execute=True,
            authorization_phrase="WRONG_AUTHORIZATION",
        ),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=_python_env(),
    )
    assert result.returncode == 1
    assert result.stdout.strip() == ""
    assert len([line for line in result.stderr.splitlines() if line.strip()]) == 1
    payload = _last_json_line(result.stderr)
    assert payload["outcome"] == "BLOCKED"
    assert payload["classification"] == "PHASE_04_5N_PROMOTION_BLOCKED"
    assert payload["execute"] is True
    assert payload["canonical_coco_modified"] is False


def test_n2_python_adapter_never_performs_git_or_atomic_file_operations() -> None:
    text = PROMOTION_PYTHON_SCRIPT.read_text(encoding="utf-8")
    assert "PromotionRequest" in text
    assert "prepare_promotion_preflight" in text
    assert "execute_atomic_promotion" in text
    assert "subprocess" not in text
    assert "os.replace" not in text
    assert "git " not in text


def test_n2_powershell_wrapper_sets_location_and_forwards_every_argument() -> None:
    text = PROMOTION_POWERSHELL_WRAPPER.read_text(encoding="utf-8-sig")
    assert "Set-Location -LiteralPath $ProjectRoot" in text
    for token in (
        "--project-root",
        "--config",
        "--n1-workspace",
        "--expected-repository-head",
        "--expected-canonical-sha256",
        "--expected-staged-sha256",
        "--authorization-phrase",
        "--timestamp",
        "--dry-run",
        "--execute",
    ):
        assert token in text
    assert "ConvertFrom-Json" not in text
    assert "os.replace" not in text
    assert "git " not in text


def test_n2_powershell_wrapper_omits_empty_authorization_native_argument() -> None:
    text = PROMOTION_POWERSHELL_WRAPPER.read_text(encoding="utf-8-sig")
    assert 'if (-not [string]::IsNullOrEmpty($AuthorizationPhrase))' in text
    assert '$Arguments += @("--authorization-phrase", $AuthorizationPhrase)' in text
    assert '"--authorization-phrase", $AuthorizationPhrase,' not in text


@pytest.mark.skipif(
    shutil.which("powershell.exe") is None,
    reason="Windows PowerShell unavailable",
)
def test_n2_powershell_wrapper_dry_run_end_to_end(tmp_path: Path) -> None:
    fixture = _build_cli_promotion_fixture(
        tmp_path,
        n1_timestamp="20260715_050000040",
    )
    fixture_script = fixture.project_root / "scripts/phase04_5_promote_annotation_corrections.py"
    fixture_script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROMOTION_PYTHON_SCRIPT, fixture_script)
    _run_git(fixture.project_root, "add", "scripts/phase04_5_promote_annotation_corrections.py")
    _run_git(fixture.project_root, "commit", "-m", "add fixture promotion entrypoint")
    _run_git(fixture.project_root, "push", "origin", "main")
    wrapper_repository_head = _run_git(fixture.project_root, "rev-parse", "HEAD")
    before = fixture.canonical_path.read_bytes()

    env = _python_env()
    env["FLEETVISION_PYTHON"] = sys.executable
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PROMOTION_POWERSHELL_WRAPPER),
            "-ProjectRoot",
            str(fixture.project_root),
            "-Config",
            str(fixture.config_path),
            "-N1Workspace",
            str(fixture.n1_workspace_root),
            "-ExpectedRepositoryHead",
            wrapper_repository_head,
            "-ExpectedCanonicalSha256",
            fixture.source_sha256,
            "-ExpectedStagedSha256",
            fixture.staged_sha256,
            "-AuthorizationPhrase",
            "",
            "-Timestamp",
            "20260715_051000040",
            "-DryRun",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = _last_json_line(result.stdout)
    assert payload["classification"] == "PHASE_04_5N_PROMOTION_PREFLIGHT_VALIDATED"
    assert fixture.canonical_path.read_bytes() == before


@pytest.mark.skipif(
    shutil.which("powershell.exe") is None,
    reason="Windows PowerShell unavailable",
)
def test_n2_powershell_wrapper_execute_end_to_end(tmp_path: Path) -> None:
    fixture = _build_cli_promotion_fixture(
        tmp_path,
        n1_timestamp="20260715_050000050",
    )
    fixture_script = fixture.project_root / "scripts/phase04_5_promote_annotation_corrections.py"
    fixture_script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROMOTION_PYTHON_SCRIPT, fixture_script)
    _run_git(fixture.project_root, "add", "scripts/phase04_5_promote_annotation_corrections.py")
    _run_git(fixture.project_root, "commit", "-m", "add fixture promotion entrypoint")
    _run_git(fixture.project_root, "push", "origin", "main")
    wrapper_repository_head = _run_git(fixture.project_root, "rev-parse", "HEAD")

    env = _python_env()
    env["FLEETVISION_PYTHON"] = sys.executable
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PROMOTION_POWERSHELL_WRAPPER),
            "-ProjectRoot",
            str(fixture.project_root),
            "-Config",
            str(fixture.config_path),
            "-N1Workspace",
            str(fixture.n1_workspace_root),
            "-ExpectedRepositoryHead",
            wrapper_repository_head,
            "-ExpectedCanonicalSha256",
            fixture.source_sha256,
            "-ExpectedStagedSha256",
            fixture.staged_sha256,
            "-AuthorizationPhrase",
            fixture.authorization_phrase,
            "-Timestamp",
            "20260715_051000050",
            "-Execute",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = _last_json_line(result.stdout)
    assert payload["CLASSIFICATION"] == "PHASE_04_5N_ANNOTATION_CORRECTIONS_PROMOTED"
    assert sha256_file(fixture.canonical_path) == fixture.staged_sha256


@pytest.mark.skipif(
    shutil.which("powershell.exe") is None,
    reason="Windows PowerShell unavailable",
)
def test_n2_powershell_wrapper_preserves_zero_exit_with_native_stderr(
    tmp_path: Path,
) -> None:
    fixture = build_phase04_5n_fixture(tmp_path)
    stub = fixture.project_root / "scripts/phase04_5_promote_annotation_corrections.py"
    stub.parent.mkdir(parents=True, exist_ok=True)
    stub.write_text(
        "import json, sys\n"
        "print('diagnostic on stderr', file=sys.stderr)\n"
        "print(json.dumps({'outcome': 'PASS', 'classification': 'STUB_PASS'}))\n",
        encoding="utf-8",
    )
    env = _python_env()
    env["FLEETVISION_PYTHON"] = sys.executable
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PROMOTION_POWERSHELL_WRAPPER),
            "-ProjectRoot",
            str(fixture.project_root),
            "-Config",
            str(fixture.config_path),
            "-N1Workspace",
            str(fixture.completed_review_root),
            "-ExpectedRepositoryHead",
            "0" * 40,
            "-ExpectedCanonicalSha256",
            "0" * 64,
            "-ExpectedStagedSha256",
            "1" * 64,
            "-AuthorizationPhrase",
            "",
            "-Timestamp",
            "20260715_051000060",
            "-DryRun",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "diagnostic on stderr" in result.stderr
    assert _last_json_line(result.stdout)["classification"] == "STUB_PASS"


@pytest.mark.skipif(
    shutil.which("powershell.exe") is None,
    reason="Windows PowerShell unavailable",
)
def test_n1_and_n2_wrappers_parse_with_windows_powershell() -> None:
    quoted_paths = [
        str(POWERSHELL_WRAPPER).replace("'", "''"),
        str(PROMOTION_POWERSHELL_WRAPPER).replace("'", "''"),
    ]
    parse_calls = "; ".join(
        "[System.Management.Automation.Language.Parser]::ParseFile("
        f"'{path}',[ref]$null,[ref]$Errors) | Out-Null"
        for path in quoted_paths
    )
    command = (
        "$Errors = @(); "
        + parse_calls
        + "; if ($Errors.Count -ne 0) { $Errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_runbook_contains_n2_preflight_and_explicit_authorization_stop() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "N2 read-only preflight" in text
    assert "PHASE_04_5N_2_CANONICAL_PROMOTION_AUTHORIZED" in text
    assert "Paste the exact verified N1 PASS workspace path" in text
    assert "must never infer the latest workspace automatically" in text
    assert "PRODUCTION N2 EXECUTE IS NOT AUTHORIZED BY IMPLEMENTATION PLAN" in text
