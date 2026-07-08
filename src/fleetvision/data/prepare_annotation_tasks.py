"""Prepare annotation task manifests from Phase 04 annotation candidates.

Phase 05 creates CSV task lists for manual bounding-box annotation preparation.
It does not copy images, read image bytes, create YOLO label files, build a
YOLO dataset, or train models.
"""

from __future__ import annotations

import argparse
import hashlib
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
    "candidate_reason",
]

TASK_COLUMNS = [
    "task_id",
    "review_id",
    "image_id",
    "source_bucket",
    "original_path",
    "filename",
    "photo_type_review",
    "angle_review",
    "severity_review",
    "candidate_reason",
    "annotation_class",
    "annotation_type",
    "annotation_status",
    "task_priority",
    "task_notes",
]

SUMMARY_COLUMNS = [
    "total_input_rows",
    "eligible_task_rows",
    "skipped_rows",
    "claimable_rows",
    "minor_rows",
    "unknown_severity_rows",
    "annotation_class",
    "annotation_type",
]

DEFAULT_CONFIG_PATH = Path("configs/data/annotation_prep_config.yaml")
DEFAULT_INPUT_CSV = Path("dataset/04_annotations/annotation_candidates.csv")
DEFAULT_TASK_MANIFEST_OUTPUT = Path("dataset/04_annotations/annotation_task_manifest.csv")
DEFAULT_SUMMARY_OUTPUT = Path("outputs/metadata/annotation_task_manifest_summary.csv")

TRUE_VALUES = {"1", "true", "yes", "y"}


@dataclass(frozen=True)
class AnnotationPrepConfig:
    """Resolved Phase 05 annotation preparation configuration."""

    input_csv: Path
    task_manifest_csv: Path
    summary_csv: Path
    annotation_class: str = "damage"
    annotation_type: str = "bbox"
    annotation_status: str = "pending"
    require_reviewed_status: bool = True
    reviewed_status_value: str = "reviewed"
    require_visible_damage: bool = True
    severity_priority: dict[str, int] | None = None
    default_priority: int = 40


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


def safe_relative_path(path: Path, root: Path) -> Path:
    """Return path relative to root when possible."""
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return path


def _get_nested(config: dict[str, Any], dotted_key: str, default: Any) -> Any:
    cursor: Any = config
    for part in dotted_key.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            return default
        cursor = cursor[part]
    return cursor


