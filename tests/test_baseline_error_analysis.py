from __future__ import annotations

import pandas as pd
import pytest

from fleetvision.evaluation.baseline_error_analysis import (
    BaselineAnalysisError,
    box_iou_xyxy,
    build_data_improvement_priorities,
    categorize_bbox_size,
    evaluate_threshold,
    select_operating_points,
    validate_analysis_config,
)


def _predictions(rows: list[dict[str, object]]) -> pd.DataFrame:
    columns = [
        "image_id",
        "prediction_id",
        "class_id",
        "confidence",
        "x1",
        "y1",
        "x2",
        "y2",
        "bbox_area_ratio",
    ]
    return pd.DataFrame(rows, columns=columns)


def _ground_truth(rows: list[dict[str, object]]) -> pd.DataFrame:
    columns = [
        "image_id",
        "gt_id",
        "class_id",
        "x1",
        "y1",
        "x2",
        "y2",
        "bbox_area_ratio",
    ]
    return pd.DataFrame(rows, columns=columns)


def test_box_iou_xyxy_identity_and_disjoint() -> None:
    assert box_iou_xyxy((0, 0, 10, 10), (0, 0, 10, 10)) == pytest.approx(1.0)
    assert box_iou_xyxy((0, 0, 10, 10), (20, 20, 30, 30)) == pytest.approx(0.0)


def test_evaluate_threshold_matches_one_to_one_and_marks_duplicate() -> None:
    predictions = _predictions(
        [
            {
                "image_id": "a.jpg",
                "prediction_id": "p1",
                "class_id": 0,
                "confidence": 0.90,
                "x1": 0,
                "y1": 0,
                "x2": 10,
                "y2": 10,
                "bbox_area_ratio": 0.10,
            },
            {
                "image_id": "a.jpg",
                "prediction_id": "p2",
                "class_id": 0,
                "confidence": 0.80,
                "x1": 1,
                "y1": 1,
                "x2": 9,
                "y2": 9,
                "bbox_area_ratio": 0.08,
            },
        ]
    )
    ground_truth = _ground_truth(
        [
            {
                "image_id": "a.jpg",
                "gt_id": "g1",
                "class_id": 0,
                "x1": 0,
                "y1": 0,
                "x2": 10,
                "y2": 10,
                "bbox_area_ratio": 0.10,
            }
        ]
    )

    result = evaluate_threshold(predictions, ground_truth, threshold=0.50)

    assert result.summary["tp"] == 1
    assert result.summary["fp"] == 1
    assert result.summary["fn"] == 0
    assert result.summary["precision"] == pytest.approx(0.5)
    assert result.summary["recall"] == pytest.approx(1.0)
    assert set(result.prediction_details["error_type"]) == {
        "true_positive",
        "duplicate_prediction",
    }


def test_evaluate_threshold_marks_localization_error_and_false_negative() -> None:
    predictions = _predictions(
        [
            {
                "image_id": "a.jpg",
                "prediction_id": "p1",
                "class_id": 0,
                "confidence": 0.70,
                "x1": 0,
                "y1": 0,
                "x2": 5,
                "y2": 10,
                "bbox_area_ratio": 0.05,
            }
        ]
    )
    ground_truth = _ground_truth(
        [
            {
                "image_id": "a.jpg",
                "gt_id": "g1",
                "class_id": 0,
                "x1": 0,
                "y1": 0,
                "x2": 10,
                "y2": 10,
                "bbox_area_ratio": 0.10,
            }
        ]
    )

    result = evaluate_threshold(
        predictions,
        ground_truth,
        threshold=0.50,
        iou_threshold=0.60,
        localization_iou_min=0.10,
    )

    assert result.summary["tp"] == 0
    assert result.summary["fp"] == 1
    assert result.summary["fn"] == 1
    assert result.prediction_details.iloc[0]["error_type"] == "localization_error"
    assert result.ground_truth_details.iloc[0]["error_type"] == "localization_miss"


