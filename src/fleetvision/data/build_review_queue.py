"""Build a human review queue from FleetVision image metadata."""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


METADATA_REQUIRED_COLUMNS = [
    "image_id",
    "source_bucket",
    "original_path",
    "filename",
    "extension",
    "file_size_bytes",
    "width",
    "height",
    "aspect_ratio",
    "is_readable",
    "created_at",
    "modified_at",
    "notes",
]

REVIEW_QUEUE_COLUMNS = [
    "review_id",
    "image_id",
    "source_bucket",
    "original_path",
    "filename",
    "extension",
    "file_size_bytes",
    "width",
    "height",
    "aspect_ratio",
    "is_readable",
    "created_at",
    "modified_at",
    "notes",
    "quality_status",
    "brightness",
    "blur_score",
    "photo_type_review",
    "angle_review",
    "is_exterior_review",
    "has_visible_damage_review",
    "severity_review",
    "review_status",
    "reviewer",
    "review_notes",
    "priority",
    "priority_reason",
]

DEFAULT_CONFIG = {
    "input_csv": "outputs/metadata/image_metadata.csv",
    "output_csv": "dataset/02_interim/03_review_queue/review_queue.csv",
    "summary_csv": "outputs/metadata/review_queue_summary.csv",
    "priority_by_source_bucket": {
        "02_claimable_damage": 10,
        "03_minor_damage": 20,
        "01_general_fleet": 30,
    },
    "default_priority": 90,
    "unreadable_priority_offset": 100,
}


def load_config(config_path: Path | None) -> dict[str, Any]:
    """Load review queue configuration, applying defaults for omitted keys."""
    config = DEFAULT_CONFIG.copy()
    config["priority_by_source_bucket"] = DEFAULT_CONFIG["priority_by_source_bucket"].copy()

    if config_path is None:
        return config

    with config_path.open(encoding="utf-8") as config_file:
        loaded_config = yaml.safe_load(config_file) or {}

    config.update(loaded_config)
    config["priority_by_source_bucket"] = {
        **DEFAULT_CONFIG["priority_by_source_bucket"],
        **loaded_config.get("priority_by_source_bucket", {}),
    }
    return config


def build_review_queue(
    input_csv: Path,
    config_path: Path | None = None,
    project_root: Path | None = None,
    max_rows: int | None = None,
) -> list[dict[str, Any]]:
    """Create review queue rows from Phase 01 image metadata."""
    project_root = (project_root or Path.cwd()).resolve()
    config = load_config(config_path)
    metadata_rows = _read_metadata_csv(input_csv)
    priority_by_source = {
        str(source_bucket): int(priority)
        for source_bucket, priority in config["priority_by_source_bucket"].items()
    }
    default_priority = int(config["default_priority"])
    unreadable_offset = int(config["unreadable_priority_offset"])

    review_rows = [
        _build_review_row(
            row=row,
            project_root=project_root,
            priority_by_source=priority_by_source,
            default_priority=default_priority,
            unreadable_offset=unreadable_offset,
        )
        for row in metadata_rows
    ]
    review_rows.sort(
        key=lambda row: (
            int(row["priority"]),
            str(row["source_bucket"]),
            str(row["filename"]),
            str(row["image_id"]),
        )
    )
    if max_rows is not None:
        review_rows = review_rows[:max_rows]
    return review_rows


