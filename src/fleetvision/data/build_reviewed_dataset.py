"""Build reviewed dataset CSV lists from validated human review labels.

Phase 04 reads a review labels CSV that should already pass Phase 03
validation, then writes downstream list CSVs for annotation preparation. It does
not read image bytes, copy image files, create YOLO labels, or train models.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

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

BASE_OUTPUT_COLUMNS = REQUIRED_COLUMNS.copy()
ANNOTATION_COLUMNS = BASE_OUTPUT_COLUMNS + ["candidate_reason"]

DEFAULT_CONFIG_PATH = Path("configs/data/reviewed_dataset_config.yaml")
DEFAULT_INPUT_CSV = Path("dataset/00_catalog/image_review_labels.csv")
DEFAULT_EXTERIOR_OUTPUT = Path("dataset/03_reviewed/exterior/exterior_image_list.csv")
DEFAULT_LOW_QUALITY_OUTPUT = Path("dataset/03_reviewed/low_quality/low_quality_image_list.csv")
DEFAULT_IRRELEVANT_OUTPUT = Path("dataset/03_reviewed/irrelevant/irrelevant_image_list.csv")
DEFAULT_ANNOTATION_CANDIDATES_OUTPUT = Path("dataset/04_annotations/annotation_candidates.csv")
DEFAULT_SUMMARY_OUTPUT = Path("outputs/metadata/reviewed_dataset_summary.csv")

TRUE_VALUES = {"1", "true", "yes", "y"}


@dataclass(frozen=True)
class ReviewedDatasetConfig:
    """Resolved Phase 04 configuration."""

    input_csv: Path
    exterior_output_csv: Path
    low_quality_output_csv: Path
    irrelevant_output_csv: Path
    annotation_candidates_csv: Path
    summary_csv: Path
    reviewed_only: bool = True
    reviewed_status_value: str = "reviewed"


def find_project_root(start: Path | None = None) -> Path:
    """Find the FleetVision project root from a starting path."""
    current = (start or Path.cwd()).resolve()
    markers = ["PROJECT_CONTEXT_BRIEF.md", "src/fleetvision", "configs/data"]
    for path in [current, *current.parents]:
        if all((path / marker).exists() for marker in markers):
            return path
    return current


def resolve_path(path: Path, project_root: Path) -> Path:
    """Resolve a project-relative path."""
    return path if path.is_absolute() else project_root / path


def path_to_posix(path: Path) -> str:
    """Return a stable POSIX path string for printed paths."""
    return path.as_posix()


def safe_relative_path(path: Path, root: Path) -> Path:
    """Return path relative to root when possible."""
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return path


def _get_nested(config: dict[str, Any], dotted_key: str, default: Any) -> Any:
    """Fetch a nested value from config with a dotted key."""
    cursor: Any = config
    for part in dotted_key.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            return default
        cursor = cursor[part]
    return cursor


def load_config(config_path: Path, project_root: Path) -> ReviewedDatasetConfig:
    """Load YAML config and resolve all configured paths."""
    if not config_path.exists():
        raise FileNotFoundError(f"Reviewed dataset config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file) or {}

    input_csv = Path(raw_config.get("input_csv", DEFAULT_INPUT_CSV))
    reviewed_only = bool(_get_nested(raw_config, "settings.reviewed_only", True))
    reviewed_status_value = str(_get_nested(raw_config, "settings.reviewed_status_value", "reviewed"))

    return ReviewedDatasetConfig(
        input_csv=resolve_path(input_csv, project_root),
        exterior_output_csv=resolve_path(
            Path(_get_nested(raw_config, "outputs.exterior_csv", DEFAULT_EXTERIOR_OUTPUT)), project_root
        ),
        low_quality_output_csv=resolve_path(
            Path(_get_nested(raw_config, "outputs.low_quality_csv", DEFAULT_LOW_QUALITY_OUTPUT)), project_root
        ),
        irrelevant_output_csv=resolve_path(
            Path(_get_nested(raw_config, "outputs.irrelevant_csv", DEFAULT_IRRELEVANT_OUTPUT)), project_root
        ),
        annotation_candidates_csv=resolve_path(
            Path(_get_nested(raw_config, "outputs.annotation_candidates_csv", DEFAULT_ANNOTATION_CANDIDATES_OUTPUT)),
            project_root,
        ),
        summary_csv=resolve_path(Path(_get_nested(raw_config, "outputs.summary_csv", DEFAULT_SUMMARY_OUTPUT)), project_root),
        reviewed_only=reviewed_only,
        reviewed_status_value=reviewed_status_value,
    )


def read_review_labels(input_csv: Path) -> pd.DataFrame:
    """Read review labels CSV as strings."""
    if not input_csv.exists():
        raise FileNotFoundError(f"Review labels CSV not found: {input_csv}")
    return pd.read_csv(input_csv, dtype="string", keep_default_na=False)


def validate_required_columns(dataframe: pd.DataFrame, required_columns: list[str] | None = None) -> None:
    """Fail fast when required columns are missing."""
    required = required_columns or REQUIRED_COLUMNS
    missing = [column for column in required if column not in dataframe.columns]
    if missing:
        raise ValueError("Review labels CSV missing required columns: " + ", ".join(missing))


def normalize_text(series: pd.Series) -> pd.Series:
    """Normalize text for filtering while preserving source output values elsewhere."""
    return series.astype("string").fillna("").str.strip().str.lower()


def is_true_series(series: pd.Series) -> pd.Series:
    """Return true for string or numeric true-like values."""
    return normalize_text(series).isin(TRUE_VALUES)


def select_output_columns(dataframe: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return a stable copy with selected output columns."""
    return dataframe.loc[:, columns].copy().reset_index(drop=True)


