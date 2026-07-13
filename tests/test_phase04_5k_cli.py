from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml


def test_cli_execute_writes_traceable_validation_only_outputs(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    predictions = pd.DataFrame(
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
                "bbox_area_ratio": 0.01,
            },
            {
                "image_id": "b.jpg",
                "prediction_id": "p2",
                "class_id": 0,
                "confidence": 0.80,
                "x1": 20,
                "y1": 20,
                "x2": 30,
                "y2": 30,
                "bbox_area_ratio": 0.02,
            },
        ]
    )
    ground_truth = pd.DataFrame(
        [
            {
                "image_id": "a.jpg",
                "gt_id": "g1",
                "class_id": 0,
                "x1": 0,
                "y1": 0,
                "x2": 10,
                "y2": 10,
                "bbox_area_ratio": 0.01,
            },
            {
                "image_id": "b.jpg",
                "gt_id": "g2",
                "class_id": 0,
                "x1": 0,
                "y1": 0,
                "x2": 10,
                "y2": 10,
                "bbox_area_ratio": 0.02,
            },
        ]
    )
    predictions_path = tmp_path / "predictions.csv"
    gt_path = tmp_path / "ground_truth.csv"
    predictions.to_csv(predictions_path, index=False)
    ground_truth.to_csv(gt_path, index=False)

    config = {
        "gate_id": "04.5K",
        "input": {
            "allowed_split": "valid",
            "expected_images": 2,
            "expected_ground_truth_instances": 2,
            "best_pt_sha256": "90A880513A42EF2DB1373902D98FF09D1756AB7A8A4EEA6A7AA231D4020B77BF",
        },
        "inference": {
            "confidence_floor": 0.001,
            "nms_iou": 0.7,
            "imgsz": 640,
            "max_det": 300,
        },
        "matching": {"iou_threshold": 0.5, "localization_iou_min": 0.1},
        "thresholds": [0.05, 0.50, 0.85],
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
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    output_root = tmp_path / "result"

    command = [
        sys.executable,
        str(project_root / "scripts/phase04_5k_analyze_baseline_errors.py"),
        "--project-root",
        str(project_root),
        "--config",
        str(config_path),
        "--predictions",
        str(predictions_path),
        "--ground-truth",
        str(gt_path),
        "--output-root",
        str(output_root),
        "--execute",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout.strip().splitlines()[-1])
    assert payload["gate_classification"] == "VALIDATION_ERROR_ANALYSIS_AND_THRESHOLD_CANDIDATES_COMPLETED"
    assert payload["test_set_used_for_tuning"] is False
    assert payload["training_started"] is False
    assert payload["deployment_acceptance"] == "NOT_YET_APPROVED"
    assert (output_root / "metrics/validation_threshold_sweep.csv").is_file()
    assert (output_root / "metrics/validation_operating_points.csv").is_file()
    assert (output_root / "records/validation_matches.csv").is_file()
    assert (output_root / "records/validation_error_cases.csv").is_file()
    assert (output_root / "reports/data_improvement_priorities.csv").is_file()
    assert (output_root / "reports/baseline_error_analysis.md").is_file()
    assert (output_root / "manifest/phase_04_5k_manifest.json").is_file()
    assert (output_root / "manifest/phase_04_5k_checksums.sha256").is_file()
    assert (output_root / "04_5K_gate_result.json").is_file()

    gate = json.loads((output_root / "04_5K_gate_result.json").read_text(encoding="utf-8"))
    assert gate["allowed_split"] == "valid"
    assert gate["test_set_used_for_tuning"] is False
    assert gate["threshold_candidate_count"] == 3


def test_cli_refuses_non_validation_image_count(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    pd.DataFrame(
        [
            {
                "image_id": "a.jpg",
                "prediction_id": "p1",
                "class_id": 0,
                "confidence": 0.9,
                "x1": 0,
                "y1": 0,
                "x2": 10,
                "y2": 10,
                "bbox_area_ratio": 0.1,
            }
        ]
    ).to_csv(tmp_path / "predictions.csv", index=False)
    pd.DataFrame(
        [
            {
                "image_id": "a.jpg",
                "gt_id": "g1",
                "class_id": 0,
                "x1": 0,
                "y1": 0,
                "x2": 10,
                "y2": 10,
                "bbox_area_ratio": 0.1,
            }
        ]
    ).to_csv(tmp_path / "ground_truth.csv", index=False)
    config = {
        "gate_id": "04.5K",
        "input": {
            "allowed_split": "valid",
            "expected_images": 2,
            "expected_ground_truth_instances": 1,
            "best_pt_sha256": "A" * 64,
        },
        "inference": {"confidence_floor": 0.001, "nms_iou": 0.7, "imgsz": 640, "max_det": 300},
        "matching": {"iou_threshold": 0.5, "localization_iou_min": 0.1},
        "thresholds": [0.05],
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
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(project_root / "scripts/phase04_5k_analyze_baseline_errors.py"),
            "--project-root",
            str(project_root),
            "--config",
            str(config_path),
            "--predictions",
            str(tmp_path / "predictions.csv"),
            "--ground-truth",
            str(tmp_path / "ground_truth.csv"),
            "--output-root",
            str(tmp_path / "result"),
            "--execute",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    payload = json.loads(completed.stdout.strip().splitlines()[-1])
    assert payload["gate_classification"] == "VALIDATION_ERROR_ANALYSIS_BLOCKED"
    assert "expected 2 validation images" in payload["error"]
    assert not (tmp_path / "result").exists()
