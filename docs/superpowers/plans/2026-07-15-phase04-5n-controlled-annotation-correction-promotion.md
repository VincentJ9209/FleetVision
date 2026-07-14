# Phase 04.5N Controlled Annotation Correction Promotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立並測試 Phase 04.5N 的兩個獨立 Gate：N1 只建立與驗證 staged corrected validation COCO；N2 僅在另行明確授權後，將已驗證 staged artifact 原子化 promotion 至 canonical validation COCO，並在任何 post-verification failure 時自動復原。

**Architecture:** 共用 contract 模組負責 04.5M predecessor evidence、固定 proposal set、canonical source discovery、hash 與 validation-only read policy；N1 staging 模組負責 annotation mapping、geometry conversion、semantic diff、overlay 與 no-overwrite workspace；N2 promotion 模組負責 N1 package re-verification、repository guard、verified backup、atomic replace、post-verification 與 rollback。Python CLI 與 PowerShell 5.1 wrapper 均為 thin adapters，正式成功判定只讀 structured JSON／JUnit XML，不解析 pytest 人類可讀摘要。

**Tech Stack:** Python 3.14.6、pytest 9.1.1、PyYAML、Pillow、pandas、SQLite-free JSON/CSV evidence、PowerShell 5.1、Git。

## Global Constraints

- Repository root: `G:\Project\FleetVision`
- Production branch: `main`
- Verified Phase 04.5M implementation/push checkpoint: `ce33812192ddeb654c6926d77d9d878c00c80fcb`
- Approved design path: `docs/superpowers/specs/2026-07-15-phase04-5n-controlled-annotation-correction-promotion-design.md`
- This plan path: `docs/superpowers/plans/2026-07-15-phase04-5n-controlled-annotation-correction-promotion.md`
- The approved design and this plan must be repository-backed, committed, pushed, and remote-verified before implementation starts.
- The implementation-start Git SHA is resolved from live Git after the docs-only commit; implementation tooling must receive it as an exact required value and must not embed an assumed successor SHA.
- Authoritative completed-review workspace: `G:\Project\FleetVision_Review_Packages\Phase04_5M\phase04_5m_annotation_correction_review_20260715_014932067`
- Predecessor classification: `PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_REVIEWED`
- Proposal count: exactly `2`
- Reviewed/pending/adjudication: `2/0/0`
- Review order is immutable: `l_687b939a3a89bb8e`, then `l_e5875a8f94620ff1`
- Proposal fingerprint 1: `C28DE952BFEB7B1C2C0F25BA348B8AF69E87032774714AC95D36B29A944A5FC4`
- Proposal fingerprint 2: `EC8ABCDC49879C817480F1A09FD71E376C5CA47EDB730D5DA699B5298BA13095`
- Canonical dataset ID: `rf_car_damage_seg_v1`
- Canonical split: `valid`
- Repository-backed approved canonical candidate: `dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1/canonical_coco/valid/_annotations.coco.json`
- Runtime canonical discovery must be config-driven and must require exactly one approved candidate to exist.
- Coordinate comparison tolerance: `0.001` absolute pixels.
- Allowed target annotation changes: exactly `bbox` and `area`.
- `segmentation`, `category_id`, `image_id`, annotation `id`, `iscrowd`, and every other field remain unchanged.
- N1 workspace root: `G:\Project\FleetVision_Review_Packages\Phase04_5N`
- N2 promotion evidence root: `G:\Project\FleetVision_Review_Packages\Phase04_5N_Promotion`
- Generated COCO, overlays, CSV, JSON, Markdown, backups, and manifests remain outside Git.
- Existing final workspace paths block execution; overwrite and rerun-in-place are forbidden.
- Implementation and tests use isolated worktrees and temporary fixture datasets; production canonical COCO is never the first integration-test environment.
- N1 implementation closure does not execute N1 against production data.
- N2 implementation closure does not execute canonical promotion.
- N1 PASS does not authorize N2.
- N2 production execution requires a new explicit user authorization and the exact phrase `PHASE_04_5N_2_CANONICAL_PROMOTION_AUTHORIZED` supplied to the execute CLI.
- `TEST_SPLIT_READ=NO`
- `MODEL_INFERENCE_EXECUTED=NO`
- `CANONICAL_ANNOTATION_MODIFIED=NO` during N1 and implementation tests.
- `CANONICAL_COCO_MODIFIED=NO` during N1 and implementation tests.
- `DATASET_MODIFIED=NO` during N1 and implementation tests.
- `REGISTRY_MODIFIED=NO`
- `FIXED_SPLITS_MODIFIED=NO`
- `TRAINING_STARTED=NO`
- `RETRAINING_STATUS=NOT_YET_APPROVED`
- `DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED`
- Do not read any `test` annotation JSON, image directory, manifest row, or derived test artifact.
- Do not run model inference, dataset materialization, training, retraining, fine-tuning, or deployment acceptance.
- Do not stage, commit, clean, delete, rename, or rewrite `outputs/metadata/external_assets/`.
- Task checkpoints use `git diff --check` and exact path review. Git commit/push occurs only in the final controlled closure task and only when that execution Gate explicitly authorizes it.

---

## Planned File Structure

### New configuration

- Create: `configs/data/phase04_5n_annotation_correction_promotion_config.yaml`
  - Fixed predecessor contract, exact proposal IDs/fingerprints, approved canonical candidate list, mapping tolerance, workspace roots, file names, allowed changed fields, N2 authorization phrase, and safety declarations.

### New domain modules

- Create: `src/fleetvision/review/annotation_correction_promotion_contract.py`
  - Config loading, hashing, canonical JSON, predecessor export verification, source-manifest verification, validation-only access ledger, canonical candidate resolution, COCO schema loading.
- Create: `src/fleetvision/review/annotation_correction_staging.py`
  - Reviewed proposal loading, local bbox-to-native annotation mapping, geometry conversion, staged COCO creation, semantic invariants, diff outputs, overlays, atomic N1 workspace creation.
- Create: `src/fleetvision/review/annotation_correction_promotion.py`
  - N1 package re-verification, N2 authorization/preflight, repository guard, backup, atomic replacement, post-verification, rollback, promotion evidence.

### New operational wrappers

- Create: `scripts/phase04_5_stage_annotation_corrections.py`
- Create: `scripts/phase04_5_stage_annotation_corrections.ps1`
- Create: `scripts/phase04_5_promote_annotation_corrections.py`
- Create: `scripts/phase04_5_promote_annotation_corrections.ps1`

### New tests and fixtures

- Create: `tests/annotation_correction_promotion_fixtures.py`
- Create: `tests/test_annotation_correction_promotion_contract.py`
- Create: `tests/test_annotation_correction_staging.py`
- Create: `tests/test_annotation_correction_promotion.py`
- Create: `tests/test_phase04_5n_cli.py`

### Documentation and governance

- Create: `docs/01_phase_guides/phase_04_5_annotation_correction_promotion.md`
- Modify: `docs/00_project_management/PROJECT_STATUS.md`
- Modify: `docs/00_project_management/HANDOFF_CURRENT.md`
- Modify: `docs/00_project_management/MASTER_PHASE_MAP.md`
- Modify: `docs/00_project_management/phase_logs/PHASE_04_5_LOG.md`
- Modify: `docs/00_project_management/DECISION_LOG.md` only if implementation resolves a repository policy not already controlled by the approved design.

No dependency-file modification is expected. PyYAML, Pillow, pandas, pytest, and PowerShell 5.1 are already available in the verified project environment.

---

### Task 1: Lock the Phase 04.5N configuration and shared evidence contract

**Files:**
- Create: `configs/data/phase04_5n_annotation_correction_promotion_config.yaml`
- Create: `src/fleetvision/review/annotation_correction_promotion_contract.py`
- Create: `tests/annotation_correction_promotion_fixtures.py`
- Create: `tests/test_annotation_correction_promotion_contract.py`

**Interfaces:**
- Consumes: Phase 04.5M completed workspace and repository project root.
- Produces:
  - `Phase04_5NConfig`
  - `ExpectedReviewedProposal`
  - `VerifiedCompletedReview`
  - `CanonicalCocoSource`
  - `CocoDocument`
  - `SourceAccessLedger`
  - `load_phase04_5n_config(config_path: Path, project_root: Path) -> Phase04_5NConfig`
  - `verify_completed_review_workspace(config: Phase04_5NConfig, workspace_root: Path) -> VerifiedCompletedReview`
  - `resolve_canonical_validation_coco(config: Phase04_5NConfig) -> CanonicalCocoSource`
  - `load_coco_document(source: CanonicalCocoSource, ledger: SourceAccessLedger) -> CocoDocument`
  - `sha256_file(path: Path) -> str`
  - `canonical_json_bytes(value: object) -> bytes`

- [ ] **Step 1: Create fixture builders before production code**

