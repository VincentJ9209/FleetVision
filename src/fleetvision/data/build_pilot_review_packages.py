"""Build two-reviewer Pilot 500 manual review collaboration packages."""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from fleetvision.data.build_pilot_review_excel import (
    EXCEL_COLUMNS,
    OPEN_IMAGE_COLUMN,
    WORKLIST_SHEET,
    PilotReviewExcelConfig,
    build_pilot_review_excel,
    write_workbook,
)
from fleetvision.data.build_pilot_review_worklist import WORKLIST_COLUMNS


DEFAULT_CONFIG_PATH = Path("configs/data/pilot_review_collaboration_config.yaml")
DEFAULT_SOURCE_WORKLIST_CSV = Path("dataset/00_catalog/image_review_labels_pilot500_human_review_worklist.csv")
DEFAULT_GUIDE_PDF = Path("docs/01_phase_guides/FleetVision_人工審核填寫指南_Excel協作版.pdf")
DEFAULT_OUTPUT_ROOT = Path("outputs/manual_review/collaboration")
ASSIGNMENT_FILENAME = "pilot500_review_assignments.csv"
PACKAGE_GUIDE_FILENAME = "FleetVision_人工審核填寫指南.pdf"
README_FILENAME = "README.txt"
WORKBOOK_FILENAME = "review_workbook.xlsx"
MANIFEST_FILENAME = "assignment_manifest.csv"
ASSIGNMENT_COLUMNS = ["assignment_order", "reviewer_id", "reviewer_name", "review_id", "image_id", "original_path"]
README_TEXT = """FleetVision 人工覆核協作包

請先完整解壓縮整個資料夾或 ZIP。
不要只移動 Excel，否則圖片連結會失效。
只修改 Excel 中的人工欄位 human_*。
完成後請關閉 Excel，再回傳整個資料夾或 ZIP。
"""


@dataclass(frozen=True)
class ReviewerConfig:
    """Reviewer assignment settings."""

    reviewer_id: str
    reviewer_name: str


@dataclass(frozen=True)
class PilotReviewCollaborationConfig:
    """Resolved settings for building collaboration packages."""

    source_worklist_csv: Path
    guide_pdf: Path
    output_root: Path
    project_root: Path
    reviewers: tuple[ReviewerConfig, ...]
    expected_rows: int = 500


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


def load_config(config_path: Path, project_root: Path) -> PilotReviewCollaborationConfig:
    """Load collaboration package YAML config."""
    if not config_path.exists():
        raise FileNotFoundError(f"collaboration config not found: {config_path}")
    raw_config: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    reviewers = tuple(
        ReviewerConfig(str(item["reviewer_id"]), str(item["reviewer_name"]))
        for item in raw_config.get("reviewers", [])
    )
    return PilotReviewCollaborationConfig(
        source_worklist_csv=resolve_path(raw_config.get("source_worklist_csv"), project_root, DEFAULT_SOURCE_WORKLIST_CSV),
        guide_pdf=resolve_path(raw_config.get("guide_pdf"), project_root, DEFAULT_GUIDE_PDF),
        output_root=resolve_path(raw_config.get("output_root"), project_root, DEFAULT_OUTPUT_ROOT),
        project_root=project_root,
        reviewers=reviewers,
        expected_rows=int(raw_config.get("expected_rows", 500)),
    )