def write_review_queue_csv(rows: list[dict[str, Any]], output_csv: Path) -> None:
    """Write review queue rows to CSV."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=REVIEW_QUEUE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_summary_csv(rows: list[dict[str, Any]], summary_csv: Path) -> None:
    """Write a compact summary CSV for the generated review queue."""
    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    summary_rows = _build_summary_rows(rows)
    with summary_csv.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(summary_rows)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the review queue builder."""
    parser = argparse.ArgumentParser(description="Build FleetVision Phase 02 review queue.")
    parser.add_argument(
        "--config",
        default="configs/data/review_queue_config.yaml",
        help="Path to review queue config YAML.",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root used to resolve relative paths. Defaults to current folder.",
    )
    parser.add_argument("--input", help="Override input metadata CSV path.")
    parser.add_argument("--output", help="Override review queue CSV output path.")
    parser.add_argument("--summary", help="Override summary CSV output path.")
    parser.add_argument("--max-rows", type=int, help="Limit output rows after priority sorting.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for building the Phase 02 review queue."""
    args = parse_args(argv)
    project_root = Path(args.project_root).resolve()
    config_path = _resolve_project_path(project_root, args.config)
    config = load_config(config_path)

    input_csv = _resolve_project_path(project_root, args.input or config["input_csv"])
    output_csv = _resolve_project_path(project_root, args.output or config["output_csv"])
    summary_csv = _resolve_project_path(project_root, args.summary or config["summary_csv"])

    rows = build_review_queue(
        input_csv=input_csv,
        config_path=config_path,
        project_root=project_root,
        max_rows=args.max_rows,
    )
    write_review_queue_csv(rows, output_csv)
    write_summary_csv(rows, summary_csv)
    _print_summary(rows, output_csv, summary_csv)
    return 0


def _read_metadata_csv(input_csv: Path) -> list[dict[str, str]]:
    if not input_csv.exists():
        raise FileNotFoundError(f"metadata CSV not found: {input_csv}")

    with input_csv.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        missing_columns = [
            column for column in METADATA_REQUIRED_COLUMNS if column not in (reader.fieldnames or [])
        ]
        if missing_columns:
            raise ValueError(
                "metadata CSV is missing required column(s): "
                + ", ".join(missing_columns)
            )
        return list(reader)


def _build_review_row(
    row: dict[str, str],
    project_root: Path,
    priority_by_source: dict[str, int],
    default_priority: int,
    unreadable_offset: int,
) -> dict[str, Any]:
    source_bucket = row["source_bucket"]
    is_readable = _parse_bool(row["is_readable"])
    quality_status = "ready" if is_readable else "unreadable"
    source_priority = priority_by_source.get(source_bucket, default_priority)
    priority = source_priority if is_readable else source_priority + unreadable_offset
    priority_reason = f"source_bucket={source_bucket}"
    if not is_readable:
        priority_reason += "; unreadable"

    review_id = _build_review_id(row["image_id"], source_bucket, row["original_path"])
    review_row: dict[str, Any] = {
        "review_id": review_id,
        "quality_status": quality_status,
        "brightness": "",
        "blur_score": "",
        "photo_type_review": "unknown",
        "angle_review": "unknown",
        "is_exterior_review": "unknown",
        "has_visible_damage_review": "unknown",
        "severity_review": "unknown",
        "review_status": "pending",
        "reviewer": "",
        "review_notes": "",
        "priority": priority,
        "priority_reason": priority_reason,
    }
    for column in METADATA_REQUIRED_COLUMNS:
        review_row[column] = _normalize_metadata_value(row[column])

    # Rebuild with stable field order and keep paths repo-relative when possible.
    review_row["original_path"] = _as_project_relative_text(
        review_row["original_path"], project_root
    )
    return {column: review_row[column] for column in REVIEW_QUEUE_COLUMNS}


def _build_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = [{"metric": "total_rows", "value": len(rows)}]
    for source_bucket, count in sorted(Counter(row["source_bucket"] for row in rows).items()):
        summary_rows.append({"metric": f"source_bucket:{source_bucket}", "value": count})
    for quality_status, count in sorted(Counter(row["quality_status"] for row in rows).items()):
        summary_rows.append({"metric": f"quality_status:{quality_status}", "value": count})
    return summary_rows


def _build_review_id(image_id: str, source_bucket: str, original_path: str) -> str:
    digest = hashlib.sha1(
        f"{image_id}|{source_bucket}|{original_path}".encode("utf-8")
    ).hexdigest()
    return digest[:16]


def _normalize_metadata_value(value: str) -> str:
    return "" if value is None else value


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _resolve_project_path(project_root: Path, path_text: str | Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return project_root / path


def _as_project_relative_text(path_text: str, project_root: Path) -> str:
    path = Path(path_text)
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _print_summary(rows: list[dict[str, Any]], output_csv: Path, summary_csv: Path) -> None:
    print("FleetVision review queue summary")
    print(f"output_csv: {output_csv}")
    print(f"summary_csv: {summary_csv}")
    print(f"total_rows: {len(rows)}")
    for source_bucket, count in sorted(Counter(row["source_bucket"] for row in rows).items()):
        print(f"{source_bucket}: {count}")
    for quality_status, count in sorted(Counter(row["quality_status"] for row in rows).items()):
        print(f"{quality_status}: {count}")


if __name__ == "__main__":
    raise SystemExit(main())
