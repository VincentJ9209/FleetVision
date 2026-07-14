# Phase 04.5L Completed Review Findings Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement, test, and document the read-only Phase 04.5L F1/F2 findings-analysis workflow that validates the frozen 130-case completed review, creates a controlled severity-scope review package, validates all scope classifications, and produces deterministic findings and advisory recommendations without reading test data or mutating any governed data/model asset.

**Architecture:** Add one focused findings-analysis module beside the existing `validation_error_human_review.py` workflow. The new module reuses the existing canonical exporter, validator, summarizer, fingerprints, and schemas; adds a minimal backward-compatible seam so summary outputs can be written to the analysis workspace while assets remain in a verified snapshot; and implements two explicit orchestration entry points: F1 package creation and F2 final analysis. All generated artifacts remain in a timestamped no-overwrite workspace outside the repository.

**Tech Stack:** Python 3.10+, pandas, openpyxl 3.1.5, PyYAML, pytest, Windows PowerShell 5.1, Git CLI.

## Global Constraints

- Repository root: `G:\Project\FleetVision`.
- Production branch: `main`.
- Current remotely verified design checkpoint: `420b6a32d1a8a8f43b6eb0ec9ae7d43339a14ae3` (`docs: specify phase04.5L completed review findings analysis`).
- The executor must freshly verify local HEAD = `origin/main` = GitHub remote HEAD before every repository write and before F1/F2 execution.
- Permitted worktree states: clean; or only `?? outputs/metadata/external_assets/` and descendants.
- Protected path `outputs/metadata/external_assets/` must never be staged, committed, deleted, cleaned, moved, or rewritten.
- `TEST_SPLIT_READ: NO`.
- `MODEL_INFERENCE_EXECUTED: NO`.
- `ANNOTATION_MODIFIED: NO`.
- `TRAINING_STARTED: NO`.
- `RETRAINING_STATUS: NOT_YET_APPROVED`.
- `DEPLOYMENT_ACCEPTANCE: NOT_YET_APPROVED`.
- Do not rerun completed Workbook export.
- Do not overwrite, open-and-save, or manually edit the frozen Completed Workbook.
- Do not modify the source Workbook, frozen package, SQLite state, audit event log, backups, GT, canonical COCO, raw datasets, Registry, or fixed splits.
- Threshold `0.20` remains `BALANCED_VALIDATION_THRESHOLD_CANDIDATE`; it is not a deployment threshold.
- Catastrophic cases must be preserved as out-of-scope/OOD governance material; they must not be deleted.
- Generated Workbooks, CSVs, extracted images, reports, and Gate evidence remain outside the repository and are not committed.
- Repository staging must use exact paths only. Never use `git add .`, `git add -A`, `git reset --hard`, or `git clean`.
- **Current authorization stop:** this document authorizes planning only. Do not execute implementation Task 1 onward, F1, or F2 until Vincent explicitly authorizes implementation after local Git reconciliation.

---

## Repository-backed context and detected reconciliation issue

The controlling current-state files are `PROJECT_STATUS.md` and `HANDOFF_CURRENT.md`: Phase 04.5L completed review is 130/130, pending 0, adjudication 0, and the next Gate is `PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS`.

Before implementation, reconcile these stale secondary records in a separately authorized docs-only checkpoint:

- `docs/00_project_management/MASTER_PHASE_MAP.md` still states the formal review Workbook is not created and the next Gate is 04.5L-3 package preparation.
- `docs/00_project_management/phase_logs/PHASE_04_5_LOG.md` ends at 04.5L-2C and does not record completed review/export or the current findings-analysis Gate.

Do not silently combine this governance repair with code implementation unless the implementation authorization explicitly includes it.

## File responsibility map

### Create

- `configs/data/phase04_5l_completed_review_findings_config.yaml` — immutable input identities, workspace layout, scope controlled values, and deterministic recommendation thresholds.
- `src/fleetvision/data/validation_error_review_findings.py` — F1/F2 domain logic, Git/artifact preflight, snapshot handling, scope Workbook validation/export, final analysis, and evidence manifests.
- `scripts/phase04_5_run_completed_review_findings_f1.py` — thin Python F1 CLI wrapper.
- `scripts/phase04_5_run_completed_review_findings_f2.py` — thin Python F2 CLI wrapper.
- `scripts/phase04_5_run_completed_review_findings_f1.ps1` — Windows PowerShell 5.1 launcher.
- `scripts/phase04_5_run_completed_review_findings_f2.ps1` — Windows PowerShell 5.1 launcher.
- `tests/test_validation_error_review_findings.py` — focused unit/integration/CLI-contract tests.
- `docs/01_phase_guides/phase_04_5_completed_review_findings_analysis.md` — operator guide and F1/F2 hold points.

### Modify

- `src/fleetvision/data/validation_error_human_review.py` — add a public validation-report writer and an optional `asset_root` parameter to the existing summarizer; preserve every existing call path.
- `tests/test_validation_error_human_review.py` — lock backward compatibility for the two new seams.

### Modify only in separately authorized governance checkpoints

- `docs/00_project_management/MASTER_PHASE_MAP.md`
- `docs/00_project_management/phase_logs/PHASE_04_5_LOG.md`
- `docs/00_project_management/PROJECT_STATUS.md`
- `docs/00_project_management/HANDOFF_CURRENT.md`
- `docs/00_project_management/DECISION_LOG.md` only if the approved scope/recommendation policy is promoted into a durable ADR.

---

### Task 0: Reconcile local Git facts and governance prerequisites

**Files:**
- No implementation file changes.
- Separately authorized governance repair: `docs/00_project_management/MASTER_PHASE_MAP.md`, `docs/00_project_management/phase_logs/PHASE_04_5_LOG.md`.

**Interfaces:**
- Consumes: remote checkpoint `420b6a32d1a8a8f43b6eb0ec9ae7d43339a14ae3` and the repository startup protocol.
- Produces: a proven clean/synchronized local base and, if authorized, a docs-only governance reconciliation checkpoint.

- [ ] **Step 1: Verify the repository and live refs in Windows PowerShell 5.1**

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location -LiteralPath "G:\Project\FleetVision"

git fetch origin main
if ($LASTEXITCODE -ne 0) { throw "git fetch failed" }

$Branch = (git branch --show-current).Trim()
$LocalHead = (git rev-parse HEAD).Trim()
$OriginMain = (git rev-parse origin/main).Trim()
$RemoteHead = ((git ls-remote origin refs/heads/main) -split "`t")[0].Trim()
$Status = @(git status --short --untracked-files=all)

[pscustomobject]@{
    Branch = $Branch
    LocalHead = $LocalHead
    OriginMain = $OriginMain
    RemoteHead = $RemoteHead
    Status = ($Status -join "`n")
} | Format-List
```

Expected before copying/committing this plan into the repository:

```text
Branch     : main
LocalHead  : 420b6a32d1a8a8f43b6eb0ec9ae7d43339a14ae3
OriginMain : 420b6a32d1a8a8f43b6eb0ec9ae7d43339a14ae3
RemoteHead : 420b6a32d1a8a8f43b6eb0ec9ae7d43339a14ae3
Status     : <blank, or only ?? outputs/metadata/external_assets/...>
```

- [ ] **Step 2: Fail closed on any unexpected worktree entry**

```powershell
$Unexpected = @(
    $Status | Where-Object {
        $_ -notmatch '^\?\? outputs/metadata/external_assets(?:/|\\|$)'
    }
)
if ($Unexpected.Count -gt 0) {
    throw "Unexpected worktree entries block planning/implementation: $($Unexpected -join '; ')"
}
if ($Branch -ne "main") { throw "Expected branch main; got $Branch" }
if (($LocalHead -ne $OriginMain) -or ($LocalHead -ne $RemoteHead)) {
    throw "HEAD mismatch: local=$LocalHead origin/main=$OriginMain remote=$RemoteHead"
}
```

- [ ] **Step 3: Copy this plan to its canonical repository path**

```powershell
$SourcePlan = "<downloaded-plan-path>\2026-07-14-phase04-5l-completed-review-findings-analysis.md"
$TargetPlan = "docs\superpowers\plans\2026-07-14-phase04-5l-completed-review-findings-analysis.md"