Create `tests/annotation_correction_promotion_fixtures.py` with these typed builders:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Phase04_5NFixture:
    project_root: Path
    config_path: Path
    completed_review_root: Path
    canonical_valid_coco: Path
    source_image_root: Path


def build_phase04_5n_fixture(tmp_path: Path) -> Phase04_5NFixture:
    """Build a two-case valid-split fixture matching the approved 04.5M export."""
    project_root = tmp_path / "FleetVision"
    completed_review_root = tmp_path / "phase04_5m_completed"
    canonical_valid_coco = (
        project_root
        / "dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1"
        / "canonical_coco/valid/_annotations.coco.json"
    )
    source_image_root = completed_review_root / "assets/original"
    config_path = project_root / "configs/data/phase04_5n_test_config.yaml"
    for directory in (
        canonical_valid_coco.parent,
        source_image_root,
        config_path.parent,
        completed_review_root / "exports",
        completed_review_root / "source",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    write_fixture_coco(canonical_valid_coco)
    write_fixture_original_images(source_image_root)
    write_fixture_completed_review(completed_review_root)
    write_fixture_config(config_path, project_root, canonical_valid_coco)
    return Phase04_5NFixture(
        project_root=project_root,
        config_path=config_path,
        completed_review_root=completed_review_root,
        canonical_valid_coco=canonical_valid_coco,
        source_image_root=source_image_root,
    )
```

The fixture must create:

- `exports/annotation_correction_proposals_reviewed.csv`
- `exports/annotation_correction_proposals_reviewed.json`
- `exports/correction_review_export_result.json`
- `exports/SHA256SUMS.csv`
- `source/source_contract.json`
- `source/source_manifest.csv`
- `source/correction_review_source.csv`
- `assets/original/l_687b939a3a89bb8e.jpg`
- `assets/original/l_e5875a8f94620ff1.jpg`
- a canonical `valid/_annotations.coco.json`
- a canonical `test/_annotations.coco.json` sentinel that raises the test if opened.

The valid COCO fixture contains two images, four annotations, one `damage` category, and native annotation IDs distinct from local IDs `gt_001` and `gt_002`.

- [ ] **Step 2: Write failing config and predecessor-verification tests**

Add these exact tests:

```python
from pathlib import Path

import pytest

from fleetvision.review.annotation_correction_promotion_contract import (
    PromotionContractError,
    SourceAccessLedger,
    load_coco_document,
    load_phase04_5n_config,
    resolve_canonical_validation_coco,
    verify_completed_review_workspace,
)


def test_completed_review_contract_accepts_exact_two_proposals(
    phase04_5n_fixture,
) -> None:
    config = load_phase04_5n_config(
        phase04_5n_fixture.config_path,
        phase04_5n_fixture.project_root,
    )
    verified = verify_completed_review_workspace(
        config,
        phase04_5n_fixture.completed_review_root,
    )
    assert verified.review_case_ids == (
        "l_687b939a3a89bb8e",
        "l_e5875a8f94620ff1",
    )
    assert verified.proposal_fingerprints == (
        "C28DE952BFEB7B1C2C0F25BA348B8AF69E87032774714AC95D36B29A944A5FC4",
        "EC8ABCDC49879C817480F1A09FD71E376C5CA47EDB730D5DA699B5298BA13095",
    )


def test_completed_review_contract_rejects_wrong_classification(
    phase04_5n_fixture,
) -> None:
    rewrite_export_result(
        phase04_5n_fixture.completed_review_root,
        classification="PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_EXPORT_BLOCKED",
    )
    refresh_completed_export_checksums(phase04_5n_fixture.completed_review_root)
    config = load_phase04_5n_config(
        phase04_5n_fixture.config_path,
        phase04_5n_fixture.project_root,
    )
    with pytest.raises(PromotionContractError, match="classification"):
        verify_completed_review_workspace(
            config,
            phase04_5n_fixture.completed_review_root,
        )


def test_historical_test_set_filename_does_not_change_valid_split(
    phase04_5n_fixture,
) -> None:
    config = load_phase04_5n_config(
        phase04_5n_fixture.config_path,
        phase04_5n_fixture.project_root,
    )
    verified = verify_completed_review_workspace(
        config,
        phase04_5n_fixture.completed_review_root,
    )
    second = verified.proposals[1]
    assert second.image_id.startswith("test_set_")
    assert second.source_split == "valid"


def test_canonical_resolution_requires_exactly_one_existing_candidate(
    phase04_5n_fixture,
) -> None:
    config = load_phase04_5n_config(
        phase04_5n_fixture.config_path,
        phase04_5n_fixture.project_root,
    )
    source = resolve_canonical_validation_coco(config)
    assert source.relative_path.as_posix().endswith(
        "canonical_coco/valid/_annotations.coco.json"
    )


def test_canonical_resolution_rejects_multiple_candidates(
    phase04_5n_fixture,
) -> None:
    add_second_existing_valid_candidate(phase04_5n_fixture)
    config = load_phase04_5n_config(
        phase04_5n_fixture.config_path,
        phase04_5n_fixture.project_root,
    )
    with pytest.raises(PromotionContractError, match="exactly one"):
        resolve_canonical_validation_coco(config)


def test_access_ledger_never_reads_test_split(phase04_5n_fixture) -> None:
    config = load_phase04_5n_config(
        phase04_5n_fixture.config_path,
        phase04_5n_fixture.project_root,
    )
    source = resolve_canonical_validation_coco(config)
    ledger = SourceAccessLedger()
    load_coco_document(source, ledger)
    assert ledger.test_split_read is False
    assert all("/test/" not in path.as_posix() for path in ledger.paths)
```

Also add tests for missing checksum member, mismatched file size/hash, proposal order change, duplicate fingerprint, pending count nonzero, adjudication count nonzero, source split not `valid`, candidate outside project root, malformed COCO arrays, duplicate image IDs, duplicate annotation IDs, and category name not `damage`.

- [ ] **Step 3: Run the focused tests and observe import failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_promotion_contract.py -q
```

Expected: collection fails with `ModuleNotFoundError` for `annotation_correction_promotion_contract`.

- [ ] **Step 4: Create the exact YAML configuration**

Create `configs/data/phase04_5n_annotation_correction_promotion_config.yaml`:

```yaml
schema_version: "1"

predecessor:
  expected_classification: PHASE_04_5M_ANNOTATION_CORRECTION_PROPOSALS_REVIEWED
  expected_review_cases: 2
  expected_reviewed: 2
  expected_pending: 0
  expected_needs_adjudication: 0
  required_export_files:
    - exports/annotation_correction_proposals_reviewed.csv
    - exports/annotation_correction_proposals_reviewed.json
    - exports/correction_review_export_result.json
    - exports/SHA256SUMS.csv
    - source/source_contract.json
    - source/source_manifest.csv
    - source/correction_review_source.csv
  expected_proposals:
    - review_case_id: l_687b939a3a89bb8e
      correction_case_id: m_57c102ad6b7c8376
      image_id: 147_jpg.rf.83b3e9e399d2f3546d5676a902148f0c.jpg
      source_split: valid
      operation: RESIZE_OR_REDRAW_BBOX
      target_gt_bbox_ids: [gt_001]
      proposal_fingerprint: C28DE952BFEB7B1C2C0F25BA348B8AF69E87032774714AC95D36B29A944A5FC4
    - review_case_id: l_e5875a8f94620ff1
      correction_case_id: m_ccb31aa1a564a66a
      image_id: test_set_188_jpg.rf.ed3c01d255f1c18dd0c5dd2667c7a096.jpg
      source_split: valid
      operation: RESIZE_OR_REDRAW_BBOX
      target_gt_bbox_ids: [gt_002]
      proposal_fingerprint: EC8ABCDC49879C817480F1A09FD71E376C5CA47EDB730D5DA699B5298BA13095

canonical_source:
  dataset_id: rf_car_damage_seg_v1
  required_split: valid
  required_category_name: damage
  approved_candidates:
    - dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1/canonical_coco/valid/_annotations.coco.json
  coordinate_tolerance_pixels: 0.001
  allowed_changed_fields: [bbox, area]

n1:
  workspace_base_root: G:\Project\FleetVision_Review_Packages\Phase04_5N
  workspace_prefix: phase04_5n_staged_annotation_corrections
  gate_classification: PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED
  staged_coco_name: staged_corrected_validation_coco.json

n2:
  evidence_base_root: G:\Project\FleetVision_Review_Packages\Phase04_5N_Promotion
  evidence_prefix: phase04_5n_annotation_correction_promotion
  authorization_phrase: PHASE_04_5N_2_CANONICAL_PROMOTION_AUTHORIZED
  gate_classification: PHASE_04_5N_ANNOTATION_CORRECTIONS_PROMOTED

safety:
  test_split_read: false
  model_inference_executed: false
  dataset_materialization_executed: false
  registry_modified: false
  fixed_splits_modified: false
  training_started: false
  retraining_status: NOT_YET_APPROVED
  deployment_acceptance: NOT_YET_APPROVED
```

The candidate is a repository-backed contract value. Runtime code must not search the filesystem for similarly named COCO files.

- [ ] **Step 5: Implement immutable config and evidence types**

Create these frozen dataclasses in `annotation_correction_promotion_contract.py`:

```python
@dataclass(frozen=True)
class ExpectedReviewedProposal:
    review_case_id: str
    correction_case_id: str
    image_id: str
    source_split: str
    operation: str
    target_gt_bbox_ids: tuple[str, ...]
    proposal_fingerprint: str


@dataclass(frozen=True)
class Phase04_5NConfig:
    project_root: Path
    expected_classification: str
    expected_review_cases: int
    expected_reviewed: int
    expected_pending: int
    expected_needs_adjudication: int
    required_export_files: tuple[Path, ...]
    expected_proposals: tuple[ExpectedReviewedProposal, ...]
    canonical_candidates: tuple[Path, ...]
    required_split: str
    required_category_name: str
    coordinate_tolerance_pixels: float
    allowed_changed_fields: tuple[str, ...]
    n1_workspace_base_root: Path
    n1_workspace_prefix: str
    n1_gate_classification: str
    staged_coco_name: str
    n2_evidence_base_root: Path
    n2_evidence_prefix: str
    n2_authorization_phrase: str
    n2_gate_classification: str


@dataclass(frozen=True)
class ReviewedProposal:
    review_case_id: str
    correction_case_id: str
    image_id: str
    source_split: str
    source_case_fingerprint: str
    source_gt_bbox_records_json: str
    correction_operation: str
    target_gt_bbox_ids_json: str
    replacement_bbox_coordinates_json: str
    proposal_fingerprint: str


@dataclass(frozen=True)
class VerifiedCompletedReview:
    workspace_root: Path
    proposals: tuple[ReviewedProposal, ...]
    review_case_ids: tuple[str, ...]
    proposal_fingerprints: tuple[str, ...]
    source_manifest_sha256: str
    export_manifest_sha256: str
    export_result_sha256: str


@dataclass(frozen=True)
class CanonicalCocoSource:
    path: Path
    relative_path: Path
    size_bytes: int
    sha256: str
    split: str


@dataclass(frozen=True)
class CocoDocument:
    payload: dict[str, object]
    images_by_id: dict[int, dict[str, object]]
    images_by_file_name: dict[str, dict[str, object]]
    annotations_by_id: dict[int, dict[str, object]]
    categories_by_id: dict[int, dict[str, object]]
```

`SourceAccessLedger.record(path, split)` must reject any split other than `valid` and expose `test_split_read=False` when all reads comply.

- [ ] **Step 6: Implement checksum-first predecessor verification**

`verify_completed_review_workspace` must:

1. resolve every required relative path beneath the supplied workspace;
2. reject path traversal and missing files;
3. verify `exports/SHA256SUMS.csv` members before parsing export data;
4. verify `source/source_manifest.csv` members, including local original images;
5. parse `correction_review_export_result.json` and verify the exact PASS classification/counts/safety flags;
6. load CSV and JSON reviewed proposals and require semantic identity;
7. require exact row order, case IDs, operations, target local bbox IDs, and fingerprints;
8. require `source_split=valid` from the record, regardless of filename text;
9. record the completed-review hashes in `VerifiedCompletedReview`.

- [ ] **Step 7: Implement canonical source resolution and COCO schema loading**

`resolve_canonical_validation_coco` must resolve only configured candidates, require exactly one existing file, ensure it remains under project root, ensure its relative path contains `/valid/` and not `/test/`, and record size/SHA256 before reading.

`load_coco_document` must reject:

- non-object root;
- missing/non-list `images`, `annotations`, or `categories`;
- duplicate image, annotation, or category IDs;
- duplicate image `file_name` values;
- any category set not exactly the configured `damage` contract;
- annotation references to missing images/categories;
- invalid image dimensions.

- [ ] **Step 8: Run focused contract tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_promotion_contract.py -q --junitxml outputs/tmp/phase04_5n_contract.xml
```

Expected structured result: zero failures/errors and all contract tests pass.

- [ ] **Step 9: Check Task 1 boundary**

Run:

```powershell
git diff --check
git status --short
```

Expected non-protected changes are exactly the four Task 1 files. Do not commit or push at this checkpoint.

---

### Task 2: Map reviewed local bbox identities to unique native COCO annotations

**Files:**
- Create: `src/fleetvision/review/annotation_correction_staging.py`
- Create: `tests/test_annotation_correction_staging.py`

**Interfaces:**
- Consumes: `Phase04_5NConfig`, `VerifiedCompletedReview`, `CocoDocument`.
- Produces:
  - `AbsoluteXYXY`
  - `CocoXYWH`
  - `NativeAnnotationMapping`
  - `CorrectionDiffRow`
  - `parse_local_gt_records(value: str) -> tuple[LocalGtRecord, ...]`
  - `map_reviewed_proposal_to_native_annotation(proposal: ReviewedProposal, source_row: Mapping[str, str], coco: CocoDocument, *, tolerance: float) -> NativeAnnotationMapping`
  - `xyxy_to_coco_xywh(box: AbsoluteXYXY) -> CocoXYWH`
  - `apply_reviewed_geometry(annotation: Mapping[str, object], box: AbsoluteXYXY) -> dict[str, object]`

- [ ] **Step 1: Write failing geometry and mapping tests**

```python
import pytest

from fleetvision.review.annotation_correction_staging import (
    AnnotationMappingError,
    AbsoluteXYXY,
    apply_reviewed_geometry,
    map_reviewed_proposal_to_native_annotation,
    xyxy_to_coco_xywh,
)


def test_xyxy_to_xywh_and_area() -> None:
    box = AbsoluteXYXY(x1=74.2, y1=192.4, x2=285.65, y2=579.75)
    xywh = xyxy_to_coco_xywh(box)
    assert xywh.x == pytest.approx(74.2)
    assert xywh.y == pytest.approx(192.4)
    assert xywh.width == pytest.approx(211.45)
    assert xywh.height == pytest.approx(387.35)
    assert xywh.area == pytest.approx(81904.6575)


def test_local_gt_id_maps_to_unique_native_annotation(
    phase04_5n_verified_inputs,
) -> None:
    proposal, coco, config = phase04_5n_verified_inputs.first
    mapping = map_reviewed_proposal_to_native_annotation(
        proposal,
        coco,
        tolerance=config.coordinate_tolerance_pixels,
    )
    assert mapping.local_gt_bbox_id == "gt_001"
    assert mapping.native_annotation_id == 101
    assert mapping.native_image_id == 11


def test_mapping_rejects_missing_native_match(phase04_5n_verified_inputs) -> None:
    proposal, coco, config = phase04_5n_verified_inputs.first
    move_native_bbox(coco, annotation_id=101, delta_x=1.0)
    with pytest.raises(AnnotationMappingError, match="zero native"):
        map_reviewed_proposal_to_native_annotation(
            proposal,
            coco,
            tolerance=config.coordinate_tolerance_pixels,
        )


def test_mapping_rejects_ambiguous_native_match(phase04_5n_verified_inputs) -> None:
    proposal, coco, config = phase04_5n_verified_inputs.first
    duplicate_annotation_geometry(coco, source_annotation_id=101, new_id=999)
    with pytest.raises(AnnotationMappingError, match="multiple native"):
        map_reviewed_proposal_to_native_annotation(
            proposal,
            coco,
            tolerance=config.coordinate_tolerance_pixels,
        )


def test_apply_geometry_preserves_every_non_geometry_field() -> None:
    annotation = {
        "id": 101,
        "image_id": 11,
        "category_id": 1,
        "bbox": [68.0, 334.0, 150.71, 188.466],
        "area": 28403.67,
        "segmentation": [[1.0, 2.0, 3.0, 4.0]],
        "iscrowd": 0,
        "custom": "preserve-me",
    }
    changed = apply_reviewed_geometry(
        annotation,
        AbsoluteXYXY(74.2, 192.4, 285.65, 579.75),
    )
    assert changed["id"] == 101
    assert changed["image_id"] == 11
    assert changed["category_id"] == 1
    assert changed["segmentation"] == annotation["segmentation"]
    assert changed["iscrowd"] == 0
    assert changed["custom"] == "preserve-me"
    assert changed["bbox"] == pytest.approx([74.2, 192.4, 211.45, 387.35])
    assert changed["area"] == pytest.approx(81904.6575)
```

Also test non-finite values, zero/negative width/height, out-of-bounds geometry, unknown local target ID, multiple local target IDs, non-`RESIZE_OR_REDRAW_BBOX` operation, image filename missing, image dimension mismatch, and tolerance values immediately below/above `0.001`.

- [ ] **Step 2: Run tests and observe the expected import failure**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_staging.py -q
```

Expected: `ModuleNotFoundError` for `annotation_correction_staging`.

- [ ] **Step 3: Implement geometry types and strict parsers**

```python
@dataclass(frozen=True)
class AbsoluteXYXY:
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class CocoXYWH:
    x: float
    y: float
    width: float
    height: float

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass(frozen=True)
class LocalGtRecord:
    bbox_id: str
    box: AbsoluteXYXY


@dataclass(frozen=True)
class NativeAnnotationMapping:
    phase04_5m_review_case_id: str
    correction_case_id: str
    proposal_fingerprint: str
    source_split: str
    image_id: str
    local_gt_bbox_id: str
    native_image_id: int
    native_annotation_id: int
    native_category_id: int
    before_bbox_xywh: tuple[float, float, float, float]
    before_bbox_xyxy: tuple[float, float, float, float]
    before_area: float
    after_bbox_xywh: tuple[float, float, float, float]
    after_bbox_xyxy: tuple[float, float, float, float]
    after_area: float
```

`parse_local_gt_records` must canonicalize local IDs, reject duplicates, and preserve source order. `parse_replacement_bbox` must require exactly `x1/y1/x2/y2` and finite floats.

- [ ] **Step 4: Implement deterministic local-to-native mapping**

Mapping algorithm:

1. locate the canonical image by exact `file_name == proposal.image_id`;
2. verify width and height match `source/correction_review_source.csv`;
3. select the local target record by exact `target_gt_bbox_ids_json`;
4. convert every canonical annotation bbox for that image from xywh to xyxy;
5. filter category to the configured `damage` category ID;
6. match all four coordinates within configured absolute tolerance;
7. require exactly one native annotation;
8. require two proposals map to distinct native annotation IDs;
9. record native IDs and immutable fields in mapping evidence.

Do not use prediction geometry to select the native annotation.

- [ ] **Step 5: Implement geometry application**

`apply_reviewed_geometry` must `deepcopy` the annotation, replace only `bbox` and `area`, and verify the changed-key set equals `{"bbox", "area"}` after normalized comparison. Preserve original list order and every other annotation key/value.

- [ ] **Step 6: Run focused mapping tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_staging.py -q --junitxml outputs/tmp/phase04_5n_mapping.xml
```

Expected structured result: zero failures/errors.

- [ ] **Step 7: Check Task 2 boundary**

```powershell
git diff --check
git status --short
```

Confirm no file under `dataset/`, `outputs/metadata/external_assets/`, Registry, or fixed-split paths changed.

---

### Task 3: Build staged COCO and enforce all semantic invariants

**Files:**
- Modify: `src/fleetvision/review/annotation_correction_staging.py`
- Modify: `tests/test_annotation_correction_staging.py`

**Interfaces:**
- Produces:
  - `StagedCocoBuild`
  - `SemanticValidationResult`
  - `build_staged_coco(source: CocoDocument, mappings: tuple[NativeAnnotationMapping, ...], replacements: Mapping[int, AbsoluteXYXY], *, source_sha256: str) -> StagedCocoBuild`
  - `validate_staged_coco(source: CocoDocument, staged_payload: dict[str, object], mappings: tuple[NativeAnnotationMapping, ...], allowed_changed_fields: tuple[str, ...], *, tolerance: float) -> SemanticValidationResult`
  - `build_diff_rows(mappings: tuple[NativeAnnotationMapping, ...], *, source_coco_sha256: str, staged_coco_sha256: str) -> tuple[CorrectionDiffRow, ...]`

- [ ] **Step 1: Add failing staged-build invariant tests**

```python
def test_staged_build_changes_exactly_two_annotations(
    phase04_5n_verified_inputs,
) -> None:
    build = build_fixture_staged_coco(phase04_5n_verified_inputs)
    assert build.validation.changed_annotation_count == 2
    assert build.validation.image_count_delta == 0
    assert build.validation.annotation_count_delta == 0
    assert build.validation.category_count_delta == 0
    assert build.validation.changed_fields == ("area", "bbox")


def test_non_target_annotations_are_semantically_identical(
    phase04_5n_verified_inputs,
) -> None:
    build = build_fixture_staged_coco(phase04_5n_verified_inputs)
    source = phase04_5n_verified_inputs.coco.annotations_by_id
    staged = index_annotations(build.payload)
    for annotation_id in set(source) - set(build.changed_annotation_ids):
        assert normalized_json_value(source[annotation_id]) == normalized_json_value(
            staged[annotation_id]
        )


def test_validation_rejects_segmentation_change(phase04_5n_verified_inputs) -> None:
    build = build_fixture_staged_coco(phase04_5n_verified_inputs)
    target = first_changed_annotation(build.payload)
    target["segmentation"] = []
    with pytest.raises(StagedCocoValidationError, match="unexpected changed fields"):
        validate_fixture_staged_payload(phase04_5n_verified_inputs, build.payload)


def test_deterministic_serialization_produces_stable_hash(
    phase04_5n_verified_inputs,
) -> None:
    first = build_fixture_staged_coco(phase04_5n_verified_inputs)
    second = build_fixture_staged_coco(phase04_5n_verified_inputs)
    assert canonical_json_bytes(first.payload) == canonical_json_bytes(second.payload)
```

Also test changes to image/category definitions, annotation/image/category ID sets, annotation array order, count deltas, a third changed annotation, duplicate changed ID, after bbox not equal to reviewed geometry, invalid area, and source hash drift after build.

- [ ] **Step 2: Run the new tests and observe failures for missing functions**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_staging.py -q
```

Expected: failures identify undefined staged-build and validation functions.

- [ ] **Step 3: Implement staged payload construction**

```python
@dataclass(frozen=True)
class SemanticValidationResult:
    passed: bool
    proposal_count: int
    mapped_annotation_count: int
    changed_annotation_count: int
    changed_annotation_ids: tuple[int, ...]
    changed_fields: tuple[str, ...]
    image_count_delta: int
    annotation_count_delta: int
    category_count_delta: int
    image_id_set_unchanged: bool
    annotation_id_set_unchanged: bool
    category_id_set_unchanged: bool
    non_target_annotations_unchanged: bool
    category_definitions_unchanged: bool


@dataclass(frozen=True)
class StagedCocoBuild:
    payload: dict[str, object]
    mappings: tuple[NativeAnnotationMapping, ...]
    diff_rows: tuple[CorrectionDiffRow, ...]
    validation: SemanticValidationResult
```

Use `copy.deepcopy(source.payload)`, index annotations by native ID, and replace the two target annotation objects in their original list positions. Do not sort or reorder source arrays.

- [ ] **Step 4: Implement normalized semantic comparison**

`normalized_json_value` recursively normalizes dictionaries by key and leaves list order intact. Numeric comparison for target bbox/area uses the configured tolerance; all other values require exact type/value equality.

Validation must prove all 20 N1 invariants from the approved design and return a complete machine-readable result. Any failed invariant raises `StagedCocoValidationError`; do not return a partial PASS result.

- [ ] **Step 5: Implement the exact diff contract**

`CorrectionDiffRow.as_dict()` must output columns in this exact order:

```text
schema_version
phase04_5m_review_case_id
correction_case_id
proposal_fingerprint
source_split
image_id
native_coco_image_id
native_coco_annotation_id
native_category_id
before_bbox_xywh
before_bbox_xyxy
before_area
after_bbox_xywh
after_bbox_xyxy
after_area
changed_fields
source_coco_sha256
staged_coco_sha256
```

JSON-valued cells use compact canonical JSON. `changed_fields` must serialize exactly as `["area","bbox"]` or the configured canonical sorted order used by every output and test.

- [ ] **Step 6: Run staged semantic tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_staging.py -q --junitxml outputs/tmp/phase04_5n_semantic.xml
```

Expected structured result: zero failures/errors.

- [ ] **Step 7: Check Task 3 boundary**

```powershell
git diff --check
git status --short
```

No canonical file may have a changed hash in any fixture assertion or local project status.

---

### Task 4: Create deterministic overlays and atomic N1 workspace packaging

**Files:**
- Modify: `src/fleetvision/review/annotation_correction_staging.py`
- Modify: `tests/test_annotation_correction_staging.py`

**Interfaces:**
- Produces:
  - `PreparedStagedCorrectionWorkspace`
  - `prepare_staged_correction_workspace(config: Phase04_5NConfig, completed_review_root: Path, *, timestamp: str | None = None) -> PreparedStagedCorrectionWorkspace`
  - `render_annotation_overlays(original_image: Path, mapping: NativeAnnotationMapping, output_root: Path) -> OverlayArtifacts`

- [ ] **Step 1: Add failing workspace and overlay tests**

Test the following exact behavior:

```python
def test_prepare_workspace_uses_atomic_final_rename(
    phase04_5n_fixture,
) -> None:
    result = prepare_fixture_n1_workspace(
        phase04_5n_fixture,
        timestamp="20260715_030000000",
    )
    assert result.workspace_root.name == (
        "phase04_5n_staged_annotation_corrections_20260715_030000000"
    )
    assert not any(
        child.name.startswith(".phase04_5n_staged_annotation_corrections")
        for child in result.workspace_root.parent.iterdir()
    )


def test_existing_final_workspace_blocks_without_overwrite(
    phase04_5n_fixture,
) -> None:
    prepare_fixture_n1_workspace(
        phase04_5n_fixture,
        timestamp="20260715_030000001",
    )
    with pytest.raises(StagedWorkspaceError, match="already exists"):
        prepare_fixture_n1_workspace(
            phase04_5n_fixture,
            timestamp="20260715_030000001",
        )


def test_overlay_rendering_is_deterministic(phase04_5n_fixture) -> None:
    first = prepare_fixture_n1_workspace(
        phase04_5n_fixture,
        timestamp="20260715_030000002",
    )
    second = prepare_fixture_n1_workspace(
        phase04_5n_fixture,
        timestamp="20260715_030000003",
    )
    assert overlay_hashes(first.workspace_root) == overlay_hashes(second.workspace_root)


def test_missing_original_image_blocks_official_n1_pass(
    phase04_5n_fixture,
) -> None:
    remove_first_original_image(phase04_5n_fixture)
    with pytest.raises(StagedWorkspaceError, match="original image"):
        prepare_fixture_n1_workspace(
            phase04_5n_fixture,
            timestamp="20260715_030000004",
        )
```

Also test source-manifest mismatch, forced overlay exception cleanup, canonical source hash drift between start/end, protected external asset fingerprint change, no-overwrite blocked evidence, and exact workspace file inventory.

- [ ] **Step 2: Run tests and observe expected missing behavior failures**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_staging.py -q
```

- [ ] **Step 3: Implement deterministic overlay rendering**

Use Pillow with fixed constants:

```python
BEFORE_COLOR = (255, 165, 0)
AFTER_COLOR = (0, 200, 0)
COMBINED_BEFORE_COLOR = (255, 80, 80)
COMBINED_AFTER_COLOR = (80, 220, 120)
LINE_WIDTH = 4
JPEG_QUALITY = 95
JPEG_SUBSAMPLING = 0
```

For each case, render:

- `overlays/before/{correction_case_id}.jpg`
- `overlays/after/{correction_case_id}.jpg`
- `overlays/combined/{correction_case_id}.jpg`

Each image must visibly include review case ID, native annotation ID, image dimensions, and before/after coordinates. Source images remain unchanged.

- [ ] **Step 4: Implement exact N1 workspace layout**

Write all outputs first to a sibling staging directory:

```text
source/
canonical_snapshot/
staged/
diff/
overlays/before/
overlays/after/
overlays/combined/
evidence/
```

Copy the exact authoritative predecessor inputs listed in the design. Copy canonical source bytes to `canonical_snapshot/canonical_validation_coco.json`; write its path/hash/schema/count contract to `canonical_snapshot/canonical_source_contract.json`.

Write:

- `staged/staged_corrected_validation_coco.json`
- `diff/annotation_correction_mapping.csv`
- `diff/annotation_correction_diff.csv`
- `diff/annotation_correction_diff.json`
- `diff/annotation_correction_diff.md`
- `evidence/semantic_validation.json`
- `evidence/workspace_manifest.csv`
- `evidence/SHA256SUMS.csv`
- `evidence/gate_result.json`

Then verify every manifest member and atomically rename staging to final.

- [ ] **Step 5: Implement N1 PASS gate payload**

`evidence/gate_result.json` must include:

```json
{
  "gate_id": "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS",
  "outcome": "PASS",
  "classification": "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED",
  "proposal_count": 2,
  "mapped_annotation_count": 2,
  "changed_annotation_count": 2,
  "image_count_delta": 0,
  "annotation_count_delta": 0,
  "category_count_delta": 0,
  "canonical_source_modified": false,
  "test_split_read": false,
  "model_inference_executed": false,
  "dataset_modified": false,
  "registry_modified": false,
  "fixed_splits_modified": false,
  "training_started": false,
  "retraining_status": "NOT_YET_APPROVED",
  "deployment_acceptance": "NOT_YET_APPROVED"
}
```

Include source/staged SHA256, exact changed native annotation IDs, predecessor workspace identity, and generated timestamp as additional fields.

- [ ] **Step 6: Implement no-overwrite BLOCKED evidence**

On failure, remove only the current staging directory and write a uniquely named JSON under:

```text
G:\Project\FleetVision_Review_Packages\Phase04_5N\_blocked_results\
```

The blocked result records failed stage, exception type/message, source hashes already verified, and all safety declarations. It never creates or modifies the intended final workspace.

- [ ] **Step 7: Run all N1 staging tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_staging.py -q --junitxml outputs/tmp/phase04_5n_n1.xml
```

Expected structured result: zero failures/errors.

- [ ] **Step 8: Check Task 4 boundary**

```powershell
git diff --check
git status --short
```

Generated fixture workspaces must be under pytest temporary directories or `outputs/tmp/`, never under tracked repository paths.

---

### Task 5: Add N1 Python CLI, PowerShell wrapper, and real wrapper integration tests

**Files:**
- Create: `scripts/phase04_5_stage_annotation_corrections.py`
- Create: `scripts/phase04_5_stage_annotation_corrections.ps1`
- Create: `tests/test_phase04_5n_cli.py`
- Create: `docs/01_phase_guides/phase_04_5_annotation_correction_promotion.md`

**Interfaces:**
- Python CLI arguments:
  - `--project-root`
  - `--config`
  - `--completed-review-workspace`
  - `--timestamp`
- PowerShell parameters:
  - `ProjectRoot`
  - `Config`
  - `CompletedReviewWorkspace`
  - `Timestamp`

- [ ] **Step 1: Write failing Python CLI integration test**

```python
def test_n1_python_cli_returns_structured_pass_json(
    phase04_5n_fixture,
    project_python: Path,
) -> None:
    result = subprocess.run(
        [
            str(project_python),
            "scripts/phase04_5_stage_annotation_corrections.py",
            "--project-root",
            str(phase04_5n_fixture.project_root),
            "--config",
            str(phase04_5n_fixture.config_path),
            "--completed-review-workspace",
            str(phase04_5n_fixture.completed_review_root),
            "--timestamp",
            "20260715_031000000",
        ],
        cwd=phase04_5n_fixture.project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["outcome"] == "PASS"
    assert payload["classification"] == (
        "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED"
    )
```

- [ ] **Step 2: Write failing Windows PowerShell wrapper test**

On Windows, invoke the actual `.ps1`, not a text parser:

```python
@pytest.mark.skipif(shutil.which("powershell.exe") is None, reason="Windows PowerShell unavailable")
def test_n1_powershell_wrapper_forwards_every_required_parameter(
    phase04_5n_fixture,
) -> None:
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "scripts/phase04_5_stage_annotation_corrections.ps1",
            "-ProjectRoot",
            str(phase04_5n_fixture.project_root),
            "-Config",
            str(phase04_5n_fixture.config_path),
            "-CompletedReviewWorkspace",
            str(phase04_5n_fixture.completed_review_root),
            "-Timestamp",
            "20260715_031000001",
        ],
        cwd=phase04_5n_fixture.project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(last_json_line(result.stdout))
    assert payload["classification"] == (
        "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED"
    )
```

This test is mandatory and directly guards against omitted wrapper parameters.

- [ ] **Step 3: Run tests and observe script-not-found failures**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase04_5n_cli.py -q
```

- [ ] **Step 4: Implement thin Python CLI**

The script imports `main` from the staging module, uses `argparse`, calls one domain function, and prints exactly one final JSON object. On a blocked result, print one structured BLOCKED JSON object to stderr and return exit code `1`.

- [ ] **Step 5: Implement thin PowerShell 5.1 wrapper**

```powershell
#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProjectRoot,
    [Parameter(Mandatory = $true)][string]$Config,
    [Parameter(Mandatory = $true)][string]$CompletedReviewWorkspace,
    [Parameter(Mandatory = $true)][string]$Timestamp
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

& $Python `
    (Join-Path $ProjectRoot "scripts\phase04_5_stage_annotation_corrections.py") `
    --project-root $ProjectRoot `
    --config $Config `
    --completed-review-workspace $CompletedReviewWorkspace `
    --timestamp $Timestamp

if ($LASTEXITCODE -ne 0) {
    throw "Phase 04.5N-1 staged correction build failed"
}
```

Do not parse, rewrite, or infer the Python JSON payload in PowerShell.

- [ ] **Step 6: Add the N1 runbook section**

Document the exact production command but mark it `NOT AUTHORIZED BY IMPLEMENTATION PLAN`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File "G:\Project\FleetVision\scripts\phase04_5_stage_annotation_corrections.ps1" `
  -ProjectRoot "G:\Project\FleetVision" `
  -Config "G:\Project\FleetVision\configs\data\phase04_5n_annotation_correction_promotion_config.yaml" `
  -CompletedReviewWorkspace "G:\Project\FleetVision_Review_Packages\Phase04_5M\phase04_5m_annotation_correction_review_20260715_014932067" `
  -Timestamp (Get-Date -Format "yyyyMMdd_HHmmssfff")
```

Document all N1 outputs and acceptance values.

- [ ] **Step 7: Run N1 CLI and wrapper tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase04_5n_cli.py -q --junitxml outputs/tmp/phase04_5n_cli_n1.xml
```

Expected structured result: zero failures/errors; PowerShell test passes on Windows.

- [ ] **Step 8: Parse the PowerShell wrapper with the PowerShell 5.1 parser**

```powershell
$Errors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
  "scripts\phase04_5_stage_annotation_corrections.ps1",
  [ref]$null,
  [ref]$Errors
) | Out-Null
if ($Errors.Count -ne 0) { throw ($Errors | Out-String) }
```

- [ ] **Step 9: Check Task 5 boundary**

Run `git diff --check` and confirm exact intended paths only.

---

### Task 6: Implement N2 package re-verification, repository guard, and explicit authorization preflight

**Files:**
- Create: `src/fleetvision/review/annotation_correction_promotion.py`
- Create: `tests/test_annotation_correction_promotion.py`

**Interfaces:**
- Produces:
  - `VerifiedN1Workspace`
  - `RepositoryPromotionState`
  - `PromotionRequest`
  - `PromotionPreflight`
  - `verify_n1_workspace(config: Phase04_5NConfig, workspace_root: Path) -> VerifiedN1Workspace`
  - `verify_repository_promotion_state(project_root: Path, *, expected_head: str, allowed_status_prefixes: tuple[str, ...]) -> RepositoryPromotionState`
  - `prepare_promotion_preflight(config: Phase04_5NConfig, request: PromotionRequest) -> PromotionPreflight`

- [ ] **Step 1: Write failing N2 preflight tests**

```python
def test_n2_requires_exact_authorization_phrase(valid_n1_workspace) -> None:
    request = make_promotion_request(
        valid_n1_workspace,
        authorization_phrase="",
        execute=True,
    )
    with pytest.raises(PromotionAuthorizationError, match="authorization"):
        prepare_promotion_preflight(valid_n1_workspace.config, request)


