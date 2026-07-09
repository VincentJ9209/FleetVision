"""Build a 500-row pilot human review worklist from auto-review suggestions."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


DEFAULT_CONFIG_PATH = Path("configs/data/pilot_review_worklist_config.yaml")
DEFAULT_PILOT_MERGE_CSV = Path("dataset/00_catalog/image_review_labels_auto_suggested_pilot500_v2.csv")
DEFAULT_SUGGESTIONS_CSV = Path("outputs/metadata/auto_review_suggestions_v2.csv")
DEFAULT_WORKLIST_CSV = Path("dataset/00_catalog/image_review_labels_pilot500_human_review_worklist.csv")
DEFAULT_SUMMARY_CSV = Path("outputs/metadata/pilot500_human_review_worklist_summary.csv")

READONLY_COLUMNS = [
    "review_id",
    "image_id",
    "source_bucket",
    "original_path",
    "filename",
]

SUGGESTION_COLUMNS = [
    "image_id",
    "suggested_photo_type_review",
    "photo_type_confidence",
    "suggested_angle_review",
    "angle_confidence",
    "auto_review_notes",
]

SEED_SOURCE_COLUMNS = [
    "photo_type_review",
    "angle_review",
    "is_exterior_review",
    "has_visible_damage_review",
    "severity_review",
    "review_status",
    "reviewer",
    "review_notes",
]

SEED_COLUMNS = [
    "seed_photo_type_review",
    "seed_angle_review",
    "seed_is_exterior_review",
    "seed_has_visible_damage_review",
    "seed_severity_review",
    "seed_review_status",
    "seed_reviewer",
    "seed_review_notes",
]

HUMAN_COLUMNS = [
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

WORKLIST_COLUMNS = [
    *READONLY_COLUMNS,
    "suggested_photo_type_review",
    "photo_type_confidence",
    "suggested_angle_review",
    "angle_confidence",
    "auto_review_notes",
    *SEED_COLUMNS,
    *HUMAN_COLUMNS,
]

SUMMARY_COLUMNS = [
    "suggestion_rows",
    "unique_suggestion_image_ids",
    "matched_rows",
    "missing_rows",
    "duplicate_suggestion_ids",
    "duplicate_pilot_ids",
    "output_rows",
    "pending_rows",
    "reviewed_rows",
    "reviewed_at_filled_rows",
    "reviewer_filled_rows",
]


@dataclass(frozen=True)
class PilotReviewWorklistConfig:
    """Resolved configuration for the pilot review worklist builder."""

    pilot_merge_csv: Path
    suggestions_csv: Path
    worklist_csv: Path
    summary_csv: Path
    expected_rows: int = 500
    default_review_status: str = "pending"
    prefill_human_fields_from_seed: bool = True
    default_reviewer_from_seed: bool = True


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


def load_config(config_path: Path, project_root: Path) -> PilotReviewWorklistConfig:
    """Load and resolve pilot review worklist YAML configuration."""
    if not config_path.exists():
        raise FileNotFoundError(f"Pilot review worklist config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        raw_config: dict[str, Any] = yaml.safe_load(file) or {}

    return PilotReviewWorklistConfig(
        pilot_merge_csv=resolve_path(raw_config.get("pilot_merge_csv"), project_root, DEFAULT_PILOT_MERGE_CSV),
        suggestions_csv=resolve_path(raw_config.get("suggestions_csv"), project_root, DEFAULT_SUGGESTIONS_CSV),
        worklist_csv=resolve_path(raw_config.get("worklist_csv"), project_root, DEFAULT_WORKLIST_CSV),
        summary_csv=resolve_path(raw_config.get("summary_csv"), project_root, DEFAULT_SUMMARY_CSV),
        expected_rows=int(raw_config.get("expected_rows", 500)),
        default_review_status=str(raw_config.get("default_review_status", "pending")),
        prefill_human_fields_from_seed=bool(raw_config.get("prefill_human_fields_from_seed", True)),
        default_reviewer_from_seed=bool(raw_config.get("default_reviewer_from_seed", True)),
    )


def read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV with UTF-8 BOM support while preserving blank strings."""
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def validate_unique_image_ids(dataframe: pd.DataFrame, source_name: str, expected_rows: int | None = None) -> None:
    """Validate a DataFrame has unique image_id values and optionally an expected unique count."""
    _validate_required_columns(dataframe, ["image_id"], source_name)
    duplicate_count = _duplicate_count(dataframe["image_id"])
    if duplicate_count:
        duplicate_values = _duplicate_values(dataframe["image_id"])
        raise ValueError(
            f"duplicate image_id in {source_name}: {duplicate_count} duplicate row(s); "
            f"examples: {', '.join(duplicate_values[:5])}"
        )

    unique_count = int(dataframe["image_id"].nunique(dropna=False))
    if expected_rows is not None and unique_count != expected_rows:
        raise ValueError(
            f"{source_name} expected {expected_rows} unique image_id value(s), found {unique_count}"
        )


