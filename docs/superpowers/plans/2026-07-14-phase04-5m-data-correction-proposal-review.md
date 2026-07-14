# Phase 04.5M Data Correction Proposal Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一套只處理兩筆 Phase 04.5L annotation-correction findings 的繁體中文 Streamlit／SQLite 人工複核流程，輸出可稽核且不可覆寫的 correction proposals，但不修改 canonical annotation、canonical COCO、dataset、Registry、fixed splits 或 training state。

**Architecture:** 採用專用 04.5M workflow，選擇性重用既有 04.5L package verification、SQLite transaction、JSONL audit、Streamlit navigation、no-overwrite export 與 bbox validation patterns。Domain mapping、package、state、app、export 各自獨立；所有 generated artifacts 位於 repository 外的 timestamped workspace。Implementation 必須先在隔離 worktree／target-like clone 完成 TDD、Windows checkout rehearsal 與 release verification，production workspace 不作第一個 integration-test environment。

**Tech Stack:** Python 3.11、pandas、PyYAML、Pillow、openpyxl、Streamlit、SQLite、pytest、PowerShell 5.1、Git。

## Global Constraints

- Repository root: `G:\Project\FleetVision`
- Production branch: `main`
- Approved parent checkpoint: `45291f06cdca8f01dad44f248c1b3bc0ba3d7d01`
- Approved design: `docs/superpowers/specs/2026-07-14-phase04-5m-data-correction-proposal-review-design.md`
- Source case count: exactly `2`
- Review case IDs: `l_687b939a3a89bb8e`, `l_e5875a8f94620ff1`
- Human review interface: `LOCAL_STREAMLIT_TRADITIONAL_CHINESE`
- Live review state: `SQLITE`
- Audit log: append-only JSONL with monotonic event IDs
- Backup interval: every successful save
- Backup retention: `20`
- Excel role: completed export/archive only
- Completed export condition: `total=2`, `reviewed=2`, `pending=0`, `needs_adjudication=0`
- Generated review workspace must remain outside the repository.
- The historical filename prefix `test_set_` must not determine split identity; verified source records must contain `split=valid`.
- `TEST_SPLIT_READ=NO`
- `MODEL_INFERENCE_EXECUTED=NO`
- `ANNOTATION_MODIFIED=NO`
- `CANONICAL_COCO_MODIFIED=NO`
- `DATASET_MODIFIED=NO`
- `REGISTRY_MODIFIED=NO`
- `FIXED_SPLITS_MODIFIED=NO`
- `TRAINING_STARTED=NO`
- Do not read the test split.
- Do not rerun model inference.
- Do not modify annotation, GT, canonical COCO, dataset, Registry, fixed splits, model artifacts, or training state.
- Do not create a promoted COCO file in Phase 04.5M.
- `RETRAINING_STATUS=NOT_YET_APPROVED`
- `DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED`
- User-visible installers and operational scripts must be release candidates rehearsed against a target-commit Windows-style checkout.
- Production workspace must not be the first integration-test environment.
- Existing Phase 04.5L scope-review modules must not be broadly refactored.
- Every task uses TDD: failing test, observed failure, minimal implementation, focused pass, regression pass, explicit checkpoint.
- During implementation, invoke `superpowers:using-git-worktrees` before creating an isolated implementation worktree.
- Before claiming implementation completion, invoke `superpowers:verification-before-completion` and `superpowers:requesting-code-review`.
- Commit and push remain separately authorized operations; plan execution must not infer permission from this document.

---

## Planned File Structure

### New configuration and domain modules

- Create: `configs/data/phase04_5m_annotation_correction_review_config.yaml`
  - Static source contract, expected F2 classification, exact case identities, reviewer/timezone, workspace name, backup policy, completed export names, controlled values.
- Create: `src/fleetvision/review/annotation_correction_review_mapping.py`
  - Controlled values, Traditional Chinese labels, bbox JSON normalization, semantic validation, canonical field derivation, deterministic proposal fingerprint.
- Create: `src/fleetvision/review/annotation_correction_review_package.py`
  - F2/F1 evidence verification, exact two-case extraction, validation-only GT/prediction loading, deterministic bbox IDs, overlay generation, no-overwrite package creation.
- Create: `src/fleetvision/review/annotation_correction_review_state.py`
  - Workspace-pinned SQLite state, audit events, event-log synchronization, every-save backups, retention, progress/filter/resume, export history.
- Create: `src/fleetvision/review/annotation_correction_review_app.py`
  - Runtime loader, view models, navigation/session isolation, Traditional Chinese Streamlit UI, save orchestration.
- Create: `src/fleetvision/review/annotation_correction_review_export.py`
  - Completion gate, CSV/JSON/XLSX/proposed-overlay export, round-trip validation, checksums, no-overwrite evidence.

### New operational wrappers

- Create: `scripts/phase04_5_prepare_annotation_correction_review.py`
- Create: `scripts/phase04_5_prepare_annotation_correction_review.ps1`
- Create: `scripts/phase04_5_run_annotation_correction_review_app.py`
- Create: `scripts/phase04_5_launch_annotation_correction_review_app.ps1`
- Create: `scripts/phase04_5_export_annotation_correction_review.py`
- Create: `scripts/phase04_5_export_annotation_correction_review.ps1`

### New tests and fixtures

- Create: `tests/annotation_correction_review_fixtures.py`
- Create: `tests/test_annotation_correction_review_mapping.py`
- Create: `tests/test_annotation_correction_review_package.py`
- Create: `tests/test_annotation_correction_review_state.py`
- Create: `tests/test_annotation_correction_review_app.py`
- Create: `tests/test_annotation_correction_review_export.py`

### Documentation and governance updates at implementation closure

- Create: `docs/01_phase_guides/phase_04_5_annotation_correction_proposal_review.md`
- Modify: `docs/00_project_management/PROJECT_STATUS.md`
- Modify: `docs/00_project_management/HANDOFF_CURRENT.md`
- Modify: `docs/00_project_management/MASTER_PHASE_MAP.md`
- Modify: `docs/00_project_management/DECISION_LOG.md` only when implementation introduces a governance decision not already covered by the approved design.
- Modify: `.gitignore` only when a repository-local generated path is unavoidable; the preferred design keeps all generated review artifacts outside Git and requires no `.gitignore` change.

No new runtime dependency is expected. `streamlit`, `pandas`, `PyYAML`, `Pillow`, and `openpyxl` are already used by the repository; dependency files must remain unchanged unless the implementation proves otherwise.

---

### Task 1: Lock the correction-review domain contract

**Files:**
- Create: `configs/data/phase04_5m_annotation_correction_review_config.yaml`
- Create: `src/fleetvision/review/annotation_correction_review_mapping.py`
- Create: `tests/test_annotation_correction_review_mapping.py`

**Interfaces:**
- Consumes: approved design values and verified Phase 04.5L F2 identities.
- Produces:
  - `BBoxCoordinates`
  - `CorrectionReviewSelection`
  - `CanonicalCorrectionFields`
  - `CONTROLLED_OPTIONS`
  - `parse_target_bbox_ids(value: object) -> tuple[str, ...]`
  - `parse_replacement_bbox(value: object) -> BBoxCoordinates | None`
  - `validate_selection(selection: CorrectionReviewSelection, *, image_width: int, image_height: int, available_gt_bbox_ids: tuple[str, ...]) -> None`
  - `derive_canonical_correction_fields(selection: CorrectionReviewSelection, *, reviewer: str, reviewed_at: datetime, image_width: int, image_height: int, available_gt_bbox_ids: tuple[str, ...]) -> CanonicalCorrectionFields`
  - `proposal_fingerprint(source_case_fingerprint: str, canonical: CanonicalCorrectionFields) -> str`

- [ ] **Step 1: Write the failing controlled-value and dataclass tests**

Add exact tests:

```python
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from fleetvision.review.annotation_correction_review_mapping import (
    BBoxCoordinates,
    CanonicalCorrectionFields,
    CorrectionMappingValidationError,
    CorrectionReviewSelection,
    derive_canonical_correction_fields,
    parse_replacement_bbox,
    parse_target_bbox_ids,
    proposal_fingerprint,
    validate_selection,
)


def test_parse_target_bbox_ids_returns_sorted_unique_tuple() -> None:
    value = '["gt_002","gt_001"]'
    assert parse_target_bbox_ids(value) == ("gt_001", "gt_002")


def test_parse_target_bbox_ids_rejects_duplicates() -> None:
    with pytest.raises(CorrectionMappingValidationError, match="重複"):
        parse_target_bbox_ids('["gt_001","gt_001"]')


def test_parse_replacement_bbox_returns_typed_coordinates() -> None:
    result = parse_replacement_bbox(
        '{"x1":10.0,"y1":20.0,"x2":110.0,"y2":120.0}'
    )
    assert result == BBoxCoordinates(x1=10.0, y1=20.0, x2=110.0, y2=120.0)


def test_reject_keep_current_requires_not_applicable_and_no_geometry() -> None:
    selection = CorrectionReviewSelection(
        correction_review_status="reviewed",
        correction_decision="REJECT_CORRECTION_KEEP_CURRENT_GT",
        correction_operation="RESIZE_OR_REDRAW_BBOX",
        target_gt_bbox_ids=(),
        replacement_bbox=None,
        correction_reason="現有 GT 正確",
    )
    with pytest.raises(CorrectionMappingValidationError, match="NOT_APPLICABLE"):
        validate_selection(
            selection,
            image_width=640,
            image_height=480,
            available_gt_bbox_ids=("gt_001",),
        )


def test_resize_requires_one_target_and_in_bounds_geometry() -> None:
    selection = CorrectionReviewSelection(
        correction_review_status="reviewed",
        correction_decision="CONFIRM_GT_CORRECTION_REQUIRED",
        correction_operation="RESIZE_OR_REDRAW_BBOX",
        target_gt_bbox_ids=("gt_001",),
        replacement_bbox=BBoxCoordinates(10.0, 20.0, 110.0, 120.0),
        correction_reason="現有框未涵蓋完整損傷",
    )
    validate_selection(
        selection,
        image_width=640,
        image_height=480,
        available_gt_bbox_ids=("gt_001", "gt_002"),
    )


def test_needs_adjudication_maps_to_non_final_status() -> None:
    selection = CorrectionReviewSelection(
        correction_review_status="needs_adjudication",
        correction_decision="NEEDS_ADJUDICATION",
        correction_operation="NOT_APPLICABLE",
        target_gt_bbox_ids=(),
        replacement_bbox=None,
        correction_reason="需要第二位 reviewer 判定",
    )
    canonical = derive_canonical_correction_fields(
        selection,
        reviewer="Vincent",
        reviewed_at=datetime(2026, 7, 14, 18, 0, tzinfo=ZoneInfo("Asia/Taipei")),
        image_width=640,
        image_height=480,
        available_gt_bbox_ids=("gt_001",),
    )
    assert canonical.correction_review_status == "needs_adjudication"
    assert canonical.correction_decision == "NEEDS_ADJUDICATION"


def test_proposal_fingerprint_is_deterministic() -> None:
    canonical = CanonicalCorrectionFields(
        correction_review_status="reviewed",
        correction_decision="CONFIRM_GT_CORRECTION_REQUIRED",
        correction_operation="REMOVE_DUPLICATE_BBOX",
        target_gt_bbox_ids_json='["gt_002"]',
        replacement_bbox_coordinates_json="",
        correction_reason="重複標註",
        correction_reviewer="Vincent",
        correction_reviewed_at_utc="2026-07-14T10:00:00+00:00",
    )
    first = proposal_fingerprint("ABCDEF", canonical)
    second = proposal_fingerprint("ABCDEF", canonical)
    assert first == second
    assert len(first) == 64
```

- [ ] **Step 2: Run the mapping tests and observe the expected import failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_review_mapping.py -q
```

Expected:

```text
ERROR collecting tests/test_annotation_correction_review_mapping.py
ModuleNotFoundError: No module named 'fleetvision.review.annotation_correction_review_mapping'
```

- [ ] **Step 3: Create the static YAML contract**

Create `configs/data/phase04_5m_annotation_correction_review_config.yaml` with exact values:

```yaml
schema_version: "1"

source:
  expected_f2_classification: PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS_COMPLETED
  expected_primary_recommendation: DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING
  expected_case_count: 2
  completed_scope_workbook_sha256: AC0EE5882E8E6C7A3E9300BF6AD1589EC18C169681AA6720F0C36132A42B3946
  expected_cases:
    - review_case_id: l_687b939a3a89bb8e
      image_id: 147_jpg.rf.83b3e9e399d2f3546d5676a902148f0c.jpg
      annotation_defect_type: wrong_damage_scope
      review_notes: 模型框的是對的
    - review_case_id: l_e5875a8f94620ff1
      image_id: test_set_188_jpg.rf.ed3c01d255f1c18dd0c5dd2667c7a096.jpg
      annotation_defect_type: extra_bbox
      review_notes: 重複標註

workspace:
  base_root: G:\Project\FleetVision_Review_Packages\Phase04_5M
  directory_prefix: phase04_5m_annotation_correction_review
  reviewer: Vincent
  timezone: Asia/Taipei
  backup_every_successful_saves: 1
  backup_retention: 20

exports:
  reviewed_csv: annotation_correction_proposals_reviewed.csv
  reviewed_json: annotation_correction_proposals_reviewed.json
  completed_workbook: annotation_correction_proposals_completed.xlsx
  result_json: correction_review_export_result.json

options:
  correction_review_status:
    - pending
    - reviewed
    - needs_adjudication
  correction_decision:
    - CONFIRM_GT_CORRECTION_REQUIRED
    - REJECT_CORRECTION_KEEP_CURRENT_GT
    - NEEDS_ADJUDICATION
  correction_operation:
    - RESIZE_OR_REDRAW_BBOX
    - REMOVE_DUPLICATE_BBOX
    - REMOVE_INVALID_BBOX
    - ADD_MISSING_BBOX
    - OTHER
    - NOT_APPLICABLE
```

The absolute `base_root` is an operator default in configuration, not an application-code constant. CLI overrides remain required.

- [ ] **Step 4: Implement the mapping module minimally**

Create immutable dataclasses and canonical JSON helpers:

```python
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Mapping


class CorrectionMappingValidationError(ValueError):
    """Raised when a correction-review decision violates the approved contract."""


STATUS_LABELS: Mapping[str, str] = {
    "pending": "尚未完成",
    "reviewed": "已完成",
    "needs_adjudication": "待裁決",
}

DECISION_LABELS: Mapping[str, str] = {
    "CONFIRM_GT_CORRECTION_REQUIRED": "確認需要修正 GT",
    "REJECT_CORRECTION_KEEP_CURRENT_GT": "拒絕修正，保留現有 GT",
    "NEEDS_ADJUDICATION": "需要進一步裁決",
}

OPERATION_LABELS: Mapping[str, str] = {
    "RESIZE_OR_REDRAW_BBOX": "調整或重畫 bbox",
    "REMOVE_DUPLICATE_BBOX": "移除重複 bbox",
    "REMOVE_INVALID_BBOX": "移除無效 bbox",
    "ADD_MISSING_BBOX": "新增缺漏 bbox",
    "OTHER": "其他",
    "NOT_APPLICABLE": "不適用",
}

CONTROLLED_OPTIONS: Mapping[str, tuple[str, ...]] = {
    "correction_review_status": tuple(STATUS_LABELS),
    "correction_decision": tuple(DECISION_LABELS),
    "correction_operation": tuple(OPERATION_LABELS),
}