def test_n2_rejects_tampered_n1_manifest(valid_n1_workspace) -> None:
    tamper_file(valid_n1_workspace.root / "diff/annotation_correction_diff.json")
    request = make_promotion_request(valid_n1_workspace, execute=False)
    with pytest.raises(PromotionPreflightError, match="SHA256"):
        prepare_promotion_preflight(valid_n1_workspace.config, request)


def test_n2_rejects_current_canonical_hash_drift(valid_n1_workspace) -> None:
    change_current_canonical(valid_n1_workspace)
    request = make_promotion_request(valid_n1_workspace, execute=False)
    with pytest.raises(PromotionPreflightError, match="canonical source SHA256"):
        prepare_promotion_preflight(valid_n1_workspace.config, request)


def test_n2_rejects_dirty_repository_outside_allowlist(
    valid_n1_workspace,
    temporary_git_project,
) -> None:
    (temporary_git_project / "unexpected.txt").write_text("dirty", encoding="utf-8")
    with pytest.raises(PromotionPreflightError, match="worktree"):
        verify_repository_promotion_state(
            temporary_git_project,
            expected_head=git_head(temporary_git_project),
            allowed_status_prefixes=("outputs/metadata/external_assets/",),
        )
```

Also test branch not `main`, local/origin disagreement, expected head mismatch, staged index nonempty, staged SHA mismatch, N1 classification not PASS, changed-count not 2, manifest missing, repeat promotion evidence path collision, and a current canonical file that already equals staged hash.

- [ ] **Step 2: Run tests and observe module import failure**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_promotion.py -q
```

