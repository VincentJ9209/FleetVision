from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

from fleetvision.data.build_pilot_review_worklist import (
    PilotReviewWorklistConfig,
    build_pilot_review_worklist,
    validate_unique_image_ids,
    write_pilot_review_worklist,
    write_summary,
)


EXPECTED_COLUMNS = [
    "review_id",
    "image_id",
    "source_bucket",
    "original_path",
    "filename",
    "suggested_photo_type_review",
    "photo_type_confidence",
    "suggested_angle_review",
    "angle_confidence",
    "auto_review_notes",
    "seed_photo_type_review",
    "seed_angle_review",
    "seed_is_exterior_review",
    "seed_has_visible_damage_review",
    "seed_severity_review",
    "seed_review_status",
    "seed_reviewer",
    "seed_review_notes",
    "human_photo_type_review",
    "human_angle_review",
    "human_is_exterior_review",
    "human_has_visible_damage_review",
    "human_severity_review",
    "human_review_status",
    "human_reviewer",
    "human_reviewed_at",
    "human_review_notes",
]


def sample_pilot_merge() -> pd.DataFrame:
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
                "severity_review": "claimable",
                "review_status": "pending",
                "reviewer": "Vincent",
                "review_notes": "seed note 1",
            },
            {
                "review_id": "rev_002",
                "image_id": "img_002",
                "source_bucket": "01_general_fleet",
                "original_path": "dataset/01_raw/01_general_fleet/images/b.jpg",
                "filename": "b.jpg",
                "photo_type_review": "interior",
                "angle_review": "unknown",
                "is_exterior_review": "0",
                "has_visible_damage_review": "0",
                "severity_review": "unknown",
                "review_status": "pending",
                "reviewer": "",
                "review_notes": "seed note 2",
            },
            {
                "review_id": "rev_003",
                "image_id": "img_003",
                "source_bucket": "03_minor_damage",
                "original_path": "dataset/01_raw/03_minor_damage/images/c.jpg",
                "filename": "c.jpg",
                "photo_type_review": "exterior",
                "angle_review": "rear_right",
                "is_exterior_review": "1",
                "has_visible_damage_review": "1",
                "severity_review": "minor",
                "review_status": "pending",
                "reviewer": "Joanna",
                "review_notes": "seed note 3",
            },
        ]
    )


def sample_suggestions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "image_id": "img_003",
                "suggested_photo_type_review": "exterior",
                "photo_type_confidence": "0.91",
                "suggested_angle_review": "rear_right",
                "angle_confidence": "0.88",
                "auto_review_notes": "suggestion 3",
            },
            {
                "image_id": "img_001",
                "suggested_photo_type_review": "exterior",
                "photo_type_confidence": "0.97",
                "suggested_angle_review": "front_left",
                "angle_confidence": "0.77",
                "auto_review_notes": "suggestion 1",
            },
            {
                "image_id": "img_002",
                "suggested_photo_type_review": "interior",
                "photo_type_confidence": "0.83",
                "suggested_angle_review": "unknown",
                "angle_confidence": "0.44",
                "auto_review_notes": "suggestion 2",
            },
        ]
    )


def sample_config(tmp_path: Path | None = None) -> PilotReviewWorklistConfig:
    root = tmp_path or Path(".")
    return PilotReviewWorklistConfig(
        pilot_merge_csv=root / "pilot_merge.csv",
        suggestions_csv=root / "suggestions.csv",
        worklist_csv=root / "worklist.csv",
        summary_csv=root / "summary.csv",
        expected_rows=3,
        default_review_status="pending",
        prefill_human_fields_from_seed=True,
        default_reviewer_from_seed=True,
    )


def write_csv(path: Path, dataframe: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False, encoding="utf-8-sig")


def test_builds_worklist_with_expected_columns_and_suggestion_order() -> None:
    worklist, summary = build_pilot_review_worklist(
        sample_pilot_merge(), sample_suggestions(), sample_config()
    )

    assert worklist.columns.tolist() == EXPECTED_COLUMNS
    assert worklist["image_id"].tolist() == ["img_003", "img_001", "img_002"]
    assert summary["matched_rows"] == 3
    assert summary["output_rows"] == 3


def test_overlapping_suggestion_columns_do_not_override_pilot_identity_columns() -> None:
    suggestions = sample_suggestions().assign(
        source_bucket="wrong_bucket",
        original_path="wrong/path.jpg",
        filename="wrong.jpg",
        review_id="wrong_review_id",
    )

    worklist, _ = build_pilot_review_worklist(sample_pilot_merge(), suggestions, sample_config())

    assert worklist["image_id"].tolist() == ["img_003", "img_001", "img_002"]
    assert worklist.columns.tolist() == EXPECTED_COLUMNS
    assert not any(column.endswith(("_x", "_y")) for column in worklist.columns)

    row = worklist.loc[worklist["image_id"] == "img_003"].iloc[0]
    assert row["review_id"] == "rev_003"
    assert row["source_bucket"] == "03_minor_damage"
    assert row["original_path"] == "dataset/01_raw/03_minor_damage/images/c.jpg"
    assert row["filename"] == "c.jpg"