def read_worklist_csv(path: Path) -> pd.DataFrame:
    """Read canonical worklist CSV."""
    if not path.exists():
        raise FileNotFoundError(f"source worklist CSV not found: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def build_assignments(worklist: pd.DataFrame, reviewers: tuple[ReviewerConfig, ...], expected_rows: int) -> pd.DataFrame:
    """Build deterministic stable round-robin assignment manifest."""
    _validate_worklist(worklist, expected_rows)
    if len(reviewers) != 2:
        raise ValueError("collaboration packages require exactly two reviewers")
    if expected_rows % len(reviewers) != 0:
        raise ValueError("expected_rows must divide evenly across reviewers")

    rows = []
    for index, row in worklist.reset_index(drop=True).iterrows():
        reviewer = reviewers[index % len(reviewers)]
        rows.append(
            {
                "assignment_order": str(index + 1),
                "reviewer_id": reviewer.reviewer_id,
                "reviewer_name": reviewer.reviewer_name,
                "review_id": row["review_id"],
                "image_id": row["image_id"],
                "original_path": row["original_path"],
            }
        )
    assignments = pd.DataFrame(rows, columns=ASSIGNMENT_COLUMNS)
    expected_per_reviewer = expected_rows // len(reviewers)
    counts = assignments["reviewer_id"].value_counts().to_dict()
    for reviewer in reviewers:
        if counts.get(reviewer.reviewer_id, 0) != expected_per_reviewer:
            raise ValueError(f"reviewer {reviewer.reviewer_id} expected {expected_per_reviewer} assigned row(s)")
    if assignments["review_id"].duplicated().any():
        raise ValueError("assignment contains duplicate review_id")
    return assignments


def build_pilot_review_packages(config: PilotReviewCollaborationConfig) -> pd.DataFrame:
    """Build reviewer folders, package ZIP files, and assignment CSV."""
    worklist = read_worklist_csv(config.source_worklist_csv)
    assignments = build_assignments(worklist, config.reviewers, config.expected_rows)
    _validate_guide_pdf(config.guide_pdf)
    _validate_images(worklist, config.project_root)

    if config.output_root.exists():
        shutil.rmtree(config.output_root)
    packages_root = config.output_root / "packages"
    packages_root.mkdir(parents=True, exist_ok=True)
    assignments.to_csv(config.output_root / ASSIGNMENT_FILENAME, index=False, encoding="utf-8-sig")

    for reviewer in config.reviewers:
        reviewer_assignments = assignments.loc[assignments["reviewer_id"] == reviewer.reviewer_id].copy()
        reviewer_worklist = worklist.loc[worklist["review_id"].isin(reviewer_assignments["review_id"])].copy()
        reviewer_worklist = reviewer_worklist.set_index("review_id").loc[reviewer_assignments["review_id"]].reset_index()
        reviewer_worklist["human_reviewer"] = reviewer.reviewer_name
        reviewer_worklist["human_review_status"] = "pending"
        reviewer_worklist["human_reviewed_at"] = ""
        reviewer_dir = packages_root / reviewer.reviewer_id
        _write_reviewer_package(
            reviewer_dir,
            reviewer,
            reviewer_assignments,
            reviewer_worklist,
            config.guide_pdf,
            config.project_root,
        )
        _zip_directory(reviewer_dir, packages_root / f"{reviewer.reviewer_id}.zip")
    return assignments


def write_assignments(assignments: pd.DataFrame, output_path: Path) -> None:
    """Write assignment manifest CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    assignments.to_csv(output_path, index=False, encoding="utf-8-sig")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description="Build FleetVision Pilot review collaboration packages.")
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--source-worklist-csv", type=Path, default=None)
    parser.add_argument("--guide-pdf", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    project_root = find_project_root(args.project_root)
    try:
        config = _apply_overrides(load_config(resolve_path(args.config, project_root, DEFAULT_CONFIG_PATH), project_root), args, project_root)
        assignments = build_pilot_review_packages(config)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("FleetVision Pilot review collaboration package summary")
    print(f"output_root: {config.output_root}")
    print(f"assigned_rows: {len(assignments)}")
    for reviewer in config.reviewers:
        print(f"{reviewer.reviewer_id}_rows: {int((assignments['reviewer_id'] == reviewer.reviewer_id).sum())}")
    return 0


def _apply_overrides(config: PilotReviewCollaborationConfig, args: argparse.Namespace, project_root: Path) -> PilotReviewCollaborationConfig:
    return PilotReviewCollaborationConfig(
        source_worklist_csv=resolve_path(args.source_worklist_csv, project_root, config.source_worklist_csv),
        guide_pdf=resolve_path(args.guide_pdf, project_root, config.guide_pdf),
        output_root=resolve_path(args.output_root, project_root, config.output_root),
        project_root=project_root,
        reviewers=config.reviewers,
        expected_rows=config.expected_rows,
    )


def _validate_worklist(worklist: pd.DataFrame, expected_rows: int) -> None:
    missing = [column for column in WORKLIST_COLUMNS if column not in worklist.columns]
    if missing:
        raise ValueError("source worklist missing required column(s): " + ", ".join(missing))
    if len(worklist) != expected_rows:
        raise ValueError(f"source worklist expected {expected_rows} row(s), found {len(worklist)}")
    for column in ["review_id", "image_id"]:
        if worklist[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"source worklist contains blank {column}")
        if worklist[column].duplicated().any():
            raise ValueError(f"source worklist contains duplicate {column}")


def _validate_guide_pdf(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"guide PDF not found: {path}")


def _validate_images(worklist: pd.DataFrame, project_root: Path) -> None:
    seen_targets: set[str] = set()
    for _, row in worklist.iterrows():
        source = _source_image_path(str(row["original_path"]), project_root)
        if not source.exists() or not source.is_file():
            raise FileNotFoundError(f"image not found: {source}")
        target_name = _image_target_name(str(row["image_id"]), source)
        if target_name in seen_targets:
            raise ValueError(f"duplicate package image target: {target_name}")
        seen_targets.add(target_name)


def _write_reviewer_package(
    reviewer_dir: Path,
    reviewer: ReviewerConfig,
    assignments: pd.DataFrame,
    worklist: pd.DataFrame,
    guide_pdf: Path,
    project_root: Path,
) -> None:
    reviewer_dir.mkdir(parents=True, exist_ok=True)
    images_dir = reviewer_dir / "images"
    images_dir.mkdir()
    assignments.to_csv(reviewer_dir / MANIFEST_FILENAME, index=False, encoding="utf-8-sig")
    shutil.copy2(guide_pdf, reviewer_dir / PACKAGE_GUIDE_FILENAME)
    (reviewer_dir / README_FILENAME).write_text(README_TEXT, encoding="utf-8")
    for _, row in worklist.iterrows():
        source = _source_image_path(str(row["original_path"]), project_root)
        shutil.copy2(source, images_dir / _image_target_name(str(row["image_id"]), source))
    workbook = build_pilot_review_excel(
        worklist.loc[:, WORKLIST_COLUMNS],
        PilotReviewExcelConfig(
            input_csv=reviewer_dir / MANIFEST_FILENAME,
            output_xlsx=reviewer_dir / WORKBOOK_FILENAME,
            project_root=project_root,
            expected_rows=len(worklist),
        ),
    )
    _rewrite_open_image_links(workbook, worklist)
    write_workbook(workbook, reviewer_dir / WORKBOOK_FILENAME)


def _rewrite_open_image_links(workbook, worklist: pd.DataFrame) -> None:
    worksheet = workbook[WORKLIST_SHEET]
    for row_number, (_, row) in enumerate(worklist.iterrows(), start=2):
        suffix = Path(str(row["original_path"])).suffix
        worksheet.cell(row=row_number, column=1).hyperlink = f"images/{row['image_id']}{suffix}"


def _source_image_path(original_path: str, project_root: Path) -> Path:
    path = Path(original_path)
    return path if path.is_absolute() else project_root / path


def _image_target_name(image_id: str, source_path: Path) -> str:
    return f"{image_id}{source_path.suffix}"


def _zip_directory(source_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for path in source_dir.rglob("*"):
            if path.is_file():
                zip_file.write(path, path.relative_to(source_dir.parent))


if __name__ == "__main__":
    raise SystemExit(main())