- [ ] **Step 3: Implement N1 package re-verification**

`verify_n1_workspace` must:

1. require `evidence/gate_result.json` PASS and exact N1 classification;
2. verify `workspace_manifest.csv` and `SHA256SUMS.csv` before reading staged COCO/diff;
3. require exactly two changed native IDs;
4. re-run the complete semantic validation using canonical snapshot and staged COCO;
5. verify staged SHA and source SHA against gate evidence;
6. verify overlays and source evidence exist and match manifests;
7. reject any test-split path.

- [ ] **Step 4: Implement repository guard without mutating Git**

Use `subprocess.run(args, cwd=project_root, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)` and evaluate `returncode`. Required facts:

- branch exactly `main`;
- `HEAD`, `origin/main`, and `git ls-remote origin refs/heads/main` equal the supplied expected head;
- staged index empty;
- worktree contains only approved pre-existing `outputs/metadata/external_assets/` entries;
- canonical file is not staged;
- no force/reset/clean operation exists in this module.

- [ ] **Step 5: Implement `PromotionRequest` and preflight**

```python
@dataclass(frozen=True)
class PromotionRequest:
    project_root: Path
    n1_workspace_root: Path
    expected_repository_head: str
    expected_canonical_sha256: str
    expected_staged_sha256: str
    authorization_phrase: str
    execute: bool
    timestamp: str


@dataclass(frozen=True)
class PromotionPreflight:
    request: PromotionRequest
    verified_n1: VerifiedN1Workspace
    repository_state: RepositoryPromotionState
    current_canonical_path: Path
    current_canonical_sha256: str
    staged_coco_path: Path
    staged_coco_sha256: str
    evidence_workspace_root: Path
```