def test_human_fields_are_prefilled_from_seed_without_marking_reviewed() -> None:
    worklist, _ = build_pilot_review_worklist(
        sample_pilot_merge(), sample_suggestions(), sample_config()
    )
    row = worklist.loc[worklist["image_id"] == "img_001"].iloc[0]

    assert row["seed_photo_type_review"] == "exterior"
    assert row["human_photo_type_review"] == "exterior"
    assert row["human_angle_review"] == "front_left"
    assert row["human_is_exterior_review"] == "1"
    assert row["human_has_visible_damage_review"] == "1"
    assert row["human_severity_review"] == "claimable"
    assert row["human_reviewer"] == "Vincent"
    assert set(worklist["human_review_status"]) == {"pending"}
    assert set(worklist["human_reviewed_at"]) == {""}
    assert set(worklist["human_review_notes"]) == {""}


def test_duplicate_suggestion_image_ids_fail() -> None:
    suggestions = pd.concat([sample_suggestions(), sample_suggestions().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate image_id in suggestions_csv"):
        build_pilot_review_worklist(sample_pilot_merge(), suggestions, sample_config())


def test_duplicate_pilot_merge_image_ids_fail() -> None:
    pilot_merge = pd.concat([sample_pilot_merge(), sample_pilot_merge().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate image_id in pilot_merge_csv"):
        build_pilot_review_worklist(pilot_merge, sample_suggestions(), sample_config())


def test_missing_pilot_row_fails() -> None:
    pilot_merge = sample_pilot_merge().loc[lambda df: df["image_id"] != "img_003"]

    with pytest.raises(ValueError, match="missing pilot_merge_csv rows for image_id"):
        build_pilot_review_worklist(pilot_merge, sample_suggestions(), sample_config())


def test_validate_unique_image_ids_requires_expected_unique_count() -> None:
    with pytest.raises(ValueError, match="expected 4 unique image_id"):
        validate_unique_image_ids(sample_suggestions(), "suggestions_csv", 4)


def test_input_dataframes_are_not_modified() -> None:
    pilot_merge = sample_pilot_merge()
    suggestions = sample_suggestions()
    pilot_before = pilot_merge.copy(deep=True)
    suggestions_before = suggestions.copy(deep=True)

    build_pilot_review_worklist(pilot_merge, suggestions, sample_config())

    pd.testing.assert_frame_equal(pilot_merge, pilot_before)
    pd.testing.assert_frame_equal(suggestions, suggestions_before)


def test_write_outputs_use_utf8_sig_and_summary_counts_are_correct(tmp_path: Path) -> None:
    config = sample_config(tmp_path)
    worklist, summary = build_pilot_review_worklist(
        sample_pilot_merge(), sample_suggestions(), config
    )

    write_pilot_review_worklist(worklist, config.worklist_csv)
    write_summary(summary, config.summary_csv)

    assert config.worklist_csv.read_bytes().startswith(b"\xef\xbb\xbf")
    assert config.summary_csv.read_bytes().startswith(b"\xef\xbb\xbf")
    summary_df = pd.read_csv(config.summary_csv, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    summary_row = summary_df.iloc[0].to_dict()
    assert summary_row["suggestion_rows"] == "3"
    assert summary_row["unique_suggestion_image_ids"] == "3"
    assert summary_row["matched_rows"] == "3"
    assert summary_row["missing_rows"] == "0"
    assert summary_row["duplicate_suggestion_ids"] == "0"
    assert summary_row["duplicate_pilot_ids"] == "0"
    assert summary_row["output_rows"] == "3"
    assert summary_row["pending_rows"] == "3"
    assert summary_row["reviewed_rows"] == "0"
    assert summary_row["reviewed_at_filled_rows"] == "0"
    assert summary_row["reviewer_filled_rows"] == "2"


def test_cli_runs_with_tmp_paths_without_touching_real_data(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pilot_merge_csv = tmp_path / "pilot_merge.csv"
    suggestions_csv = tmp_path / "suggestions.csv"
    worklist_csv = tmp_path / "out" / "worklist.csv"
    summary_csv = tmp_path / "out" / "summary.csv"
    config_csv = tmp_path / "pilot_review_worklist_config.yaml"

    write_csv(pilot_merge_csv, sample_pilot_merge())
    write_csv(suggestions_csv, sample_suggestions())
    config_csv.write_text(
        yaml.safe_dump(
            {
                "pilot_merge_csv": str(pilot_merge_csv),
                "suggestions_csv": str(suggestions_csv),
                "worklist_csv": str(worklist_csv),
                "summary_csv": str(summary_csv),
                "expected_rows": 3,
                "default_review_status": "pending",
                "prefill_human_fields_from_seed": True,
                "default_reviewer_from_seed": True,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "phase04_build_pilot_review_worklist.py"),
            "--config",
            str(config_csv),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert worklist_csv.exists()
    assert summary_csv.exists()
    assert "output_rows: 3" in completed.stdout