@dataclass(frozen=True)
class BBoxCoordinates:
    x1: float
    y1: float
    x2: float
    y2: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class CorrectionReviewSelection:
    correction_review_status: str = "pending"
    correction_decision: str = "NEEDS_ADJUDICATION"
    correction_operation: str = "NOT_APPLICABLE"
    target_gt_bbox_ids: tuple[str, ...] = ()
    replacement_bbox: BBoxCoordinates | None = None
    correction_reason: str = ""


@dataclass(frozen=True)
class CanonicalCorrectionFields:
    correction_review_status: str
    correction_decision: str
    correction_operation: str
    target_gt_bbox_ids_json: str
    replacement_bbox_coordinates_json: str
    correction_reason: str
    correction_reviewer: str
    correction_reviewed_at_utc: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_target_bbox_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, tuple):
        raw = list(value)
    elif isinstance(value, list):
        raw = value
    elif value in (None, ""):
        raw = []
    else:
        try:
            raw = json.loads(str(value))
        except json.JSONDecodeError as exc:
            raise CorrectionMappingValidationError("target bbox IDs 不是有效 JSON") from exc
    if not isinstance(raw, list):
        raise CorrectionMappingValidationError("target bbox IDs 必須是 JSON array")
    normalized = tuple(sorted(str(item).strip() for item in raw))
    if any(not item for item in normalized):
        raise CorrectionMappingValidationError("target bbox ID 不可空白")
    if len(normalized) != len(set(normalized)):
        raise CorrectionMappingValidationError("target bbox IDs 不可重複")
    return normalized


def parse_replacement_bbox(value: object) -> BBoxCoordinates | None:
    if value in (None, ""):
        return None
    if isinstance(value, BBoxCoordinates):
        return value
    if isinstance(value, dict):
        raw = value
    else:
        try:
            raw = json.loads(str(value))
        except json.JSONDecodeError as exc:
            raise CorrectionMappingValidationError("replacement bbox 不是有效 JSON") from exc
    if set(raw) != {"x1", "y1", "x2", "y2"}:
        raise CorrectionMappingValidationError("replacement bbox 欄位必須為 x1/y1/x2/y2")
    try:
        box = BBoxCoordinates(*(float(raw[key]) for key in ("x1", "y1", "x2", "y2")))
    except (TypeError, ValueError) as exc:
        raise CorrectionMappingValidationError("replacement bbox 座標必須是數值") from exc
    if not all(math.isfinite(value) for value in box.as_dict().values()):
        raise CorrectionMappingValidationError("replacement bbox 座標必須是有限數值")
    return box
```

Implement `validate_selection`, `derive_canonical_correction_fields`, and `proposal_fingerprint` with the exact semantics from the approved spec. Canonical target IDs use `_canonical_json(list(ids))`; absent geometry uses an empty string; present geometry uses `_canonical_json(box.as_dict())`. `proposal_fingerprint` hashes the source fingerprint plus canonical fields in fixed field order using SHA256 uppercase hex.

- [ ] **Step 5: Run focused mapping tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_review_mapping.py -q
```

Expected:

```text
7 passed
```

- [ ] **Step 6: Run existing mapping regression**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_severity_scope_review_mapping.py -q
```

Expected: all existing tests pass with zero failures.

- [ ] **Step 7: Review and checkpoint Task 1**

Run:

```powershell
git diff --check
git status --short
```

Expected changed paths are exactly the three Task 1 files plus protected untracked external assets. No commit or push occurs unless the implementation Gate explicitly authorizes it.

---

### Task 2: Build and verify the exact two-case review package

**Files:**
- Create: `src/fleetvision/review/annotation_correction_review_package.py`
- Create: `tests/annotation_correction_review_fixtures.py`
- Create: `tests/test_annotation_correction_review_package.py`

**Interfaces:**
- Consumes:
  - `CorrectionReviewAppConfig`
  - Phase 04.5L F2 workspace root
  - verified F1 workspace artifacts
  - approved mapping JSON helpers
- Produces:
  - `CorrectionReviewAppConfig`
  - `CorrectionSourceCase`
  - `VerifiedCorrectionReviewPackage`
  - `load_correction_review_config(config_path: Path, project_root: Path) -> CorrectionReviewAppConfig`
  - `verify_f2_predecessor(config: CorrectionReviewAppConfig, f2_root: Path) -> VerifiedF2Evidence`
  - `prepare_correction_review_package(config: CorrectionReviewAppConfig, f2_root: Path, *, timestamp: str | None = None) -> VerifiedCorrectionReviewPackage`
  - `load_verified_correction_review_package(config: CorrectionReviewAppConfig, workspace_root: Path) -> VerifiedCorrectionReviewPackage`
  - `stable_bbox_id(prefix: str, row_index: int) -> str`

- [ ] **Step 1: Create deterministic fixture builders**

Create `tests/annotation_correction_review_fixtures.py` with helpers that build:

```python
@dataclass(frozen=True)
class CorrectionFixture:
    project_root: Path
    f2_root: Path
    config_path: Path
    workspace_base: Path
    f1_root: Path
    image_paths: tuple[Path, Path]
```

Fixture data must include:

- `evidence/gate_result.json` with the exact F2 PASS classification and safety flags.
- `final_findings/retraining_recommendation.json` with the exact primary recommendation and two proposal metrics.
- `final_findings/phase04_5l_findings_report.json` with exactly two correction rows.
- `evidence/SHA256SUMS.csv` covering all fixture F2 outputs.
- F1 `evidence/F1_SHA256SUMS.csv`.
- validation-only `records/validation_ground_truth.csv`.
- validation-only `records/validation_predictions.csv`.
- two original images, including the historical filename beginning with `test_set_`.
- source records where both rows explicitly have `split=valid`.

Use Pillow to create deterministic 640×480 JPEG fixtures. The first image has one GT bbox and one prediction; the second image has two overlapping GT bboxes and one prediction.

- [ ] **Step 2: Write failing package-verification tests**

Add exact test cases:

```python
def test_prepare_package_extracts_exact_two_cases(
    correction_fixture: CorrectionFixture,
) -> None:
    config = load_correction_review_config(
        correction_fixture.config_path,
        correction_fixture.project_root,
    )
    package = prepare_correction_review_package(
        config,
        correction_fixture.f2_root,
        timestamp="20260714T180000Z",
    )
    assert tuple(case.review_case_id for case in package.cases) == (
        "l_687b939a3a89bb8e",
        "l_e5875a8f94620ff1",
    )
    assert all(case.source_split == "valid" for case in package.cases)


def test_test_set_filename_is_allowed_only_with_verified_valid_split(
    correction_fixture: CorrectionFixture,
) -> None:
    config = load_correction_review_config(
        correction_fixture.config_path,
        correction_fixture.project_root,
    )
    package = prepare_correction_review_package(
        config,
        correction_fixture.f2_root,
        timestamp="20260714T180001Z",
    )
    case = package.case_by_review_id["l_e5875a8f94620ff1"]
    assert case.image_id.startswith("test_set_")
    assert case.source_split == "valid"


def test_package_rejects_non_valid_source_record(
    correction_fixture: CorrectionFixture,
) -> None:
    rewrite_split(
        correction_fixture.f1_root / "records/validation_ground_truth.csv",
        "test",
    )
    refresh_fixture_manifest(correction_fixture)
    config = load_correction_review_config(
        correction_fixture.config_path,
        correction_fixture.project_root,
    )
    with pytest.raises(CorrectionPackageVerificationError, match="valid"):
        prepare_correction_review_package(
            config,
            correction_fixture.f2_root,
            timestamp="20260714T180002Z",
        )


