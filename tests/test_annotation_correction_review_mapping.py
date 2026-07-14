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
    assert parse_target_bbox_ids('["gt_002","gt_001"]') == ("gt_001", "gt_002")


def test_parse_target_bbox_ids_rejects_duplicates() -> None:
    with pytest.raises(CorrectionMappingValidationError, match="重複"):
        parse_target_bbox_ids('["gt_001","gt_001"]')


def test_parse_replacement_bbox_returns_typed_coordinates() -> None:
    result = parse_replacement_bbox('{"x1":10.0,"y1":20.0,"x2":110.0,"y2":120.0}')
    assert result == BBoxCoordinates(x1=10.0, y1=20.0, x2=110.0, y2=120.0)


def test_reject_keep_current_requires_not_applicable_and_no_geometry() -> None:
    selection = CorrectionReviewSelection(
        correction_review_status="reviewed",
        correction_decision="REJECT_CORRECTION_KEEP_CURRENT_GT",
        correction_operation="RESIZE_OR_REDRAW_BBOX",
        correction_reason="現有 GT 正確",
    )
    with pytest.raises(CorrectionMappingValidationError, match="NOT_APPLICABLE"):
        validate_selection(selection, image_width=640, image_height=480, available_gt_bbox_ids=("gt_001",))


def test_resize_requires_one_target_and_in_bounds_geometry() -> None:
    selection = CorrectionReviewSelection(
        correction_review_status="reviewed",
        correction_decision="CONFIRM_GT_CORRECTION_REQUIRED",
        correction_operation="RESIZE_OR_REDRAW_BBOX",
        target_gt_bbox_ids=("gt_001",),
        replacement_bbox=BBoxCoordinates(10.0, 20.0, 110.0, 120.0),
        correction_reason="現有框未涵蓋完整損傷",
    )
    validate_selection(selection, image_width=640, image_height=480, available_gt_bbox_ids=("gt_001", "gt_002"))


def test_needs_adjudication_maps_to_non_final_status() -> None:
    selection = CorrectionReviewSelection(
        correction_review_status="needs_adjudication",
        correction_decision="NEEDS_ADJUDICATION",
        correction_operation="NOT_APPLICABLE",
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


def test_pending_cannot_preconfirm() -> None:
    selection = CorrectionReviewSelection(
        correction_review_status="pending",
        correction_decision="CONFIRM_GT_CORRECTION_REQUIRED",
        correction_operation="REMOVE_DUPLICATE_BBOX",
        target_gt_bbox_ids=("gt_001",),
        correction_reason="x",
    )
    with pytest.raises(CorrectionMappingValidationError, match="pending"):
        validate_selection(selection, image_width=640, image_height=480, available_gt_bbox_ids=("gt_001",))
