"""CLI for FleetVision Phase 04.5K validation-only baseline error analysis."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from fleetvision.evaluation.baseline_error_analysis import (
    BaselineAnalysisError,
    build_data_improvement_priorities,
    categorize_bbox_size,
    evaluate_threshold,
    run_threshold_sweep,
    select_operating_points,
    validate_analysis_config,
)


CLASSIFICATION_PASS = "VALIDATION_ERROR_ANALYSIS_AND_THRESHOLD_CANDIDATES_COMPLETED"
CLASSIFICATION_BLOCKED = "VALIDATION_ERROR_ANALYSIS_BLOCKED"
DEFAULT_CONFIG = Path("configs/modeling/baseline_error_analysis_config.yaml")


class OutputPromotionError(BaselineAnalysisError):
    """Raised when staged output cannot be promoted safely."""


def find_project_root(start: Path | None = None) -> Path:
    """Find the FleetVision repository root from a starting path."""

    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "PROJECT_CONTEXT_BRIEF.md").is_file() and (candidate / "src/fleetvision").is_dir():
            return candidate
    return current


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest().upper()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def _load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise BaselineAnalysisError(f"config not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BaselineAnalysisError("config root must be a mapping")
    validate_analysis_config(payload)
    return payload


def _validate_input_counts(
    predictions: pd.DataFrame,
    ground_truth: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    image_ids = set(predictions.get("image_id", pd.Series(dtype=str)).astype(str)) | set(
        ground_truth.get("image_id", pd.Series(dtype=str)).astype(str)
    )
    expected_images = int(config["input"]["expected_images"])
    if len(image_ids) != expected_images:
        raise BaselineAnalysisError(
            f"expected {expected_images} validation images, found {len(image_ids)}"
        )
    expected_instances = int(config["input"]["expected_ground_truth_instances"])
    if len(ground_truth) != expected_instances:
        raise BaselineAnalysisError(
            f"expected {expected_instances} validation ground-truth instances, found {len(ground_truth)}"
        )
    for label, frame in [("predictions", predictions), ("ground_truth", ground_truth)]:
        if "split" in frame.columns:
            values = set(frame["split"].dropna().astype(str).str.lower())
            if values != {"valid"}:
                raise BaselineAnalysisError(f"{label} split values must be exactly ['valid'], found {sorted(values)}")


def _combine_detailed_records(
    prediction_details: pd.DataFrame,
    ground_truth_details: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    small_max = float(config["bbox_size"]["small_max_area_ratio"])
    medium_max = float(config["bbox_size"]["medium_max_area_ratio"])
    rows: list[dict[str, Any]] = []

    for row in prediction_details.to_dict(orient="records"):
        rows.append(
            {
                "source_type": "prediction",
                "image_id": str(row["image_id"]),
                "object_id": str(row["prediction_id"]),
                "counterpart_id": str(row.get("matched_gt_id", "")),
                "class_id": int(row["class_id"]),
                "confidence": float(row["confidence"]),
                "x1": float(row["x1"]),
                "y1": float(row["y1"]),
                "x2": float(row["x2"]),
                "y2": float(row["y2"]),
                "bbox_area_ratio": float(row["bbox_area_ratio"]),
                "bbox_size": categorize_bbox_size(
                    float(row["bbox_area_ratio"]), small_max=small_max, medium_max=medium_max
                ),
                "threshold": float(row["threshold"]),
                "best_iou": float(row["best_iou"]),
                "best_raw_confidence": float(row["confidence"]),
                "match_status": str(row["match_status"]),
                "error_type": str(row["error_type"]),
            }
        )

    for row in ground_truth_details.to_dict(orient="records"):
        best_raw_confidence = row.get("best_raw_confidence")
        rows.append(
            {
                "source_type": "ground_truth",
                "image_id": str(row["image_id"]),
                "object_id": str(row["gt_id"]),
                "counterpart_id": str(row.get("matched_prediction_id", "")),
                "class_id": int(row["class_id"]),
                "confidence": None,
                "x1": float(row["x1"]),
                "y1": float(row["y1"]),
                "x2": float(row["x2"]),
                "y2": float(row["y2"]),
                "bbox_area_ratio": float(row["bbox_area_ratio"]),
                "bbox_size": categorize_bbox_size(
                    float(row["bbox_area_ratio"]), small_max=small_max, medium_max=medium_max
                ),
                "threshold": float(row["threshold"]),
                "best_iou": float(row["best_iou"]),
                "best_raw_confidence": None
                if pd.isna(best_raw_confidence)
                else float(best_raw_confidence),
                "match_status": str(row["match_status"]),
                "error_type": str(row["error_type"]),
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["image_id", "source_type", "object_id"], kind="mergesort"
    ).reset_index(drop=True)


def _write_report(
    path: Path,
    sweep: pd.DataFrame,
    operating_points: pd.DataFrame,
    errors: pd.DataFrame,
    config: dict[str, Any],
) -> None:
    balanced = operating_points.loc[operating_points["operating_point"] == "balanced"].iloc[0]
    error_counts = errors["error_type"].value_counts().sort_index().to_dict() if not errors.empty else {}
    lines = [
        "# FleetVision Phase 04.5K Baseline Error Analysis",
        "",
        "## Gate",
        "",
        f"- Classification: `{CLASSIFICATION_PASS}`",
        "- Analysis split: `valid` only",
        "- Test set used for tuning: `false`",
        "- Training started: `false`",
        "- Deployment acceptance: `NOT_YET_APPROVED`",
        "",
        "## Balanced validation candidate",
        "",
        f"- Threshold: `{float(balanced['threshold']):.2f}`",
        f"- Precision: `{float(balanced['precision']):.6f}`",
        f"- Recall: `{float(balanced['recall']):.6f}`",
        f"- F1: `{float(balanced['f1']):.6f}`",
        "",
        "## Threshold candidates",
        "",
    ]
    for row in operating_points.to_dict(orient="records"):
        lines.append(
            f"- `{row['operating_point']}`: threshold={float(row['threshold']):.2f}, "
            f"P={float(row['precision']):.6f}, R={float(row['recall']):.6f}, "
            f"F1={float(row['f1']):.6f}"
        )
    lines.extend(["", "## Error counts", ""])
    if error_counts:
        for key, value in error_counts.items():
            lines.append(f"- `{key}`: {int(value)}")
    else:
        lines.append("- No validation errors at the balanced candidate.")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "These are validation threshold candidates, not a deployment threshold approval.",
            "The test set remains excluded from tuning and may not be re-used for candidate selection.",
            "",
            "## Configuration",
            "",
            f"- Matching IoU: `{float(config['matching']['iou_threshold']):.2f}`",
            f"- Localization IoU floor: `{float(config['matching']['localization_iou_min']):.2f}`",
            f"- Swept thresholds: `{len(sweep)}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _build_output(
    staging: Path,
    predictions_path: Path,
    ground_truth_path: Path,
    config_path: Path,
    predictions: pd.DataFrame,
    ground_truth: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Any]:
    metrics_dir = staging / "metrics"
    records_dir = staging / "records"
    reports_dir = staging / "reports"
    manifest_dir = staging / "manifest"
    for directory in [metrics_dir, records_dir, reports_dir, manifest_dir]:
        directory.mkdir(parents=True, exist_ok=False)

    sweep = run_threshold_sweep(
        predictions,
        ground_truth,
        thresholds=config["thresholds"],
        iou_threshold=float(config["matching"]["iou_threshold"]),
        localization_iou_min=float(config["matching"]["localization_iou_min"]),
    )
    operating_points = select_operating_points(
        sweep,
        high_recall_fraction_of_max=float(
            config["operating_points"]["high_recall_fraction_of_max"]
        ),
        high_precision_fraction_of_max=float(
            config["operating_points"]["high_precision_fraction_of_max"]
        ),
    )
    balanced_threshold = float(
        operating_points.loc[
            operating_points["operating_point"] == "balanced", "threshold"
        ].iloc[0]
    )
    detailed = evaluate_threshold(
        predictions,
        ground_truth,
        threshold=balanced_threshold,
        iou_threshold=float(config["matching"]["iou_threshold"]),
        localization_iou_min=float(config["matching"]["localization_iou_min"]),
    )
    matches = _combine_detailed_records(
        detailed.prediction_details, detailed.ground_truth_details, config
    )
    errors = matches[matches["error_type"] != "true_positive"].copy()
    priorities = build_data_improvement_priorities(
        errors[["error_type", "image_id", "object_id"]].copy()
    )

    error_summary = (
        errors.groupby(["source_type", "error_type"], dropna=False)
        .agg(affected_cases=("object_id", "count"), affected_images=("image_id", "nunique"))
        .reset_index()
        .sort_values(["source_type", "error_type"], kind="mergesort")
    )
    bbox_summary = (
        errors.groupby(["source_type", "bbox_size", "error_type"], dropna=False)
        .agg(affected_cases=("object_id", "count"), affected_images=("image_id", "nunique"))
        .reset_index()
        .sort_values(["source_type", "bbox_size", "error_type"], kind="mergesort")
    )

    sweep.to_csv(metrics_dir / "validation_threshold_sweep.csv", index=False, encoding="utf-8-sig")
    operating_points.to_csv(
        metrics_dir / "validation_operating_points.csv", index=False, encoding="utf-8-sig"
    )
    error_summary.to_csv(
        metrics_dir / "validation_error_summary.csv", index=False, encoding="utf-8-sig"
    )
    bbox_summary.to_csv(
        metrics_dir / "validation_error_by_bbox_size.csv", index=False, encoding="utf-8-sig"
    )
    matches.to_csv(records_dir / "validation_matches.csv", index=False, encoding="utf-8-sig")
    errors.to_csv(records_dir / "validation_error_cases.csv", index=False, encoding="utf-8-sig")
    priorities.to_csv(
        reports_dir / "data_improvement_priorities.csv", index=False, encoding="utf-8-sig"
    )
    _write_report(
        reports_dir / "baseline_error_analysis.md", sweep, operating_points, errors, config
    )

    gate_result = {
        "gate_id": "04.5K",
        "outcome": "PASS",
        "gate_classification": CLASSIFICATION_PASS,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "allowed_split": "valid",
        "validation_image_count": int(
            len(set(predictions["image_id"].astype(str)) | set(ground_truth["image_id"].astype(str)))
        ),
        "validation_ground_truth_instances": int(len(ground_truth)),
        "raw_prediction_count": int(len(predictions)),
        "threshold_candidate_count": int(len(operating_points)),
        "balanced_threshold": balanced_threshold,
        "best_pt_sha256": str(config["input"]["best_pt_sha256"]).upper(),
        "test_set_used_for_tuning": False,
        "training_started": False,
        "deployment_acceptance": "NOT_YET_APPROVED",
    }
    _write_json(staging / "04_5K_gate_result.json", gate_result)

    current_files = sorted(path for path in staging.rglob("*") if path.is_file())
    output_records = [
        {
            "relative_path": path.relative_to(staging).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in current_files
    ]
    manifest = {
        "gate_id": "04.5K",
        "classification": CLASSIFICATION_PASS,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "predictions": {
                "path": str(predictions_path),
                "sha256": sha256_file(predictions_path),
            },
            "ground_truth": {
                "path": str(ground_truth_path),
                "sha256": sha256_file(ground_truth_path),
            },
            "config": {"path": str(config_path), "sha256": sha256_file(config_path)},
        },
        "safety": {
            "allowed_split": "valid",
            "test_set_used_for_tuning": False,
            "training_started": False,
            "deployment_acceptance": "NOT_YET_APPROVED",
        },
        "outputs": output_records,
    }
    _write_json(manifest_dir / "phase_04_5k_manifest.json", manifest)

    checksum_lines = []
    for path in sorted(path for path in staging.rglob("*") if path.is_file()):
        if path.name == "phase_04_5k_checksums.sha256":
            continue
        checksum_lines.append(f"{sha256_file(path)}  {path.relative_to(staging).as_posix()}")
    (manifest_dir / "phase_04_5k_checksums.sha256").write_text(
        "\n".join(checksum_lines) + "\n", encoding="ascii", newline="\n"
    )
    return gate_result


def _promote(staging: Path, output_root: Path, overwrite: bool) -> None:
    if output_root.exists() and not overwrite:
        raise OutputPromotionError(f"output root already exists: {output_root}")
    backup: Path | None = None
    if output_root.exists():
        backup = output_root.with_name(
            f".{output_root.name}.backup-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )
        if backup.exists():
            raise OutputPromotionError(f"backup target already exists: {backup}")
        output_root.rename(backup)
    try:
        staging.rename(output_root)
    except Exception as exc:
        if backup is not None and backup.exists() and not output_root.exists():
            backup.rename(output_root)
        raise OutputPromotionError(f"failed to promote staged output: {exc}") from exc
    if backup is not None:
        shutil.rmtree(backup)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build validation-only Phase 04.5K threshold and error-analysis outputs."
    )
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def _print_payload(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = find_project_root(args.project_root)
    config_path = args.config if args.config.is_absolute() else project_root / args.config
    predictions_path = (
        args.predictions if args.predictions.is_absolute() else project_root / args.predictions
    )
    ground_truth_path = (
        args.ground_truth if args.ground_truth.is_absolute() else project_root / args.ground_truth
    )
    output_root = args.output_root if args.output_root.is_absolute() else project_root / args.output_root

    staging: Path | None = None
    try:
        if args.overwrite and not args.execute:
            raise BaselineAnalysisError("--overwrite requires --execute")
        config = _load_config(config_path)
        if not predictions_path.is_file():
            raise BaselineAnalysisError(f"predictions not found: {predictions_path}")
        if not ground_truth_path.is_file():
            raise BaselineAnalysisError(f"ground truth not found: {ground_truth_path}")
        predictions = pd.read_csv(predictions_path)
        ground_truth = pd.read_csv(ground_truth_path)
        _validate_input_counts(predictions, ground_truth, config)

        if not args.execute:
            _print_payload(
                {
                    "allowed_split": "valid",
                    "deployment_acceptance": "NOT_YET_APPROVED",
                    "executed": False,
                    "gate_classification": "VALIDATION_ERROR_ANALYSIS_PREFLIGHT_PASSED",
                    "ground_truth_instances": int(len(ground_truth)),
                    "test_set_used_for_tuning": False,
                    "training_started": False,
                    "validation_images": int(
                        len(
                            set(predictions["image_id"].astype(str))
                            | set(ground_truth["image_id"].astype(str))
                        )
                    ),
                }
            )
            return 0

        output_root.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=output_root.parent)
        )
        gate_result = _build_output(
            staging,
            predictions_path,
            ground_truth_path,
            config_path,
            predictions,
            ground_truth,
            config,
        )
        _promote(staging, output_root, args.overwrite)
        staging = None
        _print_payload(
            {
                **gate_result,
                "executed": True,
                "output_root": str(output_root),
            }
        )
        return 0
    except (BaselineAnalysisError, ValueError, OSError, pd.errors.ParserError) as exc:
        _print_payload(
            {
                "deployment_acceptance": "NOT_YET_APPROVED",
                "error": str(exc),
                "error_type": type(exc).__name__,
                "executed": False,
                "gate_classification": CLASSIFICATION_BLOCKED,
                "test_set_used_for_tuning": False,
                "training_started": False,
            }
        )
        return 2
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
