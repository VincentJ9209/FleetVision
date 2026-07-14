from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from annotation_correction_review_fixtures import build_fixture
from fleetvision.review.annotation_correction_review_mapping import (
    CorrectionReviewSelection,
    derive_canonical_correction_fields,
)
from fleetvision.review.annotation_correction_review_package import load_correction_review_config, prepare_correction_review_package
from fleetvision.review.annotation_correction_review_state import (
    CorrectionProgressCounts,
    CorrectionReviewStateError,
    CorrectionReviewStateStore,
)


def prepared(tmp_path: Path):
    fixture = build_fixture(tmp_path)
    config = load_correction_review_config(fixture.config_path, fixture.project_root)
    package = prepare_correction_review_package(config, fixture.f2_root, timestamp="20260714T190000Z")
    store = CorrectionReviewStateStore(package.app_workspace_root, backup_retention=20)
    store.initialize(package)
    return package, store


def test_initialize_creates_two_pending_cases(tmp_path: Path) -> None:
    _, store = prepared(tmp_path)
    assert store.progress() == CorrectionProgressCounts(2, 0, 2, 0)


def test_save_review_persists_revision_and_audit_event(tmp_path: Path) -> None:
    package, store = prepared(tmp_path)
    case = package.cases[1]
    selection = CorrectionReviewSelection(
        correction_review_status="reviewed",
        correction_decision="CONFIRM_GT_CORRECTION_REQUIRED",
        correction_operation="REMOVE_DUPLICATE_BBOX",
        target_gt_bbox_ids=("gt_002",),
        correction_reason="重複標註",
    )
    canonical = derive_canonical_correction_fields(selection, reviewer="Vincent", reviewed_at=datetime(2026,7,14,19,0,tzinfo=ZoneInfo("Asia/Taipei")), image_width=case.image_width, image_height=case.image_height, available_gt_bbox_ids=("gt_001","gt_002"))
    result = store.save_review(case.correction_case_id, selection, canonical)
    assert result.revision == 1
    assert store.progress().reviewed == 1
    assert '"event_id": 1' in store.event_log_path.read_text(encoding="utf-8")


def test_event_log_sequence_gap_fails_closed(tmp_path: Path) -> None:
    _, store = prepared(tmp_path)
    store.event_log_path.write_text('{"event_id":2}\n', encoding="utf-8")
    with pytest.raises(CorrectionReviewStateError, match="不連續"):
        store.verify_event_log_continuity()


def test_backup_retention_keeps_latest_twenty(tmp_path: Path) -> None:
    _, store = prepared(tmp_path)
    created = [store.create_backup(timestamp=f"20260714T1900{i:02d}000000Z") for i in range(22)]
    remaining = sorted(store.backup_dir.glob("*.sqlite3"))
    assert len(remaining) == 20
    assert created[-1] in remaining and created[-2] in remaining


def test_reviewer_mismatch_blocks(tmp_path: Path) -> None:
    package, store = prepared(tmp_path)
    case = package.cases[0]
    selection = CorrectionReviewSelection(correction_review_status="needs_adjudication", correction_decision="NEEDS_ADJUDICATION", correction_operation="NOT_APPLICABLE", correction_reason="待裁決")
    canonical = derive_canonical_correction_fields(selection, reviewer="Other", reviewed_at=datetime(2026,7,14,19,0,tzinfo=ZoneInfo("Asia/Taipei")), image_width=case.image_width, image_height=case.image_height, available_gt_bbox_ids=("gt_001",))
    with pytest.raises(CorrectionReviewStateError, match="reviewer"):
        store.save_review(case.correction_case_id, selection, canonical)
