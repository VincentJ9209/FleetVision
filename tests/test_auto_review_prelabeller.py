from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

from fleetvision.data.auto_review_prelabeller import (
    AutoReviewPrelabelConfig,
    load_config,
    merge_auto_suggestions,
    normalize_text,
    parse_bool01,
    validate_suggestion_columns,
)


REVIEW_COLUMNS = [
    "review_id",
    "image_id",
    "source_bucket",
    "original_path",
    "filename",
    "extension",
    "file_size_bytes",
    "width",
    "height",
    "aspect_ratio",
    "is_readable",
    "created_at",
    "modified_at",
    "notes",
    "quality_status",
    "brightness",
    "blur_score",
    "photo_type_review",
    "angle_review",
    "is_exterior_review",
    "has_visible_damage_review",
    "severity_review",
    "review_status",
    "reviewer",
    "review_notes",
    "priority",
    "priority_reason",
]


def sample_review_labels() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_id": "rv_001",
                "image_id": "img_001",
                "source_bucket": "02_claimable_damage",
                "original_path": "dataset/01_raw/02_claimable_damage/images/a.jpg",
                "filename": "a.jpg",
                "extension": ".jpg",
                "file_size_bytes": "100",
                "width": "800",
                "height": "600",
                "aspect_ratio": "1.333",
                "is_readable": "1",
                "created_at": "",
                "modified_at": "",
                "notes": "",
                "quality_status": "ok",
                "brightness": "",
                "blur_score": "",
                "photo_type_review": "",
                "angle_review": "",
                "is_exterior_review": "",
                "has_visible_damage_review": "",
                "severity_review": "",
                "review_status": "",
                "reviewer": "",
                "review_notes": "",
                "priority": "10",
                "priority_reason": "test",
            },
            {
                "review_id": "rv_002",
                "image_id": "img_002",
                "source_bucket": "01_general_fleet",
                "original_path": "dataset/01_raw/01_general_fleet/images/b.jpg",
                "filename": "b.jpg",
                "extension": ".jpg",
                "file_size_bytes": "100",
                "width": "800",
                "height": "600",
                "aspect_ratio": "1.333",
                "is_readable": "1",
                "created_at": "",
                "modified_at": "",
                "notes": "",
                "quality_status": "ok",
                "brightness": "",
                "blur_score": "",
                "photo_type_review": "interior",
                "angle_review": "unknown",
                "is_exterior_review": "0",
                "has_visible_damage_review": "0",
                "severity_review": "none",
                "review_status": "pending",
                "reviewer": "vincent",
                "review_notes": "keep human value",
                "priority": "40",
                "priority_reason": "test",
            },
        ],
        columns=REVIEW_COLUMNS,
    )


def sample_suggestions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "image_id": "img_001",
                "filename": "a.jpg",
                "original_path": "dataset/01_raw/02_claimable_damage/images/a.jpg",
                "suggested_photo_type_review": "exterior",
                "photo_type_confidence": "0.91",
                "suggested_angle_review": "front left",
                "angle_confidence": "0.72",
                "suggested_has_visible_damage_review": "yes",
                "damage_confidence": "0.88",
                "suggested_severity_review": "severe",
                "severity_confidence": "0.67",
                "auto_review_notes": "clip_zero_shot",
            },
            {
                "image_id": "img_002",
                "filename": "b.jpg",
                "original_path": "dataset/01_raw/01_general_fleet/images/b.jpg",
                "suggested_photo_type_review": "exterior",
                "photo_type_confidence": "0.99",
                "suggested_angle_review": "rear",
                "angle_confidence": "0.99",
                "suggested_has_visible_damage_review": "1",
                "damage_confidence": "0.99",
                "suggested_severity_review": "minor",
                "severity_confidence": "0.99",
                "auto_review_notes": "should not overwrite non-empty human values",
            },
        ]
    )


def make_config(tmp_path: Path) -> AutoReviewPrelabelConfig:
    config_yaml = tmp_path / "auto_review_prelab_config.yaml"
    config_yaml.write_text(
        yaml.safe_dump(
            {
                "outputs": {
                    "merged_labels_csv": "merged.csv",
                    "summary_csv": "summary.csv",
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return load_config(config_yaml, tmp_path)


def test_normalize_helpers() -> None:
    assert normalize_text(" Front Left ") == "front_left"
    assert normalize_text("rear-right") == "rear_right"
    assert parse_bool01("yes") == "1"
    assert parse_bool01("No") == "0"
    assert parse_bool01("maybe") == ""


def test_merge_suggestions_fills_empty_fields_without_marking_reviewed(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    merged, counters = merge_auto_suggestions(sample_review_labels(), sample_suggestions(), config)

    first = merged.loc[merged["image_id"] == "img_001"].iloc[0]
    assert first["photo_type_review"] == "exterior"
    assert first["angle_review"] == "front_left"
    assert first["is_exterior_review"] == "1"
    assert first["has_visible_damage_review"] == "1"
    assert first["severity_review"] == "severe"
    assert first["review_status"] == "pending"
    assert first["reviewer"] == "auto_clip_suggestion"
    assert "auto_photo_type=exterior" in first["review_notes"]

    assert counters["matched_rows"] == 2
    assert counters["photo_type_filled_rows"] == 1
    assert counters["angle_filled_rows"] == 1
    assert counters["damage_filled_rows"] == 1
    assert counters["severity_filled_rows"] == 1


def test_merge_suggestions_does_not_overwrite_existing_human_values(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    merged, _ = merge_auto_suggestions(sample_review_labels(), sample_suggestions(), config)

    second = merged.loc[merged["image_id"] == "img_002"].iloc[0]
    assert second["photo_type_review"] == "interior"
    assert second["angle_review"] == "unknown"
    assert second["is_exterior_review"] == "0"
    assert second["has_visible_damage_review"] == "0"
    assert second["severity_review"] == "none"
    assert second["reviewer"] == "vincent"


def test_low_confidence_suggestions_are_not_filled(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    suggestions = sample_suggestions()
    suggestions.loc[0, "photo_type_confidence"] = "0.01"
    suggestions.loc[0, "angle_confidence"] = "0.01"
    suggestions.loc[0, "damage_confidence"] = "0.01"
    suggestions.loc[0, "severity_confidence"] = "0.01"

    merged, counters = merge_auto_suggestions(sample_review_labels().iloc[[0]].copy(), suggestions.iloc[[0]].copy(), config)
    first = merged.iloc[0]
    assert first["photo_type_review"] == ""
    assert first["angle_review"] == ""
    assert first["has_visible_damage_review"] == ""
    assert first["severity_review"] == ""
    assert counters["photo_type_filled_rows"] == 0


def test_validate_suggestion_columns_reports_missing() -> None:
    with pytest.raises(ValueError, match="suggestions CSV missing"):
        validate_suggestion_columns(pd.DataFrame([{"image_id": "img_001"}]))


def test_cli_help() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "phase03_5_merge_auto_suggestions.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--help"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert "Merge Colab auto-review suggestions" in completed.stdout