When `execute=False`, authorization phrase may be empty and the function performs read-only preflight. When `execute=True`, the phrase must exactly match config and every expected hash/head must be explicitly supplied and equal verified facts.

- [ ] **Step 6: Run N2 preflight tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_promotion.py -q --junitxml outputs/tmp/phase04_5n_n2_preflight.xml
```

- [ ] **Step 7: Check Task 6 boundary**

Run `git diff --check`; confirm tests use temporary Git repositories and temporary canonical files only.

---

### Task 7: Implement verified backup, atomic promotion, post-verification, and rollback

**Files:**
- Modify: `src/fleetvision/review/annotation_correction_promotion.py`
- Modify: `tests/test_annotation_correction_promotion.py`

**Interfaces:**
- Produces:
  - `PromotionResult`
  - `RollbackResult`
  - `execute_atomic_promotion(config: Phase04_5NConfig, preflight: PromotionPreflight, *, fault_injector: Callable[[str], None] | None = None) -> PromotionResult`
  - `restore_verified_backup(canonical_path: Path, backup_path: Path, *, expected_before_sha256: str, evidence_root: Path) -> RollbackResult`

- [ ] **Step 1: Add failing atomic-promotion tests**

```python
def test_atomic_promotion_creates_verified_backup_and_replaces_canonical(
    valid_promotion_preflight,
) -> None:
    result = execute_atomic_promotion(
        valid_promotion_preflight.config,
        valid_promotion_preflight,
    )
    assert result.classification == "PHASE_04_5N_ANNOTATION_CORRECTIONS_PROMOTED"
    assert result.backup_verified is True
    assert result.atomic_promotion_verified is True
    assert result.post_promotion_semantic_validation == "PASS"
    assert sha256_file(result.canonical_path) == result.after_sha256
    assert sha256_file(result.backup_path) == result.before_sha256