def build_reviewed_dataset_outputs(
    review_labels: pd.DataFrame,
    *,
    reviewed_only: bool = True,
    reviewed_status_value: str = "reviewed",
) -> dict[str, pd.DataFrame]:
    """Build reviewed dataset list DataFrames from review labels."""
    validate_required_columns(review_labels)

    labels = review_labels.copy()
    review_status = normalize_text(labels["review_status"])
    photo_type = normalize_text(labels["photo_type_review"])
    is_exterior = is_true_series(labels["is_exterior_review"])
    has_visible_damage = is_true_series(labels["has_visible_damage_review"])

    if reviewed_only:
        eligible_mask = review_status == reviewed_status_value.strip().lower()
    else:
        eligible_mask = pd.Series(True, index=labels.index)

    exterior_mask = eligible_mask & (photo_type == "exterior") & is_exterior
    low_quality_mask = eligible_mask & (photo_type == "low_quality")
    irrelevant_mask = eligible_mask & (photo_type == "irrelevant")
    annotation_mask = exterior_mask & has_visible_damage

    exterior = select_output_columns(labels.loc[exterior_mask], BASE_OUTPUT_COLUMNS)
    low_quality = select_output_columns(labels.loc[low_quality_mask], BASE_OUTPUT_COLUMNS)
    irrelevant = select_output_columns(labels.loc[irrelevant_mask], BASE_OUTPUT_COLUMNS)

    annotation_candidates = select_output_columns(labels.loc[annotation_mask], BASE_OUTPUT_COLUMNS)
    annotation_candidates["candidate_reason"] = "visible_damage_reviewed"
    annotation_candidates = annotation_candidates.loc[:, ANNOTATION_COLUMNS]

    skipped_not_reviewed = int((~eligible_mask).sum()) if reviewed_only else 0
    summary = pd.DataFrame(
        [
            {
                "total_rows": int(len(labels)),
                "reviewed_rows": int(eligible_mask.sum()),
                "skipped_not_reviewed": skipped_not_reviewed,
                "exterior_rows": int(len(exterior)),
                "low_quality_rows": int(len(low_quality)),
                "irrelevant_rows": int(len(irrelevant)),
                "annotation_candidate_rows": int(len(annotation_candidates)),
                "interior_rows": int((eligible_mask & (photo_type == "interior")).sum()),
                "unknown_rows": int((eligible_mask & (photo_type == "unknown")).sum()),
            }
        ]
    )

    return {
        "exterior": exterior,
        "low_quality": low_quality,
        "irrelevant": irrelevant,
        "annotation_candidates": annotation_candidates,
        "summary": summary,
    }


