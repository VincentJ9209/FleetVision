from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from annotation_correction_review_fixtures import build_fixture
from fleetvision.review.annotation_correction_review_app import (
    case_widget_key,
    load_correction_review_runtime,
    next_case_id,
    runtime_session_identity,
    save_correction_review_selection,
    suggested_operation,
)
from fleetvision.review.annotation_correction_review_mapping import BBoxCoordinates, CorrectionReviewSelection
from fleetvision.review.annotation_correction_review_package import load_correction_review_config, prepare_correction_review_package


def runtime(tmp_path: Path):
    fixture = build_fixture(tmp_path)
    config = load_correction_review_config(fixture.config_path, fixture.project_root)
    package = prepare_correction_review_package(config, fixture.f2_root, timestamp="20260714T200000Z")
    return load_correction_review_runtime(fixture.config_path, fixture.project_root, workspace_root=package.workspace_root)


def test_next_case_id_clamps_at_boundaries() -> None:
    ids = ("m_case_001", "m_case_002")
    assert next_case_id(ids, "m_case_001", direction=-1) == "m_case_001"
    assert next_case_id(ids, "m_case_002", direction=1) == "m_case_002"


def test_case_widget_key_is_case_isolated() -> None:
    assert case_widget_key("decision", "m_case_001") != case_widget_key("decision", "m_case_002")


def test_runtime_session_identity_changes_with_workspace(tmp_path: Path) -> None:
    assert runtime_session_identity(tmp_path/"c", tmp_path/"r", tmp_path/"a") != runtime_session_identity(tmp_path/"c", tmp_path/"r", tmp_path/"b")


def test_suggestions_do_not_persist(tmp_path: Path) -> None:
    rt = runtime(tmp_path)
    assert suggested_operation(rt.package.cases[0]) == "RESIZE_OR_REDRAW_BBOX"
    assert suggested_operation(rt.package.cases[1]) == "REMOVE_DUPLICATE_BBOX"
    assert rt.store.progress().pending == 2


def test_save_creates_backup_after_every_successful_save(tmp_path: Path) -> None:
    rt = runtime(tmp_path)
    case = rt.package.cases[0]
    selection = CorrectionReviewSelection(
        correction_review_status="reviewed",
        correction_decision="CONFIRM_GT_CORRECTION_REQUIRED",
        correction_operation="RESIZE_OR_REDRAW_BBOX",
        target_gt_bbox_ids=("gt_001",),
        replacement_bbox=BBoxCoordinates(18, 28, 220, 190),
        correction_reason="依影像重畫損傷範圍",
    )
    result = save_correction_review_selection(rt, case.correction_case_id, selection, reviewed_at=datetime(2026,7,14,20,0,tzinfo=ZoneInfo("Asia/Taipei")))
    assert result.backup_path.is_file()
    assert result.progress.reviewed == 1
