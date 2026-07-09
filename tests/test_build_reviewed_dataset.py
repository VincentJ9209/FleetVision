from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

from fleetvision.data.build_reviewed_dataset import (
    build_reviewed_dataset_outputs,
    load_config,
    read_review_labels,
    validate_required_columns,
    write_reviewed_dataset_outputs,
)


REQUIRED_COLUMNS = [
    "review_id",
    "image_id",
    "source_bucket",
    "original_path",
    "filename",
    "photo_type_review",
    "angle_review",
    "is_exterior_review",
    "has_visible_damage_review",
    "severity_review",
    "review_status",
    "reviewer",
    "review_notes",
]


def sample_review_labels() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_id": "rev_001",
                "image_id": "img_001",
                "source_bucket": "02_claimable_damage",
                "original_path": "dataset/01_raw/02_claimable_damage/images/a.jpg",
                "filename": "a.jpg",
                "photo_type_review": "exterior",
                "angle_review": "front_left",
                "is_exterior_review": "1",
                "has_visible_damage_review": "1",
                "severity_review": "severe",
                "review_status": "reviewed",
                "reviewer": "tester",
                "review_notes": "visible bumper damage",
            },
            {
                "review_id": "rev_002",
                "image_id": "img_002",
                "source_bucket": "01_general_fleet",
                "original_path": "dataset/01_raw/01_general_fleet/images/b.jpg",
                "filename": "b.jpg",
                "photo_type_review": "exterior",
                "angle_review": "rear_right",
                "is_exterior_review": "1",
                "has_visible_damage_review": "0",
                "severity_review": "none",
                "review_status": "reviewed",
                "reviewer": "tester",
                "review_notes": "clean exterior",
            },
            {
                "review_id": "rev_003",
                "image_id": "img_003",
                "source_bucket": "01_general_fleet",
                "original_path": "dataset/01_raw/01_general_fleet/images/c.jpg",
                "filename": "c.jpg",
                "photo_type_review": "low_quality",
                "angle_review": "unknown",
                "is_exterior_review": "0",
                "has_visible_damage_review": "unknown",
                "severity_review": "unknown",
                "review_status": "reviewed",
                "reviewer": "tester",
                "review_notes": "too blurry",
            },
            {
                "review_id": "rev_004",
                "image_id": "img_004",
                "source_bucket": "01_general_fleet",
                "original_path": "dataset/01_raw/01_general_fleet/images/d.jpg",
                "filename": "d.jpg",
                "photo_type_review": "irrelevant",
                "angle_review": "unknown",
                "is_exterior_review": "0",
                "has_visible_damage_review": "unknown",
                "severity_review": "unknown",
                "review_status": "reviewed",
                "reviewer": "tester",
                "review_notes": "not a vehicle",
            },
            {
                "review_id": "rev_005",
                "image_id": "img_005",
                "source_bucket": "03_minor_damage",
                "original_path": "dataset/01_raw/03_minor_damage/images/e.jpg",
                "filename": "e.jpg",
                "photo_type_review": "exterior",
                "angle_review": "rear_left",
                "is_exterior_review": "1",
                "has_visible_damage_review": "1",
                "severity_review": "minor",
                "review_status": "pending",
                "reviewer": "",
                "review_notes": "not ready",
            },
            {
                "review_id": "rev_006",
                "image_id": "img_006",
                "source_bucket": "01_general_fleet",
                "original_path": "dataset/01_raw/01_general_fleet/images/f.jpg",
                "filename": "f.jpg",
                "photo_type_review": "interior",
                "angle_review": "unknown",
                "is_exterior_review": "0",
                "has_visible_damage_review": "0",
                "severity_review": "unknown",
                "review_status": "reviewed",
                "reviewer": "tester",
                "review_notes": "dashboard",
            },
            {
                "review_id": "rev_007",
                "image_id": "img_007",
                "source_bucket": "01_general_fleet",
                "original_path": "dataset/01_raw/01_general_fleet/images/g.jpg",
                "filename": "g.jpg",
                "photo_type_review": "unknown",
                "angle_review": "unknown",
                "is_exterior_review": "unknown",
                "has_visible_damage_review": "unknown",
                "severity_review": "unknown",
                "review_status": "reviewed",
                "reviewer": "tester",
                "review_notes": "needs review",
            },
        ],
        columns=REQUIRED_COLUMNS,
    )