def test_package_rejects_changed_f2_checksum(
    correction_fixture: CorrectionFixture,
) -> None:
    path = correction_fixture.f2_root / "final_findings/phase04_5l_findings_report.json"
    path.write_text("{}", encoding="utf-8")
    config = load_correction_review_config(
        correction_fixture.config_path,
        correction_fixture.project_root,
    )
    with pytest.raises(CorrectionPackageVerificationError, match="SHA256"):
        prepare_correction_review_package(
            config,
            correction_fixture.f2_root,
            timestamp="20260714T180003Z",
        )


def test_bbox_ids_are_stable_and_ordered() -> None:
    assert stable_bbox_id("gt", 1) == "gt_001"
    assert stable_bbox_id("pred", 12) == "pred_012"
```

Also test:

- F2 recommendation mismatch blocks.
- case set with one or three rows blocks.
- duplicate case ID blocks.
- missing original image blocks.
- output workspace collision blocks.
- staging directory is removed after a forced overlay failure.
- source CSV row order is exactly the approved config order.
- GT/prediction JSON is canonical and contains stable IDs.
- package evidence declares all safety flags `false`.

- [ ] **Step 3: Run package tests and observe import failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_review_package.py -q
```

Expected: collection fails because the package module does not exist.

- [ ] **Step 4: Implement configuration and predecessor verification**

Implement these frozen dataclasses:

```python
@dataclass(frozen=True)
class ExpectedCorrectionCase:
    review_case_id: str
    image_id: str
    annotation_defect_type: str
    review_notes: str


@dataclass(frozen=True)
class CorrectionReviewAppConfig:
    schema_version: str
    project_root: Path
    workspace_base_root: Path
    workspace_directory_prefix: str
    expected_f2_classification: str
    expected_primary_recommendation: str
    expected_case_count: int
    completed_scope_workbook_sha256: str
    expected_cases: tuple[ExpectedCorrectionCase, ...]
    reviewer: str
    timezone: str
    backup_every_successful_saves: int
    backup_retention: int
    reviewed_csv_name: str
    reviewed_json_name: str
    completed_workbook_name: str
    result_json_name: str


@dataclass(frozen=True)
class VerifiedF2Evidence:
    f2_root: Path
    gate_result_path: Path
    findings_report_path: Path
    recommendation_path: Path
    checksum_manifest_path: Path
    gate_result_sha256: str
    findings_report_sha256: str
    recommendation_sha256: str
    completed_scope_workbook_sha256: str
```

`verify_f2_predecessor` must:

1. verify F2 root is outside repository;
2. parse and verify the checksum manifest schema;
3. hash every manifest member before reading the findings;
4. verify classification, counts, recommendation, and safety flags;
5. verify the completed scope Workbook hash;
6. compare the exact two-case set against config;
7. verify no final F2 output is missing.

- [ ] **Step 5: Implement validation-only record loading and stable bbox identity**

Use explicit source columns:

```python
GT_REQUIRED_COLUMNS = ("split", "image_id", "x1", "y1", "x2", "y2")
PRED_REQUIRED_COLUMNS = (
    "split",
    "image_id",
    "confidence",
    "x1",
    "y1",
    "x2",
    "y2",
)
```

Rules:

- filter by exact `image_id`, never filename substring;
- require all matching source rows to have `split=valid`;
- retain source row order;
- assign `gt_001`, `gt_002`, and `pred_001` in retained order;
- validate finite geometry and image bounds;
- canonical JSON row keys:
  - GT: `bbox_id`, `x1`, `y1`, `x2`, `y2`
  - prediction: `bbox_id`, `confidence`, `x1`, `y1`, `x2`, `y2`.

- [ ] **Step 6: Implement deterministic overlays and atomic package creation**

Generate four asset types using Pillow:

- original copy;
- GT overlay: solid bbox plus `gt_###` label;
- prediction overlay: bbox plus `pred_###` and confidence;
- combined overlay: both label sets.

Do not use random visual styling. Use fixed line widths and fixed RGB values defined as module constants. JPEG save parameters must be fixed to make tests deterministic.

Create package in a sibling staging directory, write:

- `source/correction_review_source.csv`
- `source/source_manifest.csv`
- `source/source_contract.json`
- assets
- `evidence/package_gate_result.json`
- `evidence/SHA256SUMS.csv`

Then atomically rename staging to final workspace. Any exception removes only staging.

Expected gate payload includes:

```json
{
  "gate_id": "PHASE_04_5M_ANNOTATION_CORRECTION_REVIEW_PACKAGE",
  "outcome": "PASS",
  "classification": "PHASE_04_5M_ANNOTATION_CORRECTION_REVIEW_PACKAGE_PREPARED",
  "review_cases": 2,
  "pending": 2,
  "test_split_read": false,
  "model_inference_executed": false,
  "annotation_modified": false,
  "dataset_modified": false,
  "registry_modified": false,
  "fixed_splits_modified": false,
  "training_started": false,
  "retraining_status": "NOT_YET_APPROVED",
  "deployment_acceptance": "NOT_YET_APPROVED"
}
```

- [ ] **Step 7: Run focused package tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_review_package.py -q
```

Expected: all package tests pass.

- [ ] **Step 8: Run package regressions**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_severity_scope_review_package.py tests/test_validation_error_review_findings.py -q
```

Expected: all existing tests pass.

- [ ] **Step 9: Review Task 2 boundary**

Run:

```powershell
git diff --check
git status --short
```

Confirm no file under `dataset/`, canonical COCO, Registry, fixed splits, or `outputs/metadata/external_assets/` was modified.

---

### Task 3: Implement workspace-pinned SQLite state, audit, and every-save backup

**Files:**
- Create: `src/fleetvision/review/annotation_correction_review_state.py`
- Create: `tests/test_annotation_correction_review_state.py`

**Interfaces:**
- Consumes:
  - `VerifiedCorrectionReviewPackage`
  - `CorrectionReviewSelection`
  - `CanonicalCorrectionFields`
- Produces:
  - `StoredCorrectionReview`
  - `CorrectionProgressCounts`
  - `CorrectionReviewStateStore`
  - `initialize(package: VerifiedCorrectionReviewPackage) -> None`
  - `save_review(correction_case_id: str, selection: CorrectionReviewSelection, canonical: CanonicalCorrectionFields) -> StoredCorrectionReview`
  - `get_review(correction_case_id: str) -> StoredCorrectionReview | None`
  - `progress() -> CorrectionProgressCounts`
  - `case_ids(filter_name: str = "all") -> tuple[str, ...]`
  - `last_viewed_case_id() -> str`
  - `successful_save_count() -> int`
  - `create_backup() -> Path`
  - `record_export(output_path: Path, sha256: str) -> None`

- [ ] **Step 1: Write failing state-store tests**

Cover exact behavior:

