"""Validate FleetVision human review label CSV files."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


SUMMARY_COLUMNS = ["metric", "value"]
ERROR_COLUMNS = ["row_number", "column", "value", "error_type", "message"]


@dataclass(frozen=True)
class ValidationResult:
    """Result object returned by review label validation."""

    is_valid: bool
    total_rows: int
    error_count: int
    errors: list[dict[str, Any]]


def load_schema(schema_path: Path) -> dict[str, Any]:
    """Load and minimally validate review label schema YAML."""
    if not schema_path.exists():
        raise FileNotFoundError(f"review label schema not found: {schema_path}")

    with schema_path.open(encoding="utf-8") as schema_file:
        schema = yaml.safe_load(schema_file) or {}

    required_settings = [
        "required_columns",
        "identity_columns",
        "allowed_values",
        "unique_columns",
    ]
    missing_settings = [setting for setting in required_settings if setting not in schema]
    if missing_settings:
        raise ValueError(
            "review label schema is missing required setting(s): "
            + ", ".join(missing_settings)
        )
    return schema


def validate_review_labels(
    input_csv: Path,
    schema_path: Path,
    summary_csv: Path | None = None,
    errors_csv: Path | None = None,
) -> ValidationResult:
    """Validate a human-created review labels CSV against the configured schema."""
    schema = load_schema(schema_path)
    if not input_csv.exists():
        raise FileNotFoundError(f"review labels CSV not found: {input_csv}")

    with input_csv.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    errors: list[dict[str, Any]] = []
    errors.extend(_validate_required_columns(fieldnames, schema["required_columns"]))
    if not errors:
        errors.extend(_validate_rows(rows, schema))

    result = ValidationResult(
        is_valid=not errors,
        total_rows=len(rows),
        error_count=len(errors),
        errors=errors,
    )

    if summary_csv is not None:
        write_summary_csv(result, summary_csv)
    if errors_csv is not None:
        write_errors_csv(errors, errors_csv)
    return result


def write_summary_csv(result: ValidationResult, summary_csv: Path) -> None:
    """Write validation summary metrics to CSV."""
    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {"metric": "total_rows", "value": result.total_rows},
        {"metric": "error_count", "value": result.error_count},
        {"metric": "is_valid", "value": str(result.is_valid).lower()},
    ]
    with summary_csv.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_errors_csv(errors: list[dict[str, Any]], errors_csv: Path) -> None:
    """Write validation errors to CSV."""
    errors_csv.parent.mkdir(parents=True, exist_ok=True)
    with errors_csv.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=ERROR_COLUMNS)
        writer.writeheader()
        writer.writerows(errors)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for review label validation."""
    parser = argparse.ArgumentParser(description="Validate FleetVision review labels CSV.")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root used to resolve relative paths. Defaults to current folder.",
    )
    parser.add_argument(
        "--schema",
        default="configs/data/review_label_schema.yaml",
        help="Path to review label schema YAML.",
    )
    parser.add_argument("--input", help="Override input review labels CSV path.")
    parser.add_argument("--report", help="Override validation summary CSV output path.")
    parser.add_argument("--errors", help="Override validation errors CSV output path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for validating FleetVision review labels."""
    args = parse_args(argv)
    project_root = Path(args.project_root).resolve()
    schema_path = _resolve_project_path(project_root, args.schema)

    try:
        schema = load_schema(schema_path)
        input_csv = _resolve_project_path(project_root, args.input or schema["input_csv"])
        summary_csv = _resolve_project_path(
            project_root, args.report or schema["summary_csv"]
        )
        errors_csv = _resolve_project_path(
            project_root, args.errors or schema["errors_csv"]
        )
        result = validate_review_labels(
            input_csv=input_csv,
            schema_path=schema_path,
            summary_csv=summary_csv,
            errors_csv=errors_csv,
        )
    except (FileNotFoundError, KeyError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    _print_summary(result, summary_csv, errors_csv)
    return 0 if result.is_valid else 1


def _validate_required_columns(
    fieldnames: list[str], required_columns: list[str]
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for column in required_columns:
        if column not in fieldnames:
            errors.append(
                _error(
                    row_number=1,
                    column=column,
                    value="",
                    error_type="missing_column",
                    message="required column is missing",
                )
            )
    return errors


def _validate_rows(
    rows: list[dict[str, str]], schema: dict[str, Any]
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    identity_columns = list(schema["identity_columns"])
    allowed_values = dict(schema["allowed_values"])

    for row_index, row in enumerate(rows, start=2):
        errors.extend(_validate_identity_values(row_index, row, identity_columns))
        errors.extend(_validate_allowed_values(row_index, row, allowed_values))
        errors.extend(_validate_conditional_rules(row_index, row))

    errors.extend(_validate_duplicate_values(rows, list(schema["unique_columns"])))
    return errors


def _validate_identity_values(
    row_number: int, row: dict[str, str], identity_columns: list[str]
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for column in identity_columns:
        value = row.get(column, "")
        if not value.strip():
            errors.append(
                _error(
                    row_number=row_number,
                    column=column,
                    value=value,
                    error_type="empty_required_value",
                    message="identity value must not be empty",
                )
            )
    return errors


def _validate_allowed_values(
    row_number: int,
    row: dict[str, str],
    allowed_values: dict[str, list[str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for column, allowed in allowed_values.items():
        value = row.get(column, "")
        if value not in allowed:
            errors.append(
                _error(
                    row_number=row_number,
                    column=column,
                    value=value,
                    error_type="invalid_value",
                    message="value must be one of: " + ", ".join(allowed),
                )
            )
    return errors


def _validate_conditional_rules(
    row_number: int, row: dict[str, str]
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    photo_type = row["photo_type_review"]
    is_exterior = row["is_exterior_review"]
    has_visible_damage = row["has_visible_damage_review"]
    severity = row["severity_review"]
    review_status = row["review_status"]
    reviewer = row["reviewer"]

    if review_status == "reviewed" and not reviewer.strip():
        errors.append(
            _error(
                row_number,
                "reviewer",
                reviewer,
                "conditional_rule",
                "review_status=reviewed requires reviewer",
            )
        )
    if photo_type == "exterior" and is_exterior != "1":
        errors.append(
            _error(
                row_number,
                "is_exterior_review",
                is_exterior,
                "conditional_rule",
                "photo_type_review=exterior requires is_exterior_review=1",
            )
        )
    if photo_type in {"interior", "low_quality", "irrelevant"} and is_exterior != "0":
        errors.append(
            _error(
                row_number,
                "is_exterior_review",
                is_exterior,
                "conditional_rule",
                f"photo_type_review={photo_type} requires is_exterior_review=0",
            )
        )
    if has_visible_damage == "0" and severity != "unknown":
        errors.append(
            _error(
                row_number,
                "severity_review",
                severity,
                "conditional_rule",
                "has_visible_damage_review=0 requires severity_review=unknown",
            )
        )
    return errors


def _validate_duplicate_values(
    rows: list[dict[str, str]], unique_columns: list[str]
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    seen: dict[str, dict[str, int]] = {column: {} for column in unique_columns}

    for row_index, row in enumerate(rows, start=2):
        for column in unique_columns:
            value = row.get(column, "")
            if not value:
                continue
            if value in seen[column]:
                errors.append(
                    _error(
                        row_number=row_index,
                        column=column,
                        value=value,
                        error_type="duplicate_value",
                        message=f"duplicate {column}; first seen on row {seen[column][value]}",
                    )
                )
            else:
                seen[column][value] = row_index
    return errors


def _error(
    row_number: int,
    column: str,
    value: Any,
    error_type: str,
    message: str,
) -> dict[str, Any]:
    return {
        "row_number": row_number,
        "column": column,
        "value": value,
        "error_type": error_type,
        "message": message,
    }


def _resolve_project_path(project_root: Path, path_text: str | Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return project_root / path


def _print_summary(
    result: ValidationResult, summary_csv: Path, errors_csv: Path
) -> None:
    print("FleetVision review label validation summary")
    print(f"summary_csv: {summary_csv}")
    print(f"errors_csv: {errors_csv}")
    print(f"total_rows: {result.total_rows}")
    print(f"error_count: {result.error_count}")
    print(f"is_valid: {str(result.is_valid).lower()}")


if __name__ == "__main__":
    raise SystemExit(main())
