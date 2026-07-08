"""Merge Colab auto-review suggestions into a review-label CSV copy.

Phase 03.5 is an assistive pre-labeling step. It never marks rows as
`reviewed` and should not replace human review. The Colab notebook produces
`auto_review_suggestions.csv`; this module merges high-confidence suggestions
into a separate CSV so the user can review/edit it before Phase 03 validation.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

DEFAULT_CONFIG_PATH = Path("configs/data/auto_review_prelab_config.yaml")
DEFAULT_INPUT_LABELS_CSV = Path("dataset/00_catalog/image_review_labels.csv")
DEFAULT_SUGGESTIONS_CSV = Path("outputs/metadata/auto_review_suggestions.csv")
DEFAULT_MERGED_OUTPUT_CSV = Path("dataset/00_catalog/image_review_labels_auto_suggested.csv")
DEFAULT_SUMMARY_OUTPUT = Path("outputs/metadata/auto_review_merge_summary.csv")

REVIEW_COLUMNS = [
    "photo_type_review",
    "angle_review",
    "is_exterior_review",
    "has_visible_damage_review",
    "severity_review",
    "review_status",
    "reviewer",
    "review_notes",
]

SUGGESTION_COLUMNS = [
    "image_id",
    "suggested_photo_type_review",
    "photo_type_confidence",
    "suggested_angle_review",
    "angle_confidence",
    "suggested_has_visible_damage_review",
    "damage_confidence",
    "suggested_severity_review",
    "severity_confidence",
    "auto_review_notes",
]

SUMMARY_COLUMNS = [
    "input_rows",
    "suggestion_rows",
    "matched_rows",
    "photo_type_filled_rows",
    "angle_filled_rows",
    "damage_filled_rows",
    "severity_filled_rows",
    "review_status_set_pending_rows",
    "reviewer_filled_rows",
]

DEFAULT_ALLOWED_VALUES = {
    "photo_type_review": {"exterior", "interior", "low_quality", "irrelevant", "unknown"},
    "angle_review": {
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
    "severity_review": {"none", "minor", "moderate", "severe", "unknown"},
}

TRUE_VALUES = {"1", "true", "yes", "y"}
FALSE_VALUES = {"0", "false", "no", "n"}


@dataclass(frozen=True)
class AutoReviewPrelabelConfig:
    """Resolved Phase 03.5 merge configuration."""

    input_labels_csv: Path
    suggestions_csv: Path
    merged_labels_csv: Path
    summary_csv: Path
    fill_empty_only: bool
    keep_review_status_pending: bool
    pending_status_value: str
    auto_reviewer_value: str
    append_notes: bool
    confidence_thresholds: dict[str, float]
    allowed_values: dict[str, set[str]]


def resolve_project_root(project_root: Path | None = None) -> Path:
    """Resolve the FleetVision project root."""

    if project_root is not None:
        return project_root.resolve()

    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "PROJECT_CONTEXT_BRIEF.md").exists() and (candidate / "src").exists():
            return candidate
    return current


def resolve_path(project_root: Path, value: str | Path | None, default: Path) -> Path:
    """Resolve a possibly relative path against the project root."""

    raw = Path(value) if value is not None else default
    return raw if raw.is_absolute() else project_root / raw


def load_config(config_path: Path, project_root: Path) -> AutoReviewPrelabelConfig:
    """Load Phase 03.5 configuration from YAML."""

    if config_path.exists():
        data: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    else:
        data = {}

    outputs = data.get("outputs", {}) or {}
    settings = data.get("settings", {}) or {}
    thresholds = data.get("confidence_thresholds", {}) or {}
    allowed = data.get("allowed_values", {}) or {}

    allowed_values = {
        key: {normalize_text(value) for value in values}
        for key, values in DEFAULT_ALLOWED_VALUES.items()
    }
    for key, values in allowed.items():
        if key in allowed_values:
            allowed_values[key] = {normalize_text(value) for value in values}

    confidence_thresholds = {
        "photo_type_review": float(thresholds.get("photo_type_review", 0.45)),
        "angle_review": float(thresholds.get("angle_review", 0.35)),
        "has_visible_damage_review": float(thresholds.get("has_visible_damage_review", 0.55)),
        "severity_review": float(thresholds.get("severity_review", 0.40)),
    }

    return AutoReviewPrelabelConfig(
        input_labels_csv=resolve_path(project_root, data.get("input_labels_csv"), DEFAULT_INPUT_LABELS_CSV),
        suggestions_csv=resolve_path(project_root, data.get("suggestions_csv"), DEFAULT_SUGGESTIONS_CSV),
        merged_labels_csv=resolve_path(project_root, outputs.get("merged_labels_csv"), DEFAULT_MERGED_OUTPUT_CSV),
        summary_csv=resolve_path(project_root, outputs.get("summary_csv"), DEFAULT_SUMMARY_OUTPUT),
        fill_empty_only=bool(settings.get("fill_empty_only", True)),
        keep_review_status_pending=bool(settings.get("keep_review_status_pending", True)),
        pending_status_value=str(settings.get("pending_status_value", "pending")),
        auto_reviewer_value=str(settings.get("auto_reviewer_value", "auto_clip_suggestion")),
        append_notes=bool(settings.get("append_notes", True)),
        confidence_thresholds=confidence_thresholds,
        allowed_values=allowed_values,
    )


def normalize_text(value: Any) -> str:
    """Normalize scalar text used in CSV values."""

    if pd.isna(value):
        return ""
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def is_blank(value: Any) -> bool:
    """Return True when a CSV cell is effectively blank."""

    return normalize_text(value) == ""


def parse_bool01(value: Any) -> str:
    """Parse a loose bool-like value into '1', '0', or blank."""

    normalized = normalize_text(value)
    if normalized in TRUE_VALUES:
        return "1"
    if normalized in FALSE_VALUES:
        return "0"
    return ""


def confidence_at_least(value: Any, threshold: float) -> bool:
    """Safely compare a confidence value with a threshold."""

    try:
        return float(value) >= threshold
    except (TypeError, ValueError):
        return False


def read_csv_utf8(path: Path) -> pd.DataFrame:
    """Read a CSV using UTF-8 and keep empty strings stable."""

    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def validate_review_labels_columns(df: pd.DataFrame) -> None:
    """Validate the review-label CSV has columns required for merging."""

    required = ["image_id", *REVIEW_COLUMNS]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError("review labels CSV missing required column(s): " + ", ".join(missing))


def validate_suggestion_columns(df: pd.DataFrame) -> None:
    """Validate the Colab suggestion CSV schema."""

    missing = [column for column in SUGGESTION_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError("suggestions CSV missing required column(s): " + ", ".join(missing))


def normalize_suggestions(suggestions: pd.DataFrame, config: AutoReviewPrelabelConfig) -> pd.DataFrame:
    """Normalize suggestion values and blank out invalid choices."""

    result = suggestions.copy()

    choice_map = {
        "suggested_photo_type_review": "photo_type_review",
        "suggested_angle_review": "angle_review",
        "suggested_severity_review": "severity_review",
    }
    for source_column, target_column in choice_map.items():
        result[source_column] = result[source_column].map(normalize_text)
        allowed = config.allowed_values[target_column]
        result.loc[~result[source_column].isin(allowed), source_column] = ""

    result["suggested_has_visible_damage_review"] = result["suggested_has_visible_damage_review"].map(parse_bool01)
    return result


def should_fill(current_value: Any, config: AutoReviewPrelabelConfig) -> bool:
    """Return True if a current review value may be filled by automation."""

    return (not config.fill_empty_only) or is_blank(current_value)


def append_note(existing: Any, note: str) -> str:
    """Append an auto-review note without destroying existing human notes."""

    existing_text = "" if pd.isna(existing) else str(existing).strip()
    if not note:
        return existing_text
    if not existing_text:
        return note
    if note in existing_text:
        return existing_text
    return f"{existing_text} | {note}"


def merge_auto_suggestions(
    review_labels: pd.DataFrame,
    suggestions: pd.DataFrame,
    config: AutoReviewPrelabelConfig,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Merge high-confidence auto suggestions into a review-label CSV copy."""

    validate_review_labels_columns(review_labels)
    validate_suggestion_columns(suggestions)

    suggestions_normalized = normalize_suggestions(suggestions, config)
    suggestion_by_image_id = {
        str(row["image_id"]): row for _, row in suggestions_normalized.drop_duplicates("image_id", keep="last").iterrows()
    }

    result = review_labels.copy()
    counters = {
        "input_rows": int(len(review_labels)),
        "suggestion_rows": int(len(suggestions)),
        "matched_rows": 0,
        "photo_type_filled_rows": 0,
        "angle_filled_rows": 0,
        "damage_filled_rows": 0,
        "severity_filled_rows": 0,
        "review_status_set_pending_rows": 0,
        "reviewer_filled_rows": 0,
    }

    for idx, row in result.iterrows():
        image_id = str(row.get("image_id", ""))
        suggestion = suggestion_by_image_id.get(image_id)
        if suggestion is None:
            continue

        counters["matched_rows"] += 1
        note_parts: list[str] = []

        photo_type = suggestion["suggested_photo_type_review"]
        if photo_type and should_fill(row["photo_type_review"], config) and confidence_at_least(
            suggestion["photo_type_confidence"], config.confidence_thresholds["photo_type_review"]
        ):
            result.at[idx, "photo_type_review"] = photo_type
            counters["photo_type_filled_rows"] += 1
            note_parts.append(f"auto_photo_type={photo_type}:{float(suggestion['photo_type_confidence']):.3f}")

        angle = suggestion["suggested_angle_review"]
        if angle and should_fill(row["angle_review"], config) and confidence_at_least(
            suggestion["angle_confidence"], config.confidence_thresholds["angle_review"]
        ):
            result.at[idx, "angle_review"] = angle
            counters["angle_filled_rows"] += 1
            note_parts.append(f"auto_angle={angle}:{float(suggestion['angle_confidence']):.3f}")

        damage = suggestion["suggested_has_visible_damage_review"]
        if damage and should_fill(row["has_visible_damage_review"], config) and confidence_at_least(
            suggestion["damage_confidence"], config.confidence_thresholds["has_visible_damage_review"]
        ):
            result.at[idx, "has_visible_damage_review"] = damage
            counters["damage_filled_rows"] += 1
            note_parts.append(f"auto_damage={damage}:{float(suggestion['damage_confidence']):.3f}")

        severity = suggestion["suggested_severity_review"]
        if severity and should_fill(row["severity_review"], config) and confidence_at_least(
            suggestion["severity_confidence"], config.confidence_thresholds["severity_review"]
        ):
            result.at[idx, "severity_review"] = severity
            counters["severity_filled_rows"] += 1
            note_parts.append(f"auto_severity={severity}:{float(suggestion['severity_confidence']):.3f}")

        if is_blank(result.at[idx, "is_exterior_review"]):
            result.at[idx, "is_exterior_review"] = "1" if normalize_text(result.at[idx, "photo_type_review"]) == "exterior" else "0"

        if is_blank(result.at[idx, "has_visible_damage_review"]):
            severity_value = normalize_text(result.at[idx, "severity_review"])
            if severity_value == "none":
                result.at[idx, "has_visible_damage_review"] = "0"
            elif severity_value in {"minor", "moderate", "severe"}:
                result.at[idx, "has_visible_damage_review"] = "1"

        if config.keep_review_status_pending and is_blank(result.at[idx, "review_status"]):
            result.at[idx, "review_status"] = config.pending_status_value
            counters["review_status_set_pending_rows"] += 1

        if is_blank(result.at[idx, "reviewer"]):
            result.at[idx, "reviewer"] = config.auto_reviewer_value
            counters["reviewer_filled_rows"] += 1

        notebook_note = str(suggestion.get("auto_review_notes", "")).strip()
        if notebook_note:
            note_parts.append(notebook_note)
        if config.append_notes and note_parts:
            result.at[idx, "review_notes"] = append_note(result.at[idx, "review_notes"], "; ".join(note_parts))

    return result, counters


