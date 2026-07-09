from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

from fleetvision.data.validate_pilot_human_review import (
    ERROR_COLUMNS,
    PilotHumanReviewValidationConfig,
    read_csv,
    validate_pilot_human_review,
    write_errors_csv,
    write_summary_csv,
)


REQUIRED_COLUMNS = [
    "review_id",
    "image_id",
    "source_bucket",
    "original_path",
    "filename",
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


def sample_config(tmp_path: Path | None = None, expected_rows: int = 1) -> PilotHumanReviewValidationConfig:
    root = tmp_path or Path(".")
    return PilotHumanReviewValidationConfig(
        input_csv=root / "worklist.csv",
        summary_csv=root / "summary.csv",
        errors_csv=root / "errors.csv",
        expected_rows=expected_rows,
        require_unique_review_id=True,
        require_unique_image_id=True,
        reviewed_status_value="reviewed",
        pending_status_value="pending",
        followup_status_value="needs_followup",
        skipped_status_value="skipped",
    )


def make_row(index: int = 1, **overrides: str) -> dict[str, str]:
    row = {
        "review_id": f"review-{index:03d}",
        "image_id": f"image-{index:03d}",
        "source_bucket": "02_claimable_damage",
        "original_path": f"dataset/01_raw/02_claimable_damage/images/{index:03d}.jpg",
        "filename": f"{index:03d}.jpg",
        "human_photo_type_review": "exterior",
        "human_angle_review": "front_left",
        "human_is_exterior_review": "1",
        "human_has_visible_damage_review": "1",
        "human_severity_review": "minor",
        "human_review_status": "pending",
        "human_reviewer": "Vincent",
        "human_reviewed_at": "",
        "human_review_notes": "",
    }
    row.update(overrides)
    return row


def make_dataframe(rows: list[dict[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=REQUIRED_COLUMNS)


def write_csv(path: Path, dataframe: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False, encoding="utf-8-sig")


def write_config(path: Path, input_csv: Path, summary_csv: Path, errors_csv: Path, expected_rows: int) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "input_csv": str(input_csv),
                "summary_csv": str(summary_csv),
                "errors_csv": str(errors_csv),
                "expected_rows": expected_rows,
                "require_unique_review_id": True,
                "require_unique_image_id": True,
                "reviewed_status_value": "reviewed",
                "pending_status_value": "pending",
                "followup_status_value": "needs_followup",
                "skipped_status_value": "skipped",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def messages(result) -> set[str]:
    return {error["message"] for error in result.errors}


def test_500_pending_initial_worklist_passes_validation() -> None:
    rows = [make_row(index) for index in range(1, 501)]
    rows[0]["human_review_status"] = " Pending "
    dataframe = make_dataframe(rows)

    result = validate_pilot_human_review(dataframe, sample_config(expected_rows=500))

    assert result.is_valid is True
    assert result.total_rows == 500
    assert result.valid_rows == 500
    assert result.error_count == 0
    assert result.pending_rows == 500
    assert result.reviewed_rows == 0
    assert result.reviewed_at_filled_rows == 0


def test_pending_with_reviewed_at_fails() -> None:
    result = validate_pilot_human_review(
        make_dataframe([make_row(human_reviewed_at="2026-07-10T09:00:00")]),
        sample_config(),
    )

    assert result.is_valid is False
    assert "human_reviewed_at must be blank when human_review_status=pending" in messages(result)


def test_reviewed_missing_reviewer_fails() -> None:
    result = validate_pilot_human_review(
        make_dataframe([make_row(human_review_status="reviewed", human_reviewer="", human_reviewed_at="2026-07-10T09:00:00")]),
        sample_config(),
    )

    assert any(error["column"] == "human_reviewer" for error in result.errors)


def test_reviewed_missing_reviewed_at_fails() -> None:
    result = validate_pilot_human_review(
        make_dataframe([make_row(human_review_status="reviewed", human_reviewer="Vincent", human_reviewed_at="")]),
        sample_config(),
    )

    assert any(error["column"] == "human_reviewed_at" for error in result.errors)


def test_reviewed_at_invalid_format_fails() -> None:
    result = validate_pilot_human_review(
        make_dataframe([make_row(human_review_status="reviewed", human_reviewed_at="not-a-date")]),
        sample_config(),
    )

    assert "human_reviewed_at must be an ISO 8601 datetime" in messages(result)


def test_exterior_with_is_exterior_zero_fails() -> None:
    result = validate_pilot_human_review(
        make_dataframe([make_row(human_photo_type_review="exterior", human_is_exterior_review="0")]),
        sample_config(),
    )

    assert "human_photo_type_review=exterior requires human_is_exterior_review=1" in messages(result)


def test_interior_with_is_exterior_one_fails() -> None:
    result = validate_pilot_human_review(
        make_dataframe([make_row(human_photo_type_review="interior", human_is_exterior_review="1")]),
        sample_config(),
    )

    assert "human_photo_type_review=interior requires human_is_exterior_review=0" in messages(result)


def test_damage_zero_requires_none_severity() -> None:
    result = validate_pilot_human_review(
        make_dataframe([make_row(human_has_visible_damage_review="0", human_severity_review="minor")]),
        sample_config(),
    )

    assert "human_has_visible_damage_review=0 requires human_severity_review=none" in messages(result)


def test_damage_one_cannot_use_none_severity() -> None:
    result = validate_pilot_human_review(
        make_dataframe([make_row(human_has_visible_damage_review="1", human_severity_review="none")]),
        sample_config(),
    )

    assert "human_has_visible_damage_review=1 cannot use human_severity_review=none" in messages(result)


def test_damage_unknown_requires_unknown_severity() -> None:
    result = validate_pilot_human_review(
        make_dataframe([make_row(human_has_visible_damage_review="unknown", human_severity_review="minor")]),
        sample_config(),
    )

    assert "human_has_visible_damage_review=unknown requires human_severity_review=unknown" in messages(result)


def test_needs_followup_missing_notes_fails() -> None:
    result = validate_pilot_human_review(
        make_dataframe([make_row(human_review_status="needs_followup", human_reviewer="Vincent", human_review_notes="")]),
        sample_config(),
    )

    assert any(error["column"] == "human_review_notes" for error in result.errors)


def test_skipped_missing_notes_fails() -> None:
    result = validate_pilot_human_review(
        make_dataframe([make_row(human_review_status="skipped", human_reviewer="Vincent", human_review_notes="")]),
        sample_config(),
    )

    assert any(error["column"] == "human_review_notes" for error in result.errors)


def test_duplicate_review_id_fails() -> None:
    dataframe = make_dataframe([make_row(1), make_row(2, review_id="review-001")])

    result = validate_pilot_human_review(dataframe, sample_config(expected_rows=2))

    assert any(error["column"] == "review_id" and error["error_code"] == "duplicate_value" for error in result.errors)


def test_duplicate_image_id_fails() -> None:
    dataframe = make_dataframe([make_row(1), make_row(2, image_id="image-001")])

    result = validate_pilot_human_review(dataframe, sample_config(expected_rows=2))

    assert any(error["column"] == "image_id" and error["error_code"] == "duplicate_value" for error in result.errors)


def test_missing_required_column_fails_clearly() -> None:
    dataframe = make_dataframe([make_row()]).drop(columns=["human_reviewer"])

    result = validate_pilot_human_review(dataframe, sample_config())

    assert result.is_valid is False
    assert result.errors[0]["error_code"] == "missing_column"
    assert result.errors[0]["column"] == "human_reviewer"


def test_input_dataframe_is_not_modified() -> None:
    dataframe = make_dataframe([make_row(human_review_status=" Reviewed ", human_reviewed_at="2026-07-10T09:00:00")])
    before = dataframe.copy(deep=True)

    validate_pilot_human_review(dataframe, sample_config())

    pd.testing.assert_frame_equal(dataframe, before)


def test_cli_writes_summary_and_errors_with_tmp_paths(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_csv = tmp_path / "worklist.csv"
    summary_csv = tmp_path / "summary.csv"
    errors_csv = tmp_path / "errors.csv"
    config_yaml = tmp_path / "pilot_human_review_validation_config.yaml"
    write_csv(input_csv, make_dataframe([make_row()]))
    write_config(config_yaml, input_csv, summary_csv, errors_csv, expected_rows=1)

    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "phase04_validate_pilot_human_review.py"),
            "--config",
            str(config_yaml),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert summary_csv.exists()
    assert errors_csv.exists()
    assert "is_valid: True" in completed.stdout


def test_empty_errors_csv_still_contains_header(tmp_path: Path) -> None:
    dataframe = make_dataframe([make_row()])
    result = validate_pilot_human_review(dataframe, sample_config())

    write_errors_csv(result.errors, tmp_path / "errors.csv")

    assert (tmp_path / "errors.csv").read_text(encoding="utf-8-sig").strip() == ",".join(ERROR_COLUMNS)


def test_validator_does_not_use_source_bucket_to_modify_damage_or_severity(tmp_path: Path) -> None:
    dataframe = make_dataframe(
        [
            make_row(
                source_bucket="01_general_fleet",
                human_has_visible_damage_review="1",
                human_severity_review="none",
            )
        ]
    )
    before = dataframe.copy(deep=True)

    result = validate_pilot_human_review(dataframe, sample_config())
    write_summary_csv(result, tmp_path / "summary.csv")

    assert result.is_valid is False
    assert "human_has_visible_damage_review=1 cannot use human_severity_review=none" in messages(result)
    pd.testing.assert_frame_equal(dataframe, before)


def test_read_csv_preserves_blank_strings_and_utf8_sig(tmp_path: Path) -> None:
    csv_path = tmp_path / "worklist.csv"
    write_csv(csv_path, make_dataframe([make_row(human_reviewer="")]))

    dataframe = read_csv(csv_path)

    assert dataframe.loc[0, "human_reviewer"] == ""