def test_evaluate_threshold_identifies_low_confidence_miss_from_raw_predictions() -> None:
    predictions = _predictions(
        [
            {
                "image_id": "a.jpg",
                "prediction_id": "p1",
                "class_id": 0,
                "confidence": 0.20,
                "x1": 0,
                "y1": 0,
                "x2": 10,
                "y2": 10,
                "bbox_area_ratio": 0.10,
            }
        ]
    )
    ground_truth = _ground_truth(
        [
            {
                "image_id": "a.jpg",
                "gt_id": "g1",
                "class_id": 0,
                "x1": 0,
                "y1": 0,
                "x2": 10,
                "y2": 10,
                "bbox_area_ratio": 0.10,
            }
        ]
    )

    result = evaluate_threshold(predictions, ground_truth, threshold=0.50)

    assert result.summary["predictions_count"] == 0
    assert result.summary["fn"] == 1
    assert result.ground_truth_details.iloc[0]["error_type"] == "low_confidence_miss"
    assert result.ground_truth_details.iloc[0]["best_raw_confidence"] == pytest.approx(0.20)


def test_select_operating_points_is_deterministic() -> None:
    sweep = pd.DataFrame(
        [
            {"threshold": 0.10, "precision": 0.40, "recall": 0.80, "f1": 0.5333},
            {"threshold": 0.20, "precision": 0.50, "recall": 0.75, "f1": 0.6000},
            {"threshold": 0.30, "precision": 0.60, "recall": 0.60, "f1": 0.6000},
            {"threshold": 0.40, "precision": 0.75, "recall": 0.40, "f1": 0.5217},
        ]
    )

    selected = select_operating_points(
        sweep,
        high_recall_fraction_of_max=0.95,
        high_precision_fraction_of_max=0.95,
    )

    by_name = selected.set_index("operating_point")
    assert by_name.loc["high_recall", "threshold"] == pytest.approx(0.10)
    assert by_name.loc["balanced", "threshold"] == pytest.approx(0.30)
    assert by_name.loc["high_precision", "threshold"] == pytest.approx(0.40)
    assert set(by_name["status"]) == {"VALIDATION_THRESHOLD_CANDIDATE"}


def test_bbox_size_categories_use_configured_area_ratio_boundaries() -> None:
    assert categorize_bbox_size(0.005, small_max=0.01, medium_max=0.05) == "small"
    assert categorize_bbox_size(0.01, small_max=0.01, medium_max=0.05) == "small"
    assert categorize_bbox_size(0.03, small_max=0.01, medium_max=0.05) == "medium"
    assert categorize_bbox_size(0.20, small_max=0.01, medium_max=0.05) == "large"


def test_build_data_improvement_priorities_orders_data_quality_before_collection() -> None:
    errors = pd.DataFrame(
        [
            {"error_type": "suspected_annotation_issue", "image_id": "a.jpg", "object_id": "x"},
            {"error_type": "background_false_positive", "image_id": "b.jpg", "object_id": "y"},
            {"error_type": "background_false_positive", "image_id": "c.jpg", "object_id": "z"},
        ]
    )

    priorities = build_data_improvement_priorities(errors)

    assert priorities.iloc[0]["priority_band"] == "P0"
    assert priorities.iloc[0]["issue_category"] == "suspected_annotation_issue"
    assert priorities["priority_rank"].tolist() == list(range(1, len(priorities) + 1))


def test_validate_analysis_config_rejects_test_split_and_training_permission() -> None:
    valid = {
        "gate_id": "04.5K",
        "input": {
            "allowed_split": "valid",
            "expected_images": 168,
            "expected_ground_truth_instances": 325,
            "best_pt_sha256": "A" * 64,
        },
        "inference": {
            "confidence_floor": 0.001,
            "nms_iou": 0.7,
            "imgsz": 640,
            "max_det": 300,
        },
        "matching": {"iou_threshold": 0.5, "localization_iou_min": 0.1},
        "thresholds": [0.05, 0.10],
        "operating_points": {
            "high_recall_fraction_of_max": 0.95,
            "high_precision_fraction_of_max": 0.95,
        },
        "bbox_size": {"small_max_area_ratio": 0.01, "medium_max_area_ratio": 0.05},
        "safety": {
            "forbid_test_tuning": True,
            "forbid_training": True,
            "deployment_acceptance": "NOT_YET_APPROVED",
        },
    }
    validate_analysis_config(valid)

    invalid_split = {**valid, "input": {**valid["input"], "allowed_split": "test"}}
    with pytest.raises(BaselineAnalysisError, match="allowed_split must be valid"):
        validate_analysis_config(invalid_split)

    invalid_training = {**valid, "safety": {**valid["safety"], "forbid_training": False}}
    with pytest.raises(BaselineAnalysisError, match="forbid_training must be true"):
        validate_analysis_config(invalid_training)