def write_summary(path: Path, counters: dict[str, int]) -> None:
    """Write one-row merge summary CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{column: counters.get(column, 0) for column in SUMMARY_COLUMNS}]).to_csv(
        path, index=False, encoding="utf-8-sig"
    )


def run_merge(config: AutoReviewPrelabelConfig) -> dict[str, int]:
    """Run the Phase 03.5 suggestion merge."""

    review_labels = read_csv_utf8(config.input_labels_csv)
    suggestions = read_csv_utf8(config.suggestions_csv)
    merged, counters = merge_auto_suggestions(review_labels, suggestions, config)

    config.merged_labels_csv.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(config.merged_labels_csv, index=False, encoding="utf-8-sig")
    write_summary(config.summary_csv, counters)
    return counters


def build_parser() -> argparse.ArgumentParser:
    """Build the Phase 03.5 CLI parser."""

    parser = argparse.ArgumentParser(description="Merge Colab auto-review suggestions into a review-label CSV copy.")
    parser.add_argument("--project-root", type=Path, default=None, help="FleetVision project root. Default: auto-detect.")
    parser.add_argument("--config", type=Path, default=None, help="Path to auto review prelabel config YAML.")
    parser.add_argument("--input", type=Path, default=None, help="Override review labels input CSV.")
    parser.add_argument("--suggestions", type=Path, default=None, help="Override auto review suggestions CSV.")
    parser.add_argument("--output", type=Path, default=None, help="Override merged labels output CSV.")
    parser.add_argument("--summary-output", type=Path, default=None, help="Override summary CSV output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)

    project_root = resolve_project_root(args.project_root)
    config_path = resolve_path(project_root, args.config, DEFAULT_CONFIG_PATH)
    config = load_config(config_path, project_root)

    if args.input is not None:
        config = AutoReviewPrelabelConfig(
            **{**config.__dict__, "input_labels_csv": resolve_path(project_root, args.input, DEFAULT_INPUT_LABELS_CSV)}
        )
    if args.suggestions is not None:
        config = AutoReviewPrelabelConfig(
            **{**config.__dict__, "suggestions_csv": resolve_path(project_root, args.suggestions, DEFAULT_SUGGESTIONS_CSV)}
        )
    if args.output is not None:
        config = AutoReviewPrelabelConfig(
            **{**config.__dict__, "merged_labels_csv": resolve_path(project_root, args.output, DEFAULT_MERGED_OUTPUT_CSV)}
        )
    if args.summary_output is not None:
        config = AutoReviewPrelabelConfig(
            **{**config.__dict__, "summary_csv": resolve_path(project_root, args.summary_output, DEFAULT_SUMMARY_OUTPUT)}
        )

    try:
        counters = run_merge(config)
    except Exception as exc:  # noqa: BLE001 - CLI should show concise errors.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("FleetVision auto review suggestion merge summary")
    print(f"merged_labels_csv: {config.merged_labels_csv}")
    print(f"summary_csv: {config.summary_csv}")
    for column in SUMMARY_COLUMNS:
        print(f"{column}: {counters.get(column, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
