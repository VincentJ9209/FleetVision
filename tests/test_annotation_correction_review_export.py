from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from annotation_correction_review_fixtures import build_fixture
from fleetvision.review.annotation_correction_review_app import load_correction_review_runtime, save_correction_review_selection
from fleetvision.review.annotation_correction_review_export import CorrectionReviewExportError, export_completed_correction_review
from fleetvision.review.annotation_correction_review_mapping import BBoxCoordinates, CorrectionReviewSelection
from fleetvision.review.annotation_correction_review_package import load_correction_review_config, prepare_correction_review_package, sha256_file


def setup_runtime(tmp_path: Path):
    fixture = build_fixture(tmp_path)
    config = load_correction_review_config(fixture.config_path, fixture.project_root)
    package = prepare_correction_review_package(config, fixture.f2_root, timestamp="20260714T210000Z")
    runtime = load_correction_review_runtime(fixture.config_path, fixture.project_root, workspace_root=package.workspace_root)
    return package, runtime


def complete(package, runtime):
    case1, case2 = package.cases
    save_correction_review_selection(runtime, case1.correction_case_id, CorrectionReviewSelection(
        correction_review_status="reviewed", correction_decision="CONFIRM_GT_CORRECTION_REQUIRED",
        correction_operation="RESIZE_OR_REDRAW_BBOX", target_gt_bbox_ids=("gt_001",),
        replacement_bbox=BBoxCoordinates(18,28,220,190), correction_reason="依影像重畫損傷範圍"),
        reviewed_at=datetime(2026,7,14,21,0,tzinfo=ZoneInfo("Asia/Taipei")))
    save_correction_review_selection(runtime, case2.correction_case_id, CorrectionReviewSelection(
        correction_review_status="reviewed", correction_decision="CONFIRM_GT_CORRECTION_REQUIRED",
        correction_operation="REMOVE_DUPLICATE_BBOX", target_gt_bbox_ids=("gt_002",),
        correction_reason="重複標註"), reviewed_at=datetime(2026,7,14,21,5,tzinfo=ZoneInfo("Asia/Taipei")))


def test_export_blocks_incomplete_review(tmp_path: Path) -> None:
    package, runtime = setup_runtime(tmp_path)
    with pytest.raises(CorrectionReviewExportError, match="2/2"):
        export_completed_correction_review(package, runtime.store)


def test_completed_export_creates_expected_artifacts(tmp_path: Path) -> None:
    package, runtime = setup_runtime(tmp_path)
    source_hash = sha256_file(package.source_csv_path)
    complete(package, runtime)
    result = export_completed_correction_review(package, runtime.store)
    assert result.reviewed_csv_path.is_file()
    assert result.reviewed_json_path.is_file()
    assert result.completed_workbook_path.is_file()
    assert result.result_json_path.is_file()
    assert all(path.is_file() for path in result.proposed_overlay_paths)
    assert sha256_file(package.source_csv_path) == source_hash
    assert not list(result.export_root.rglob("*coco*.json"))


def test_completed_export_is_no_overwrite(tmp_path: Path) -> None:
    package, runtime = setup_runtime(tmp_path)
    complete(package, runtime)
    export_completed_correction_review(package, runtime.store)
    with pytest.raises(CorrectionReviewExportError, match="overwrite"):
        export_completed_correction_review(package, runtime.store)
