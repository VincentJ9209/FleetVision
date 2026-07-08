from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

from fleetvision.data.prepare_annotation_tasks import (
    AnnotationPrepConfig,
    build_annotation_task_manifest,
    build_eligible_candidates,
    build_summary,
    load_config,
    validate_required_columns,
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
    "candidate_reason",
]


def sample_candidates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_id": "rev_001",
                "image_id": "img_001",
                "source_bucket": "02_claimable_damage",
                "original_path": "dataset/01_raw/02_claimable_damage/images/a.jpg",
                "filename": "a.jpg",
                "photo_type_review": "exterior",
                "angle_review": "left_front",
                "is_exterior_review": "1",
                "has_visible_damage_review": "1",
                "severity_review": "claimable",
                "review_status": "reviewed",
                "reviewer": "tester",
                "review_notes": "visible bumper damage",
                "candidate_reason": "visible_damage_reviewed",
            },
            {
                "review_id": "rev_002",
                "image_id": "img_002",
                "source_bucket": "03_minor_damage",
                "original_path": "dataset/01_raw/03_minor_damage/images/b.jpg",
                "filename": "b.jpg",
                "photo_type_review": "exterior",
                "angle_review": "right_rear",
                "is_exterior_review": "1",
                "has_visible_damage_review": "1",
                "severity_review": "minor",
                "review_status": "reviewed",
                "reviewer": "tester",
                "review_notes": "minor scratch",
                "candidate_reason": "visible_damage_reviewed",
            },
            {
                "review_id": "rev_003",
                "image_id": "img_003",
                "source_bucket": "01_general_fleet",
                "original_path": "dataset/01_raw/01_general_fleet/images/c.jpg",
                "filename": "c.jpg",
                "photo_type_review": "exterior",
                "angle_review": "left_rear",
                "is_exterior_review": "1",
                "has_visible_damage_review": "1",
                "severity_review": "unknown",
                "review_status": "reviewed",
                "reviewer": "tester",
                "review_notes": "visible but unknown severity",
                "candidate_reason": "visible_damage_reviewed",
            },
            {
                "review_id": "rev_004",
                "image_id": "img_004",
                "source_bucket": "01_general_fleet",
                "original_path": "dataset/01_raw/01_general_fleet/images/d.jpg",
                "filename": "d.jpg",
                "photo_type_review": "exterior",
                "angle_review": "left_rear",
                "is_exterior_review": "1",
                "has_visible_damage_review": "0",
                "severity_review": "unknown",
                "review_status": "reviewed",
                "reviewer": "tester",
                "review_notes": "clean exterior",
                "candidate_reason": "visible_damage_reviewed",
            },
            {
                "review_id": "rev_005",
                "image_id": "img_005",
                "source_bucket": "03_minor_damage",
                "original_path": "dataset/01_raw/03_minor_damage/images/e.jpg",
                "filename": "e.jpg",
                "photo_type_review": "exterior",
                "angle_review": "right_front",
                "is_exterior_review": "1",
                "has_visible_damage_review": "1",
                "severity_review": "minor",
                "review_status": "pending",
                "reviewer": "",
                "review_notes": "not reviewed",
                "candidate_reason": "visible_damage_reviewed",
            },
            {
                "review_id": "rev_006",
                "image_id": "img_006",
                "source_bucket": "01_general_fleet",
                "original_path": "dataset/01_raw/01_general_fleet/images/f.jpg",
                "filename": "f.jpg",
                "photo_type_review": "interior",
                "angle_review": "other",
                "is_exterior_review": "0",
                "has_visible_damage_review": "1",
                "severity_review": "unknown",
                "review_status": "reviewed",
                "reviewer": "tester",
                "review_notes": "interior",
                "candidate_reason": "visible_damage_reviewed",
            },
        ],
        columns=REQUIRED_COLUMNS,
    )


def default_config(tmp_path: Path) -> AnnotationPrepConfig:
    return AnnotationPrepConfig(
        input_csv=tmp_path / "annotation_candidates.csv",
        task_manifest_csv=tmp_path / "annotation_task_manifest.csv",
        summary_csv=tmp_path / "summary.csv",
        severity_priority={"claimable": 10, "minor": 20, "unknown": 30},
    )


def test_build_eligible_candidates_filters_expected_rows(tmp_path: Path) -> None:
    config = default_config(tmp_path)

    eligible = build_eligible_candidates(sample_candidates(), config)

    assert eligible["review_id"].tolist() == ["rev_001", "rev_002", "rev_003"]


def test_build_annotation_task_manifest_has_expected_columns_and_priority(tmp_path: Path) -> None:
    config = default_config(tmp_path)

    manifest = build_annotation_task_manifest(sample_candidates(), config)

    assert manifest["review_id"].tolist() == ["rev_001", "rev_002", "rev_003"]
    assert manifest["annotation_class"].unique().tolist() == ["damage"]
    assert manifest["annotation_type"].unique().tolist() == ["bbox"]
    assert manifest["annotation_status"].unique().tolist() == ["pending"]
    assert manifest["task_priority"].tolist() == [10, 20, 30]
    assert manifest["task_id"].is_unique


def test_summary_counts_input_eligible_and_skipped_rows(tmp_path: Path) -> None:
    config = default_config(tmp_path)
    manifest = build_annotation_task_manifest(sample_candidates(), config)

    summary = build_summary(sample_candidates(), manifest, config).iloc[0].to_dict()

    assert summary["total_input_rows"] == 6
    assert summary["eligible_task_rows"] == 3
    assert summary["skipped_rows"] == 3
    assert summary["claimable_rows"] == 1
    assert summary["minor_rows"] == 1
    assert summary["unknown_severity_rows"] == 1


def test_missing_required_columns_fail_clearly() -> None:
    candidates = sample_candidates().drop(columns=["candidate_reason"])

    with pytest.raises(ValueError, match="candidate_reason"):
        validate_required_columns(candidates)


def test_cli_runs_with_tmp_config_without_touching_real_data(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_csv = tmp_path / "input" / "annotation_candidates.csv"
    input_csv.parent.mkdir(parents=True, exist_ok=True)
    sample_candidates().to_csv(input_csv, index=False)

    config = {
        "input_csv": str(input_csv),
        "outputs": {
            "task_manifest_csv": str(tmp_path / "out" / "annotation_task_manifest.csv"),
            "summary_csv": str(tmp_path / "out" / "summary.csv"),
        },
        "settings": {
            "annotation_class": "damage",
            "annotation_type": "bbox",
            "annotation_status": "pending",
            "require_reviewed_status": True,
            "reviewed_status_value": "reviewed",
            "require_visible_damage": True,
        },
        "priority_rules": {
            "severity_review": {"claimable": 10, "minor": 20, "unknown": 30},
            "default_priority": 40,
        },
    }
    config_path = tmp_path / "annotation_prep_config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "phase05_prepare_annotation_tasks.py"),
            "--project-root",
            str(repo_root),
            "--config",
            str(config_path),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    manifest = pd.read_csv(tmp_path / "out" / "annotation_task_manifest.csv")
    summary = pd.read_csv(tmp_path / "out" / "summary.csv")
    assert manifest.shape[0] == 3
    assert summary.loc[0, "eligible_task_rows"] == 3