def test_post_replace_failure_restores_original_bytes(
    valid_promotion_preflight,
) -> None:
    original = valid_promotion_preflight.current_canonical_path.read_bytes()

    def fail_after_replace(stage: str) -> None:
        if stage == "after_replace_before_postverify":
            raise RuntimeError("injected post-replace failure")

    with pytest.raises(PromotionExecutionError, match="restored"):
        execute_atomic_promotion(
            valid_promotion_preflight.config,
            valid_promotion_preflight,
            fault_injector=fail_after_replace,
        )
    assert valid_promotion_preflight.current_canonical_path.read_bytes() == original


def test_backup_hash_mismatch_blocks_before_replace(valid_promotion_preflight) -> None:
    corrupt_backup_copy_during_test(valid_promotion_preflight)
    with pytest.raises(PromotionExecutionError, match="backup SHA256"):
        execute_atomic_promotion(
            valid_promotion_preflight.config,
            valid_promotion_preflight,
        )
```

Also test temp-file hash mismatch, `os.replace` failure, rollback temp-file failure, rollback hash mismatch, evidence workspace collision, second execution blocked, canonical path symlink/reparse escape blocked, and no downstream command invocation.

- [ ] **Step 2: Run tests and observe missing execution behavior**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_promotion.py -q
```

- [ ] **Step 3: Implement the N2 evidence workspace**

Use:

