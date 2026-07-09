"""Phase 03.6 external dataset/model asset scout.

This module initializes a lightweight external asset registry and local folder
layout for Kaggle, Roboflow, Hugging Face, or other public assets. It does not
login, download datasets, call external APIs, or store secrets.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

DEFAULT_CONFIG_PATH = Path("configs/data/external_asset_scout_config.yaml")
DEFAULT_REGISTRY_CSV = Path("dataset/00_catalog/external_asset_registry.csv")
DEFAULT_SUMMARY_CSV = Path("outputs/metadata/external_asset_scout_summary.csv")

REGISTRY_COLUMNS = [
    "asset_id",
    "source_name",
    "platform",
    "url_or_slug",
    "license",
    "dataset_size",
    "task_type",
    "annotation_format",
    "classes",
    "image_count",
    "has_bbox",
    "has_yolo_format",
    "can_map_to_damage",
    "can_use_for_training",
    "can_use_for_prelabel",
    "risk_notes",
    "decision",
    "reviewer",
    "last_checked_at",
]

DEFAULT_ALLOWED_VALUES = {
    "platform": {"kaggle", "roboflow", "huggingface", "github", "other"},
    "task_type": {"object_detection", "segmentation", "classification", "unknown"},
    "annotation_format": {"yolo", "coco", "voc", "cvat", "labelstudio", "image_only", "unknown"},
    "decision": {"pending", "approved_for_download", "rejected", "downloaded", "audited", "converted"},
}

DEFAULT_BOOLEAN_COLUMNS = [
    "has_bbox",
    "has_yolo_format",
    "can_map_to_damage",
    "can_use_for_training",
    "can_use_for_prelabel",
]

TRUE_FALSE_UNKNOWN = {"true", "false", "unknown", ""}


@dataclass(frozen=True)
class ExternalAssetScoutConfig:
    """Resolved Phase 03.6 external asset scout configuration."""

    registry_csv: Path
    summary_csv: Path
    external_raw_root: Path
    external_yolo_labels_raw_root: Path
    external_assets_metadata_root: Path
    provider_subdirs: list[str]
    future_yolo_dataset_roots: dict[str, Path]
    allowed_values: dict[str, set[str]]
    boolean_columns: list[str]


def resolve_project_root(project_root: Path | None = None) -> Path:
    """Resolve FleetVision project root."""

    if project_root is not None:
        return project_root.resolve()

    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "PROJECT_CONTEXT_BRIEF.md").exists() and (candidate / "src").exists():
            return candidate
    return current


def resolve_path(project_root: Path, value: str | Path | None, default: Path) -> Path:
    """Resolve a project-relative path."""

    raw = Path(value) if value is not None else default
    return raw if raw.is_absolute() else project_root / raw


def _nested(data: dict[str, Any], key: str, default: Any) -> Any:
    cursor: Any = data
    for part in key.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            return default
        cursor = cursor[part]
    return cursor


def load_config(config_path: Path, project_root: Path) -> ExternalAssetScoutConfig:
    """Load and resolve external asset scout config."""

    data: dict[str, Any] = {}
    if config_path.exists():
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    roots = data.get("external_data_roots", {}) or {}
    future_roots = data.get("future_yolo_dataset_roots", {}) or {}
    allowed_raw = data.get("allowed_values", {}) or {}

    allowed_values = {
        key: set(values)
        for key, values in DEFAULT_ALLOWED_VALUES.items()
    }
    for key, values in allowed_raw.items():
        if key in allowed_values:
            allowed_values[key] = {str(value).strip().lower() for value in values}

    provider_subdirs = [str(value).strip().lower() for value in data.get("provider_subdirs", ["kaggle", "roboflow", "huggingface"])]

    return ExternalAssetScoutConfig(
        registry_csv=resolve_path(project_root, data.get("registry_csv"), DEFAULT_REGISTRY_CSV),
        summary_csv=resolve_path(project_root, data.get("summary_csv"), DEFAULT_SUMMARY_CSV),
        external_raw_root=resolve_path(project_root, roots.get("external_raw_root"), Path("dataset/01_raw/99_external")),
        external_yolo_labels_raw_root=resolve_path(
            project_root,
            roots.get("external_yolo_labels_raw_root"),
            Path("dataset/04_annotations/external_yolo_labels_raw"),
        ),
        external_assets_metadata_root=resolve_path(
            project_root,
            roots.get("external_assets_metadata_root"),
            Path("outputs/metadata/external_assets"),
        ),
        provider_subdirs=provider_subdirs,
        future_yolo_dataset_roots={
            name: resolve_path(project_root, value, Path(value))
            for name, value in future_roots.items()
        },
        allowed_values=allowed_values,
        boolean_columns=list(data.get("boolean_columns", DEFAULT_BOOLEAN_COLUMNS)),
    )


def build_empty_registry() -> pd.DataFrame:
    """Return an empty external asset registry template."""

    return pd.DataFrame(columns=REGISTRY_COLUMNS)


def initialize_external_dirs(config: ExternalAssetScoutConfig) -> list[Path]:
    """Create external dataset directory structure without downloading data."""

    dirs: list[Path] = [
        config.registry_csv.parent,
        config.summary_csv.parent,
        config.external_raw_root,
        config.external_yolo_labels_raw_root,
        config.external_assets_metadata_root,
    ]

    for provider in config.provider_subdirs:
        dirs.extend([
            config.external_raw_root / provider,
            config.external_yolo_labels_raw_root / provider,
            config.external_assets_metadata_root / provider,
        ])

    dirs.extend(config.future_yolo_dataset_roots.values())

    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)

    return dirs


def write_registry_template(registry_csv: Path, *, overwrite: bool = False) -> bool:
    """Write an empty registry CSV template. Return True when written."""

    if registry_csv.exists() and not overwrite:
        return False

    registry_csv.parent.mkdir(parents=True, exist_ok=True)
    build_empty_registry().to_csv(registry_csv, index=False, encoding="utf-8-sig")
    return True


def normalize_value(value: Any) -> str:
    """Normalize CSV scalar values for validation."""

    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def validate_registry(registry_csv: Path, config: ExternalAssetScoutConfig) -> list[str]:
    """Validate external asset registry structure and simple value constraints."""

    errors: list[str] = []
    if not registry_csv.exists():
        return [f"registry does not exist: {registry_csv}"]

    df = pd.read_csv(registry_csv, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    missing = [column for column in REGISTRY_COLUMNS if column not in df.columns]
    if missing:
        errors.append("missing columns: " + ", ".join(missing))
        return errors

    for column, allowed in config.allowed_values.items():
        if column not in df.columns:
            continue
        invalid = sorted({normalize_value(value) for value in df[column] if normalize_value(value) and normalize_value(value) not in allowed})
        if invalid:
            errors.append(f"invalid {column} values: {invalid}")

    for column in config.boolean_columns:
        if column not in df.columns:
            continue
        invalid = sorted({normalize_value(value) for value in df[column] if normalize_value(value) not in TRUE_FALSE_UNKNOWN})
        if invalid:
            errors.append(f"invalid {column} boolean values: {invalid}")

    if "asset_id" in df.columns:
        duplicated = int(df["asset_id"].astype(str).str.strip().replace("", pd.NA).duplicated().sum())
        if duplicated:
            errors.append(f"duplicated non-empty asset_id values: {duplicated}")

    return errors


def write_summary(config: ExternalAssetScoutConfig, *, dirs_created: int, registry_written: bool, validation_errors: list[str]) -> None:
    """Write one-row external asset scout summary."""

    config.summary_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {
            "registry_csv": str(config.registry_csv),
            "dirs_created_or_confirmed": dirs_created,
            "registry_template_written": registry_written,
            "validation_error_count": len(validation_errors),
            "validation_errors": " | ".join(validation_errors[:20]),
        }
    ]).to_csv(config.summary_csv, index=False, encoding="utf-8-sig")


def run(config: ExternalAssetScoutConfig, *, overwrite: bool, validate: bool) -> dict[str, Any]:
    """Initialize external asset structure and optionally validate registry."""

    dirs = initialize_external_dirs(config)
    registry_written = write_registry_template(config.registry_csv, overwrite=overwrite)
    validation_errors = validate_registry(config.registry_csv, config) if validate else []
    write_summary(config, dirs_created=len(dirs), registry_written=registry_written, validation_errors=validation_errors)
    return {
        "dirs_created_or_confirmed": len(dirs),
        "registry_written": registry_written,
        "validation_errors": validation_errors,
        "registry_csv": config.registry_csv,
        "summary_csv": config.summary_csv,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize and validate FleetVision external asset registry.")
    parser.add_argument("--project-root", type=Path, default=None, help="FleetVision project root. Default: auto-detect.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to external asset scout config YAML.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite registry CSV template if it already exists.")
    parser.add_argument("--validate", action="store_true", help="Validate registry after initialization.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project_root = resolve_project_root(args.project_root)
    config_path = resolve_path(project_root, args.config, DEFAULT_CONFIG_PATH)
    config = load_config(config_path, project_root)

    try:
        result = run(config, overwrite=args.overwrite, validate=args.validate)
    except Exception as exc:  # noqa: BLE001 - concise CLI error.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("FleetVision external asset scout summary")
    print(f"registry_csv: {result['registry_csv']}")
    print(f"summary_csv: {result['summary_csv']}")
    print(f"dirs_created_or_confirmed: {result['dirs_created_or_confirmed']}")
    print(f"registry_written: {result['registry_written']}")
    print(f"validation_error_count: {len(result['validation_errors'])}")
    if result["validation_errors"]:
        for error in result["validation_errors"][:10]:
            print(f"validation_error: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