if (Test-Path -LiteralPath $TargetPlan) {
    throw "Plan already exists; overwrite is forbidden: $TargetPlan"
}
Copy-Item -LiteralPath $SourcePlan -Destination $TargetPlan
```

- [ ] **Step 4: Validate and commit only the plan file**

```powershell
git diff --check -- $TargetPlan
if ($LASTEXITCODE -ne 0) { throw "git diff --check failed" }

git add -- $TargetPlan
$Staged = @(git diff --cached --name-only)
if (($Staged.Count -ne 1) -or ($Staged[0] -ne $TargetPlan.Replace('\','/'))) {
    throw "Unexpected staged files: $($Staged -join ', ')"
}

git commit -m "docs: plan phase04.5L completed review findings analysis"
if ($LASTEXITCODE -ne 0) { throw "plan commit failed" }

git push origin main
if ($LASTEXITCODE -ne 0) { throw "plan push failed" }
```

- [ ] **Step 5: Re-verify local/origin/remote equality after the plan commit**

Run the commands from Step 1 again.

Expected: all three SHA values equal the new plan commit; worktree is clean or protected-untracked-only.

- [ ] **Step 6: Obtain explicit authorization for the docs-only stale-state reconciliation**

Do not edit `MASTER_PHASE_MAP.md` or `PHASE_04_5_LOG.md` until this authorization is explicit. The reconciliation must record the completed 130/130 review, frozen artifact hashes, current Gate, and the planning checkpoint without changing any data/model acceptance state.

---

### Task 1: Add backward-compatible seams to the existing completed-review workflow

**Files:**
- Modify: `src/fleetvision/data/validation_error_human_review.py:1235-1420` (validation output writer and summarizer area; resolve exact lines in the implementation checkout).
- Modify: `tests/test_validation_error_human_review.py`.

**Interfaces:**
- Consumes: existing `ValidationResult`, `validate_canonical_dataframe`, and `summarize_canonical_review` behavior.
- Produces:
  - `write_validation_outputs(result: ValidationResult, report_json: Path, errors_csv: Path) -> None`
  - `summarize_canonical_review(..., *, asset_root: Path | None = None) -> SummaryResult`

- [ ] **Step 1: Write failing compatibility tests**

Append these tests to `tests/test_validation_error_human_review.py`:

```python
def test_public_validation_output_writer_preserves_no_overwrite(tmp_path: Path) -> None:
    config, prepared, _ = _prepare(tmp_path)
    _complete_workbook(prepared.workbook_path)
    canonical_csv = tmp_path / "canonical.csv"
    export_review_workbook(config, prepared.workbook_path, canonical_csv)
    result = validate_canonical_csv(
        config,
        canonical_csv,
        workbook_path=prepared.workbook_path,
        batch_root=prepared.batch_root,
    )

    report_json = tmp_path / "reports" / "validation_report.json"
    errors_csv = tmp_path / "reports" / "validation_errors.csv"
    review_module.write_validation_outputs(result, report_json, errors_csv)

    assert json.loads(report_json.read_text(encoding="utf-8"))["classification"] == (
        "VALIDATION_ERROR_HUMAN_REVIEW_VERIFIED"
    )
    assert errors_csv.is_file()
    with pytest.raises(HumanReviewError, match="overwrite is forbidden"):
        review_module.write_validation_outputs(result, report_json, errors_csv)


def test_summarizer_can_separate_output_root_from_asset_root(tmp_path: Path) -> None:
    config, prepared, _ = _prepare(tmp_path)
    _complete_workbook(prepared.workbook_path)
    canonical_csv = tmp_path / "canonical.csv"
    export_review_workbook(config, prepared.workbook_path, canonical_csv)

    output_root = tmp_path / "analysis_workspace"
    output_root.mkdir()
    result = summarize_canonical_review(
        config,
        canonical_csv,
        output_root,
        asset_root=prepared.batch_root,
    )

    assert result.action_count == 2
    assert (output_root / "reports" / "review_summary.json").is_file()
    assert not (prepared.batch_root / "reports" / "review_summary.json").exists()
```

- [ ] **Step 2: Run the two tests and verify they fail for the intended reasons**

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_validation_error_human_review.py::test_public_validation_output_writer_preserves_no_overwrite `
  tests/test_validation_error_human_review.py::test_summarizer_can_separate_output_root_from_asset_root `
  -v
```

Expected: one failure because `write_validation_outputs` is absent; one failure because `asset_root` is not accepted.

- [ ] **Step 3: Add the minimal public writer and optional asset root**

In `src/fleetvision/data/validation_error_human_review.py`, add immediately after `_write_validation_outputs`:

```python
def write_validation_outputs(
    result: ValidationResult,
    report_json: Path,
    errors_csv: Path,
) -> None:
    """Write deterministic validation evidence without overwriting outputs."""

    _write_validation_outputs(result, report_json, errors_csv)
```

Change the summarizer signature and validation call to:

```python
def summarize_canonical_review(
    config: ReviewConfig,
    canonical_csv: Path,
    batch_root: Path,
    *,
    asset_root: Path | None = None,
) -> SummaryResult:
    """Create summary, action queue, and non-applied annotation proposals."""

    batch_root = batch_root.resolve()
    resolved_asset_root = (
        asset_root.resolve() if asset_root is not None else batch_root
    )
    frame = _load_csv(canonical_csv, CANONICAL_COLUMNS)
    validation = validate_canonical_dataframe(
        frame,
        config,
        require_complete=True,
        batch_root=resolved_asset_root,
    )
```

Do not change any output paths or existing default behavior.

- [ ] **Step 4: Re-run the focused tests**

Expected: `2 passed`.

- [ ] **Step 5: Run the entire existing human-review test module**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_error_human_review.py -v
```

Expected: all tests in the module pass with no new skips or failures.

- [ ] **Step 6: Commit this compatibility seam as an isolated checkpoint**

```powershell
git add -- `
  src/fleetvision/data/validation_error_human_review.py `
  tests/test_validation_error_human_review.py

git commit -m "refactor: expose phase04.5L findings workflow seams"
```

---

### Task 2: Define the immutable findings-analysis configuration and contracts

**Files:**
- Create: `configs/data/phase04_5l_completed_review_findings_config.yaml`.
- Create: `src/fleetvision/data/validation_error_review_findings.py`.
- Create: `tests/test_validation_error_review_findings.py`.

**Interfaces:**
- Consumes: `CANONICAL_COLUMNS`, `ReviewConfig`, `HumanReviewError`, `load_config`, `sha256_file`, `read_workbook_dataframe`, and `logical_fingerprint` from the existing module.
- Produces: `FindingsConfig`, `ScopeValidationResult`, `RecommendationResult`, and immutable schema constants.

- [ ] **Step 1: Add the exact YAML configuration**

Create `configs/data/phase04_5l_completed_review_findings_config.yaml`:

```yaml
schema_version: "1"

existing_review_config: configs/data/validation_error_human_review_config.yaml
expected_validator_classification: VALIDATION_ERROR_HUMAN_REVIEW_VERIFIED

repository:
  branch: main
  protected_untracked_path: outputs/metadata/external_assets/

completed_review:
  workbook_path: 'G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_review_workspace\exports\validation_error_human_review_completed.xlsx'
  workbook_size_bytes: 31871231
  workbook_sha256: C9DF0A38B115406791DF03BFDC714901A66A47BE95CE0E2047E573FCC8D6FB6C
  logical_fingerprint: F87882E8F6DBF20B6603FC5106BE5A78BD61E4A22A6500E9586E51498B4AAC35
  source_workbook_path: 'G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1\workbook\validation_error_human_review.xlsx'
  source_workbook_sha256: 5DC9C1FDA69865D36C60EACB90A0AEA0FC9F4B263F30281723BB0E1172549DE5
  frozen_package_path: 'G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_PACKAGE.zip'
  frozen_package_sha256: 6D6243FE8F3E12910C03A5EDCFF178CE20B180473EED43DED2B36301A877B42A
  review_cases: 130
  reviewed: 130
  pending: 0
  needs_adjudication: 0
  reviewer: Vincent
  export_classification: LOCAL_REVIEW_APP_COMPLETED_WORKBOOK_EXPORTED

workspace:
  parent_dir: 'G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_review_workspace\analysis'
  prefix: phase04_5l_completed_review_findings
  canonical_filename: validation_error_human_review.csv
  scope_workbook_filename: severity_scope_review.xlsx
  scope_source_filename: severity_scope_review_source.csv
  scope_asset_manifest_filename: scope_asset_manifest.csv
  scope_export_filename: severity_scope_classification.csv

scope_options:
  scope_review_status:
    - pending
    - reviewed
    - needs_adjudication
  scope_group:
    - IN_SCOPE_LIGHT_MODERATE
    - BOUNDARY_HEAVY_DAMAGE
    - OUT_OF_SCOPE_CATASTROPHIC
  scope_reason:
    - light_surface_damage
    - moderate_external_damage
    - heavy_external_damage
    - structural_damage
    - catastrophic_collision
    - extensive_multi_panel_damage
    - vehicle_integrity_compromised
    - insufficient_visual_evidence
    - other
  operability:
    - drivable_or_likely_drivable
    - uncertain
    - non_drivable_or_likely_non_drivable
  scope_confidence:
    - high
    - medium
    - low

recommendation_rules:
  additional_review_low_confidence_share: 0.10
  scope_rebalancing_non_scope_share: 0.20
  distribution_total_variation_threshold: 0.10
  threshold_tradeoff_share_delta: 0.10
  retraining_in_scope_priority_share: 0.30
  retraining_in_scope_confirmed_error_share: 0.30

safety:
  test_split_read: false
  model_inference_executed: false
  annotation_modified: false
  training_started: false
  retraining_status: NOT_YET_APPROVED
  deployment_acceptance: NOT_YET_APPROVED
```

Before implementation, verify the `source_workbook_path` against the frozen package layout. If the authoritative file is at a different path, update only the path string after proving its SHA256 remains `5DC9...9DE5`; do not infer or search by opening/saving the Workbook.

- [ ] **Step 2: Write configuration-contract tests**

Create the test module with imports and these tests:

```python
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

import fleetvision.data.validation_error_review_findings as findings


def _write_config(tmp_path: Path) -> Path:
    payload = yaml.safe_load(
        Path("configs/data/phase04_5l_completed_review_findings_config.yaml")
        .read_text(encoding="utf-8")
    )
    payload["completed_review"]["workbook_path"] = str(tmp_path / "completed.xlsx")
    payload["completed_review"]["source_workbook_path"] = str(tmp_path / "source.xlsx")
    payload["completed_review"]["frozen_package_path"] = str(tmp_path / "package.zip")
    payload["workspace"]["parent_dir"] = str(tmp_path / "analysis")
    path = tmp_path / "findings.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_load_findings_config_has_exact_scope_contract(tmp_path: Path) -> None:
    config = findings.load_findings_config(_write_config(tmp_path), Path.cwd())
    assert config.expected_case_count == 130
    assert config.scope_options["scope_group"] == (
        "IN_SCOPE_LIGHT_MODERATE",
        "BOUNDARY_HEAVY_DAMAGE",
        "OUT_OF_SCOPE_CATASTROPHIC",
    )
    assert config.retraining_status == "NOT_YET_APPROVED"
    assert config.deployment_acceptance == "NOT_YET_APPROVED"


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("test_split_read", True),
        ("model_inference_executed", True),
        ("annotation_modified", True),
        ("training_started", True),
    ],
)
def test_load_findings_config_rejects_enabled_prohibited_boundary(
    tmp_path: Path,
    key: str,
    value: bool,
) -> None:
    path = _write_config(tmp_path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["safety"][key] = value
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(findings.FindingsAnalysisError, match=key):
        findings.load_findings_config(path, Path.cwd())
```

- [ ] **Step 3: Run tests and confirm import/config failures**

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_validation_error_review_findings.py `
  -k "load_findings_config" -v
```

Expected: collection/import failure because the module does not exist.

- [ ] **Step 4: Create the module contracts and strict config loader**

The new module must begin with these exact public contracts:

```python
"""Read-only Phase 04.5L completed-review findings analysis."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping, Sequence

import pandas as pd
import yaml
from openpyxl import Workbook, load_workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font, PatternFill, Protection
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

from fleetvision.data.validation_error_human_review import (
    CANONICAL_COLUMNS,
    HumanReviewError,
    ReviewConfig,
    export_review_workbook,
    load_config as load_existing_review_config,
    logical_fingerprint,
    read_workbook_dataframe,
    sha256_file,
    summarize_canonical_review,
    validate_canonical_csv,
    write_validation_outputs,
)

DEFAULT_CONFIG_PATH = Path(
    "configs/data/phase04_5l_completed_review_findings_config.yaml"
)

SCOPE_COLUMNS = (
    "scope_review_status",
    "scope_group",
    "scope_reason",
    "operability",
    "scope_confidence",
    "scope_reviewer_notes",
    "scope_reviewer",
    "scope_reviewed_at_utc",
)
SCOPE_EXPORT_COLUMNS = CANONICAL_COLUMNS + SCOPE_COLUMNS
SCOPE_WORKBOOK_SHEETS = (
    "Instructions",
    "Scope_Review",
    "Option_Lists",
    "Manifest",
    "Progress_Summary",
)
PRIMARY_RECOMMENDATIONS = (
    "NO_RETRAINING_RECOMMENDED",
    "DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING",
    "SCOPE_REBALANCING_REQUIRED_BEFORE_RETRAINING",
    "RETRAINING_PROPOSAL_JUSTIFIED",
    "ADDITIONAL_REVIEW_REQUIRED",
)


class FindingsAnalysisError(RuntimeError):
    """Raised when a findings-analysis safety or data contract fails."""


@dataclass(frozen=True)
class FindingsConfig:
    project_root: Path
    existing_review_config_path: Path
    expected_validator_classification: str
    expected_branch: str
    protected_untracked_path: str
    completed_workbook: Path
    completed_workbook_size: int
    completed_workbook_sha256: str
    completed_logical_fingerprint: str
    source_workbook: Path
    source_workbook_sha256: str
    frozen_package: Path
    frozen_package_sha256: str
    expected_case_count: int
    expected_reviewer: str
    expected_export_classification: str
    workspace_parent: Path
    workspace_prefix: str
    canonical_filename: str
    scope_workbook_filename: str
    scope_source_filename: str
    scope_asset_manifest_filename: str
    scope_export_filename: str
    scope_options: Mapping[str, tuple[str, ...]]
    recommendation_rules: Mapping[str, float]
    retraining_status: str
    deployment_acceptance: str


@dataclass(frozen=True)
class RepositoryState:
    branch: str
    local_head: str
    origin_main: str
    remote_head: str
    unexpected_status: tuple[str, ...]


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path
    completed_snapshot: Path
    package_snapshot: Path
    extracted_package: Path
    canonical_csv: Path
    validation_report: Path
    validation_errors: Path
    scope_workbook: Path
    scope_source_csv: Path
    scope_asset_manifest: Path
    scope_export_csv: Path


@dataclass(frozen=True)
class ScopeValidationResult:
    passed: bool
    row_count: int
    issue_count: int
    issues: tuple[dict[str, str], ...]
    counts: Mapping[str, int]


@dataclass(frozen=True)
class RecommendationResult:
    primary: str
    reasons: tuple[str, ...]
    metrics: Mapping[str, float]
```

Implement `load_findings_config(config_path, project_root)` with these non-negotiable validations:

- all three expected hashes are exactly 64 uppercase hexadecimal characters;
- expected case count is exactly 130;
- `scope_group`, `scope_reason`, `operability`, `scope_confidence`, and `scope_review_status` equal the approved controlled sets without blanks or duplicates;
- every recommendation threshold is in `[0.0, 1.0]`;
- all four prohibited booleans are false;
- retraining and deployment states equal `NOT_YET_APPROVED`;
- `expected_validator_classification` equals `VALIDATION_ERROR_HUMAN_REVIEW_VERIFIED`;
- paths are resolved without changing their content.

- [ ] **Step 5: Run configuration tests**

Expected: all config tests pass.

- [ ] **Step 6: Commit the config/contracts checkpoint**

```powershell
git add -- `
  configs/data/phase04_5l_completed_review_findings_config.yaml `
  src/fleetvision/data/validation_error_review_findings.py `
  tests/test_validation_error_review_findings.py

git commit -m "feat: define phase04.5L findings analysis contracts"
```

---

### Task 3: Implement Git preflight, authoritative hash verification, and no-overwrite workspace snapshots

**Files:**
- Modify: `src/fleetvision/data/validation_error_review_findings.py`.
- Modify: `tests/test_validation_error_review_findings.py`.

**Interfaces:**
- Produces:
  - `inspect_repository_state(project_root, expected_head, runner=None) -> RepositoryState`
  - `verify_authoritative_inputs(config) -> dict[str, dict[str, str]]`
  - `create_workspace(config, timestamp=None) -> WorkspacePaths`
  - `snapshot_authoritative_inputs(config, paths) -> Path` returning the extracted package asset root.

- [ ] **Step 1: Add repository-state tests with an injected Git runner**

```python
def test_repository_state_requires_all_heads_equal_and_allowed_status(tmp_path: Path) -> None:
    head = "a" * 40
    outputs = {
        ("branch", "--show-current"): "main\n",
        ("rev-parse", "HEAD"): f"{head}\n",
        ("rev-parse", "origin/main"): f"{head}\n",
        ("ls-remote", "origin", "refs/heads/main"): f"{head}\trefs/heads/main\n",
        ("status", "--porcelain=v1", "--untracked-files=all"): (
            "?? outputs/metadata/external_assets/source.bin\n"
        ),
    }

    def runner(args: Sequence[str], cwd: Path) -> str:
        return outputs[tuple(args)]

    state = findings.inspect_repository_state(tmp_path, head, runner=runner)
    assert state.local_head == head
    assert state.unexpected_status == ()


def test_repository_state_blocks_unexpected_worktree_entry(tmp_path: Path) -> None:
    head = "b" * 40

    def runner(args: Sequence[str], cwd: Path) -> str:
        mapping = {
            ("branch", "--show-current"): "main\n",
            ("rev-parse", "HEAD"): f"{head}\n",
            ("rev-parse", "origin/main"): f"{head}\n",
            ("ls-remote", "origin", "refs/heads/main"): f"{head}\trefs/heads/main\n",
            ("status", "--porcelain=v1", "--untracked-files=all"): " M dataset/01_raw/a.jpg\n",
        }
        return mapping[tuple(args)]

    with pytest.raises(findings.FindingsAnalysisError, match="unexpected worktree"):
        findings.inspect_repository_state(tmp_path, head, runner=runner)
```

Add separate tests for branch mismatch and local/origin/remote SHA mismatch.

- [ ] **Step 2: Implement the exact Git preflight**

```python
GitRunner = Callable[[Sequence[str], Path], str]


def _run_git(args: Sequence[str], cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise FindingsAnalysisError(
            f"git {' '.join(args)} failed: {completed.stderr.strip()}"
        )
    return completed.stdout


def inspect_repository_state(
    project_root: Path,
    expected_head: str,
    *,
    runner: GitRunner | None = None,
) -> RepositoryState:
    resolved = project_root.resolve()
    command = runner or _run_git
    branch = command(("branch", "--show-current"), resolved).strip()
    local_head = command(("rev-parse", "HEAD"), resolved).strip()
    origin_main = command(("rev-parse", "origin/main"), resolved).strip()
    remote_line = command(
        ("ls-remote", "origin", "refs/heads/main"), resolved
    ).strip()
    remote_head = remote_line.split()[0] if remote_line else ""
    status_lines = tuple(
        line
        for line in command(
            ("status", "--porcelain=v1", "--untracked-files=all"),
            resolved,
        ).splitlines()
        if line.strip()
    )
    allowed_prefix = "outputs/metadata/external_assets/"
    unexpected = tuple(
        line
        for line in status_lines
        if not (
            line.startswith("?? ")
            and line[3:].replace("\\", "/").startswith(allowed_prefix)
        )
    )
    if branch != "main":
        raise FindingsAnalysisError(f"expected branch main; got {branch!r}")
    if not expected_head or len(expected_head) != 40:
        raise FindingsAnalysisError("expected_head must be a 40-character commit SHA")
    if {local_head, origin_main, remote_head} != {expected_head}:
        raise FindingsAnalysisError(
            "repository HEAD mismatch: "
            f"expected={expected_head} local={local_head} "
            f"origin/main={origin_main} remote={remote_head}"
        )
    if unexpected:
        raise FindingsAnalysisError(
            f"unexpected worktree entries block the Gate: {unexpected}"
        )
    return RepositoryState(
        branch=branch,
        local_head=local_head,
        origin_main=origin_main,
        remote_head=remote_head,
        unexpected_status=unexpected,
    )
```

- [ ] **Step 3: Add authoritative-input and no-overwrite tests**

Use fixtures that create three small files, calculate their SHA256 values, update the temporary YAML, and assert:

```python
def test_authoritative_inputs_verify_size_and_hash(tmp_path: Path) -> None:
    config = _make_materialized_findings_config(tmp_path)
    results = findings.verify_authoritative_inputs(config)
    assert set(results) == {"completed_workbook", "source_workbook", "frozen_package"}
    assert all(row["match"] == "true" for row in results.values())


def test_authoritative_hash_mismatch_fails_before_workspace_creation(tmp_path: Path) -> None:
    config = _make_materialized_findings_config(tmp_path)
    config.completed_workbook.write_bytes(b"changed")
    with pytest.raises(findings.FindingsAnalysisError, match="completed_workbook"):
        findings.verify_authoritative_inputs(config)
    assert not config.workspace_parent.exists()


def test_workspace_creation_is_timestamped_and_no_overwrite(tmp_path: Path) -> None:
    config = _make_materialized_findings_config(tmp_path)
    paths = findings.create_workspace(config, timestamp="20260714T120000Z")
    assert paths.root.name == "phase04_5l_completed_review_findings_20260714T120000Z"
    with pytest.raises(findings.FindingsAnalysisError, match="already exists"):
        findings.create_workspace(config, timestamp="20260714T120000Z")
```

- [ ] **Step 4: Implement file verification and workspace creation**

Use uppercase `sha256_file`, exact size checks for the completed Workbook, and `mkdir(parents=True, exist_ok=False)` for the timestamped workspace. `create_workspace` must create only the approved directories from the design plus `evidence/f1_gate_result.json` and `evidence/F1_SHA256SUMS.csv` as later outputs; it must not pre-create output files.

- [ ] **Step 5: Implement safe copy and ZIP extraction**

The extraction helper must reject absolute paths, `..`, and symlinks before writing any member:

```python
def _safe_extract_zip(source_zip: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    root = destination.resolve()
    with zipfile.ZipFile(source_zip, "r") as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise FindingsAnalysisError(f"frozen package CRC failure: {bad_member}")
        for member in archive.infolist():
            pure = PurePosixPath(member.filename.replace("\\", "/"))
            unix_mode = member.external_attr >> 16
            is_symlink = (unix_mode & 0o170000) == 0o120000
            if pure.is_absolute() or ".." in pure.parts or is_symlink:
                raise FindingsAnalysisError(
                    f"unsafe frozen-package member: {member.filename}"
                )
            target = (destination / Path(*pure.parts)).resolve()
            if not target.is_relative_to(root):
                raise FindingsAnalysisError(
                    f"frozen-package member escapes snapshot: {member.filename}"
                )
        archive.extractall(destination)
```

`shutil.copy2` each approved input, then compare source/copy size and SHA256. Never extract the original ZIP directly; extract only the verified copy.

- [ ] **Step 6: Run the Task 3 focused tests**

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_validation_error_review_findings.py `
  -k "repository_state or authoritative or workspace or snapshot or extract" `
  -v
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit the preflight/snapshot checkpoint**

```powershell
git add -- `
  src/fleetvision/data/validation_error_review_findings.py `
  tests/test_validation_error_review_findings.py

git commit -m "feat: add phase04.5L findings preflight and snapshots"
```

---

### Task 4: Implement F1 canonical validation, summarization, and severity-scope package creation

**Files:**
- Modify: `src/fleetvision/data/validation_error_review_findings.py`.
- Modify: `tests/test_validation_error_review_findings.py`.

**Interfaces:**
- Consumes: verified copies, existing canonical export/validator/summarizer, extracted asset root.
- Produces:
  - `run_f1(config, expected_head, timestamp=None, git_runner=None) -> WorkspacePaths`
  - `scope_review/severity_scope_review.xlsx`
  - `scope_review/severity_scope_review_source.csv`
  - `scope_review/scope_asset_manifest.csv`
  - F1 evidence and classification `PHASE_04_5L_COMPLETED_REVIEW_VALIDATED_AND_SCOPE_REVIEW_PACKAGE_CREATED`.

- [ ] **Step 1: Create an end-to-end controlled F1 fixture**

The fixture must reuse the existing review test helpers or reproduce their contracts to create:

- a two-case completed Workbook with valid canonical fields;
- a source Workbook with an independently configured expected SHA;
- a ZIP containing the two original/overlay assets at the canonical relative paths;
- a temporary existing-review config with `expected_case_count=2`;
- a temporary findings config with the same two-case count and hashes.

The fixture must never use a path component named `test` for any split-like asset directory; use `valid_fixture`.

- [ ] **Step 2: Add the F1 orchestration assertions**

```python
def test_run_f1_reuses_existing_validation_and_creates_scope_package(
    tmp_path: Path,
) -> None:
    fixture = _make_f1_fixture(tmp_path)
    result = findings.run_f1(
        fixture.findings_config,
        expected_head="c" * 40,
        timestamp="20260714T120000Z",
        git_runner=fixture.git_runner,
    )

    assert result.canonical_csv.is_file()
    assert result.validation_report.is_file()
    assert result.scope_workbook.is_file()
    assert result.scope_source_csv.is_file()
    assert result.scope_asset_manifest.is_file()

    report = json.loads(result.validation_report.read_text(encoding="utf-8"))
    assert report["classification"] == "VALIDATION_ERROR_HUMAN_REVIEW_VERIFIED"

    gate = json.loads(
        (result.root / "evidence" / "f1_gate_result.json").read_text(
            encoding="utf-8"
        )
    )
    assert gate["classification"] == (
        "PHASE_04_5L_COMPLETED_REVIEW_VALIDATED_AND_SCOPE_REVIEW_PACKAGE_CREATED"
    )
    assert gate["test_split_read"] is False
    assert gate["model_inference_executed"] is False
    assert gate["annotation_modified"] is False
    assert gate["training_started"] is False
```

Add tests that F1 blocks when the completed logical fingerprint differs, when an asset is missing, and when any existing output path already exists.

- [ ] **Step 3: Implement the existing-workflow orchestration in this exact order**

`run_f1` must:

1. call `inspect_repository_state`;
2. call `verify_authoritative_inputs` before workspace creation;
3. create the workspace;
4. snapshot/copy inputs and safely extract the copied package;
5. read only the copied completed Workbook and verify its logical fingerprint;
6. call `export_review_workbook(existing_config, copied_workbook, canonical_csv)`;
7. call `validate_canonical_csv(existing_config, canonical_csv, workbook_path=copied_workbook, batch_root=asset_root)`;
8. require `result.passed` and write `validation_report.json`/`validation_errors.csv` through `write_validation_outputs`;
9. call `summarize_canonical_review(existing_config, canonical_csv, workspace_root, asset_root=asset_root)`;
10. build the scope source CSV, Workbook, and asset manifest;
11. write F1 evidence and checksums;
12. return without attempting scope completion or F2 analysis.

- [ ] **Step 4: Implement scope source rows and immutable fingerprints**

Every `severity_scope_review_source.csv` row must contain all `CANONICAL_COLUMNS`, the eight blank/pending scope fields, and preserve canonical order. Initialize only:

```python
scope_review_status = "pending"
scope_group = ""
scope_reason = ""
operability = ""
scope_confidence = ""
scope_reviewer_notes = ""
scope_reviewer = ""
scope_reviewed_at_utc = ""
```

Write UTF-8-SIG with `lineterminator="\n"`, then read it back and require exact columns and dataframe equality.

- [ ] **Step 5: Implement the scope Workbook**

The Workbook must contain `SCOPE_WORKBOOK_SHEETS` in exact order. `Scope_Review` must contain:

1. `Original Preview`
2. `Overlay Preview`
3. all `SCOPE_EXPORT_COLUMNS`

Requirements:

- preserve source row order exactly;
- lock all canonical/source cells;
- unlock only the eight scope fields;
- add named-range Data Validation for five controlled fields;
- embed scaled original and overlay previews from the extracted snapshot or provide relative `HYPERLINK` formulas if an image cannot be embedded;
- set `scope_review_status=pending` for every row;
- create `Progress_Summary` formulas for total, reviewed, pending, adjudication, and completion rate;
- set workbook recalculation flags;
- save only to the no-overwrite scope output path.

The scope asset manifest columns are:

```text
review_case_id,asset_type,relative_path,size_bytes,sha256
```

Each case must have exactly one `original` and one `overlay` row.

- [ ] **Step 6: Run the F1 tests**

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_validation_error_review_findings.py `
  -k "run_f1 or scope_package or logical_fingerprint or missing_asset" `
  -v
```

Expected: all selected tests pass; no output is written inside the repository fixture root except pytest temporary content.

- [ ] **Step 7: Commit F1 implementation**

```powershell
git add -- `
  src/fleetvision/data/validation_error_review_findings.py `
  tests/test_validation_error_review_findings.py

git commit -m "feat: create phase04.5L F1 scope review package"
```

---

### Task 5: Implement F2 scope semantics, source immutability, and deterministic export

**Files:**
- Modify: `src/fleetvision/data/validation_error_review_findings.py`.
- Modify: `tests/test_validation_error_review_findings.py`.

**Interfaces:**
- Produces:
  - `read_scope_workbook(path) -> pd.DataFrame`
  - `validate_scope_dataframe(frame, source_frame, config) -> ScopeValidationResult`
  - `export_scope_classification(config, workbook_path, source_csv, output_csv) -> ScopeValidationResult`

- [ ] **Step 1: Add parameterized controlled-value and conditional-rule tests**

Create a valid reviewed two-row frame, then parameterize these invalid mutations and expected codes:

```python
@pytest.mark.parametrize(
    ("column", "value", "error_code"),
    [
        ("scope_review_status", "done", "INVALID_SCOPE_CONTROLLED_VALUE"),
        ("scope_group", "HEAVY", "INVALID_SCOPE_CONTROLLED_VALUE"),
        ("scope_reason", "unknown_reason", "INVALID_SCOPE_CONTROLLED_VALUE"),
        ("operability", "broken", "INVALID_SCOPE_CONTROLLED_VALUE"),
        ("scope_confidence", "certain", "INVALID_SCOPE_CONTROLLED_VALUE"),
    ],
)
def test_scope_controlled_values_are_enforced(...):
    ...
```

Add explicit tests for each approved semantic rule:

- reviewed rows require reviewer and timezone-aware timestamp;
- low confidence requires notes;
- `other` reason requires notes;
- catastrophic requires an approved catastrophic reason;
- catastrophic + likely drivable requires notes;
- in-scope cannot use catastrophic collision or integrity-compromised reason;
- insufficient evidence requires low confidence and notes;
- source-field change, row insertion, row deletion, row reorder, duplicate identity, pending, and adjudication each block F2.

- [ ] **Step 2: Implement deterministic scope validation**

Validation must compare the Workbook dataframe to the F1 source CSV by position and by identity. It must report issues with columns:

```text
row_number,error_code,message
```

The source immutability check is exact:

```python
source_columns = list(CANONICAL_COLUMNS)
if not frame.loc[:, source_columns].equals(source_frame.loc[:, source_columns]):
    # additionally locate changed rows/columns for evidence
```

F2 PASS contract:

```text
rows = expected_case_count
unique review_case_id = expected_case_count
scope reviewed = expected_case_count
pending = 0
needs adjudication = 0
invalid controlled values = 0
conditional-rule violations = 0
source-field changes = 0
row insertions = 0
row deletions = 0
row reordering = 0
```

- [ ] **Step 3: Implement transactional UTF-8-SIG export**

Use `tempfile.mkstemp` in the final output directory, write `SCOPE_EXPORT_COLUMNS`, round-trip read, require exact dataframe equality, then `Path.replace`. Delete the staging file on any failure. Refuse when the output already exists.

- [ ] **Step 4: Run the F2 validation/export tests**

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_validation_error_review_findings.py `
  -k "scope_controlled or scope_semantic or source_immutability or scope_export" `
  -v
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit F2 validation/export**

```powershell
git add -- `
  src/fleetvision/data/validation_error_review_findings.py `
  tests/test_validation_error_review_findings.py

git commit -m "feat: validate and export phase04.5L scope review"
```

---

### Task 6: Implement distributions, cross-tabulations, composition sensitivity, and advisory recommendation rules

**Files:**
- Modify: `src/fleetvision/data/validation_error_review_findings.py`.
- Modify: `tests/test_validation_error_review_findings.py`.

**Interfaces:**
- Produces:
  - `build_findings_payload(combined: pd.DataFrame, config: FindingsConfig) -> dict[str, Any]`
  - `classify_recommendation(combined, payload, config) -> RecommendationResult`
  - deterministic JSON/Markdown final reports.

- [ ] **Step 1: Add exact analytical helper tests**

```python
def test_total_variation_distance_detects_scope_composition_shift() -> None:
    all_counts = {"confirmed_model_error": 70, "annotation_issue": 30}
    in_scope_counts = {"confirmed_model_error": 90, "annotation_issue": 10}
    assert findings.total_variation_distance(all_counts, in_scope_counts) == pytest.approx(0.20)


def test_recommendation_precedence_is_fail_closed() -> None:
    config = _make_materialized_findings_config(...)
    assert findings.choose_primary_recommendation(
        additional_review=True,
        data_correction=True,
        scope_rebalancing=True,
        retraining_justified=True,
    ) == "ADDITIONAL_REVIEW_REQUIRED"
    assert findings.choose_primary_recommendation(
        additional_review=False,
        data_correction=True,
        scope_rebalancing=True,
        retraining_justified=True,
    ) == "DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING"
```

Add tests covering all five primary recommendation outcomes.

- [ ] **Step 2: Implement deterministic distributions and cross-tabs**

For every distribution, output sorted records:

```json
{"value": "confirmed_model_error", "count": 42, "percentage": 32.307692}
```

Required distributions:

- `error_disposition`
- `primary_root_cause`
- `secondary_root_cause`
- `annotation_quality`
- `annotation_defect_type`
- `recommended_action`
- `retraining_priority`
- `scope_group`
- `operability`
- `scope_reason`
- `scope_confidence`

Required cross-tabs:

- scope group × error disposition
- scope group × primary root cause
- scope group × annotation quality
- scope group × recommended action
- scope group × retraining priority

Use sorted row/column keys and integer counts so output is deterministic.

- [ ] **Step 3: Implement all-130 versus in-scope comparison**

For these five dimensions:

```text
error_disposition
primary_root_cause
annotation_quality
recommended_action
retraining_priority
```

calculate total variation distance between the all-case distribution and `IN_SCOPE_LIGHT_MODERATE` distribution. Set:

```python
composition_distortion_detected = (
    non_scope_share >= rules["scope_rebalancing_non_scope_share"]
    or max_tvd >= rules["distribution_total_variation_threshold"]
)
```

Threshold candidate sensitivity is advisory only:

```python
all_tradeoff_share = share(error_disposition == "expected_threshold_tradeoff")
in_scope_tradeoff_share = share(
    (scope_group == "IN_SCOPE_LIGHT_MODERATE")
    & (error_disposition == "expected_threshold_tradeoff")
)
threshold_candidate_composition_sensitive = (
    abs(all_tradeoff_share - in_scope_tradeoff_share)
    >= rules["threshold_tradeoff_share_delta"]
)
```

Do not read predictions, recalculate metrics, tune thresholds, or inspect test data.

- [ ] **Step 4: Implement recommendation precedence**

The exact precedence is:

1. `ADDITIONAL_REVIEW_REQUIRED` when insufficient-visual-evidence exists or low-confidence share exceeds the configured threshold.
2. `DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING` when any annotation correction proposal exists or any reviewed row has `annotation_quality=defect_suspected`.
3. `SCOPE_REBALANCING_REQUIRED_BEFORE_RETRAINING` when composition distortion is detected.
4. `RETRAINING_PROPOSAL_JUSTIFIED` only when, inside the in-scope subset, both the medium/high retraining-priority share and confirmed-model-error share meet their configured thresholds.
5. `NO_RETRAINING_RECOMMENDED` otherwise.

The recommendation JSON must always include:

```json
{
  "primary_recommendation": "...",
  "advisory_only": true,
  "retraining_status": "NOT_YET_APPROVED",
  "deployment_acceptance": "NOT_YET_APPROVED",
  "reasons": [],
  "metrics": {}
}
```

- [ ] **Step 5: Implement final report rendering**

Create:

- `final_findings/severity_scope_summary.json`
- `final_findings/severity_scope_summary.md`
- `final_findings/phase04_5l_findings_report.json`
- `final_findings/phase04_5l_findings_report.md`
- `final_findings/retraining_recommendation.json`

The Markdown report must contain the 19 required design outputs and explicitly state that recommendation is advisory and does not change retraining/deployment status.

- [ ] **Step 6: Run analytical tests**

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_validation_error_review_findings.py `
  -k "distribution or cross_tab or variation or recommendation or sensitivity" `
  -v
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit analysis/recommendation logic**

```powershell
git add -- `
  src/fleetvision/data/validation_error_review_findings.py `
  tests/test_validation_error_review_findings.py

git commit -m "feat: analyze phase04.5L scope and recommendations"
```

---

### Task 7: Implement F2 orchestration and complete evidence manifests

**Files:**
- Modify: `src/fleetvision/data/validation_error_review_findings.py`.
- Modify: `tests/test_validation_error_review_findings.py`.

**Interfaces:**
- Produces: `run_f2(config, workspace_root, expected_head, git_runner=None) -> RecommendationResult` and final Gate classification `PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS_COMPLETED`.

- [ ] **Step 1: Add F2 happy-path and fail-closed tests**

F2 happy path must start from an F1 fixture, fill all scope rows, and assert all required final files exist. Add fail-closed tests for:

- original authoritative hash changed after F1;
- F1 source CSV changed;
- Workbook source field changed;
- row reorder;
- pending classification;
- existing final output;
- repository SHA mismatch.

- [ ] **Step 2: Implement F2 sequence**

`run_f2` must perform exactly:

1. fresh Git preflight against the explicit implementation-closure SHA;
2. fresh authoritative hash/size verification of original frozen inputs;
3. verification of F1 source hashes, copied-input hashes, F1 gate PASS, scope source CSV SHA, scope Workbook source identity, and asset manifest;
4. scope Workbook validation;
5. deterministic severity-scope CSV export;
6. merge by exact ordered `review_case_id` with the existing canonical CSV;
7. distributions, cross-tabs, comparison, sensitivity, and recommendation generation;
8. final report writes through staging paths;
9. workspace-after inventory;
10. final Gate result and checksum manifest.

- [ ] **Step 3: Define evidence schemas**

`evidence/source_hashes.csv`:

```text
artifact,original_path,snapshot_path,expected_size_bytes,actual_size_bytes,expected_sha256,actual_sha256,snapshot_sha256,match
```

`evidence/workspace_before.csv`:

```text
entry_name,entry_type,target_name_collision
```

`evidence/workspace_after.csv`:

```text
relative_path,size_bytes,sha256
```

`evidence/gate_result.json` must include:

```json
{
  "gate_id": "PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS",
  "outcome": "PASS",
  "classification": "PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS_COMPLETED",
  "review_cases": 130,
  "scope_reviewed": 130,
  "pending": 0,
  "needs_adjudication": 0,
  "primary_recommendation": "...",
  "test_split_read": false,
  "model_inference_executed": false,
  "annotation_modified": false,
  "training_started": false,
  "retraining_status": "NOT_YET_APPROVED",
  "deployment_acceptance": "NOT_YET_APPROVED"
}
```

`evidence/SHA256SUMS.csv` must list every final workspace file except itself, sorted by POSIX relative path.

- [ ] **Step 4: Preserve blocked evidence without promoting incomplete final outputs**

On F1/F2 exception:

- write a stage-specific blocked Gate result under `evidence/` when the workspace exists;
- retain already written evidence;
- delete only `.staging-*` files/directories created by the failing operation;
- do not delete or alter frozen inputs;
- do not create the final PASS `gate_result.json`;
- return nonzero through the CLI.

- [ ] **Step 5: Run F2 integration tests**

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_validation_error_review_findings.py `
  -k "run_f2 or gate_result or checksum or blocked_evidence" `
  -v
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit F2/evidence implementation**

```powershell
git add -- `
  src/fleetvision/data/validation_error_review_findings.py `
  tests/test_validation_error_review_findings.py

git commit -m "feat: complete phase04.5L F2 findings evidence"
```

---

### Task 8: Add CLI wrappers, PowerShell 5.1 launchers, and operator documentation

**Files:**
- Create: `scripts/phase04_5_run_completed_review_findings_f1.py`.
- Create: `scripts/phase04_5_run_completed_review_findings_f2.py`.
- Create: `scripts/phase04_5_run_completed_review_findings_f1.ps1`.
- Create: `scripts/phase04_5_run_completed_review_findings_f2.ps1`.
- Create: `docs/01_phase_guides/phase_04_5_completed_review_findings_analysis.md`.
- Modify: `tests/test_validation_error_review_findings.py`.

**Interfaces:**
- Consumes: `main_f1()` and `main_f2()` in the findings module.
- Produces: operator-safe Windows commands with explicit expected HEAD and no hidden mutation.

- [ ] **Step 1: Add `main_f1` and `main_f2` to the module**

F1 arguments:

```text
--config
--project-root
--expected-head (required)
--timestamp (optional deterministic test override)
```

F2 arguments:

```text
--config
--project-root
--expected-head (required)
--workspace-root (required)
```

Both must print one consolidated result block and all safety declarations. Blocked execution returns `1`; PASS returns `0`.

- [ ] **Step 2: Create thin Python wrappers**

F1 wrapper:

```python
"""FleetVision Phase 04.5L completed-review findings F1 wrapper."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fleetvision.data.validation_error_review_findings import main_f1  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main_f1())
```

F2 wrapper is identical except it imports/calls `main_f2`.

- [ ] **Step 3: Create the F1 PowerShell 5.1 launcher**

```powershell
#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$ProjectRoot = "G:\Project\FleetVision",
    [string]$Config = "configs/data/phase04_5l_completed_review_findings_config.yaml",
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{40}$')]
    [string]$ExpectedHead,
    [string]$Timestamp = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\phase04_5_run_completed_review_findings_f1.py"
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Python not found: $Python" }
if (-not (Test-Path -LiteralPath $Script -PathType Leaf)) { throw "F1 script not found: $Script" }

$Arguments = @(
    $Script,
    "--project-root", $ProjectRoot,
    "--config", $Config,
    "--expected-head", $ExpectedHead
)
if ($Timestamp) { $Arguments += @("--timestamp", $Timestamp) }

Push-Location -LiteralPath $ProjectRoot
try {
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "F1 blocked with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
```

F2 launcher uses mandatory `WorkspaceRoot` and calls the F2 Python wrapper.

- [ ] **Step 4: Add CLI and PowerShell contract tests**

Tests must assert:

- wrappers contain no implementation logic and import the correct main function;
- PowerShell files contain `#requires -Version 5.1`, `Set-StrictMode -Version Latest`, `$ErrorActionPreference = "Stop"`, mandatory expected SHA, and no forbidden Git/data/model command;
- `main_f1`/`main_f2` return `1` on preflight failure and print the blocked classification;
- no CLI exposes test split, weights, inference, annotation-apply, Registry, or training arguments.

- [ ] **Step 5: Write the operator guide**

The guide must include:

- authoritative input paths/hashes;
- exact implementation-closure prerequisite;
- F1 command;
- the F1 PASS classification and output checklist;
- a hard stop for human scope review;
- scope field definitions and conditional rules;
- F2 command;
- final PASS classification and output checklist;
- recovery/no-overwrite behavior;
- all prohibited boundaries;
- explicit statement that F2 PASS does not authorize retraining/deployment.

Use commands:

```powershell
.\scripts\phase04_5_run_completed_review_findings_f1.ps1 `
  -ExpectedHead <IMPLEMENTATION_CLOSURE_SHA>
```

and, only after 130/130 scope completion:

```powershell
.\scripts\phase04_5_run_completed_review_findings_f2.ps1 `
  -ExpectedHead <IMPLEMENTATION_CLOSURE_SHA> `
  -WorkspaceRoot '<F1_WORKSPACE_ROOT>'
```

- [ ] **Step 6: Run CLI/launcher tests**

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_validation_error_review_findings.py `
  -k "cli or wrapper or powershell" `
  -v
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit launchers and guide**

```powershell
git add -- `
  scripts/phase04_5_run_completed_review_findings_f1.py `
  scripts/phase04_5_run_completed_review_findings_f2.py `
  scripts/phase04_5_run_completed_review_findings_f1.ps1 `
  scripts/phase04_5_run_completed_review_findings_f2.ps1 `
  docs/01_phase_guides/phase_04_5_completed_review_findings_analysis.md `
  src/fleetvision/data/validation_error_review_findings.py `
  tests/test_validation_error_review_findings.py

git commit -m "docs: add phase04.5L findings operation workflow"
```

---

### Task 9: Verify implementation closure without executing F1 or F2

**Files:**
- All implementation files from Tasks 1–8.
- Governance files only if separately authorized.

**Interfaces:**
- Produces: a remote-verified implementation checkpoint ready for a later explicit F1 execution authorization.

- [ ] **Step 1: Run focused tests**

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_validation_error_human_review.py `
  tests/test_validation_error_review_findings.py `
  -v
```

Expected: all focused tests pass; zero failures. Record the exact count from fresh output.

- [ ] **Step 2: Run the full repository suite**

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected: full suite passes. Record exact passed/skipped counts; do not summarize from memory.

- [ ] **Step 3: Compile the new Python entry points**

```powershell
.\.venv\Scripts\python.exe -m py_compile `
  src\fleetvision\data\validation_error_review_findings.py `
  scripts\phase04_5_run_completed_review_findings_f1.py `
  scripts\phase04_5_run_completed_review_findings_f2.py
```

Expected: exit code 0 and no output.

- [ ] **Step 4: Perform a read-only CLI help smoke test only**

```powershell
.\.venv\Scripts\python.exe scripts\phase04_5_run_completed_review_findings_f1.py --help
.\.venv\Scripts\python.exe scripts\phase04_5_run_completed_review_findings_f2.py --help
```

Expected: help text only. **Do not provide `--expected-head` and do not execute F1/F2.**

- [ ] **Step 5: Audit the diff and protected boundaries**

```powershell
git diff --check
git status --short --untracked-files=all
git diff --name-only
```

Expected changed paths are restricted to the explicit implementation allowlist. `dataset/`, Registry, annotations, splits, model outputs, completed review artifacts, and `outputs/metadata/external_assets/` must not be changed/staged.

- [ ] **Step 6: Inspect for prohibited imports/commands**

```powershell
$Files = @(
  "src\fleetvision\data\validation_error_review_findings.py",
  "scripts\phase04_5_run_completed_review_findings_f1.py",
  "scripts\phase04_5_run_completed_review_findings_f2.py",
  "scripts\phase04_5_run_completed_review_findings_f1.ps1",
  "scripts\phase04_5_run_completed_review_findings_f2.ps1"
)
Select-String -Path $Files -Pattern `
  'ultralytics|YOLO\(|\.train\(|\.predict\(|dataset[\\/]05_yolo|canonical_coco.*write|Registry.*write' `
  -CaseSensitive:$false
```

Expected: no executable prohibited operation. Documentation strings that state prohibitions must be reviewed manually, not treated as implementation.

- [ ] **Step 7: Commit the final implementation closure**

Stage only exact paths still modified after the prior commits. Use a subject such as:

```powershell
git commit -m "feat: complete phase04.5L findings analysis implementation"
```

Do not commit generated workspaces or test artifacts.

- [ ] **Step 8: Push and remotely verify**

```powershell
git push origin main
if ($LASTEXITCODE -ne 0) { throw "push failed" }

git fetch origin main
$LocalHead = (git rev-parse HEAD).Trim()
$OriginMain = (git rev-parse origin/main).Trim()
$RemoteHead = ((git ls-remote origin refs/heads/main) -split "`t")[0].Trim()
if (($LocalHead -ne $OriginMain) -or ($LocalHead -ne $RemoteHead)) {
    throw "post-push remote verification failed"
}
git status --short --untracked-files=all
```

Expected: local/origin/remote equal; worktree clean or protected-untracked-only.

- [ ] **Step 9: Stop before operational F1**

Implementation closure must report:

```text
F1_EXECUTED: NO
F2_EXECUTED: NO
TEST_SPLIT_READ: NO
MODEL_INFERENCE_EXECUTED: NO
ANNOTATION_MODIFIED: NO
TRAINING_STARTED: NO
RETRAINING_STATUS: NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE: NOT_YET_APPROVED
```

Do not run F1 merely because implementation tests pass. A new explicit operational authorization is required.

---

### Task 10: Future operational Gate sequence after separate authorization

This task is documented so implementation and execution cannot be conflated. It is **not authorized by the current planning request**.

- [ ] **F1 Gate:** verify current implementation HEAD/worktree, frozen hashes/fingerprint, create the isolated workspace, run existing export/validator/summarizer, and create the scope-review package.
- [ ] **Human hold:** Vincent completes exactly 130 severity-scope classifications; no code or data mutation occurs.
- [ ] **F2 Gate:** re-verify all inputs/F1 identities, validate/export scope results, generate final findings/recommendation/evidence.
- [ ] **Governance decision Gate:** review the advisory recommendation and explicitly decide whether to authorize annotation proposal handling, data acquisition, threshold-only analysis, scope rebalancing, or a separate retraining proposal.
- [ ] **Retraining remains blocked** unless a later Gate changes `RETRAINING_STATUS` through an explicit repository-backed decision.
- [ ] **Deployment remains blocked** unless a later Gate changes `DEPLOYMENT_ACCEPTANCE` through an explicit repository-backed decision.

---

## Plan self-review

### Spec coverage

- Frozen Workbook/package/source identities: Tasks 2–4 and 7.
- Live Git/worktree verification: Tasks 0, 3, 7, and 9.
- Existing exporter/validator/summarizer reuse: Tasks 1 and 4.
- F1 no-overwrite workspace and evidence: Tasks 3–4.
- Scope Workbook schema, controlled values, and semantics: Tasks 4–5.
- Source immutability and ordering: Task 5.
- F2 distributions/cross-tabs/comparison/sensitivity: Task 6.
- Exactly one advisory recommendation: Task 6.
- Complete final evidence/checksums: Task 7.
- PowerShell 5.1 and CLI contracts: Task 8.
- Focused/full tests and implementation closure without operational execution: Task 9.
- Governance synchronization remains separately gated: Tasks 0 and 10.

### Placeholder scan

No `TBD`, `TODO`, “implement later,” or unspecified error handling remains. The only runtime-resolved values are explicit commit SHA and workspace path arguments that cannot be known until the corresponding future Gate.

### Type/interface consistency

- `FindingsConfig` is consumed by all new operations.
- `WorkspacePaths` is produced by F1 and consumed by F2/test fixtures.
- Existing `ReviewConfig` remains owned by `validation_error_human_review.py`.
- `asset_root` is optional and backward compatible.
- F2 exports `SCOPE_EXPORT_COLUMNS = CANONICAL_COLUMNS + SCOPE_COLUMNS` in deterministic order.

## Execution handoff

After local Git reconciliation, plan commit/push, stale governance-state reconciliation, and explicit implementation authorization:

1. **Subagent-Driven (recommended):** use `superpowers:subagent-driven-development`, one fresh implementation worker per Task with review between checkpoints.
2. **Inline Execution:** use `superpowers:executing-plans`, execute in small batches with the listed verification gates.

No implementation or F1/F2 execution is authorized by the current request.