def write_csv(dataframe: pd.DataFrame, output_path: Path) -> None:
    """Write CSV with UTF-8 BOM for Excel compatibility."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False, encoding="utf-8-sig")


def write_reviewed_dataset_outputs(outputs: dict[str, pd.DataFrame], config: ReviewedDatasetConfig) -> dict[str, Path]:
    """Write all Phase 04 generated outputs."""
    output_paths = {
        "exterior": config.exterior_output_csv,
        "low_quality": config.low_quality_output_csv,
        "irrelevant": config.irrelevant_output_csv,
        "annotation_candidates": config.annotation_candidates_csv,
        "summary": config.summary_csv,
    }
    for name, output_path in output_paths.items():
        write_csv(outputs[name], output_path)
    return output_paths


def build_reviewed_dataset(config: ReviewedDatasetConfig) -> tuple[dict[str, pd.DataFrame], dict[str, Path]]:
    """Read labels, build outputs, and write CSV files."""
    review_labels = read_review_labels(config.input_csv)
    outputs = build_reviewed_dataset_outputs(
        review_labels,
        reviewed_only=config.reviewed_only,
        reviewed_status_value=config.reviewed_status_value,
    )
    output_paths = write_reviewed_dataset_outputs(outputs, config)
    return outputs, output_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Phase 04 reviewed dataset CSV lists.")
    parser.add_argument("--project-root", type=Path, default=None, help="FleetVision project root. Default: auto-detect.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to reviewed dataset config YAML.")
    parser.add_argument("--input", type=Path, default=None, help="Override review labels input CSV.")
    parser.add_argument("--exterior-output", type=Path, default=None, help="Override exterior image list output CSV.")
    parser.add_argument("--low-quality-output", type=Path, default=None, help="Override low-quality image list output CSV.")
    parser.add_argument("--irrelevant-output", type=Path, default=None, help="Override irrelevant image list output CSV.")
    parser.add_argument(
        "--annotation-candidates-output",
        type=Path,
        default=None,
        help="Override annotation candidates output CSV.",
    )
    parser.add_argument("--summary-output", type=Path, default=None, help="Override summary output CSV.")
    return parser.parse_args()


def apply_overrides(config: ReviewedDatasetConfig, args: argparse.Namespace, project_root: Path) -> ReviewedDatasetConfig:
    """Apply CLI path overrides to a resolved config."""
    return ReviewedDatasetConfig(
        input_csv=resolve_path(args.input, project_root) if args.input is not None else config.input_csv,
        exterior_output_csv=resolve_path(args.exterior_output, project_root)
        if args.exterior_output is not None
        else config.exterior_output_csv,
        low_quality_output_csv=resolve_path(args.low_quality_output, project_root)
        if args.low_quality_output is not None
        else config.low_quality_output_csv,
        irrelevant_output_csv=resolve_path(args.irrelevant_output, project_root)
        if args.irrelevant_output is not None
        else config.irrelevant_output_csv,
        annotation_candidates_csv=resolve_path(args.annotation_candidates_output, project_root)
        if args.annotation_candidates_output is not None
        else config.annotation_candidates_csv,
        summary_csv=resolve_path(args.summary_output, project_root) if args.summary_output is not None else config.summary_csv,
        reviewed_only=config.reviewed_only,
        reviewed_status_value=config.reviewed_status_value,
    )


def main() -> None:
    args = parse_args()
    project_root = find_project_root(args.project_root)
    config_path = resolve_path(args.config, project_root)

    try:
        config = load_config(config_path, project_root)
        config = apply_overrides(config, args, project_root)
        outputs, output_paths = build_reviewed_dataset(config)
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    summary_row = outputs["summary"].iloc[0].to_dict()
    for key in [
        "total_rows",
        "reviewed_rows",
        "skipped_not_reviewed",
        "exterior_rows",
        "low_quality_rows",
        "irrelevant_rows",
        "annotation_candidate_rows",
    ]:
        print(f"{key}: {summary_row[key]}")

    for name, output_path in output_paths.items():
        print(f"{name}_output: {safe_relative_path(output_path, project_root)}")


if __name__ == "__main__":
    main()