```python
def test_initialize_creates_two_pending_cases(
    prepared_correction_package: VerifiedCorrectionReviewPackage,
) -> None:
    store = CorrectionReviewStateStore(
        prepared_correction_package.app_workspace_root,
        backup_retention=20,
    )
    store.initialize(prepared_correction_package)
    assert store.progress() == CorrectionProgressCounts(
        total=2,
        reviewed=0,
        pending=2,
        needs_adjudication=0,
    )


def test_save_review_persists_revision_and_audit_event(
    initialized_correction_store: CorrectionReviewStateStore,
    reviewed_remove_duplicate_selection: CorrectionReviewSelection,
    reviewed_remove_duplicate_canonical: CanonicalCorrectionFields,
) -> None:
    result = initialized_correction_store.save_review(
        "m_case_002",
        reviewed_remove_duplicate_selection,
        reviewed_remove_duplicate_canonical,
    )
    assert result.revision == 1
    events = read_jsonl(initialized_correction_store.event_log_path)
    assert events[-1]["event_type"] == "annotation_correction_review_saved"
    assert events[-1]["event_id"] == 1


def test_initialize_rejects_workspace_identity_mismatch(
    prepared_correction_package: VerifiedCorrectionReviewPackage,
) -> None:
    store = CorrectionReviewStateStore(
        prepared_correction_package.app_workspace_root,
        backup_retention=20,
    )
    store.initialize(prepared_correction_package)
    changed = replace(
        prepared_correction_package,
        source_csv_sha256="A" * 64,
    )
    with pytest.raises(CorrectionReviewStateError, match="identity"):
        store.initialize(changed)


def test_event_log_sequence_gap_fails_closed(
    initialized_correction_store: CorrectionReviewStateStore,
) -> None:
    initialized_correction_store.event_log_path.write_text(
        '{"event_id":2}\n',
        encoding="utf-8",
    )
    with pytest.raises(CorrectionReviewStateError, match="不連續"):
        initialized_correction_store.verify_event_log_continuity()


def test_backup_retention_keeps_latest_twenty(
    initialized_correction_store: CorrectionReviewStateStore,
) -> None:
    created = [
        initialized_correction_store.create_backup(
            timestamp=f"20260714T1800{index:02d}000000Z"
        )
        for index in range(22)
    ]
    remaining = sorted(initialized_correction_store.backup_dir.glob("*.sqlite3"))
    assert len(remaining) == 20
    assert created[-1] in remaining
    assert created[-2] in remaining
```

Also test:

- reviewer mismatch blocks;
- timezone-naive timestamp blocks;
- unknown case ID blocks;
- source fingerprint mismatch blocks;
- pending/reviewed/adjudication filters;
- resume last-viewed case;
- backup is a valid SQLite snapshot;
- export path uniqueness;
- JSONL is repaired from committed DB audit rows after an interrupted append;
- DB integrity check must return `ok`.

- [ ] **Step 2: Run state tests and observe import failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_review_state.py -q
```

Expected: module import failure.

- [ ] **Step 3: Implement the SQLite schema**

Use these tables:

```sql
CREATE TABLE workspace_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE review_cases (
    correction_case_id TEXT PRIMARY KEY,
    case_index INTEGER NOT NULL UNIQUE,
    review_case_id TEXT NOT NULL UNIQUE,
    source_case_fingerprint TEXT NOT NULL,
    image_id TEXT NOT NULL,
    ui_selection_json TEXT NOT NULL DEFAULT '{}',
    canonical_fields_json TEXT NOT NULL DEFAULT '{}',
    review_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (review_status IN ('pending','reviewed','needs_adjudication')),
    correction_decision TEXT NOT NULL DEFAULT '',
    correction_operation TEXT NOT NULL DEFAULT '',
    revision INTEGER NOT NULL DEFAULT 0 CHECK (revision >= 0),
    saved_at_utc TEXT NOT NULL DEFAULT ''
);

CREATE TABLE app_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    correction_case_id TEXT,
    revision INTEGER,
    event_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);

CREATE TABLE export_history (
    export_id INTEGER PRIMARY KEY AUTOINCREMENT,
    output_path TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL,
    exported_at_utc TEXT NOT NULL
);
```

Connection pragmas match the stable 04.5L store:

```python
connection.execute("PRAGMA foreign_keys = ON")
connection.execute("PRAGMA busy_timeout = 30000")
connection.execute("PRAGMA journal_mode = WAL")
connection.execute("PRAGMA synchronous = FULL")
```

- [ ] **Step 4: Implement transactional save and audit synchronization**

A save must:

1. verify workspace metadata and reviewer;
2. verify the case source fingerprint against the package identity stored at initialization;
3. calculate `revision + 1`;
4. update the case and insert the audit event inside `BEGIN IMMEDIATE`;
5. increment `successful_save_count`;
6. update `last_viewed_case_id`;
7. commit;
8. synchronize committed DB events to JSONL in strict event order;
9. fsync the JSONL file.

The state store itself does not derive canonical fields; it stores already-validated mapping output.

- [ ] **Step 5: Implement backup and retention**

Use `sqlite3.Connection.backup()` into a temporary file, run `PRAGMA integrity_check` on the temporary backup, then atomically rename to:

```text
correction_review_state_<UTC token>.sqlite3
```

Sort backups by filename and delete only the oldest files beyond retention. Never delete the active database or event log.

- [ ] **Step 6: Run focused state tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_review_state.py -q
```

Expected: all tests pass.

- [ ] **Step 7: Run state regressions**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_severity_scope_review_state.py -q
```

Expected: all existing tests pass.

---

### Task 4: Implement runtime orchestration and Traditional Chinese Streamlit UI

**Files:**
- Create: `src/fleetvision/review/annotation_correction_review_app.py`
- Create: `scripts/phase04_5_run_annotation_correction_review_app.py`
- Create: `tests/test_annotation_correction_review_app.py`

**Interfaces:**
- Consumes:
  - package loader
  - state store
  - mapping derivation
- Produces:
  - `CorrectionReviewRuntime`
  - `CorrectionCaseViewModel`
  - `SaveCorrectionReviewResult`
  - `next_case_id`
  - `queue_case_selection`
  - `apply_pending_case_selection`
  - `case_widget_key`
  - `runtime_session_identity`
  - `selection_for_case`
  - `status_for_case`
  - `load_correction_review_runtime`
  - `save_correction_review_selection`
  - `render_app`
  - CLI `main(argv: Sequence[str] | None = None) -> int`

- [ ] **Step 1: Write failing pure app-logic tests**

Add tests independent of Streamlit rendering:

```python
def test_next_case_id_clamps_at_boundaries() -> None:
    ids = ("m_case_001", "m_case_002")
    assert next_case_id(ids, "m_case_001", direction=-1) == "m_case_001"
    assert next_case_id(ids, "m_case_002", direction=1) == "m_case_002"


def test_case_widget_key_is_case_isolated() -> None:
    assert case_widget_key("decision", "m_case_001") == "decision:m_case_001"
    assert case_widget_key("decision", "m_case_002") == "decision:m_case_002"


def test_runtime_session_identity_changes_with_workspace(
    tmp_path: Path,
) -> None:
    first = runtime_session_identity(
        tmp_path / "config.yaml",
        tmp_path / "repo",
        tmp_path / "workspace-a",
    )
    second = runtime_session_identity(
        tmp_path / "config.yaml",
        tmp_path / "repo",
        tmp_path / "workspace-b",
    )
    assert first != second


def test_save_creates_backup_after_every_successful_save(
    correction_runtime: CorrectionReviewRuntime,
    reviewed_resize_selection: CorrectionReviewSelection,
) -> None:
    result = save_correction_review_selection(
        correction_runtime,
        "m_case_001",
        reviewed_resize_selection,
        reviewed_at=datetime(
            2026,
            7,
            14,
            18,
            0,
            tzinfo=ZoneInfo("Asia/Taipei"),
        ),
    )
    assert result.backup_path is not None
    assert result.backup_path.is_file()
    assert result.progress.reviewed == 1
```

Also test:

- default selection is pending and does not silently confirm a correction;
- `wrong_damage_scope` suggestion returns `RESIZE_OR_REDRAW_BBOX`;
- `extra_bbox` suggestion returns `REMOVE_DUPLICATE_BBOX`;
- suggestions affect visual priority only and are not persisted before save;
- saved selection resumes exactly;
- filter options are all/pending/reviewed/needs_adjudication;
- current case selection is preserved across reruns;
- view model exposes four verified image paths and both bbox tables.

- [ ] **Step 2: Run app tests and observe import failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_review_app.py -q
```

Expected: module import failure.

- [ ] **Step 3: Implement runtime and save orchestration**

Use runtime dataclasses:

```python
@dataclass(frozen=True)
class CorrectionReviewRuntime:
    package: VerifiedCorrectionReviewPackage
    store: CorrectionReviewStateStore
    case_by_id: Mapping[str, CorrectionSourceCase]


@dataclass(frozen=True)
class CorrectionCaseViewModel:
    case_index: int
    total_cases: int
    correction_case_id: str
    review_case_id: str
    image_id: str
    original_annotation_defect_type: str
    original_review_notes: str
    original_path: Path
    gt_overlay_path: Path
    prediction_overlay_path: Path
    combined_overlay_path: Path
    gt_bbox_rows: tuple[Mapping[str, object], ...]
    prediction_bbox_rows: tuple[Mapping[str, object], ...]
    review_status: str
    revision: int


@dataclass(frozen=True)
class SaveCorrectionReviewResult:
    stored_review: StoredCorrectionReview
    backup_path: Path
    progress: CorrectionProgressCounts
```

`save_correction_review_selection` derives canonical fields using the configured timezone and calls `create_backup()` after every successful save because the interval is fixed at `1`.

- [ ] **Step 4: Implement the Streamlit page**

Required visible text:

```text
FleetVision｜標註修正提案人工複核
本介面只處理 validation-only 的 2 筆 annotation correction proposals；
不讀取 test、不重新推論、不修改標註／資料集，也不開始訓練。
```

Layout:

1. four top metrics: total, reviewed, pending, adjudication;
2. progress bar;
3. sidebar filter and direct case selector;
4. display-mode radio:
   - 四圖比較
   - 原圖
   - GT Overlay
   - Prediction Overlay
   - Combined Overlay
5. source finding panel;
6. GT bbox dataframe;
7. prediction bbox dataframe;
8. decision selector;
9. operation selector;
10. target GT multiselect;
11. replacement x1/y1/x2/y2 numeric inputs;
12. correction reason text area;
13. save button;
14. previous/next buttons.

Widget keys must include `correction_case_id`. The save button must show mapping validation errors without writing state. After successful save, show revision, backup path, and updated progress.

No UI action exports or promotes annotations.

- [ ] **Step 5: Implement the Python CLI wrapper**

`scripts/phase04_5_run_annotation_correction_review_app.py`:

```python
"""FleetVision Phase 04.5M local annotation-correction review app."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fleetvision.review.annotation_correction_review_app import main


if __name__ == "__main__":
    raise SystemExit(main())
```

The module CLI accepts:

```text
--project-root
--config
--workspace-root
```

It calls `render_app`; Streamlit launch itself is handled by the PowerShell wrapper in Task 6.

- [ ] **Step 6: Run focused app tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_review_app.py -q
```

Expected: all tests pass.

- [ ] **Step 7: Run app regressions**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_severity_scope_review_app.py -q
```

Expected: all existing tests pass.

---

### Task 5: Implement completed proposal export and deterministic proposed overlays

**Files:**
- Create: `src/fleetvision/review/annotation_correction_review_export.py`
- Create: `scripts/phase04_5_export_annotation_correction_review.py`
- Create: `tests/test_annotation_correction_review_export.py`

**Interfaces:**
- Consumes:
  - verified package
  - completed SQLite state
- Produces:
  - `CorrectionReviewExport`
  - `export_completed_correction_review(package: VerifiedCorrectionReviewPackage, store: CorrectionReviewStateStore) -> CorrectionReviewExport`
  - CLI `main(argv: Sequence[str] | None = None) -> int`

- [ ] **Step 1: Write failing export tests**

Required cases:

```python
def test_export_blocks_incomplete_review(
    prepared_correction_package: VerifiedCorrectionReviewPackage,
    initialized_correction_store: CorrectionReviewStateStore,
) -> None:
    with pytest.raises(CorrectionReviewExportError, match="2/2"):
        export_completed_correction_review(
            prepared_correction_package,
            initialized_correction_store,
        )


def test_export_blocks_needs_adjudication(
    completed_with_adjudication_store: CorrectionReviewStateStore,
    prepared_correction_package: VerifiedCorrectionReviewPackage,
) -> None:
    with pytest.raises(CorrectionReviewExportError, match="needs_adjudication"):
        export_completed_correction_review(
            prepared_correction_package,
            completed_with_adjudication_store,
        )


def test_completed_export_creates_expected_artifacts(
    fully_reviewed_correction_store: CorrectionReviewStateStore,
    prepared_correction_package: VerifiedCorrectionReviewPackage,
) -> None:
    result = export_completed_correction_review(
        prepared_correction_package,
        fully_reviewed_correction_store,
    )
    assert result.reviewed_csv_path.is_file()
    assert result.reviewed_json_path.is_file()
    assert result.completed_workbook_path.is_file()
    assert result.result_json_path.is_file()
    assert len(result.proposed_overlay_paths) == 2
    assert all(path.is_file() for path in result.proposed_overlay_paths)


def test_completed_export_is_no_overwrite(
    fully_reviewed_correction_store: CorrectionReviewStateStore,
    prepared_correction_package: VerifiedCorrectionReviewPackage,
) -> None:
    export_completed_correction_review(
        prepared_correction_package,
        fully_reviewed_correction_store,
    )
    with pytest.raises(CorrectionReviewExportError, match="overwrite"):
        export_completed_correction_review(
            prepared_correction_package,
            fully_reviewed_correction_store,
        )


def test_export_does_not_create_coco_or_modify_sources(
    fully_reviewed_correction_store: CorrectionReviewStateStore,
    prepared_correction_package: VerifiedCorrectionReviewPackage,
) -> None:
    before = source_hashes(prepared_correction_package)
    result = export_completed_correction_review(
        prepared_correction_package,
        fully_reviewed_correction_store,
    )
    assert source_hashes(prepared_correction_package) == before
    assert not tuple(result.export_root.rglob("*coco*.json"))
```

Also test:

- CSV column order;
- JSON proposal fingerprint;
- XLSX sheet names and row count;
- source fields and row order immutable;
- removal operation proposed overlay excludes selected GT box;
- resize operation proposed overlay uses replacement geometry;
- reject/keep-current overlay equals current GT overlay geometry;
- all exported bbox geometry remains in bounds;
- result JSON declares safety flags and `PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_REVIEWED`;
- checksum manifest includes every export artifact;
- staging cleanup after forced XLSX or image write error;
- CSV UTF-8-SIG round-trip;
- JSON and CSV represent identical decisions.

- [ ] **Step 2: Run export tests and observe import failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_review_export.py -q
```

Expected: module import failure.

- [ ] **Step 3: Implement completion and source-integrity checks**

Before writing:

1. progress total must equal `2`;
2. reviewed must equal `2`;
3. pending and adjudication must equal `0`;
4. package source CSV, source contract, source manifest, F2 evidence, and assets must match stored SHA256;
5. every stored review must be final and map to one immutable source case;
6. proposal fingerprint must recompute identically.

- [ ] **Step 4: Implement canonical export rows**

Use fixed columns:

```python
EXPORT_COLUMNS = (
    "schema_version",
    "correction_review_batch_id",
    "correction_case_id",
    "review_case_id",
    "image_id",
    "source_split",
    "source_case_fingerprint",
    "original_annotation_defect_type",
    "original_review_notes",
    "source_gt_bbox_records_json",
    "source_prediction_bbox_records_json",
    "correction_review_status",
    "correction_decision",
    "correction_operation",
    "target_gt_bbox_ids_json",
    "replacement_bbox_coordinates_json",
    "correction_reason",
    "correction_reviewer",
    "correction_reviewed_at_utc",
    "proposal_fingerprint",
)
```

Write CSV with UTF-8-SIG and LF line endings, then read it back and compare exact columns and values.

Write JSON as:

```json
{
  "schema_version": "1",
  "proposal_count": 2,
  "proposals": []
}
```

The `proposals` array follows source case order.

- [ ] **Step 5: Implement proposed geometry and overlays**

Create a pure function:

```python
def proposed_gt_boxes(
    source_boxes: tuple[BBoxRecord, ...],
    canonical: CanonicalCorrectionFields,
) -> tuple[BBoxRecord, ...]:
    ...