def build_pilot_review_worklist(
    pilot_merge: pd.DataFrame,
    suggestions: pd.DataFrame,
    config: PilotReviewWorklistConfig,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Build the pilot human review worklist without mutating source DataFrames."""
    _validate_required_columns(pilot_merge, [*READONLY_COLUMNS, *SEED_SOURCE_COLUMNS], "pilot_merge_csv")
    _validate_required_columns(suggestions, SUGGESTION_COLUMNS, "suggestions_csv")

    suggestion_rows = int(len(suggestions))
    unique_suggestion_image_ids = int(suggestions["image_id"].nunique(dropna=False))
    duplicate_suggestion_ids = _duplicate_count(suggestions["image_id"])
    duplicate_pilot_ids = _duplicate_count(pilot_merge["image_id"])

    validate_unique_image_ids(suggestions, "suggestions_csv", config.expected_rows)
    validate_unique_image_ids(pilot_merge, "pilot_merge_csv")
    if suggestion_rows != config.expected_rows:
        raise ValueError(
            f"suggestions_csv expected {config.expected_rows} row(s), found {suggestion_rows}"
        )

    suggestions_copy = suggestions.loc[:, SUGGESTION_COLUMNS].copy(deep=True)
    suggestions_copy["_suggestion_order"] = range(len(suggestions_copy))
    pilot_copy = pilot_merge.loc[:, [*READONLY_COLUMNS, *SEED_SOURCE_COLUMNS]].copy(deep=True)

    matched = suggestions_copy.merge(
        pilot_copy,
        on="image_id",
        how="left",
        sort=False,
        validate="one_to_one",
    ).sort_values("_suggestion_order", kind="stable")
    missing_mask = matched["review_id"].isna() | (matched["review_id"].astype(str) == "")
    missing_rows = int(missing_mask.sum())
    if missing_rows:
        missing_ids = matched.loc[missing_mask, "image_id"].astype(str).tolist()
        raise ValueError(
            "missing pilot_merge_csv rows for image_id: " + ", ".join(missing_ids[:10])
        )

    worklist = pd.DataFrame(
        {
            "review_id": matched["review_id"],
            "image_id": matched["image_id"],
            "source_bucket": matched["source_bucket"],
            "original_path": matched["original_path"],
            "filename": matched["filename"],
            "suggested_photo_type_review": matched["suggested_photo_type_review"],
            "photo_type_confidence": matched["photo_type_confidence"],
            "suggested_angle_review": matched["suggested_angle_review"],
            "angle_confidence": matched["angle_confidence"],
            "auto_review_notes": matched["auto_review_notes"],
            "seed_photo_type_review": matched["photo_type_review"],
            "seed_angle_review": matched["angle_review"],
            "seed_is_exterior_review": matched["is_exterior_review"],
            "seed_has_visible_damage_review": matched["has_visible_damage_review"],
            "seed_severity_review": matched["severity_review"],
            "seed_review_status": matched["review_status"],
            "seed_reviewer": matched["reviewer"],
            "seed_review_notes": matched["review_notes"],
        }
    ).fillna("")

    if config.prefill_human_fields_from_seed:
        worklist["human_photo_type_review"] = worklist["seed_photo_type_review"]
        worklist["human_angle_review"] = worklist["seed_angle_review"]
        worklist["human_is_exterior_review"] = worklist["seed_is_exterior_review"]
        worklist["human_has_visible_damage_review"] = worklist["seed_has_visible_damage_review"]
        worklist["human_severity_review"] = worklist["seed_severity_review"]
    else:
        worklist["human_photo_type_review"] = ""
        worklist["human_angle_review"] = ""
        worklist["human_is_exterior_review"] = ""
        worklist["human_has_visible_damage_review"] = ""
        worklist["human_severity_review"] = ""

    worklist["human_review_status"] = config.default_review_status
    worklist["human_reviewer"] = worklist["seed_reviewer"] if config.default_reviewer_from_seed else ""
    worklist["human_reviewed_at"] = ""
    worklist["human_review_notes"] = ""
    worklist = worklist.loc[:, WORKLIST_COLUMNS].astype(str)

    summary = {
        "suggestion_rows": suggestion_rows,
        "unique_suggestion_image_ids": unique_suggestion_image_ids,
        "matched_rows": int(len(worklist)),
        "missing_rows": missing_rows,
        "duplicate_suggestion_ids": duplicate_suggestion_ids,
        "duplicate_pilot_ids": duplicate_pilot_ids,
        "output_rows": int(len(worklist)),
        "pending_rows": int((worklist["human_review_status"] == "pending").sum()),
        "reviewed_rows": int((worklist["human_review_status"] == "reviewed").sum()),
        "reviewed_at_filled_rows": int((worklist["human_reviewed_at"].str.strip() != "").sum()),
        "reviewer_filled_rows": int((worklist["human_reviewer"].str.strip() != "").sum()),
    }
    return worklist, summary


def write_pilot_review_worklist(worklist: pd.DataFrame, output_path: Path) -> None:
    """Write the worklist CSV using UTF-8 BOM for Excel compatibility."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    worklist.to_csv(output_path, index=False, encoding="utf-8-sig")


def write_summary(summary: dict[str, int], output_path: Path) -> None:
    """Write one-row summary CSV using UTF-8 BOM."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{column: summary.get(column, 0) for column in SUMMARY_COLUMNS}]).to_csv(
        output_path, index=False, encoding="utf-8-sig"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description="Build the Pilot 500 human review worklist.")
    parser.add_argument("--project-root", type=Path, default=None, help="FleetVision project root. Default: auto-detect.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to worklist config YAML.")
    parser.add_argument("--pilot-merge", type=Path, default=None, help="Override pilot merged labels CSV.")
    parser.add_argument("--suggestions", type=Path, default=None, help="Override auto review suggestions CSV.")
    parser.add_argument("--output", type=Path, default=None, help="Override worklist output CSV.")
    parser.add_argument("--summary-output", type=Path, default=None, help="Override summary output CSV.")
    return parser.parse_args(argv)


def _apply_overrides(
    config: PilotReviewWorklistConfig,
    args: argparse.Namespace,
    project_root: Path,
) -> PilotReviewWorklistConfig:
    """Apply CLI path overrides to a resolved config."""
    return PilotReviewWorklistConfig(
        pilot_merge_csv=resolve_path(args.pilot_merge, project_root, config.pilot_merge_csv),
        suggestions_csv=resolve_path(args.suggestions, project_root, config.suggestions_csv),
        worklist_csv=resolve_path(args.output, project_root, config.worklist_csv),
        summary_csv=resolve_path(args.summary_output, project_root, config.summary_csv),
        expected_rows=config.expected_rows,
        default_review_status=config.default_review_status,
        prefill_human_fields_from_seed=config.prefill_human_fields_from_seed,
        default_reviewer_from_seed=config.default_reviewer_from_seed,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    project_root = find_project_root(args.project_root)
    config_path = resolve_path(args.config, project_root, DEFAULT_CONFIG_PATH)

    try:
        config = load_config(config_path, project_root)
        config = _apply_overrides(config, args, project_root)
        pilot_merge = read_csv(config.pilot_merge_csv)
        suggestions = read_csv(config.suggestions_csv)
        worklist, summary = build_pilot_review_worklist(pilot_merge, suggestions, config)
        write_pilot_review_worklist(worklist, config.worklist_csv)
        write_summary(summary, config.summary_csv)
    except Exception as exc:  # noqa: BLE001 - CLI should return concise errors.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("FleetVision Pilot 500 human review worklist summary")
    print(f"worklist_csv: {config.worklist_csv}")
    print(f"summary_csv: {config.summary_csv}")
    for column in SUMMARY_COLUMNS:
        print(f"{column}: {summary[column]}")
    return 0


def _validate_required_columns(dataframe: pd.DataFrame, required_columns: list[str], source_name: str) -> None:
    missing = [column for column in required_columns if column not in dataframe.columns]
    if missing:
        raise ValueError(f"{source_name} missing required column(s): " + ", ".join(missing))


def _duplicate_count(series: pd.Series) -> int:
    return int(series.duplicated(keep=False).sum())


def _duplicate_values(series: pd.Series) -> list[str]:
    duplicated = series[series.duplicated(keep=False)].astype(str)
    return sorted(duplicated.unique().tolist())


if __name__ == "__main__":
    raise SystemExit(main())