```text
Phase04_5N_Promotion/
└─ phase04_5n_annotation_correction_promotion_{timestamp}/
   ├─ source/
   │  ├─ n1_gate_result.json
   │  ├─ n1_workspace_manifest.csv
   │  └─ n1_sha256sums.csv
   ├─ backup/
   │  └─ canonical_validation_coco.before.json
   └─ evidence/
      ├─ preflight.json
      ├─ promotion_result.json
      ├─ rollback_result.json        # only when rollback is attempted
      ├─ workspace_manifest.csv
      └─ SHA256SUMS.csv
```

Create it no-overwrite. It remains outside Git.

- [ ] **Step 4: Implement verified backup**

Copy canonical bytes with `shutil.copyfile`, flush and `os.fsync`, then verify backup size/SHA256 equals current canonical before creating any destination-directory temp file. Record source and backup paths/hashes.

- [ ] **Step 5: Implement atomic replacement**

Create a unique temp file in the canonical destination directory, copy staged bytes, flush/fsync, verify temp SHA equals N1 staged SHA, then call `os.replace(temp_path, canonical_path)`. After replace, verify canonical SHA equals staged SHA.

- [ ] **Step 6: Implement complete post-promotion semantic validation**

Reload promoted canonical and compare against N1 canonical snapshot/staged evidence:

- exactly two changed native annotations;
- exact before/after bbox and area;
- all other annotations/images/categories unchanged;
- counts and ID sets unchanged;
- promoted SHA equals staged SHA;
- no test read/inference/materialization/Registry/split/training side effect.

- [ ] **Step 7: Implement rollback on every post-replace exception**

If replacement happened and any later step fails:

1. create a temp restore file in the canonical directory from the verified backup;
2. flush/fsync and verify backup SHA;
3. atomically replace canonical with restore temp;
4. verify restored SHA equals original before SHA;
5. write `rollback_result.json` with `RESTORED_AND_VERIFIED` or `RESTORE_FAILED`;
6. raise `PromotionExecutionError` and stop.

Never continue to any downstream phase after rollback.

- [ ] **Step 8: Implement N2 PASS result**

`promotion_result.json` must include:

```text
OUTCOME=PASS
CLASSIFICATION=PHASE_04_5N_ANNOTATION_CORRECTIONS_PROMOTED
PROMOTED_ANNOTATION_COUNT=2
BACKUP_VERIFIED=YES
ATOMIC_PROMOTION_VERIFIED=YES
POST_PROMOTION_SEMANTIC_VALIDATION=PASS
TEST_SPLIT_READ=NO
MODEL_INFERENCE_EXECUTED=NO
DATASET_MATERIALIZATION_EXECUTED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```

Also record repository head, N1 workspace identity, canonical path, before/staged/after/backup hashes, native annotation IDs, and timestamps.

- [ ] **Step 9: Run all N2 atomic and rollback tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_annotation_correction_promotion.py -q --junitxml outputs/tmp/phase04_5n_n2_atomic.xml
```

- [ ] **Step 10: Check Task 7 boundary**

Confirm the real repository canonical COCO remains byte-identical; all mutation tests operated only on temporary fixture repositories.

---

### Task 8: Add N2 CLI/PowerShell wrappers and full Windows fixture execution tests

**Files:**
- Create: `scripts/phase04_5_promote_annotation_corrections.py`
- Create: `scripts/phase04_5_promote_annotation_corrections.ps1`
- Modify: `tests/test_phase04_5n_cli.py`
- Modify: `docs/01_phase_guides/phase_04_5_annotation_correction_promotion.md`

**Interfaces:**
- Python CLI:
  - `--project-root`
  - `--config`
  - `--n1-workspace`
  - `--expected-repository-head`
  - `--expected-canonical-sha256`
  - `--expected-staged-sha256`
  - `--authorization-phrase`
  - `--timestamp`
  - mutually exclusive `--dry-run` / `--execute`; default is dry-run.
- PowerShell parameters mirror every Python argument exactly.

- [ ] **Step 1: Write failing N2 dry-run CLI test**

Use a temporary Git repository with `main`, a bare `origin`, exact local/origin/remote equality, a valid N1 fixture workspace, and a temporary canonical COCO. Assert dry-run returns structured preflight PASS and does not change canonical hash.

- [ ] **Step 2: Write failing N2 execute CLI test against temporary canonical data**

Invoke the actual Python script with `--execute` and the exact authorization phrase. Assert canonical hash changes to staged hash, backup exists, and result classification is exact.

- [ ] **Step 3: Write actual PowerShell wrapper end-to-end tests**

On Windows, invoke `scripts/phase04_5_promote_annotation_corrections.ps1` twice in separate fresh fixtures:

1. dry-run mode;
2. execute mode with authorization.

The test must fail if any required argument is not forwarded, if native stderr is incorrectly treated as failure when exit code is zero, or if the wrapper parses human-readable output instead of the final JSON line.

- [ ] **Step 4: Run tests and observe script-not-found failures**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase04_5n_cli.py -q
```

- [ ] **Step 5: Implement thin Python promotion CLI**

The CLI creates `PromotionRequest`, runs preflight, and only calls `execute_atomic_promotion` when `--execute` is present. Final stdout line is one JSON object. All BLOCKED results use exit code `1` and structured JSON to stderr.

- [ ] **Step 6: Implement thin PowerShell wrapper**

Use mandatory parameters for project/config/N1 workspace/expected hashes/head/timestamp. Use switches `DryRun` and `Execute`, reject both or neither only when Python defaults cannot safely disambiguate, and forward the exact authorization phrase. Do not perform Git mutation or canonical file operations in PowerShell.

- [ ] **Step 7: Parse both wrappers with PowerShell 5.1 parser**

Run parser checks for N1 and N2 scripts. Zero parser errors are required.

- [ ] **Step 8: Complete N2 runbook with authorization stop**

Document read-only preflight command. For the execute command, populate values from N1 gate evidence instead of handwritten placeholders:

```powershell
$ProjectRoot = "G:\Project\FleetVision"
$Config = Join-Path $ProjectRoot "configs\data\phase04_5n_annotation_correction_promotion_config.yaml"
$N1Workspace = Read-Host "Paste the exact verified N1 PASS workspace path"
if ([string]::IsNullOrWhiteSpace($N1Workspace)) {
    throw "N1 workspace path is required"
}
$N1Gate = Get-Content (Join-Path $N1Workspace "evidence\gate_result.json") -Raw | ConvertFrom-Json
$Head = (git -C $ProjectRoot rev-parse HEAD).Trim()

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File (Join-Path $ProjectRoot "scripts\phase04_5_promote_annotation_corrections.ps1") `
  -ProjectRoot $ProjectRoot `
  -Config $Config `
  -N1Workspace $N1Workspace `
  -ExpectedRepositoryHead $Head `
  -ExpectedCanonicalSha256 $N1Gate.canonical_source_sha256 `
  -ExpectedStagedSha256 $N1Gate.staged_coco_sha256 `
  -AuthorizationPhrase "PHASE_04_5N_2_CANONICAL_PROMOTION_AUTHORIZED" `
  -Timestamp (Get-Date -Format "yyyyMMdd_HHmmssfff") `
  -Execute
```

The operator must paste one exact verified N1 PASS workspace path. The implementation must never infer the latest workspace automatically.

- [ ] **Step 9: Run all CLI/wrapper integration tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_phase04_5n_cli.py -q --junitxml outputs/tmp/phase04_5n_cli_all.xml
```

Expected: Python and PowerShell fixture integrations pass; real canonical data remains untouched.

- [ ] **Step 10: Check Task 8 boundary**

Run `git diff --check`, inspect exact changed paths, and confirm no generated fixture artifact is tracked.

---

### Task 9: Full regression, documentation synchronization, controlled closure, and execution handoff

**Files:**
- Modify: `docs/00_project_management/PROJECT_STATUS.md`
- Modify: `docs/00_project_management/HANDOFF_CURRENT.md`
- Modify: `docs/00_project_management/MASTER_PHASE_MAP.md`
- Modify: `docs/00_project_management/phase_logs/PHASE_04_5_LOG.md`
- Modify: `docs/00_project_management/DECISION_LOG.md` only when required by a newly discovered governance decision.
- Review all new Phase 04.5N files.

**Interfaces:**
- Produces implementation closure classification:
  - `PHASE_04_5N_IMPLEMENTED_TESTED_AND_READY_FOR_N1_EXECUTION`
- Does not execute N1 or N2 against production artifacts.

- [ ] **Step 1: Re-read the approved design and create a requirement-to-test matrix**

Add a table to the phase guide mapping every design section 2–17 to a production function and at least one focused test. Missing coverage blocks closure.

- [ ] **Step 2: Run all Phase 04.5N focused tests using JUnit XML**

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_annotation_correction_promotion_contract.py `
  tests/test_annotation_correction_staging.py `
  tests/test_annotation_correction_promotion.py `
  tests/test_phase04_5n_cli.py `
  -q `
  --junitxml outputs/tmp/phase04_5n_focused.xml
```

Read the XML and require `failures=0`, `errors=0`, and `skipped=0` on the Windows release environment.

