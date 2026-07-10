"""Merge two Pilot review collaboration workbooks into a canonical result CSV."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from fleetvision.data.build_pilot_review_packages import ASSIGNMENT_COLUMNS, ReviewerConfig, find_project_root, resolve_path
from fleetvision.data.build_pilot_review_worklist import HUMAN_COLUMNS, WORKLIST_COLUMNS
from fleetvision.data.export_pilot_review_excel import read_review_workbook
from fleetvision.data.validate_pilot_human_review import (
    PilotHumanReviewValidationConfig,
    validate_pilot_human_review,
    write_errors_csv,
)


DEFAULT_CONFIG_PATH = Path("configs/data/pilot_review_collaboration_config.yaml")
DEFAULT_SOURCE_WORKLIST_CSV = Path("dataset/00_catalog/image_review_labels_pilot500_human_review_worklist.csv")
DEFAULT_ASSIGNMENT_CSV = Path("outputs/manual_review/collaboration/pilot500_review_assignments.csv")
DEFAULT_VINCENT_WORKBOOK = Path("outputs/manual_review/collaboration/packages/vincent/review_workbook.xlsx")
DEFAULT_SISTER_WORKBOOK = Path("outputs/manual_review/collaboration/packages/sister/review_workbook.xlsx")
DEFAULT_OUTPUT_CSV = Path("outputs/manual_review/collaboration/pilot500_human_review_results_collaboration.csv")
DEFAULT_SUMMARY_CSV = Path("outputs/metadata/pilot500_human_review_collaboration_summary.csv")
DEFAULT_ERRORS_CSV = Path("outputs/metadata/pilot500_human_review_collaboration_errors.csv")
SUMMARY_COLUMNS = [
    "source_rows",
    "assigned_rows",
    "vincent_rows",
    "sister_rows",
    "merged_rows",
    "pending_rows",
    "reviewed_rows",
    "needs_followup_rows",
    "skipped_rows",
    "validation_error_count",
]


@dataclass(frozen=True)
class PilotReviewCollaborationMergeConfig:
    """Resolved settings for merging collaboration workbooks."""

    source_worklist_csv: Path
    assignment_csv: Path
    vincent_workbook: Path
    sister_workbook: Path
    output_csv: Path
    summary_csv: Path
    errors_csv: Path
    reviewers: tuple[ReviewerConfig, ...]
    expected_rows: int = 500


@dataclass(frozen=True)
class MergeResult:
    """Collaboration merge result."""

    is_valid: bool
    summary: dict[str, int]
    errors: list[dict[str, Any]]
    merged_dataframe: pd.DataFrame


def load_config(config_path: Path, project_root: Path) -> PilotReviewCollaborationMergeConfig:
    """Load collaboration merge YAML config."""
    if not config_path.exists():
        raise FileNotFoundError(f"collaboration config not found: {config_path}")
    raw_config: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    reviewers = tuple(
        ReviewerConfig(str(item["reviewer_id"]), str(item["reviewer_name"]))
        for item in raw_config.get("reviewers", [])
    )
    return PilotReviewCollaborationMergeConfig(
        source_worklist_csv=resolve_path(raw_config.get("source_worklist_csv"), project_root, DEFAULT_SOURCE_WORKLIST_CSV),
        assignment_csv=resolve_path(raw_config.get("assignment_csv"), project_root, DEFAULT_ASSIGNMENT_CSV),
        vincent_workbook=resolve_path(raw_config.get("vincent_workbook"), project_root, DEFAULT_VINCENT_WORKBOOK),
        sister_workbook=resolve_path(raw_config.get("sister_workbook"), project_root, DEFAULT_SISTER_WORKBOOK),
        output_csv=resolve_path(raw_config.get("output_csv"), project_root, DEFAULT_OUTPUT_CSV),
        summary_csv=resolve_path(raw_config.get("summary_csv"), project_root, DEFAULT_SUMMARY_CSV),
        errors_csv=resolve_path(raw_config.get("errors_csv"), project_root, DEFAULT_ERRORS_CSV),
        reviewers=reviewers,
        expected_rows=int(raw_config.get("expected_rows", 500)),
    )


def read_csv(path: Path, source_name: str) -> pd.DataFrame:
    """Read a CSV with UTF-8 BOM support."""
    if not path.exists():
        raise FileNotFoundError(f"{source_name} not found: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def merge_pilot_review_packages(config: PilotReviewCollaborationMergeConfig) -> MergeResult:
    """Merge reviewer workbooks into canonical order and validate result."""
    source = read_csv(config.source_worklist_csv, "source worklist CSV")
    assignments = read_csv(config.assignment_csv, "assignment CSV")
    _validate_source_and_assignments(source, assignments, config)
    workbook_frames = []
    for reviewer in config.reviewers:
        workbook_path = _workbook_path_for_reviewer(config, reviewer.reviewer_id)
        workbook = read_review_workbook(workbook_path)
        workbook_frames.append(_validate_reviewer_workbook(workbook, source, assignments, reviewer))
    combined = pd.concat(workbook_frames, ignore_index=True)
    if combined["review_id"].duplicated().any():
        raise ValueError("reviewer workbooks contain overlapping review_id values")
    merged = _merge_human_fields(source, combined)
    validation_config = PilotHumanReviewValidationConfig(
        input_csv=config.output_csv,
        summary_csv=config.summary_csv,
        errors_csv=config.errors_csv,
        expected_rows=config.expected_rows,
    )
    validation = validate_pilot_human_review(merged, validation_config)
    summary = _build_summary(source, assignments, merged, validation, config.reviewers)
    return MergeResult(validation.is_valid, summary, validation.errors, merged)


def write_merge_outputs(result: MergeResult, config: PilotReviewCollaborationMergeConfig) -> None:
    """Write summary/errors and atomically write result CSV only when valid."""
    write_summary_csv(result.summary, config.summary_csv)
    write_errors_csv(result.errors, config.errors_csv)
    if result.is_valid:
        _atomic_write_csv(result.merged_dataframe, config.output_csv)


def write_summary_csv(summary: dict[str, int], summary_csv: Path) -> None:
    """Write one-row merge summary."""
    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{column: summary.get(column, 0) for column in SUMMARY_COLUMNS}]).to_csv(
        summary_csv, index=False, encoding="utf-8-sig"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description="Merge FleetVision Pilot review collaboration workbooks.")
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--source-worklist-csv", type=Path, default=None)
    parser.add_argument("--assignment-csv", type=Path, default=None)
    parser.add_argument("--vincent-workbook", type=Path, default=None)
    parser.add_argument("--sister-workbook", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--summary-csv", type=Path, default=None)
    parser.add_argument("--errors-csv", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    project_root = find_project_root(args.project_root)
    try:
        config = _apply_overrides(load_config(resolve_path(args.config, project_root, DEFAULT_CONFIG_PATH), project_root), args, project_root)
        result = merge_pilot_review_packages(config)
        write_merge_outputs(result, config)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("FleetVision Pilot review collaboration merge summary")
    print(f"output_csv: {config.output_csv}")
    print(f"summary_csv: {config.summary_csv}")
    print(f"errors_csv: {config.errors_csv}")
    for column in SUMMARY_COLUMNS:
        print(f"{column}: {result.summary[column]}")
    return 0 if result.is_valid else 1


def _apply_overrides(config: PilotReviewCollaborationMergeConfig, args: argparse.Namespace, project_root: Path) -> PilotReviewCollaborationMergeConfig:
    return PilotReviewCollaborationMergeConfig(
        source_worklist_csv=resolve_path(args.source_worklist_csv, project_root, config.source_worklist_csv),
        assignment_csv=resolve_path(args.assignment_csv, project_root, config.assignment_csv),
        vincent_workbook=resolve_path(args.vincent_workbook, project_root, config.vincent_workbook),
        sister_workbook=resolve_path(args.sister_workbook, project_root, config.sister_workbook),
        output_csv=resolve_path(args.output_csv, project_root, config.output_csv),
        summary_csv=resolve_path(args.summary_csv, project_root, config.summary_csv),
        errors_csv=resolve_path(args.errors_csv, project_root, config.errors_csv),
        reviewers=config.reviewers,
        expected_rows=config.expected_rows,
    )


def _validate_source_and_assignments(source: pd.DataFrame, assignments: pd.DataFrame, config: PilotReviewCollaborationMergeConfig) -> None:
    missing_source = [column for column in WORKLIST_COLUMNS if column not in source.columns]
    if missing_source:
        raise ValueError("source worklist missing required column(s): " + ", ".join(missing_source))
    missing_assignments = [column for column in ASSIGNMENT_COLUMNS if column not in assignments.columns]
    if missing_assignments:
        raise ValueError("assignment CSV missing required column(s): " + ", ".join(missing_assignments))
    if len(source) != config.expected_rows or len(assignments) != config.expected_rows:
        raise ValueError("source and assignment row counts must match expected_rows")
    if assignments["review_id"].duplicated().any():
        raise ValueError("assignment CSV contains duplicate review_id")
    source_ids = set(source["review_id"])
    assignment_ids = set(assignments["review_id"])
    if source_ids != assignment_ids:
        raise ValueError("assignment CSV review_id values do not match source worklist")


def _validate_reviewer_workbook(workbook: pd.DataFrame, source: pd.DataFrame, assignments: pd.DataFrame, reviewer: ReviewerConfig) -> pd.DataFrame:
    assigned = assignments.loc[assignments["reviewer_id"] == reviewer.reviewer_id].copy()
    assigned_ids = set(assigned["review_id"])
    workbook_ids = set(workbook.get("review_id", pd.Series(dtype=str)).astype(str))
    if workbook["review_id"].astype(str).str.strip().eq("").any():
        raise ValueError(f"{reviewer.reviewer_id} workbook contains blank review_id")
    if workbook["review_id"].duplicated().any():
        raise ValueError(f"{reviewer.reviewer_id} workbook contains duplicate review_id")
    unknown = sorted(workbook_ids - assigned_ids)
    missing = sorted(assigned_ids - workbook_ids)
    if unknown:
        raise ValueError(f"{reviewer.reviewer_id} workbook contains unassigned review_id: {', '.join(unknown[:10])}")
    if missing:
        raise ValueError(f"{reviewer.reviewer_id} workbook missing review_id: {', '.join(missing[:10])}")
    workbook_by_id = workbook.set_index("review_id", drop=False)
    source_by_id = source.set_index("review_id", drop=False)
    assignment_by_id = assigned.set_index("review_id", drop=False)
    for review_id in assigned["review_id"].tolist():
        if assignment_by_id.at[review_id, "reviewer_name"] != reviewer.reviewer_name:
            raise ValueError(f"assignment reviewer mismatch for review_id {review_id}")
        for column in ["image_id", "original_path"]:
            if str(workbook_by_id.at[review_id, column]) != str(source_by_id.at[review_id, column]):
                raise ValueError(f"{reviewer.reviewer_id} workbook {column} mismatch for review_id {review_id}")
        for column in HUMAN_COLUMNS:
            value = workbook_by_id.at[review_id, column]
            if isinstance(value, str) and value.startswith("="):
                raise ValueError(f"{reviewer.reviewer_id} workbook human field contains formula for review_id {review_id}: {column}")
        status = str(workbook_by_id.at[review_id, "human_review_status"]).strip().lower()
        human_reviewer = str(workbook_by_id.at[review_id, "human_reviewer"]).strip()
        if status in {"reviewed", "needs_followup", "skipped"} and human_reviewer != reviewer.reviewer_name:
            raise ValueError(f"completed row reviewer mismatch for review_id {review_id}")
    return workbook


def _merge_human_fields(source: pd.DataFrame, combined: pd.DataFrame) -> pd.DataFrame:
    workbook_by_id = combined.set_index("review_id", drop=False)
    merged = source.copy(deep=True)
    for column in HUMAN_COLUMNS:
        merged[column] = merged["review_id"].map(workbook_by_id[column]).fillna("").astype(str)
    merged = merged.loc[:, WORKLIST_COLUMNS].astype(str)
    if any(column.endswith(("_x", "_y")) for column in merged.columns):
        raise ValueError("merge produced unexpected suffix columns")
    return merged


def _build_summary(source, assignments, merged, validation, reviewers) -> dict[str, int]:
    reviewer_counts = assignments["reviewer_id"].value_counts().to_dict()
    return {
        "source_rows": int(len(source)),
        "assigned_rows": int(len(assignments)),
        "vincent_rows": int(reviewer_counts.get("vincent", 0)),
        "sister_rows": int(reviewer_counts.get("sister", 0)),
        "merged_rows": int(len(merged)) if validation.is_valid else 0,
        "pending_rows": int(validation.pending_rows),
        "reviewed_rows": int(validation.reviewed_rows),
        "needs_followup_rows": int(validation.needs_followup_rows),
        "skipped_rows": int(validation.skipped_rows),
        "validation_error_count": int(validation.error_count),
    }


def _workbook_path_for_reviewer(config: PilotReviewCollaborationMergeConfig, reviewer_id: str) -> Path:
    if reviewer_id == "vincent":
        return config.vincent_workbook
    if reviewer_id == "sister":
        return config.sister_workbook
    raise ValueError(f"unsupported reviewer_id: {reviewer_id}")


def _atomic_write_csv(dataframe: pd.DataFrame, output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8-sig", suffix=".csv", delete=False, dir=output_csv.parent) as temp_file:
        temp_path = Path(temp_file.name)
        dataframe.to_csv(temp_file, index=False)
    os.replace(temp_path, output_csv)


if __name__ == "__main__":
    raise SystemExit(main())
