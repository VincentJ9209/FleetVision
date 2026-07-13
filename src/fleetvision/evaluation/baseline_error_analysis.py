"""Deterministic validation-only error analysis for FleetVision Phase 04.5K."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


PREDICTION_REQUIRED_COLUMNS = {
    "image_id",
    "prediction_id",
    "class_id",
    "confidence",
    "x1",
    "y1",
    "x2",
    "y2",
    "bbox_area_ratio",
}
GROUND_TRUTH_REQUIRED_COLUMNS = {
    "image_id",
    "gt_id",
    "class_id",
    "x1",
    "y1",
    "x2",
    "y2",
    "bbox_area_ratio",
}


class BaselineAnalysisError(RuntimeError):
    """Raised when Phase 04.5K inputs or controls violate the approved contract."""


@dataclass(frozen=True)
class ThresholdEvaluation:
    """Threshold-specific metrics and traceable prediction/ground-truth outcomes."""

    summary: dict[str, Any]
    prediction_details: pd.DataFrame
    ground_truth_details: pd.DataFrame


def box_iou_xyxy(
    left: Sequence[float],
    right: Sequence[float],
) -> float:
    """Return intersection-over-union for two ``(x1, y1, x2, y2)`` boxes."""

    lx1, ly1, lx2, ly2 = (float(value) for value in left)
    rx1, ry1, rx2, ry2 = (float(value) for value in right)
    left_area = max(0.0, lx2 - lx1) * max(0.0, ly2 - ly1)
    right_area = max(0.0, rx2 - rx1) * max(0.0, ry2 - ry1)
    if left_area <= 0.0 or right_area <= 0.0:
        return 0.0

    ix1 = max(lx1, rx1)
    iy1 = max(ly1, ry1)
    ix2 = min(lx2, rx2)
    iy2 = min(ly2, ry2)
    intersection = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = left_area + right_area - intersection
    return 0.0 if union <= 0.0 else float(intersection / union)


def categorize_bbox_size(
    area_ratio: float,
    *,
    small_max: float,
    medium_max: float,
) -> str:
    """Categorize a box using configured image-area ratio boundaries."""

    value = float(area_ratio)
    if not 0.0 <= small_max < medium_max <= 1.0:
        raise BaselineAnalysisError("bbox size thresholds must satisfy 0 <= small < medium <= 1")
    if value <= small_max:
        return "small"
    if value <= medium_max:
        return "medium"
    return "large"


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise BaselineAnalysisError(f"{label} missing required columns: {missing}")


def _validate_boxes(frame: pd.DataFrame, label: str) -> None:
    if frame.empty:
        return
    coords = frame[["x1", "y1", "x2", "y2"]].astype(float)
    invalid = (coords["x2"] <= coords["x1"]) | (coords["y2"] <= coords["y1"])
    if bool(invalid.any()):
        bad_count = int(invalid.sum())
        raise BaselineAnalysisError(f"{label} contains {bad_count} invalid xyxy boxes")


def _best_raw_prediction_for_gt(
    raw_predictions: pd.DataFrame,
    gt_row: pd.Series,
) -> tuple[str, float, float]:
    same_class = raw_predictions[raw_predictions["class_id"] == gt_row["class_id"]]
    if same_class.empty:
        return "", 0.0, float("nan")

    gt_box = (gt_row.x1, gt_row.y1, gt_row.x2, gt_row.y2)
    ranked: list[tuple[float, float, str]] = []
    for pred in same_class.itertuples(index=False):
        iou = box_iou_xyxy(
            (pred.x1, pred.y1, pred.x2, pred.y2),
            gt_box,
        )
        ranked.append((iou, float(pred.confidence), str(pred.prediction_id)))
    ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
    best_iou, best_confidence, best_id = ranked[0]
    return best_id, float(best_iou), float(best_confidence)


def evaluate_threshold(
    predictions: pd.DataFrame,
    ground_truth: pd.DataFrame,
    *,
    threshold: float,
    iou_threshold: float = 0.50,
    localization_iou_min: float = 0.10,
) -> ThresholdEvaluation:
    """Evaluate one confidence threshold with deterministic one-to-one matching.

    Predictions are sorted by confidence descending and then ``prediction_id``.
    Each prediction may match at most one currently-unmatched ground-truth box.
    Unmatched predictions are classified as duplicate, localization, or background
    false positives. Unmatched ground-truth boxes are classified using the complete
    low-confidence prediction inventory so threshold-induced misses remain visible.
    """

    _require_columns(predictions, PREDICTION_REQUIRED_COLUMNS, "predictions")
    _require_columns(ground_truth, GROUND_TRUTH_REQUIRED_COLUMNS, "ground_truth")
    _validate_boxes(predictions, "predictions")
    _validate_boxes(ground_truth, "ground_truth")

    threshold = float(threshold)
    iou_threshold = float(iou_threshold)
    localization_iou_min = float(localization_iou_min)
    if not 0.0 <= threshold <= 1.0:
        raise BaselineAnalysisError("threshold must be between 0 and 1")
    if not 0.0 < iou_threshold <= 1.0:
        raise BaselineAnalysisError("iou_threshold must be in (0, 1]")
    if not 0.0 <= localization_iou_min < iou_threshold:
        raise BaselineAnalysisError("localization_iou_min must be below iou_threshold")

    raw_predictions = predictions.copy()
    all_ground_truth = ground_truth.copy()
    active_predictions = raw_predictions[raw_predictions["confidence"].astype(float) >= threshold].copy()

    pred_details: list[dict[str, Any]] = []
    gt_details: list[dict[str, Any]] = []
    image_ids = sorted(
        set(raw_predictions["image_id"].astype(str))
        | set(all_ground_truth["image_id"].astype(str))
    )

    for image_id in image_ids:
        image_raw = raw_predictions[raw_predictions["image_id"].astype(str) == image_id].copy()
        image_active = active_predictions[
            active_predictions["image_id"].astype(str) == image_id
        ].copy()
        image_gt = all_ground_truth[all_ground_truth["image_id"].astype(str) == image_id].copy()

        image_active = image_active.sort_values(
            ["confidence", "prediction_id"],
            ascending=[False, True],
            kind="mergesort",
        )
        image_gt = image_gt.sort_values("gt_id", kind="mergesort")
        matched_gt_ids: set[str] = set()
        gt_match_map: dict[str, tuple[str, float]] = {}

        for pred in image_active.itertuples(index=False):
            pred_box = (pred.x1, pred.y1, pred.x2, pred.y2)
            candidates: list[tuple[float, str, bool]] = []
            for gt in image_gt.itertuples(index=False):
                if int(gt.class_id) != int(pred.class_id):
                    continue
                iou = box_iou_xyxy(pred_box, (gt.x1, gt.y1, gt.x2, gt.y2))
                candidates.append((iou, str(gt.gt_id), str(gt.gt_id) in matched_gt_ids))
            candidates.sort(key=lambda item: (-item[0], item[1]))

            best_iou = float(candidates[0][0]) if candidates else 0.0
            best_gt_id = candidates[0][1] if candidates else ""
            unmatched_candidates = [item for item in candidates if not item[2]]
            best_unmatched = unmatched_candidates[0] if unmatched_candidates else None

            matched_gt_id = ""
            match_status = "unmatched"
            if best_unmatched is not None and best_unmatched[0] >= iou_threshold:
                matched_gt_id = best_unmatched[1]
                match_status = "matched"
                error_type = "true_positive"
                matched_gt_ids.add(matched_gt_id)
                gt_match_map[matched_gt_id] = (str(pred.prediction_id), float(best_unmatched[0]))
                best_iou = float(best_unmatched[0])
                best_gt_id = matched_gt_id
            elif best_iou >= iou_threshold and best_gt_id in matched_gt_ids:
                error_type = "duplicate_prediction"
            elif best_iou >= localization_iou_min:
                error_type = "localization_error"
            else:
                error_type = "background_false_positive"

            pred_details.append(
                {
                    **pred._asdict(),
                    "threshold": threshold,
                    "matched_gt_id": matched_gt_id,
                    "best_gt_id": best_gt_id,
                    "best_iou": best_iou,
                    "match_status": match_status,
                    "error_type": error_type,
                }
            )

        for gt in image_gt.itertuples(index=False):
            gt_id = str(gt.gt_id)
            if gt_id in gt_match_map:
                matched_prediction_id, best_iou = gt_match_map[gt_id]
                error_type = "true_positive"
                best_raw_prediction_id = matched_prediction_id
                best_raw_confidence = float(
                    image_raw.loc[
                        image_raw["prediction_id"].astype(str) == matched_prediction_id,
                        "confidence",
                    ].iloc[0]
                )
                match_status = "matched"
            else:
                best_raw_prediction_id, best_iou, best_raw_confidence = _best_raw_prediction_for_gt(
                    image_raw,
                    pd.Series(gt._asdict()),
                )
                match_status = "unmatched"
                if best_iou >= iou_threshold and (
                    np.isnan(best_raw_confidence) or best_raw_confidence < threshold
                ):
                    error_type = "low_confidence_miss"
                elif best_iou >= localization_iou_min:
                    error_type = "localization_miss"
                else:
                    error_type = "no_detection"
                matched_prediction_id = ""

            gt_details.append(
                {
                    **gt._asdict(),
                    "threshold": threshold,
                    "matched_prediction_id": matched_prediction_id,
                    "best_raw_prediction_id": best_raw_prediction_id,
                    "best_iou": float(best_iou),
                    "best_raw_confidence": best_raw_confidence,
                    "match_status": match_status,
                    "error_type": error_type,
                }
            )

    prediction_details = pd.DataFrame(pred_details)
    ground_truth_details = pd.DataFrame(gt_details)
    if prediction_details.empty:
        prediction_details = pd.DataFrame(
            columns=[
                *predictions.columns,
                "threshold",
                "matched_gt_id",
                "best_gt_id",
                "best_iou",
                "match_status",
                "error_type",
            ]
        )
    if ground_truth_details.empty:
        ground_truth_details = pd.DataFrame(
            columns=[
                *ground_truth.columns,
                "threshold",
                "matched_prediction_id",
                "best_raw_prediction_id",
                "best_iou",
                "best_raw_confidence",
                "match_status",
                "error_type",
            ]
        )

    tp = int((prediction_details["error_type"] == "true_positive").sum())
    fp = int(len(prediction_details) - tp)
    fn = int((ground_truth_details["error_type"] != "true_positive").sum())
    precision = float(tp / (tp + fp)) if tp + fp else 0.0
    recall = float(tp / (tp + fn)) if tp + fn else 0.0
    f1 = float(2.0 * precision * recall / (precision + recall)) if precision + recall else 0.0
    images_with_fp = int(
        prediction_details.loc[
            prediction_details["error_type"] != "true_positive",
            "image_id",
        ].astype(str).nunique()
    )
    images_with_fn = int(
        ground_truth_details.loc[
            ground_truth_details["error_type"] != "true_positive",
            "image_id",
        ].astype(str).nunique()
    )

    summary = {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "predictions_count": int(len(prediction_details)),
        "ground_truth_count": int(len(ground_truth_details)),
        "images_with_fp": images_with_fp,
        "images_with_fn": images_with_fn,
    }
    return ThresholdEvaluation(summary, prediction_details, ground_truth_details)


def run_threshold_sweep(
    predictions: pd.DataFrame,
    ground_truth: pd.DataFrame,
    *,
    thresholds: Iterable[float],
    iou_threshold: float = 0.50,
    localization_iou_min: float = 0.10,
) -> pd.DataFrame:
    """Return deterministic metrics for every configured validation threshold."""

    ordered = sorted({float(value) for value in thresholds})
    if not ordered:
        raise BaselineAnalysisError("thresholds must not be empty")
    summaries = [
        evaluate_threshold(
            predictions,
            ground_truth,
            threshold=value,
            iou_threshold=iou_threshold,
            localization_iou_min=localization_iou_min,
        ).summary
        for value in ordered
    ]
    return pd.DataFrame(summaries).sort_values("threshold", kind="mergesort").reset_index(drop=True)


def _select_row(frame: pd.DataFrame, sort_columns: list[str], ascending: list[bool]) -> pd.Series:
    return frame.sort_values(sort_columns, ascending=ascending, kind="mergesort").iloc[0]


def select_operating_points(
    sweep: pd.DataFrame,
    *,
    high_recall_fraction_of_max: float,
    high_precision_fraction_of_max: float,
) -> pd.DataFrame:
    """Select high-recall, balanced, and high-precision validation candidates."""

    required = {"threshold", "precision", "recall", "f1"}
    missing = sorted(required - set(sweep.columns))
    if missing:
        raise BaselineAnalysisError(f"sweep missing required columns: {missing}")
    if sweep.empty:
        raise BaselineAnalysisError("sweep must not be empty")
    for value, label in [
        (high_recall_fraction_of_max, "high_recall_fraction_of_max"),
        (high_precision_fraction_of_max, "high_precision_fraction_of_max"),
    ]:
        if not 0.0 < float(value) <= 1.0:
            raise BaselineAnalysisError(f"{label} must be in (0, 1]")

    max_recall = float(sweep["recall"].max())
    recall_candidates = sweep[
        sweep["recall"] >= max_recall * float(high_recall_fraction_of_max)
    ]
    high_recall = _select_row(
        recall_candidates,
        ["precision", "recall", "threshold"],
        [False, False, False],
    )

    balanced = _select_row(
        sweep,
        ["f1", "precision", "recall", "threshold"],
        [False, False, False, False],
    )

    max_precision = float(sweep["precision"].max())
    precision_candidates = sweep[
        sweep["precision"] >= max_precision * float(high_precision_fraction_of_max)
    ]
    high_precision = _select_row(
        precision_candidates,
        ["recall", "precision", "threshold"],
        [False, False, False],
    )

    rows: list[dict[str, Any]] = []
    for name, row in [
        ("high_recall", high_recall),
        ("balanced", balanced),
        ("high_precision", high_precision),
    ]:
        payload = row.to_dict()
        payload.update(
            {
                "operating_point": name,
                "status": "VALIDATION_THRESHOLD_CANDIDATE",
            }
        )
        rows.append(payload)
    columns = ["operating_point", "status", *sweep.columns.tolist()]
    return pd.DataFrame(rows)[columns]


_PRIORITY_RULES: dict[str, tuple[str, str, str, str]] = {
    "suspected_annotation_issue": (
        "P0",
        "Audit annotation correctness before changing model behavior.",
        "high",
        "medium",
    ),
    "low_confidence_miss": (
        "P1",
        "Add representative positive examples and review confidence calibration.",
        "high",
        "medium",
    ),
    "no_detection": (
        "P1",
        "Collect or curate similar missed damages, prioritizing small and low-contrast cases.",
        "high",
        "high",
    ),
    "localization_miss": (
        "P1",
        "Review bbox consistency and add targeted localization examples.",
        "high",
        "medium",
    ),
    "localization_error": (
        "P1",
        "Review bbox consistency and add targeted localization examples.",
        "high",
        "medium",
    ),
    "background_false_positive": (
        "P2",
        "Add hard negatives representing the recurring visual pattern.",
        "medium",
        "medium",
    ),
    "duplicate_prediction": (
        "P2",
        "Inspect adjacent-damage annotation policy and later evaluate NMS settings on validation only.",
        "medium",
        "low",
    ),
}


def build_data_improvement_priorities(error_cases: pd.DataFrame) -> pd.DataFrame:
    """Aggregate traceable error cases into deterministic improvement priorities."""

    required = {"error_type", "image_id", "object_id"}
    missing = sorted(required - set(error_cases.columns))
    if missing:
        raise BaselineAnalysisError(f"error_cases missing required columns: {missing}")
    columns = [
        "priority_rank",
        "priority_band",
        "issue_category",
        "affected_case_count",
        "affected_image_count",
        "estimated_error_share",
        "recommended_action",
        "expected_benefit",
        "implementation_effort",
        "annotation_risk",
        "evidence_source",
    ]
    if error_cases.empty:
        return pd.DataFrame(columns=columns)

    total = len(error_cases)
    rows: list[dict[str, Any]] = []
    for error_type, group in error_cases.groupby("error_type", sort=True):
        band, action, benefit, effort = _PRIORITY_RULES.get(
            str(error_type),
            (
                "P3",
                "Retain as a model or augmentation hypothesis for a later approved experiment.",
                "unknown",
                "unknown",
            ),
        )
        rows.append(
            {
                "priority_band": band,
                "issue_category": str(error_type),
                "affected_case_count": int(len(group)),
                "affected_image_count": int(group["image_id"].astype(str).nunique()),
                "estimated_error_share": float(len(group) / total),
                "recommended_action": action,
                "expected_benefit": benefit,
                "implementation_effort": effort,
                "annotation_risk": "high" if band == "P0" else "medium" if "localization" in str(error_type) else "low",
                "evidence_source": "validation_error_cases",
            }
        )

    band_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    output = pd.DataFrame(rows)
    output["_band_order"] = output["priority_band"].map(band_order)
    output = output.sort_values(
        ["_band_order", "affected_case_count", "issue_category"],
        ascending=[True, False, True],
        kind="mergesort",
    ).drop(columns="_band_order")
    output.insert(0, "priority_rank", range(1, len(output) + 1))
    return output[columns].reset_index(drop=True)


def _require_mapping(config: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = config.get(key)
    if not isinstance(value, Mapping):
        raise BaselineAnalysisError(f"config {key} must be a mapping")
    return value


def validate_analysis_config(config: Mapping[str, Any]) -> None:
    """Validate the fail-closed Phase 04.5K validation-only configuration."""

    if config.get("gate_id") != "04.5K":
        raise BaselineAnalysisError("gate_id must be 04.5K")

    input_cfg = _require_mapping(config, "input")
    inference_cfg = _require_mapping(config, "inference")
    matching_cfg = _require_mapping(config, "matching")
    operating_cfg = _require_mapping(config, "operating_points")
    bbox_cfg = _require_mapping(config, "bbox_size")
    safety_cfg = _require_mapping(config, "safety")

    if input_cfg.get("allowed_split") != "valid":
        raise BaselineAnalysisError("allowed_split must be valid")
    if int(input_cfg.get("expected_images", 0)) <= 0:
        raise BaselineAnalysisError("expected_images must be positive")
    if int(input_cfg.get("expected_ground_truth_instances", 0)) <= 0:
        raise BaselineAnalysisError("expected_ground_truth_instances must be positive")
    best_hash = str(input_cfg.get("best_pt_sha256", ""))
    if len(best_hash) != 64 or any(char not in "0123456789abcdefABCDEF" for char in best_hash):
        raise BaselineAnalysisError("best_pt_sha256 must be a 64-character hexadecimal SHA256")

    confidence_floor = float(inference_cfg.get("confidence_floor", -1))
    if not 0.0 <= confidence_floor < 1.0:
        raise BaselineAnalysisError("confidence_floor must be in [0, 1)")
    nms_iou = float(inference_cfg.get("nms_iou", -1))
    if not 0.0 < nms_iou <= 1.0:
        raise BaselineAnalysisError("nms_iou must be in (0, 1]")
    if int(inference_cfg.get("imgsz", 0)) <= 0:
        raise BaselineAnalysisError("imgsz must be positive")
    if int(inference_cfg.get("max_det", 0)) <= 0:
        raise BaselineAnalysisError("max_det must be positive")

    iou_threshold = float(matching_cfg.get("iou_threshold", -1))
    localization_iou_min = float(matching_cfg.get("localization_iou_min", -1))
    if not 0.0 < iou_threshold <= 1.0:
        raise BaselineAnalysisError("iou_threshold must be in (0, 1]")
    if not 0.0 <= localization_iou_min < iou_threshold:
        raise BaselineAnalysisError("localization_iou_min must be below iou_threshold")

    thresholds = config.get("thresholds")
    if not isinstance(thresholds, list) or not thresholds:
        raise BaselineAnalysisError("thresholds must be a non-empty list")
    normalized = [float(value) for value in thresholds]
    if normalized != sorted(set(normalized)):
        raise BaselineAnalysisError("thresholds must be unique and ascending")
    if normalized[0] < confidence_floor:
        raise BaselineAnalysisError("thresholds cannot be below confidence_floor")
    if any(not 0.0 <= value <= 1.0 for value in normalized):
        raise BaselineAnalysisError("thresholds must be between 0 and 1")

    for key in ["high_recall_fraction_of_max", "high_precision_fraction_of_max"]:
        value = float(operating_cfg.get(key, 0))
        if not 0.0 < value <= 1.0:
            raise BaselineAnalysisError(f"{key} must be in (0, 1]")

    small_max = float(bbox_cfg.get("small_max_area_ratio", -1))
    medium_max = float(bbox_cfg.get("medium_max_area_ratio", -1))
    if not 0.0 <= small_max < medium_max <= 1.0:
        raise BaselineAnalysisError("bbox size thresholds must satisfy 0 <= small < medium <= 1")

    if safety_cfg.get("forbid_test_tuning") is not True:
        raise BaselineAnalysisError("forbid_test_tuning must be true")
    if safety_cfg.get("forbid_training") is not True:
        raise BaselineAnalysisError("forbid_training must be true")
    if safety_cfg.get("deployment_acceptance") != "NOT_YET_APPROVED":
        raise BaselineAnalysisError("deployment_acceptance must remain NOT_YET_APPROVED")