def load_config(config_path: Path, project_root: Path) -> AnnotationPrepConfig:
    """Load YAML config and resolve paths."""
    if not config_path.exists():
        raise FileNotFoundError(f"Annotation prep config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file) or {}

    severity_priority = _get_nested(
        raw_config,
        "priority_rules.severity_review",
        {"claimable": 10, "minor": 20, "unknown": 30},
    )
    if not isinstance(severity_priority, dict):
        raise ValueError("priority_rules.severity_review must be a mapping")

    return AnnotationPrepConfig(
        input_csv=resolve_path(Path(raw_config.get("input_csv", DEFAULT_INPUT_CSV)), project_root),
        task_manifest_csv=resolve_path(
            Path(_get_nested(raw_config, "outputs.task_manifest_csv", DEFAULT_TASK_MANIFEST_OUTPUT)), project_root
        ),
        summary_csv=resolve_path(Path(_get_nested(raw_config, "outputs.summary_csv", DEFAULT_SUMMARY_OUTPUT)), project_root),
        annotation_class=str(_get_nested(raw_config, "settings.annotation_class", "damage")),
        annotation_type=str(_get_nested(raw_config, "settings.annotation_type", "bbox")),
        annotation_status=str(_get_nested(raw_config, "settings.annotation_status", "pending")),
        require_reviewed_status=bool(_get_nested(raw_config, "settings.require_reviewed_status", True)),
        reviewed_status_value=str(_get_nested(raw_config, "settings.reviewed_status_value", "reviewed")),
        require_visible_damage=bool(_get_nested(raw_config, "settings.require_visible_damage", True)),
        severity_priority={str(key): int(value) for key, value in severity_priority.items()},
        default_priority=int(_get_nested(raw_config, "priority_rules.default_priority", 40)),
    )


def read_annotation_candidates(input_csv: Path) -> pd.DataFrame:
    """Read Phase 04 annotation candidates CSV."""
    if not input_csv.exists():
        raise FileNotFoundError(f"Annotation candidates CSV not found: {input_csv}")
    return pd.read_csv(input_csv, dtype=str, keep_default_na=False)


def validate_required_columns(dataframe: pd.DataFrame, required_columns: list[str] | None = None) -> None:
    """Fail fast when expected candidate columns are missing."""
    required = required_columns or REQUIRED_COLUMNS
    missing = [column for column in required if column not in dataframe.columns]
    if missing:
        raise ValueError("Annotation candidates CSV is missing required columns: " + ", ".join(missing))


def normalize_bool_string(value: Any) -> str:
    """Normalize user-facing boolean-like values to strings."""
    return str(value).strip().lower()


def is_true_value(value: Any) -> bool:
    """Return True for standard truthy review label strings."""
    return normalize_bool_string(value) in TRUE_VALUES


def make_task_id(row: pd.Series) -> str:
    """Create a stable annotation task ID from review and image identity."""
    raw = f"{row.get('review_id', '')}|{row.get('image_id', '')}|{row.get('original_path', '')}".encode("utf-8")
    return "task_" + hashlib.sha1(raw).hexdigest()[:16]


def build_eligible_candidates(candidates: pd.DataFrame, config: AnnotationPrepConfig) -> pd.DataFrame:
    """Filter Phase 04 annotation candidates to Phase 05 annotation tasks."""
    validate_required_columns(candidates)
    eligible = candidates.copy()

    eligible = eligible[
        (eligible["photo_type_review"].astype(str).str.strip().str.lower() == "exterior")
        & eligible["is_exterior_review"].map(is_true_value)
    ]

    if config.require_reviewed_status:
        eligible = eligible[eligible["review_status"].astype(str).str.strip().str.lower() == config.reviewed_status_value]

    if config.require_visible_damage:
        eligible = eligible[eligible["has_visible_damage_review"].map(is_true_value)]

    return eligible.reset_index(drop=True)


def build_annotation_task_manifest(candidates: pd.DataFrame, config: AnnotationPrepConfig) -> pd.DataFrame:
    """Build an annotation task manifest from eligible candidates."""
    eligible = build_eligible_candidates(candidates, config)
    if eligible.empty:
        return pd.DataFrame(columns=TASK_COLUMNS)

    manifest = pd.DataFrame()
    manifest["task_id"] = eligible.apply(make_task_id, axis=1)
    for column in [
        "review_id",
        "image_id",
        "source_bucket",
        "original_path",
        "filename",
        "photo_type_review",
        "angle_review",
        "severity_review",
        "candidate_reason",
    ]:
        manifest[column] = eligible[column]
    manifest["annotation_class"] = config.annotation_class
    manifest["annotation_type"] = config.annotation_type
    manifest["annotation_status"] = config.annotation_status
    manifest["task_priority"] = eligible["severity_review"].map(config.severity_priority or {}).fillna(config.default_priority).astype(int)
    manifest["task_notes"] = ""
    return manifest[TASK_COLUMNS].sort_values(["task_priority", "source_bucket", "filename"]).reset_index(drop=True)


def build_summary(candidates: pd.DataFrame, manifest: pd.DataFrame, config: AnnotationPrepConfig) -> pd.DataFrame:
    """Build a compact Phase 05 summary DataFrame."""
    severity = manifest["severity_review"] if "severity_review" in manifest.columns else pd.Series(dtype=str)
    row = {
        "total_input_rows": int(len(candidates)),
        "eligible_task_rows": int(len(manifest)),
        "skipped_rows": int(len(candidates) - len(manifest)),
        "claimable_rows": int((severity == "claimable").sum()),
        "minor_rows": int((severity == "minor").sum()),
        "unknown_severity_rows": int((severity == "unknown").sum()),
        "annotation_class": config.annotation_class,
        "annotation_type": config.annotation_type,
    }
    return pd.DataFrame([row], columns=SUMMARY_COLUMNS)


def write_csv(dataframe: pd.DataFrame, output_path: Path) -> None:
    """Write a CSV with UTF-8 BOM for Excel compatibility."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False, encoding="utf-8-sig")


def build_annotation_tasks(config: AnnotationPrepConfig) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Path]]:
    """Read input candidates, build manifest and summary, then write outputs."""
    candidates = read_annotation_candidates(config.input_csv)
    manifest = build_annotation_task_manifest(candidates, config)
    summary = build_summary(candidates, manifest, config)
    write_csv(manifest, config.task_manifest_csv)
    write_csv(summary, config.summary_csv)
    return manifest, summary, {"task_manifest": config.task_manifest_csv, "summary": config.summary_csv}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Phase 05 annotation task manifest CSV files.")
    parser.add_argument("--project-root", type=Path, default=None, help="FleetVision project root. Default: auto-detect.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to annotation prep config YAML.")
    parser.add_argument("--input", type=Path, default=None, help="Override annotation candidates input CSV.")
    parser.add_argument("--output", type=Path, default=None, help="Override annotation task manifest output CSV.")
    parser.add_argument("--summary-output", type=Path, default=None, help="Override summary output CSV.")
    return parser.parse_args()


def apply_overrides(config: AnnotationPrepConfig, args: argparse.Namespace, project_root: Path) -> AnnotationPrepConfig:
    """Apply CLI path overrides to a resolved config."""
    return AnnotationPrepConfig(
        input_csv=resolve_path(args.input, project_root) if args.input is not None else config.input_csv,
        task_manifest_csv=resolve_path(args.output, project_root) if args.output is not None else config.task_manifest_csv,
        summary_csv=resolve_path(args.summary_output, project_root) if args.summary_output is not None else config.summary_csv,
        annotation_class=config.annotation_class,
        annotation_type=config.annotation_type,
        annotation_status=config.annotation_status,
        require_reviewed_status=config.require_reviewed_status,
        reviewed_status_value=config.reviewed_status_value,
        require_visible_damage=config.require_visible_damage,
        severity_priority=config.severity_priority,
        default_priority=config.default_priority,
    )


def main() -> None:
    args = parse_args()
    project_root = find_project_root(args.project_root)
    config_path = resolve_path(args.config, project_root)

    try:
        config = load_config(config_path, project_root)
        config = apply_overrides(config, args, project_root)
        manifest, summary, output_paths = build_annotation_tasks(config)
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    summary_row = summary.iloc[0].to_dict()
    for key in [
        "total_input_rows",
        "eligible_task_rows",
        "skipped_rows",
        "claimable_rows",
        "minor_rows",
        "unknown_severity_rows",
    ]:
        print(f"{key}: {summary_row[key]}")

    for name, output_path in output_paths.items():
        print(f"{name}_output: {safe_relative_path(output_path, project_root)}")


if __name__ == "__main__":
    main()