```

Rules:

- reject keep-current: unchanged source boxes;
- remove duplicate/invalid: omit selected bbox IDs;
- resize/redraw: replace exactly one selected bbox geometry, preserving its bbox ID;
- add missing: append a new proposal-only ID `proposed_001`;
- other: apply only the explicitly validated geometry contract.

Draw proposed overlays from `proposed_gt_boxes`; never mutate source files.

- [ ] **Step 6: Implement XLSX archive and result evidence**

Workbook sheets:

```text
Instructions
Correction_Proposals
Source_Hashes
Manifest
```

- source and identity cells locked;
- archive is not intended for reimport;
- include original, current GT, combined, and proposed overlay hyperlinks;
- include all canonical review fields.

Result JSON:

```json
{
  "gate_id": "PHASE_04_5M_ANNOTATION_CORRECTION_REVIEW_EXPORT",
  "outcome": "PASS",
  "classification": "PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_REVIEWED",
  "review_cases": 2,
  "reviewed": 2,
  "pending": 0,
  "needs_adjudication": 0,
  "canonical_annotation_modified": false,
  "canonical_coco_modified": false,
  "dataset_modified": false,
  "registry_modified": false,
  "fixed_splits_modified": false,
  "test_split_read": false,
  "model_inference_executed": false,
  "training_started": false,
  "retraining_status": "NOT_YET_APPROVED",
  "deployment_acceptance": "NOT_YET_APPROVED"
}
```

Write all outputs into an export staging directory, validate them, then atomically rename to the final export paths. Record the reviewed CSV hash in SQLite export history only after successful finalization.

- [ ] **Step 7: Implement the Python export wrapper**

`scripts/phase04_5_export_annotation_correction_review.py` resolves config and workspace root, loads the verified package and state store, calls the exporter, prints one consolidated result block, and returns nonzero on any blocked condition.

- [ ] **Step 8: Run focused export tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_review_export.py -q
```

Expected: all tests pass.

- [ ] **Step 9: Run export regressions**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_severity_scope_review_export.py tests/test_validation_error_review_findings.py -q
```

Expected: all existing tests pass.

---

### Task 6: Add PowerShell 5.1 operational wrappers and operator guide

**Files:**
- Create: `scripts/phase04_5_prepare_annotation_correction_review.py`
- Create: `scripts/phase04_5_prepare_annotation_correction_review.ps1`
- Create: `scripts/phase04_5_launch_annotation_correction_review_app.ps1`
- Create: `scripts/phase04_5_export_annotation_correction_review.ps1`
- Create: `docs/01_phase_guides/phase_04_5_annotation_correction_proposal_review.md`
- Modify: `tests/test_annotation_correction_review_package.py`
- Modify: `tests/test_annotation_correction_review_app.py`
- Modify: `tests/test_annotation_correction_review_export.py`

**Interfaces:**
- Produces three operator commands:
  - package preparation;
  - local app launch;
  - completed export.

- [ ] **Step 1: Write wrapper-contract tests**

Tests read wrapper text and assert:

```python
def test_powershell_wrappers_use_strict_fail_closed_contract() -> None:
    for path in WRAPPER_PATHS:
        text = path.read_text(encoding="utf-8-sig")
        assert "#requires -Version 5.1" in text
        assert "Set-StrictMode -Version Latest" in text
        assert '$ErrorActionPreference = "Stop"' in text
        assert "F2_EXECUTED" not in text
        assert "TRAINING_STARTED" in text
```

Also assert:

- no `Start-Process`;
- no `git add .`;
- no force push;
- project Python is `.venv\Scripts\python.exe`;
- package wrapper requires `-F2WorkspaceRoot`;
- launcher requires `-WorkspaceRoot`;
- exporter requires `-WorkspaceRoot`;
- wrappers do not reference test paths;
- the app port is explicit and configurable, default `8503`;
- launcher displays `http://127.0.0.1:8503`;
- each wrapper prints safety declarations.

- [ ] **Step 2: Run wrapper tests and observe missing-file failures**

Run focused tests and confirm expected failures because the wrappers are absent.

- [ ] **Step 3: Implement the package Python wrapper**

`scripts/phase04_5_prepare_annotation_correction_review.py`:

- import from `src`;
- accept `--project-root`, `--config`, `--f2-workspace-root`, optional `--timestamp`;
- call package preparation;
- print classification, workspace, case count, source hashes, and safety flags;
- return `1` with a blocked classification on exception.

- [ ] **Step 4: Implement the package PowerShell wrapper**

Required parameters:

```powershell
param(
    [string]$ProjectRoot = "G:\Project\FleetVision",
    [string]$Config = "configs\data\phase04_5m_annotation_correction_review_config.yaml",
    [Parameter(Mandatory = $true)]
    [string]$F2WorkspaceRoot,
    [string]$Timestamp = ""
)
```

Run the project Python wrapper directly in the current console. Do not open new windows. Reject missing project root, Python, script, config, or F2 workspace.

- [ ] **Step 5: Implement the Streamlit launcher**

Required parameters:

```powershell
param(
    [string]$ProjectRoot = "G:\Project\FleetVision",
    [string]$Config = "configs\data\phase04_5m_annotation_correction_review_config.yaml",
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,
    [int]$Port = 8503
)
```

Command:

```powershell
& $Python -m streamlit run $Script -- `
    --project-root $ProjectRoot `
    --config $Config `
    --workspace-root $WorkspaceRoot `
    --server.address 127.0.0.1 `
    --server.port $Port
```

Because Streamlit CLI options must precede app arguments, implement the actual command in the verified order:

```powershell
& $Python -m streamlit run `
    $Script `
    --server.address 127.0.0.1 `
    --server.port $Port `
    -- `
    --project-root $ProjectRoot `
    --config $Config `
    --workspace-root $WorkspaceRoot
```

Keep the terminal attached so errors remain visible.

- [ ] **Step 6: Implement the export PowerShell wrapper**

Parameters mirror the launcher without port. It calls the Python exporter and prints one consolidated PASS/BLOCKED block.

- [ ] **Step 7: Write the Traditional Chinese operator guide**

The guide contains exactly these phases:

1. preflight and safety boundaries;
2. prepare a two-case package;
3. verify package classification;
4. launch app;
5. review case `l_687b939a3a89bb8e`;
6. review case `l_e5875a8f94620ff1`;
7. confirm `2/2`, pending `0`, adjudication `0`;
8. stop Streamlit with `Ctrl+C`;
9. export completed proposals;
10. verify hashes and safety declarations;
11. stop before Phase 04.5N.

Explain operation choices and geometry rules in Traditional Chinese. State that completed XLSX is archive-only and must not be edited as live state.

- [ ] **Step 8: Run focused wrapper and guide tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_annotation_correction_review_package.py `
  tests/test_annotation_correction_review_app.py `
  tests/test_annotation_correction_review_export.py -q
```

Expected: all tests pass.

- [ ] **Step 9: Compile and parse operational files**

Run:

```powershell
.\.venv\Scripts\python.exe -m py_compile `
  scripts\phase04_5_prepare_annotation_correction_review.py `
  scripts\phase04_5_run_annotation_correction_review_app.py `
  scripts\phase04_5_export_annotation_correction_review.py `
  src\fleetvision\review\annotation_correction_review_mapping.py `
  src\fleetvision\review\annotation_correction_review_package.py `
  src\fleetvision\review\annotation_correction_review_state.py `
  src\fleetvision\review\annotation_correction_review_app.py `
  src\fleetvision\review\annotation_correction_review_export.py
```

Parse PowerShell 5.1 syntax:

```powershell
$Errors = @()
Get-ChildItem `
  scripts\phase04_5_*annotation_correction_review*.ps1 |
ForEach-Object {
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $_.FullName,
        [ref]$null,
        [ref]$Errors
    )
}
if ($Errors.Count -ne 0) {
    $Errors | Format-List
    throw "PowerShell parser errors detected"
}
```