- [ ] **Step 3: Run Phase 04.5M regressions**

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_annotation_correction_review_mapping.py `
  tests/test_annotation_correction_review_package.py `
  tests/test_annotation_correction_review_state.py `
  tests/test_annotation_correction_review_app.py `
  tests/test_annotation_correction_review_export.py `
  -q `
  --junitxml outputs/tmp/phase04_5m_regression_for_n.xml
```

Require zero failures/errors.

- [ ] **Step 4: Run existing canonical COCO and promotion regressions**

Run the repository tests covering:

```text
tests/test_normalize_external_coco_categories.py
tests/test_validate_external_annotation_split_balance.py
tests/test_repair_external_coco_bbox.py
tests/test_promote_human_review_schema.py
```

Use JUnit XML and require zero failures/errors.

- [ ] **Step 5: Run the full repository suite**

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml outputs/tmp/phase04_5n_full_repository.xml
```

Use the XML counts as authoritative. Do not parse the console phrase `passed`.

- [ ] **Step 6: Compile every changed Python file**

```powershell
.\.venv\Scripts\python.exe -m py_compile `
  src/fleetvision/review/annotation_correction_promotion_contract.py `
  src/fleetvision/review/annotation_correction_staging.py `
  src/fleetvision/review/annotation_correction_promotion.py `
  scripts/phase04_5_stage_annotation_corrections.py `
  scripts/phase04_5_promote_annotation_corrections.py `
  tests/annotation_correction_promotion_fixtures.py `
  tests/test_annotation_correction_promotion_contract.py `
  tests/test_annotation_correction_staging.py `
  tests/test_annotation_correction_promotion.py `
  tests/test_phase04_5n_cli.py
```

- [ ] **Step 7: Re-run PowerShell 5.1 parser and wrapper end-to-end tests**

Both `.ps1` files must parse with zero errors and both actual wrapper integration tests must pass on the Windows release checkout.

- [ ] **Step 8: Capture protected fingerprints before and after verification**

Capture content fingerprints for:

- canonical train/valid/test COCO files;
- `dataset/00_catalog/external_dataset_registry.csv`;
- fixed split artifacts;
- `outputs/metadata/external_assets/`;
- completed 04.5M workspace.

For implementation closure, every fingerprint must remain identical. The only allowed changes are repository code/config/tests/docs in the exact allowlist.

- [ ] **Step 9: Update repository governance documents**

Record:

```text
PHASE=04.5N
IMPLEMENTATION_OUTCOME=PASS
CLASSIFICATION=PHASE_04_5N_IMPLEMENTED_TESTED_AND_READY_FOR_N1_EXECUTION
N1_EXECUTED=NO
N2_EXECUTED=NO
CANONICAL_COCO_MODIFIED=NO
TEST_SPLIT_READ=NO
MODEL_INFERENCE_EXECUTED=NO
DATASET_MODIFIED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
NEXT_AUTHORIZED_ACTION=PHASE_04_5N_1_STAGED_CORRECTION_BUILD_AND_VALIDATION
```

- [ ] **Step 10: Verify the exact repository allowlist**

Expected implementation paths are exactly:

```text
configs/data/phase04_5n_annotation_correction_promotion_config.yaml
docs/01_phase_guides/phase_04_5_annotation_correction_promotion.md
docs/00_project_management/PROJECT_STATUS.md
docs/00_project_management/HANDOFF_CURRENT.md
docs/00_project_management/MASTER_PHASE_MAP.md
docs/00_project_management/phase_logs/PHASE_04_5_LOG.md
scripts/phase04_5_stage_annotation_corrections.py
scripts/phase04_5_stage_annotation_corrections.ps1
scripts/phase04_5_promote_annotation_corrections.py
scripts/phase04_5_promote_annotation_corrections.ps1
src/fleetvision/review/annotation_correction_promotion_contract.py
src/fleetvision/review/annotation_correction_staging.py
src/fleetvision/review/annotation_correction_promotion.py
tests/annotation_correction_promotion_fixtures.py
tests/test_annotation_correction_promotion_contract.py
tests/test_annotation_correction_staging.py
tests/test_annotation_correction_promotion.py
tests/test_phase04_5n_cli.py
```

`DECISION_LOG.md` may be added only when the implementation actually introduces a new governance decision and the final allowlist is updated before staging.

- [ ] **Step 11: Run Git whitespace and staged-diff checks**

```powershell
git diff --check
git status --short
git diff --name-only
```

No broad `git add .`, `git add -A`, force push, hard reset, clean, or protected-path staging is permitted.

- [ ] **Step 12: Exact-stage and commit only when the implementation Gate authorizes it**

```powershell
git add -- `
  configs/data/phase04_5n_annotation_correction_promotion_config.yaml `
  docs/01_phase_guides/phase_04_5_annotation_correction_promotion.md `
  docs/00_project_management/PROJECT_STATUS.md `
  docs/00_project_management/HANDOFF_CURRENT.md `
  docs/00_project_management/MASTER_PHASE_MAP.md `
  docs/00_project_management/phase_logs/PHASE_04_5_LOG.md `
  scripts/phase04_5_stage_annotation_corrections.py `
  scripts/phase04_5_stage_annotation_corrections.ps1 `
  scripts/phase04_5_promote_annotation_corrections.py `
  scripts/phase04_5_promote_annotation_corrections.ps1 `
  src/fleetvision/review/annotation_correction_promotion_contract.py `
  src/fleetvision/review/annotation_correction_staging.py `
  src/fleetvision/review/annotation_correction_promotion.py `
  tests/annotation_correction_promotion_fixtures.py `
  tests/test_annotation_correction_promotion_contract.py `
  tests/test_annotation_correction_staging.py `
  tests/test_annotation_correction_promotion.py `
  tests/test_phase04_5n_cli.py

git diff --cached --name-only
git diff --cached --check
git commit -m "feat: implement phase04.5N annotation correction promotion"
```

Verify the staged path set equals the allowlist before commit.

- [ ] **Step 13: Non-force push and remote reconciliation only when authorized**

```powershell
git push origin main
git fetch origin main
git rev-parse HEAD
git rev-parse origin/main
git ls-remote origin refs/heads/main
```

All three SHAs must agree. Force push is prohibited.

- [ ] **Step 14: Produce implementation closure evidence**

Create a Result ZIP containing source/config/tests/docs diffs, JUnit XML files, compile evidence, PowerShell parser evidence, wrapper integration evidence, protected fingerprints, exact staged/committed paths, commit SHA, push state, and safety declarations. The ZIP is evidence only and remains outside Git.

- [ ] **Step 15: Stop before production N1 execution**

Implementation closure must state:

```text
N1_EXECUTED=NO
N2_EXECUTED=NO
CANONICAL_COCO_MODIFIED=NO
NEXT_AUTHORIZED_ACTION=PHASE_04_5N_1_STAGED_CORRECTION_BUILD_AND_VALIDATION
```

Do not automatically run the production N1 command from the implementation release workflow.

---

## Production Execution Handoff After Implementation Approval

### N1 execution

After implementation is committed, pushed, and separately authorized, run the actual N1 wrapper against the fixed 04.5M completed workspace. Verify the Result workspace classification and upload a package containing the complete N1 workspace plus SHA256.

N1 PASS must end at:

```text
PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_VALIDATED
CANONICAL_SOURCE_MODIFIED=NO
```

### N2 authorization stop

After N1 PASS, stop and request explicit canonical promotion authorization. Do not infer authorization from N1 PASS, implementation approval, plan approval, or schedule pressure.

### N2 execution

Only after the user explicitly authorizes N2, run dry-run preflight first, verify the preflight evidence, then run execute with the exact expected repository head and N1-recorded source/staged hashes. A successful N2 ends at:

```text
PHASE_04_5N_ANNOTATION_CORRECTIONS_PROMOTED
```

No dataset materialization, retraining, evaluation, or deployment acceptance follows automatically.

---

## Plan Self-Review

- Spec coverage: every approved-design section 2–17 maps to Tasks 1–9.
- Placeholder scan: no deferred implementation marker is used; runtime-selected workspace values are explicitly operator-supplied and never auto-discovered.
- Type consistency: shared types originate in `annotation_correction_promotion_contract.py`; N1 and N2 signatures consistently consume those types.
- Scope check: N1 and N2 are implemented in separate modules/Gates; production N2 execution remains separately authorized.
- Failure model: no-overwrite staging, structured BLOCKED evidence, verified backup, atomic replace, post-verification, and rollback are all explicitly tested.
- Wrapper risk: actual Windows PowerShell wrappers are executed in fixture integration tests, preventing parameter-forwarding omissions from escaping static review.
- Safety boundary: implementation tests never mutate real canonical COCO, read test split, run inference/training, or modify Registry/fixed splits/protected assets.

The plan itself authorizes no implementation, N1 execution, canonical promotion, dataset materialization, retraining, evaluation, or deployment acceptance.
