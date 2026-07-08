"""Build image metadata for FleetVision raw image buckets."""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from PIL import Image


METADATA_COLUMNS = [
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

DEFAULT_BUCKET_NAME_MAP = {
    "general_fleet": "01_general_fleet",
    "claimable_damage": "02_claimable_damage",
    "minor_damage": "03_minor_damage",
}


def load_config(config_path: Path) -> dict[str, Any]:
    """Load metadata builder settings from a YAML config file."""
    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}

    if "output_csv" not in config:
        raise ValueError("metadata config must define output_csv")

    if "source_buckets" not in config and "source_groups" not in config:
        raise ValueError("metadata config must define source_buckets")

    return config


def build_metadata(config_path: Path, project_root: Path | None = None) -> list[dict[str, Any]]:
    """Scan configured raw image folders and return one metadata row per image."""
    project_root = (project_root or Path.cwd()).resolve()
    config = load_config(config_path)
    source_buckets = _read_source_buckets(config)
    supported_extensions = _read_supported_extensions(config)

    rows: list[dict[str, Any]] = []
    for source_bucket, source_dir_text in source_buckets.items():
        source_dir = _resolve_project_path(project_root, source_dir_text)
        if not source_dir.exists():
            raise FileNotFoundError(f"source bucket folder not found: {source_dir}")

        image_paths = sorted(
            path
            for path in source_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in supported_extensions
        )
        for image_path in image_paths:
            rows.append(_build_image_row(image_path, source_bucket, project_root))

    return rows


def write_metadata_csv(rows: list[dict[str, Any]], output_csv: Path) -> None:
    """Write image metadata rows to CSV with stable column order."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=METADATA_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for the metadata builder."""
    parser = argparse.ArgumentParser(description="Build FleetVision image metadata CSV.")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to metadata config YAML, for example configs/data/metadata_config.yaml.",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root used to resolve relative config paths. Defaults to current folder.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for building FleetVision image metadata."""
    args = parse_args(argv)
    project_root = Path(args.project_root).resolve()
    config_path = _resolve_project_path(project_root, args.config)
    config = load_config(config_path)
    output_csv = _resolve_project_path(project_root, config["output_csv"])

    rows = build_metadata(config_path=config_path, project_root=project_root)
    write_metadata_csv(rows, output_csv)
    _print_summary(rows, output_csv)
    return 0


def _read_source_buckets(config: dict[str, Any]) -> dict[str, str]:
    raw_sources = config.get("source_buckets") or config.get("source_groups") or {}
    return {
        _normalize_source_bucket_name(source_name, source_dir): str(source_dir)
        for source_name, source_dir in raw_sources.items()
    }


def _normalize_source_bucket_name(source_name: str, source_dir: Any) -> str:
    source_name_text = str(source_name)
    if source_name_text in DEFAULT_BUCKET_NAME_MAP:
        return DEFAULT_BUCKET_NAME_MAP[source_name_text]
    if source_name_text[:3] in {"01_", "02_", "03_"}:
        return source_name_text

    source_path = Path(str(source_dir))
    parent_name = source_path.parent.name if source_path.name == "images" else source_path.name
    return DEFAULT_BUCKET_NAME_MAP.get(parent_name, parent_name)


def _read_supported_extensions(config: dict[str, Any]) -> set[str]:
    raw_extensions = config.get("supported_extensions") or [".jpg", ".jpeg", ".png"]
    return {
        extension.lower() if str(extension).startswith(".") else f".{str(extension).lower()}"
        for extension in raw_extensions
    }


def _build_image_row(
    image_path: Path, source_bucket: str, project_root: Path
) -> dict[str, Any]:
    stat = image_path.stat()
    width: int | None = None
    height: int | None = None
    aspect_ratio: float | None = None
    is_readable = True
    notes = ""

    try:
        with Image.open(image_path) as image:
            width, height = image.size
            image.verify()
        if width and height:
            aspect_ratio = round(width / height, 6)
    except Exception as exc:
        is_readable = False
        notes = f"unreadable: {exc.__class__.__name__}"

    original_path = _as_project_relative_path(image_path, project_root)
    return {
        "image_id": _build_image_id(source_bucket, original_path),
        "source_bucket": source_bucket,
        "original_path": original_path,
        "filename": image_path.name,
        "extension": image_path.suffix.lower(),
        "file_size_bytes": stat.st_size,
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "is_readable": is_readable,
        "created_at": _format_timestamp(stat.st_ctime),
        "modified_at": _format_timestamp(stat.st_mtime),
        "notes": notes,
    }


def _build_image_id(source_bucket: str, original_path: str) -> str:
    digest = hashlib.sha1(f"{source_bucket}|{original_path}".encode("utf-8")).hexdigest()
    return digest[:16]


def _format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat(timespec="seconds")


def _resolve_project_path(project_root: Path, path_text: str | Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return project_root / path


def _as_project_relative_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _print_summary(rows: list[dict[str, Any]], output_csv: Path) -> None:
    counts = Counter(row["source_bucket"] for row in rows)
    unreadable_count = sum(1 for row in rows if not row["is_readable"])

    print("FleetVision metadata summary")
    print(f"output_csv: {output_csv}")
    print(f"total_images: {len(rows)}")
    for source_bucket in sorted(counts):
        print(f"{source_bucket}: {counts[source_bucket]}")
    print(f"unreadable_images: {unreadable_count}")


if __name__ == "__main__":
    raise SystemExit(main())
