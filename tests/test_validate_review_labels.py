import csv
from pathlib import Path

import yaml

from fleetvision.data.validate_review_labels import main, validate_review_labels


REVIEW_LABEL_COLUMNS = [
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


def _valid_rows() -> list[dict[str, str]]:
    return [
        {
            "review_id": "review-1",
            "image_id": "image-1",
            "source_bucket": "02_claimable_damage",
            "original_path": "dataset/01_raw/02_claimable_damage/images/claim.jpg",
            "filename": "claim.jpg",
            "photo_type_review": "exterior",
            "angle_review": "left_front",
            "is_exterior_review": "1",
            "has_visible_damage_review": "1",
            "severity_review": "claimable",
            "review_status": "reviewed",
            "reviewer": "Vincent",
            "review_notes": "visible scrape",
        },
        {
            "review_id": "review-2",
            "image_id": "image-2",
            "source_bucket": "01_general_fleet",
            "original_path": "dataset/01_raw/01_general_fleet/images/interior.png",
            "filename": "interior.png",
            "photo_type_review": "interior",
            "angle_review": "unknown",
            "is_exterior_review": "0",
            "has_visible_damage_review": "unknown",
            "severity_review": "unknown",
            "review_status": "pending",
            "reviewer": "",
            "review_notes": "",
        },
        {
            "review_id": "review-3",
            "image_id": "image-3",
            "source_bucket": "03_minor_damage",
            "original_path": "dataset/01_raw/03_minor_damage/images/minor.jpg",
            "filename": "minor.jpg",
            "photo_type_review": "exterior",
            "angle_review": "right_rear",
            "is_exterior_review": "1",
            "has_visible_damage_review": "0",
            "severity_review": "unknown",
            "review_status": "needs_followup",
            "reviewer": "",
            "review_notes": "needs second look",
        },
    ]


def _write_labels_csv(
    path: Path,
    rows: list[dict[str, str]],
    columns: list[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns or REVIEW_LABEL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_schema(project_root: Path) -> Path:
    schema_path = project_root / "configs" / "data" / "review_label_schema.yaml"
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema = {
        "input_csv": "dataset/00_catalog/image_review_labels.csv",
        "summary_csv": "outputs/metadata/review_label_validation_summary.csv",
        "errors_csv": "outputs/metadata/review_label_validation_errors.csv",
        "required_columns": REVIEW_LABEL_COLUMNS,
        "identity_columns": [
            "review_id",
            "image_id",
            "source_bucket",
            "original_path",
            "filename",
        ],
        "allowed_values": {
            "photo_type_review": [
                "exterior",
                "interior",
                "low_quality",
                "irrelevant",
                "unknown",
            ],
            "angle_review": [
                "left_front",
                "left_rear",
                "right_front",
                "right_rear",
                "other",
                "unknown",
            ],
            "is_exterior_review": ["0", "1", "unknown"],
            "has_visible_damage_review": ["0", "1", "unknown"],
            "severity_review": ["minor", "claimable", "unknown"],
            "review_status": ["pending", "reviewed", "needs_followup", "skipped"],
        },
        "unique_columns": ["review_id", "image_id"],
    }
    schema_path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
    return schema_path


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def test_valid_review_labels_pass_and_write_summary(tmp_path: Path) -> None:
    labels_csv = tmp_path / "dataset" / "00_catalog" / "image_review_labels.csv"
    summary_csv = tmp_path / "outputs" / "metadata" / "summary.csv"
    errors_csv = tmp_path / "outputs" / "metadata" / "errors.csv"
    schema_path = _write_schema(tmp_path)
    _write_labels_csv(labels_csv, _valid_rows())

    result = validate_review_labels(
        input_csv=labels_csv,
        schema_path=schema_path,
        summary_csv=summary_csv,
        errors_csv=errors_csv,
    )

    assert result.is_valid is True
    assert result.total_rows == 3
    assert result.error_count == 0
    assert summary_csv.exists()
    assert errors_csv.exists()
    assert _read_csv(errors_csv) == []
    assert {"metric": "total_rows", "value": "3"} in _read_csv(summary_csv)


def test_missing_required_column_fails(tmp_path: Path) -> None:
    labels_csv = tmp_path / "labels.csv"
    schema_path = _write_schema(tmp_path)
    columns = [column for column in REVIEW_LABEL_COLUMNS if column != "reviewer"]
    rows = [{key: value for key, value in _valid_rows()[0].items() if key in columns}]
    _write_labels_csv(labels_csv, rows, columns=columns)

    result = validate_review_labels(input_csv=labels_csv, schema_path=schema_path)

    assert result.is_valid is False
    assert result.errors[0]["error_type"] == "missing_column"
    assert result.errors[0]["column"] == "reviewer"


def test_invalid_enum_reports_row_column_and_value(tmp_path: Path) -> None:
    labels_csv = tmp_path / "labels.csv"
    schema_path = _write_schema(tmp_path)
    rows = _valid_rows()
    rows[0]["photo_type_review"] = "outside"
    _write_labels_csv(labels_csv, rows)

    result = validate_review_labels(input_csv=labels_csv, schema_path=schema_path)

    assert result.is_valid is False
    assert {
        "row_number": 2,
        "column": "photo_type_review",
        "value": "outside",
        "error_type": "invalid_value",
        "message": "value must be one of: exterior, interior, low_quality, irrelevant, unknown",
    } in result.errors


def test_conditional_rules_fail_for_inconsistent_review_labels(tmp_path: Path) -> None:
    labels_csv = tmp_path / "labels.csv"
    schema_path = _write_schema(tmp_path)
    rows = _valid_rows()
    rows[0]["is_exterior_review"] = "0"
    rows[1]["has_visible_damage_review"] = "0"
    rows[1]["severity_review"] = "minor"
    rows[2]["review_status"] = "reviewed"
    rows[2]["reviewer"] = ""
    _write_labels_csv(labels_csv, rows)

    result = validate_review_labels(input_csv=labels_csv, schema_path=schema_path)

    messages = {error["message"] for error in result.errors}
    assert "photo_type_review=exterior requires is_exterior_review=1" in messages
    assert "has_visible_damage_review=0 requires severity_review=unknown" in messages
    assert "review_status=reviewed requires reviewer" in messages


def test_duplicate_review_id_and_image_id_fail(tmp_path: Path) -> None:
    labels_csv = tmp_path / "labels.csv"
    schema_path = _write_schema(tmp_path)
    rows = _valid_rows()
    rows[1]["review_id"] = rows[0]["review_id"]
    rows[1]["image_id"] = rows[0]["image_id"]
    _write_labels_csv(labels_csv, rows)

    result = validate_review_labels(input_csv=labels_csv, schema_path=schema_path)

    duplicate_errors = [
        error for error in result.errors if error["error_type"] == "duplicate_value"
    ]
    assert {error["column"] for error in duplicate_errors} == {"review_id", "image_id"}


def test_cli_writes_summary_and_errors_and_returns_validation_exit_code(
    tmp_path: Path,
) -> None:
    labels_csv = tmp_path / "dataset" / "00_catalog" / "image_review_labels.csv"
    schema_path = _write_schema(tmp_path)
    rows = _valid_rows()
    rows[0]["angle_review"] = "front"
    _write_labels_csv(labels_csv, rows)
    summary_csv = tmp_path / "outputs" / "metadata" / "summary.csv"
    errors_csv = tmp_path / "outputs" / "metadata" / "errors.csv"

    exit_code = main(
        [
            "--project-root",
            str(tmp_path),
            "--schema",
            str(schema_path),
            "--input",
            str(labels_csv),
            "--report",
            str(summary_csv),
            "--errors",
            str(errors_csv),
        ]
    )

    assert exit_code == 1
    assert {"metric": "error_count", "value": "1"} in _read_csv(summary_csv)
    assert _read_csv(errors_csv)[0]["column"] == "angle_review"