Expected: no parser errors.

---

### Task 7: End-to-end rehearsal, governance synchronization, and release-candidate verification

**Files:**
- Modify after verified implementation:
  - `docs/00_project_management/PROJECT_STATUS.md`
  - `docs/00_project_management/HANDOFF_CURRENT.md`
  - `docs/00_project_management/MASTER_PHASE_MAP.md`
- Create when required:
  - `docs/00_project_management/phase_logs/phase_04_5m_annotation_correction_review.md`
- Test all new and existing files.
- No generated review artifact is committed.

**Interfaces:**
- Produces:
  - implementation verification evidence;
  - exact changed-path allowlist;
  - release-candidate operational package or installer when separately authorized;
  - next Gate classification `PHASE_04_5M_IMPLEMENTED_TESTED_AND_READY_FOR_PACKAGE_PREPARATION`.

- [ ] **Step 1: Create an isolated target-like worktree**

At execution time, invoke `superpowers:using-git-worktrees`. Create a Windows-compatible checkout at the approved parent commit. Configure:

```powershell
git config core.autocrlf true
git config core.safecrlf true
```

Do not use `G:\Project\FleetVision` as the first integration environment.

- [ ] **Step 2: Run cheap structural checks before tests**

Run:

```powershell
git diff --check
git status --short
.\.venv\Scripts\python.exe -m py_compile `
  src\fleetvision\review\annotation_correction_review_mapping.py `
  src\fleetvision\review\annotation_correction_review_package.py `
  src\fleetvision\review\annotation_correction_review_state.py `
  src\fleetvision\review\annotation_correction_review_app.py `
  src\fleetvision\review\annotation_correction_review_export.py
```

Run the PowerShell parser check from Task 6. Verify all new config and documentation files decode as UTF-8/UTF-8-SIG.

- [ ] **Step 3: Run focused tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_annotation_correction_review_mapping.py `
  tests/test_annotation_correction_review_package.py `
  tests/test_annotation_correction_review_state.py `
  tests/test_annotation_correction_review_app.py `
  tests/test_annotation_correction_review_export.py -q
```

Expected: all 04.5M tests pass.

- [ ] **Step 4: Run relevant regressions**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_severity_scope_review_mapping.py `
  tests/test_severity_scope_review_package.py `
  tests/test_severity_scope_review_state.py `
  tests/test_severity_scope_review_app.py `
  tests/test_severity_scope_review_export.py `
  tests/test_validation_error_review_findings.py -q
```

Expected: all existing 04.5L tests pass.

- [ ] **Step 5: Run the full repository suite**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: zero failures. Report exact passed/skipped counts from fresh output.

- [ ] **Step 6: Execute an end-to-end fixture rehearsal**

In a temporary directory:

1. build verified F2/F1 fixture evidence;
2. run package preparation;
3. initialize SQLite;
4. save one resize/redraw decision;
5. save one remove-duplicate decision;
6. verify two independent backups;
7. export completed proposals;
8. verify CSV/JSON/XLSX/proposed overlays/result/checksums;
9. rerun exporter and verify no-overwrite block;
10. verify fixture source hashes unchanged;
11. verify no COCO output exists.

Expected classifications:

```text
PHASE_04_5M_ANNOTATION_CORRECTION_REVIEW_PACKAGE_PREPARED
PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_REVIEWED
```

- [ ] **Step 7: Rehearse the exact user-visible installer or patch**

When a user-visible installer is authorized:

1. apply the exact installer to a fresh clone at the approved base commit;
2. verify the exact changed-path allowlist;
3. run `git diff --check`;
4. compile/parse;
5. run focused, regression, full tests;
6. verify idempotency or deterministic second-run block;
7. verify rollback leaves no partial tracked changes;
8. verify protected external assets are untouched;
9. calculate installer SHA256;
10. deliver only this release candidate.

- [ ] **Step 8: Update governance after fresh verification**

Update repository-backed status with:

```text
PHASE=04.5M
GATE=IMPLEMENTATION
OUTCOME=PASS
CLASSIFICATION=PHASE_04_5M_IMPLEMENTED_TESTED_AND_READY_FOR_PACKAGE_PREPARATION
IMPLEMENTATION_EXECUTED=YES
FORMAL_REVIEW_PACKAGE_CREATED=NO
HUMAN_REVIEW_STARTED=NO
ANNOTATION_MODIFIED=NO
CANONICAL_COCO_MODIFIED=NO
DATASET_MODIFIED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
NEXT_AUTHORIZED_ACTION=PHASE_04_5M_1_CORRECTION_REVIEW_PACKAGE_PREPARATION
```

Do not record PASS until all verification steps use fresh command output.

- [ ] **Step 9: Perform final changed-path and protected-asset audit**

Run:

```powershell
git diff --name-status
git diff --check
git status --short
```

Expected tracked changes are only the approved implementation/config/test/script/docs paths. Final worktree must be clean or contain only:

```text
?? outputs/metadata/external_assets/
```

No generated SQLite, JSONL, images, XLSX, CSV, backups, or review workspaces may be staged.

- [ ] **Step 10: Request code review and prepare controlled checkpoint**

Invoke `superpowers:requesting-code-review`, address findings using `superpowers:receiving-code-review` when applicable, then invoke `superpowers:verification-before-completion`.

The final report must include:

- current Phase and Gate;
- skills used and unavailable;
- root implementation approach;
- exact files changed;
- focused/regression/full test counts;
- `git diff --check`;
- final `git status --short`;
- protected-asset result;
- commit/push status;
- remaining risks;
- next Gate;
- token-load estimate.

Commit/push only under explicit authorization. Never use force push or broad staging.

---

## Plan Self-Review

### Spec coverage

- Exact two-case source contract: Task 1 and Task 2.
- Validation-only provenance and `test_set_` filename exception: Task 2.
- Stable GT/prediction bbox identities: Task 2.
- Conditional decision/operation/geometry semantics: Task 1.
- Traditional Chinese Streamlit interface: Task 4.
- SQLite transaction, audit continuity, resume, backup: Task 3 and Task 4.
- Completed CSV/JSON/XLSX/proposed-overlay export: Task 5.
- Failure-no-overwrite and staging cleanup: Task 2 and Task 5.
- PowerShell 5.1 operator workflow: Task 6.
- Existing 04.5L regression protection: Tasks 1–7.
- Target-environment rehearsal and release-candidate delivery: Task 7.
- Governance and next Gate synchronization: Task 7.
- No annotation/COCO/dataset/Registry/split/training mutation: Global Constraints and Tasks 2, 5, 7.

### Placeholder scan

The plan contains no deferred implementation markers. Every task identifies exact files, interfaces, tests, commands, expected failures, implementation contracts, and verification outputs.

### Type consistency

- Mapping produces `CorrectionReviewSelection` and `CanonicalCorrectionFields`.
- Package produces `VerifiedCorrectionReviewPackage` and `CorrectionSourceCase`.
- State consumes package/mapping types and produces `StoredCorrectionReview`.
- App consumes package/state/mapping types.
- Export consumes package/state/mapping types.
- Wrapper names and CLI arguments are consistent across Tasks 4–6.

## Execution Handoff

Plan execution must use one of these modes only after separate implementation authorization:

1. **Subagent-Driven Development — recommended**
   - invoke `superpowers:subagent-driven-development`;
   - one fresh implementation subagent per task;
   - review at each task boundary;
   - use an isolated worktree.

2. **Inline Execution**
   - invoke `superpowers:executing-plans`;
   - execute task batches with checkpoints;
   - use an isolated worktree.

For this FleetVision environment, production changes must ultimately be delivered as a rehearsed release candidate and applied through the controlled Windows PowerShell workflow. The plan itself does not authorize implementation.