def test_build_reviewed_dataset_outputs_filters_expected_rows() -> None:
    outputs = build_reviewed_dataset_outputs(sample_review_labels())

    assert outputs["exterior"].shape[0] == 2
    assert outputs["low_quality"]["review_id"].tolist() == ["rev_003"]
    assert outputs["irrelevant"]["review_id"].tolist() == ["rev_004"]
    assert outputs["annotation_candidates"]["review_id"].tolist() == ["rev_001"]
    assert outputs["annotation_candidates"].loc[0, "candidate_reason"] == "visible_damage_reviewed"

    summary = outputs["summary"].iloc[0].to_dict()
    assert summary["total_rows"] == 7
    assert summary["reviewed_rows"] == 6
    assert summary["skipped_not_reviewed"] == 1
    assert summary["exterior_rows"] == 2
    assert summary["annotation_candidate_rows"] == 1
    assert summary["interior_rows"] == 1
    assert summary["unknown_rows"] == 1


def test_missing_required_columns_fail_clearly() -> None:
    labels = sample_review_labels().drop(columns=["review_id"])

    with pytest.raises(ValueError, match="review_id"):
        validate_required_columns(labels)


def test_write_outputs_creates_all_csv_files(tmp_path: Path) -> None:
    outputs = build_reviewed_dataset_outputs(sample_review_labels())
    config_file = tmp_path / "reviewed_dataset_config.yaml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "input_csv": "labels.csv",
                "outputs": {
                    "exterior_csv": "out/exterior.csv",
                    "low_quality_csv": "out/low_quality.csv",
                    "irrelevant_csv": "out/irrelevant.csv",
                    "annotation_candidates_csv": "out/annotation_candidates.csv",
                    "summary_csv": "out/summary.csv",
                },
                "settings": {"reviewed_only": True, "reviewed_status_value": "reviewed"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    config = load_config(config_file, tmp_path)

    output_paths = write_reviewed_dataset_outputs(outputs, config)

    for output_path in output_paths.values():
        assert output_path.exists()
    assert pd.read_csv(tmp_path / "out/annotation_candidates.csv").shape[0] == 1
    assert pd.read_csv(tmp_path / "out/summary.csv").loc[0, "reviewed_rows"] == 6


def test_cli_runs_with_tmp_config_without_touching_real_data(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_csv = tmp_path / "input" / "image_review_labels.csv"
    input_csv.parent.mkdir(parents=True, exist_ok=True)
    sample_review_labels().to_csv(input_csv, index=False)

    config = {
        "input_csv": str(input_csv),
        "outputs": {
            "exterior_csv": str(tmp_path / "out" / "exterior.csv"),
            "low_quality_csv": str(tmp_path / "out" / "low_quality.csv"),
            "irrelevant_csv": str(tmp_path / "out" / "irrelevant.csv"),
            "annotation_candidates_csv": str(tmp_path / "out" / "annotation_candidates.csv"),
            "summary_csv": str(tmp_path / "out" / "summary.csv"),
        },
        "settings": {"reviewed_only": True, "reviewed_status_value": "reviewed"},
    }
    config_file = tmp_path / "reviewed_dataset_config.yaml"
    config_file.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "phase04_build_reviewed_dataset.py"),
            "--project-root",
            str(repo_root),
            "--config",
            str(config_file),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "annotation_candidate_rows: 1" in completed.stdout
    assert (tmp_path / "out" / "exterior.csv").exists()
    assert (tmp_path / "out" / "summary.csv").exists()


def test_read_review_labels_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_review_labels(tmp_path / "missing.csv")
