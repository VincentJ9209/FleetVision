"""Validate Pilot 500 human review worklist CSV files."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


DEFAULT_CONFIG_PATH = Path("configs/data/pilot_human_review_validation_config.yaml")
DEFAULT_INPUT_CSV = Path("dataset/00_catalog/image_review_labels_pilot500_human_review_worklist.csv")
DEFAULT_SUMMARY_CSV = Path("outputs/metadata/pilot500_human_review_validation_summary.csv")
DEFAULT_ERRORS_CSV = Path("outputs/metadata/pilot500_human_review_validation_errors.csv")

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

ALLOWED_VALUES = {
    "human_photo_type_review": {"exterior", "interior", "low_quality", "irrelevant", "unknown"},
    "human_angle_review": {
        "front",
        "rear",
        "left",
        "right",
        "front_left",
        "front_right",
        "rear_left",
        "rear_right",
        "unknown",
    },
    "human_is_exterior_review": {"0", "1", "unknown"},
    "human_has_visible_damage_review": {"0", "1", "unknown"},
    "human_severity_review": {"none", "minor", "moderate", "severe", "unknown"},
    "human_review_status": {"pending", "reviewed", "needs_followup", "skipped"},
}

ERROR_COLUMNS = ["row_number", "review_id", "image_id", "column", "error_code", "message", "value"]
SUMMARY_COLUMNS = [
    "total_rows",
    "valid_rows",
    "invalid_rows",
    "error_count",
    "pending_rows",
    "reviewed_rows",
    "needs_followup_rows",
    "skipped_rows",
    "reviewed_at_filled_rows",
    "is_valid",
]


@dataclass(frozen=True)
class PilotHumanReviewValidationConfig:
    """Resolved configuration for Pilot 500 human review validation."""

    input_csv: Path
    summary_csv: Path
    errors_csv: Path
    expected_rows: int = 500
    require_unique_review_id: bool = True
    require_unique_image_id: bool = True
    reviewed_status_value: str = "reviewed"
    pending_status_value: str = "pending"
    followup_status_value: str = "needs_followup"
    skipped_status_value: str = "skipped"


@dataclass(frozen=True)
class ValidationResult:
    """Validation result for a Pilot 500 human review worklist."""

    total_rows: int
    valid_rows: int
    invalid_rows: int
    error_count: int
    pending_rows: int
    reviewed_rows: int
    needs_followup_rows: int
    skipped_rows: int
    reviewed_at_filled_rows: int
    is_valid: bool
    errors: list[dict[str, Any]]


def find_project_root(start: Path | None = None) -> Path:
    """Find the FleetVision project root from a starting path."""
    current = (start or Path.cwd()).resolve()
    markers = ["PROJECT_CONTEXT_BRIEF.md", "src/fleetvision", "configs/data"]
    for path in [current, *current.parents]:
        if all((path / marker).exists() for marker in markers):
            return path
    return current


def resolve_path(path: str | Path | None, project_root: Path, default: Path | None = None) -> Path:
    """Resolve a possibly relative path against the project root."""
    raw = Path(path) if path is not None else default
    if raw is None:
        raise ValueError("path or default must be provided")
    return raw if raw.is_absolute() else project_root / raw


def load_config(config_path: Path, project_root: Path) -> PilotHumanReviewValidationConfig:
    """Load and resolve Pilot 500 human review validation YAML config."""
    if not config_path.exists():
        raise FileNotFoundError(f"Pilot human review validation config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        raw_config: dict[str, Any] = yaml.safe_load(file) or {}

    return PilotHumanReviewValidationConfig(
        input_csv=resolve_path(raw_config.get("input_csv"), project_root, DEFAULT_INPUT_CSV),
        summary_csv=resolve_path(raw_config.get("summary_csv"), project_root, DEFAULT_SUMMARY_CSV),
        errors_csv=resolve_path(raw_config.get("errors_csv"), project_root, DEFAULT_ERRORS_CSV),
        expected_rows=int(raw_config.get("expected_rows", 500)),
        require_unique_review_id=bool(raw_config.get("require_unique_review_id", True)),
        require_unique_image_id=bool(raw_config.get("require_unique_image_id", True)),
        reviewed_status_value=str(raw_config.get("reviewed_status_value", "reviewed")).strip().lower(),
        pending_status_value=str(raw_config.get("pending_status_value", "pending")).strip().lower(),
        followup_status_value=str(raw_config.get("followup_status_value", "needs_followup")).strip().lower(),
        skipped_status_value=str(raw_config.get("skipped_status_value", "skipped")).strip().lower(),
    )


def read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV with UTF-8 BOM support while preserving blank strings."""
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def validate_required_columns(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    """Validate required human review columns exist."""
    errors: list[dict[str, Any]] = []
    for column in REQUIRED_COLUMNS:
        if column not in dataframe.columns:
            errors.append(
                _error(
                    row_number=1,
                    review_id="",
                    image_id="",
                    column=column,
                    error_code="missing_column",
                    message="required column is missing",
                    value="",
                )
            )
    return errors


def validate_pilot_human_review(
    dataframe: pd.DataFrame,
    config: PilotHumanReviewValidationConfig,
) -> ValidationResult:
    """Validate a Pilot 500 human review worklist without mutating the input DataFrame."""
    errors = validate_required_columns(dataframe)
    total_rows = int(len(dataframe))

    if total_rows != config.expected_rows:
        errors.append(
            _error(
                row_number=1,
                review_id="",
                image_id="",
                column="__row_count__",
                error_code="unexpected_row_count",
                message=f"expected {config.expected_rows} row(s), found {total_rows}",
                value=str(total_rows),
            )
        )

    if errors and any(error["error_code"] == "missing_column" for error in errors):
        return _build_result(dataframe, errors, config)

    normalized = _normalized_required_values(dataframe)

    for row_index, row in dataframe.iterrows():
        row_number = int(row_index) + 2
        review_id = str(row["review_id"])
        image_id = str(row["image_id"])
        normalized_row = {column: normalized[column].iat[row_index] for column in REQUIRED_COLUMNS}

        errors.extend(_validate_identity_values(row_number, review_id, image_id, normalized_row))
        errors.extend(_validate_allowed_values(row_number, review_id, image_id, normalized_row))
        errors.extend(_validate_status_rules(row_number, review_id, image_id, normalized_row, config))
        errors.extend(_validate_consistency_rules(row_number, review_id, image_id, normalized_row))

    if config.require_unique_review_id:
        errors.extend(_validate_duplicate_values(dataframe, "review_id"))
    if config.require_unique_image_id:
        errors.extend(_validate_duplicate_values(dataframe, "image_id"))

    return _build_result(dataframe, errors, config)


def write_summary_csv(result: ValidationResult, summary_csv: Path) -> None:
    """Write one-row validation summary CSV using UTF-8 BOM."""
    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    row = {column: getattr(result, column) for column in SUMMARY_COLUMNS}
    pd.DataFrame([row], columns=SUMMARY_COLUMNS).to_csv(summary_csv, index=False, encoding="utf-8-sig")


def write_errors_csv(errors: list[dict[str, Any]], errors_csv: Path) -> None:
    """Write validation errors CSV using UTF-8 BOM, including a header when empty."""
    errors_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(errors, columns=ERROR_COLUMNS).to_csv(errors_csv, index=False, encoding="utf-8-sig")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description="Validate FleetVision Pilot 500 human review worklist CSV.")
    parser.add_argument("--project-root", type=Path, default=None, help="FleetVision project root. Default: auto-detect.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to validation config YAML.")
    parser.add_argument("--input", type=Path, default=None, help="Override input human review worklist CSV.")
    parser.add_argument("--summary-output", type=Path, default=None, help="Override validation summary CSV.")
    parser.add_argument("--errors-output", type=Path, default=None, help="Override validation errors CSV.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    project_root = find_project_root(args.project_root)
    config_path = resolve_path(args.config, project_root, DEFAULT_CONFIG_PATH)

    try:
        config = load_config(config_path, project_root)
        config = _apply_overrides(config, args, project_root)
        dataframe = read_csv(config.input_csv)
        result = validate_pilot_human_review(dataframe, config)
        write_summary_csv(result, config.summary_csv)
        write_errors_csv(result.errors, config.errors_csv)
    except Exception as exc:  # noqa: BLE001 - CLI should return concise errors.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print("FleetVision Pilot 500 human review validation summary")
    print(f"summary_csv: {config.summary_csv}")
    print(f"errors_csv: {config.errors_csv}")
    for column in SUMMARY_COLUMNS:
        print(f"{column}: {getattr(result, column)}")
    return 0 if result.is_valid else 1


def _apply_overrides(
    config: PilotHumanReviewValidationConfig,
    args: argparse.Namespace,
    project_root: Path,
) -> PilotHumanReviewValidationConfig:
    return PilotHumanReviewValidationConfig(
        input_csv=resolve_path(args.input, project_root, config.input_csv),
        summary_csv=resolve_path(args.summary_output, project_root, config.summary_csv),
        errors_csv=resolve_path(args.errors_output, project_root, config.errors_csv),
        expected_rows=config.expected_rows,
        require_unique_review_id=config.require_unique_review_id,
        require_unique_image_id=config.require_unique_image_id,
        reviewed_status_value=config.reviewed_status_value,
        pending_status_value=config.pending_status_value,
        followup_status_value=config.followup_status_value,
        skipped_status_value=config.skipped_status_value,
    )


def _normalized_required_values(dataframe: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        column: dataframe[column].astype(str).str.strip().str.lower()
        for column in REQUIRED_COLUMNS
    }


def _validate_identity_values(
    row_number: int,
    review_id: str,
    image_id: str,
    row: dict[str, str],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for column in ["review_id", "image_id"]:
        if row[column] == "":
            errors.append(
                _error(row_number, review_id, image_id, column, "empty_required_value", f"{column} must not be blank", row[column])
            )
    return errors


def _validate_allowed_values(
    row_number: int,
    review_id: str,
    image_id: str,
    row: dict[str, str],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for column, allowed in ALLOWED_VALUES.items():
        value = row[column]
        if value not in allowed:
            errors.append(
                _error(
                    row_number,
                    review_id,
                    image_id,
                    column,
                    "invalid_value",
                    "value must be one of: " + ", ".join(sorted(allowed)),
                    value,
                )
            )
    return errors


def _validate_status_rules(
    row_number: int,
    review_id: str,
    image_id: str,
    row: dict[str, str],
    config: PilotHumanReviewValidationConfig,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    status = row["human_review_status"]

    if status == config.reviewed_status_value:
        required_nonblank = [
            "human_reviewer",
            "human_reviewed_at",
            "human_photo_type_review",
            "human_is_exterior_review",
            "human_has_visible_damage_review",
            "human_severity_review",
        ]
        if row["human_photo_type_review"] == "exterior":
            required_nonblank.append("human_angle_review")
        for column in required_nonblank:
            if row[column] == "":
                errors.append(_error(row_number, review_id, image_id, column, "reviewed_required_value", f"{column} is required when human_review_status=reviewed", row[column]))
        if row["human_reviewed_at"] and not _is_iso_datetime(row["human_reviewed_at"]):
            errors.append(_error(row_number, review_id, image_id, "human_reviewed_at", "invalid_datetime", "human_reviewed_at must be an ISO 8601 datetime", row["human_reviewed_at"]))

    if status == config.pending_status_value and row["human_reviewed_at"] != "":
        errors.append(_error(row_number, review_id, image_id, "human_reviewed_at", "pending_reviewed_at_filled", "human_reviewed_at must be blank when human_review_status=pending", row["human_reviewed_at"]))

    if status in {config.followup_status_value, config.skipped_status_value}:
        if row["human_reviewer"] == "":
            errors.append(_error(row_number, review_id, image_id, "human_reviewer", "status_required_reviewer", f"human_reviewer is required when human_review_status={status}", row["human_reviewer"]))
        if row["human_review_notes"] == "":
            errors.append(_error(row_number, review_id, image_id, "human_review_notes", "status_required_notes", f"human_review_notes is required when human_review_status={status}", row["human_review_notes"]))

    return errors


def _validate_consistency_rules(
    row_number: int,
    review_id: str,
    image_id: str,
    row: dict[str, str],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    photo_type = row["human_photo_type_review"]
    is_exterior = row["human_is_exterior_review"]
    has_damage = row["human_has_visible_damage_review"]
    severity = row["human_severity_review"]

    if photo_type == "exterior" and is_exterior != "1":
        errors.append(_error(row_number, review_id, image_id, "human_is_exterior_review", "inconsistent_exterior_flag", "human_photo_type_review=exterior requires human_is_exterior_review=1", is_exterior))
    if photo_type in {"interior", "low_quality", "irrelevant"} and is_exterior != "0":
        errors.append(_error(row_number, review_id, image_id, "human_is_exterior_review", "inconsistent_exterior_flag", f"human_photo_type_review={photo_type} requires human_is_exterior_review=0", is_exterior))
    if has_damage == "0" and severity != "none":
        errors.append(_error(row_number, review_id, image_id, "human_severity_review", "inconsistent_damage_severity", "human_has_visible_damage_review=0 requires human_severity_review=none", severity))
    if has_damage == "1" and severity == "none":
        errors.append(_error(row_number, review_id, image_id, "human_severity_review", "inconsistent_damage_severity", "human_has_visible_damage_review=1 cannot use human_severity_review=none", severity))
    if has_damage == "unknown" and severity != "unknown":
        errors.append(_error(row_number, review_id, image_id, "human_severity_review", "inconsistent_damage_severity", "human_has_visible_damage_review=unknown requires human_severity_review=unknown", severity))
    return errors


def _validate_duplicate_values(dataframe: pd.DataFrame, column: str) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    normalized = dataframe[column].astype(str).str.strip()
    seen: dict[str, int] = {}
    for row_index, value in enumerate(normalized.tolist(), start=2):
        if value == "":
            continue
        if value in seen:
            source_row = dataframe.iloc[row_index - 2]
            errors.append(
                _error(
                    row_number=row_index,
                    review_id=str(source_row.get("review_id", "")),
                    image_id=str(source_row.get("image_id", "")),
                    column=column,
                    error_code="duplicate_value",
                    message=f"duplicate {column}; first seen on row {seen[value]}",
                    value=value,
                )
            )
        else:
            seen[value] = row_index
    return errors


def _build_result(
    dataframe: pd.DataFrame,
    errors: list[dict[str, Any]],
    config: PilotHumanReviewValidationConfig,
) -> ValidationResult:
    total_rows = int(len(dataframe))
    invalid_row_numbers = {int(error["row_number"]) for error in errors if int(error["row_number"]) >= 2}
    invalid_rows = len(invalid_row_numbers)
    if any(int(error["row_number"]) == 1 for error in errors):
        invalid_rows = total_rows if total_rows else 0
    valid_rows = max(total_rows - invalid_rows, 0)

    if "human_review_status" in dataframe.columns:
        statuses = dataframe["human_review_status"].astype(str).str.strip().str.lower()
    else:
        statuses = pd.Series([], dtype=str)
    if "human_reviewed_at" in dataframe.columns:
        reviewed_at = dataframe["human_reviewed_at"].astype(str).str.strip()
    else:
        reviewed_at = pd.Series([], dtype=str)

    return ValidationResult(
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        error_count=len(errors),
        pending_rows=int((statuses == config.pending_status_value).sum()),
        reviewed_rows=int((statuses == config.reviewed_status_value).sum()),
        needs_followup_rows=int((statuses == config.followup_status_value).sum()),
        skipped_rows=int((statuses == config.skipped_status_value).sum()),
        reviewed_at_filled_rows=int((reviewed_at != "").sum()),
        is_valid=len(errors) == 0,
        errors=errors,
    )


def _is_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _error(
    row_number: int,
    review_id: str,
    image_id: str,
    column: str,
    error_code: str,
    message: str,
    value: Any,
) -> dict[str, Any]:
    return {
        "row_number": row_number,
        "review_id": review_id,
        "image_id": image_id,
        "column": column,
        "error_code": error_code,
        "message": message,
        "value": value,
    }


if __name__ == "__main__":
    raise SystemExit(main())
