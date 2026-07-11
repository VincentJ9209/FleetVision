"""Controlled external dataset intake for FleetVision Phase 04.5.

This module ingests one pre-approved external dataset archive into the isolated
``dataset/01_raw/99_external`` area. It preserves the downloaded archive,
keeps original annotation format, records license/version evidence, performs
COCO structural and bounding-box validation, and never creates YOLO labels,
dataset splits, or training artifacts.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import stat
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable

import pandas as pd
import yaml

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
REQUIRED_COCO_KEYS = {"images", "annotations", "categories"}


class DatasetIntakeError(RuntimeError):
    """Raised when a controlled intake gate fails."""


@dataclass(frozen=True)
class ControlledIntakeConfig:
    """Resolved configuration for one controlled external dataset intake."""

    dataset_id: str
    registry_csv: Path
    raw_dataset_root: Path
    metadata_root: Path
    provider: str
    project_url: str
    version_url: str
    license_name: str
    license_url: str
    expected_classes: tuple[str, ...]
    mapped_class: str
    export_format: str
    dataset_version: str
    reported_project_image_count: int
    reported_version_image_count: int
    lineage_status: str


@dataclass(frozen=True)
class CocoInspectionResult:
    """COCO export inspection result."""

    summary: dict[str, Any]
    errors: list[str]
    image_rows: list[dict[str, Any]]
    annotation_rows: list[dict[str, Any]]
    archive_rows: list[dict[str, Any]]


def load_controlled_intake_config(config_path: Path, project_root: Path) -> ControlledIntakeConfig:
    """Load one controlled intake YAML and resolve project-relative paths."""

    if not config_path.is_file():
        raise DatasetIntakeError(f"config not found: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    source = data.get("source", {}) or {}
    paths = data.get("paths", {}) or {}

    def resolve(value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else project_root / path

    required_top = ["dataset_id", "provider", "expected_classes", "mapped_class", "export_format"]
    missing_top = [key for key in required_top if not data.get(key)]
    required_source = [
        "project_url",
        "version_url",
        "license_name",
        "license_url",
        "dataset_version",
        "reported_project_image_count",
        "reported_version_image_count",
        "lineage_status",
    ]
    missing_source = [key for key in required_source if source.get(key) in {None, ""}]
    required_paths = ["registry_csv", "raw_dataset_root", "metadata_root"]
    missing_paths = [key for key in required_paths if not paths.get(key)]
    if missing_top or missing_source or missing_paths:
        raise DatasetIntakeError(
            "config missing required values: "
            f"top={missing_top}, source={missing_source}, paths={missing_paths}"
        )

    return ControlledIntakeConfig(
        dataset_id=str(data["dataset_id"]),
        registry_csv=resolve(str(paths["registry_csv"])),
        raw_dataset_root=resolve(str(paths["raw_dataset_root"])),
        metadata_root=resolve(str(paths["metadata_root"])),
        provider=str(data["provider"]),
        project_url=str(source["project_url"]),
        version_url=str(source["version_url"]),
        license_name=str(source["license_name"]),
        license_url=str(source["license_url"]),
        expected_classes=tuple(str(value) for value in data["expected_classes"]),
        mapped_class=str(data["mapped_class"]),
        export_format=str(data["export_format"]),
        dataset_version=str(source["dataset_version"]),
        reported_project_image_count=int(source["reported_project_image_count"]),
        reported_version_image_count=int(source["reported_version_image_count"]),
        lineage_status=str(source["lineage_status"]),
    )


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return uppercase SHA256 for one file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _normalize_scalar(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_registry_row(registry_csv: Path, dataset_id: str) -> dict[str, str]:
    """Load and validate one approved registry row."""

    if not registry_csv.is_file():
        raise DatasetIntakeError(f"registry not found: {registry_csv}")

    frame = pd.read_csv(registry_csv, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    required = {"dataset_id", "license_verified", "usage_status"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise DatasetIntakeError(f"registry missing columns: {missing}")

    matched = frame[frame["dataset_id"].astype(str).str.strip() == dataset_id]
    if len(matched) != 1:
        raise DatasetIntakeError(
            f"registry dataset_id must match exactly one row: {dataset_id}; matched={len(matched)}"
        )

    row = {column: _normalize_scalar(value) for column, value in matched.iloc[0].items()}
    if row["license_verified"].lower() not in {"yes", "true", "1"}:
        raise DatasetIntakeError(f"registry license is not verified for {dataset_id}")
    if row["usage_status"].lower() != "approved_for_download":
        raise DatasetIntakeError(
            f"registry usage_status must be approved_for_download for {dataset_id}; "
            f"got={row['usage_status']!r}"
        )
    return row


def _zip_member_is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = info.external_attr >> 16
    return stat.S_ISLNK(mode)


def safe_extract_zip(archive_path: Path, destination: Path) -> list[dict[str, Any]]:
    """Extract a ZIP after blocking path traversal, absolute paths, and symlinks."""

    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    rows: list[dict[str, Any]] = []

    try:
        archive = zipfile.ZipFile(archive_path)
    except zipfile.BadZipFile as exc:
        raise DatasetIntakeError(f"invalid ZIP archive: {archive_path}") from exc

    with archive:
        for info in archive.infolist():
            member = PurePosixPath(info.filename.replace("\\", "/"))
            if (
                member.is_absolute()
                or any(part in {"..", ""} for part in member.parts)
                or (member.parts and ":" in member.parts[0])
                or _zip_member_is_symlink(info)
            ):
                raise DatasetIntakeError(f"unsafe ZIP member: {info.filename}")

            target = destination.joinpath(*member.parts)
            try:
                target.resolve().relative_to(root)
            except ValueError as exc:
                raise DatasetIntakeError(f"unsafe ZIP member: {info.filename}") from exc

            rows.append(
                {
                    "archive_member": info.filename,
                    "is_directory": info.is_dir(),
                    "compressed_size": info.compress_size,
                    "uncompressed_size": info.file_size,
                    "crc32": f"{info.CRC:08X}",
                }
            )

        archive.extractall(destination)

    return rows


def _load_coco_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or not REQUIRED_COCO_KEYS.issubset(data):
        return None
    return data


def _find_image_path(annotation_path: Path, extracted_root: Path, file_name: str) -> Path | None:
    direct = annotation_path.parent / Path(file_name)
    if direct.is_file():
        return direct

    normalized = extracted_root / Path(file_name)
    if normalized.is_file():
        return normalized

    matches = [path for path in extracted_root.rglob(Path(file_name).name) if path.is_file()]
    return matches[0] if len(matches) == 1 else None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_segmentation(segmentation: Any) -> str:
    if isinstance(segmentation, dict):
        if "counts" in segmentation and "size" in segmentation:
            return "valid_rle"
        return "invalid_rle"
    if not isinstance(segmentation, list) or not segmentation:
        return "missing_or_empty"
    for polygon in segmentation:
        if not isinstance(polygon, list) or len(polygon) < 6 or len(polygon) % 2 != 0:
            return "invalid_polygon_shape"
        if not all(_is_number(value) for value in polygon):
            return "invalid_polygon_coordinate"
    return "valid_polygon"


def inspect_coco_export(
    extracted_root: Path,
    *,
    expected_classes: tuple[str, ...],
    archive_rows: list[dict[str, Any]] | None = None,
) -> CocoInspectionResult:
    """Inspect all COCO annotation files and referenced images."""

    annotation_files: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(extracted_root.rglob("*.json")):
        data = _load_coco_json(path)
        if data is not None:
            annotation_files.append((path, data))

    if not annotation_files:
        raise DatasetIntakeError("no COCO annotation JSON found in extracted archive")

    errors: list[str] = []
    image_rows: list[dict[str, Any]] = []
    annotation_rows: list[dict[str, Any]] = []
    class_names: set[str] = set()
    seen_image_keys: set[tuple[str, str]] = set()

    for annotation_path, data in annotation_files:
        split = annotation_path.parent.relative_to(extracted_root).as_posix() or "."
        categories = {
            category.get("id"): str(category.get("name", "")).strip()
            for category in data.get("categories", [])
            if isinstance(category, dict)
        }
        class_names.update(name for name in categories.values() if name)

        images = {
            image.get("id"): image
            for image in data.get("images", [])
            if isinstance(image, dict) and "id" in image
        }

        for image_id, image in images.items():
            file_name = str(image.get("file_name", "")).strip()
            width = image.get("width")
            height = image.get("height")
            resolved = _find_image_path(annotation_path, extracted_root, file_name) if file_name else None
            relative_path = (
                resolved.relative_to(extracted_root).as_posix() if resolved is not None else ""
            )
            key = (split, str(image_id))
            if key in seen_image_keys:
                errors.append(f"duplicate image id within split: split={split} image_id={image_id}")
            seen_image_keys.add(key)

            valid_dimensions = (
                _is_number(width)
                and _is_number(height)
                and float(width) > 0
                and float(height) > 0
            )
            if not file_name:
                errors.append(f"empty image file_name: split={split} image_id={image_id}")
            if resolved is None:
                errors.append(
                    f"referenced image missing or ambiguous: split={split} image_id={image_id} file={file_name}"
                )
            if not valid_dimensions:
                errors.append(f"invalid image dimensions: split={split} image_id={image_id}")

            image_rows.append(
                {
                    "split": split,
                    "annotation_json": annotation_path.relative_to(extracted_root).as_posix(),
                    "image_id": image_id,
                    "file_name": file_name,
                    "relative_image_path": relative_path,
                    "width": width,
                    "height": height,
                    "file_exists": resolved is not None,
                    "size_bytes": resolved.stat().st_size if resolved is not None else "",
                    "sha256": sha256_file(resolved) if resolved is not None else "",
                }
            )

        for annotation in data.get("annotations", []):
            if not isinstance(annotation, dict):
                errors.append(f"non-object annotation: split={split}")
                continue

            annotation_id = annotation.get("id")
            image_id = annotation.get("image_id")
            category_id = annotation.get("category_id")
            image = images.get(image_id)
            category_name = categories.get(category_id, "")
            bbox = annotation.get("bbox")
            bbox_status = "valid"

            if image is None:
                bbox_status = "missing_image_reference"
                errors.append(
                    f"annotation references missing image: split={split} annotation_id={annotation_id}"
                )
            elif not isinstance(bbox, list) or len(bbox) != 4 or not all(_is_number(v) for v in bbox):
                bbox_status = "invalid_bbox_shape"
                errors.append(f"invalid bbox shape: split={split} annotation_id={annotation_id}")
            else:
                x, y, width, height = map(float, bbox)
                image_width = float(image.get("width", 0) or 0)
                image_height = float(image.get("height", 0) or 0)
                if width <= 0 or height <= 0:
                    bbox_status = "non_positive_bbox"
                    errors.append(f"non-positive bbox: split={split} annotation_id={annotation_id}")
                elif x < 0 or y < 0:
                    bbox_status = "negative_bbox_origin"
                    errors.append(f"negative bbox origin: split={split} annotation_id={annotation_id}")
                elif x + width > image_width + 1e-6 or y + height > image_height + 1e-6:
                    bbox_status = "bbox_out_of_bounds"
                    errors.append(f"bbox out of bounds: split={split} annotation_id={annotation_id}")

            if not category_name:
                errors.append(
                    f"annotation references missing category: split={split} annotation_id={annotation_id}"
                )

            segmentation_status = _validate_segmentation(annotation.get("segmentation"))
            if not segmentation_status.startswith("valid_"):
                errors.append(
                    f"invalid segmentation ({segmentation_status}): split={split} annotation_id={annotation_id}"
                )

            annotation_rows.append(
                {
                    "split": split,
                    "annotation_json": annotation_path.relative_to(extracted_root).as_posix(),
                    "annotation_id": annotation_id,
                    "image_id": image_id,
                    "category_id": category_id,
                    "category_name": category_name,
                    "bbox": json.dumps(bbox, ensure_ascii=False),
                    "bbox_status": bbox_status,
                    "segmentation_status": segmentation_status,
                    "area": annotation.get("area", ""),
                    "iscrowd": annotation.get("iscrowd", ""),
                }
            )

    expected_set = set(expected_classes)
    if class_names != expected_set:
        errors.append(
            f"class mismatch: expected={sorted(expected_set)} actual={sorted(class_names)}"
        )

    hash_counts: dict[str, int] = {}
    for row in image_rows:
        digest = str(row.get("sha256", ""))
        if digest:
            hash_counts[digest] = hash_counts.get(digest, 0) + 1
    duplicate_groups = {digest: count for digest, count in hash_counts.items() if count > 1}

    invalid_bbox_count = sum(row["bbox_status"] != "valid" for row in annotation_rows)
    invalid_segmentation_count = sum(
        not str(row["segmentation_status"]).startswith("valid_") for row in annotation_rows
    )
    missing_image_count = sum(not bool(row["file_exists"]) for row in image_rows)

    summary = {
        "annotation_file_count": len(annotation_files),
        "image_record_count": len(image_rows),
        "image_file_count": sum(bool(row["file_exists"]) for row in image_rows),
        "annotation_count": len(annotation_rows),
        "valid_bbox_count": len(annotation_rows) - invalid_bbox_count,
        "invalid_bbox_count": invalid_bbox_count,
        "invalid_segmentation_count": invalid_segmentation_count,
        "missing_image_count": missing_image_count,
        "class_names": sorted(class_names),
        "exact_duplicate_group_count": len(duplicate_groups),
        "exact_duplicate_image_count": sum(duplicate_groups.values()),
        "split_counts": _count_values(image_rows, "split"),
    }

    return CocoInspectionResult(
        summary=summary,
        errors=errors,
        image_rows=image_rows,
        annotation_rows=annotation_rows,
        archive_rows=list(archive_rows or []),
    )


def _count_values(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, ""))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _default_evidence_fetcher(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "FleetVision-External-Dataset-Intake/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - fixed approved HTTPS URLs.
            payload = response.read()
    except Exception as exc:  # noqa: BLE001 - report external network failure clearly.
        raise DatasetIntakeError(f"failed to fetch license/version evidence: {url}: {exc}") from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)


def _verify_evidence(config: ControlledIntakeConfig, project_html: Path, version_html: Path) -> None:
    project_text = project_html.read_text(encoding="utf-8", errors="ignore")
    version_text = version_html.read_text(encoding="utf-8", errors="ignore")

    project_checks = ["Car-Damage", "Public Domain"]
    if not all(value.lower() in project_text.lower() for value in project_checks):
        raise DatasetIntakeError("project license evidence does not contain Car-Damage and Public Domain")

    project_count_ok = str(config.reported_project_image_count) in project_text or "4.9k" in project_text.lower()
    if not project_count_ok:
        raise DatasetIntakeError("project evidence does not contain reported 4,869/4.9k image count")

    version_checks = ["Car-Damage", str(config.reported_version_image_count)]
    if not all(value.lower() in version_text.lower() for value in version_checks):
        raise DatasetIntakeError("version evidence does not contain expected class and 11,685 image count")
    if "outputs per training example" not in version_text.lower():
        raise DatasetIntakeError("version evidence does not record augmentation output multiplier")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        frame = pd.DataFrame(rows)
        if fieldnames is not None:
            for column in fieldnames:
                if column not in frame.columns:
                    frame[column] = ""
            frame = frame[fieldnames]
    else:
        frame = pd.DataFrame(columns=fieldnames or [])
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def _build_registry_update_proposal(
    registry_row: dict[str, str],
    *,
    config: ControlledIntakeConfig,
    summary: dict[str, Any],
    now_utc: str,
) -> dict[str, str]:
    proposal = dict(registry_row)
    proposal.update(
        {
            "download_date": now_utc[:10],
            "image_count_downloaded": str(summary["image_record_count"]),
            "bbox_count_reported": str(summary["annotation_count"]),
            "bbox_count_valid": str(summary["valid_bbox_count"]),
            "accepted_image_count": str(summary["image_record_count"] - summary["missing_image_count"]),
            "rejected_image_count": str(summary["missing_image_count"]),
            "bbox_quality_status": (
                "downloaded_structural_qa_pass"
                if summary["invalid_bbox_count"] == 0 and summary["invalid_segmentation_count"] == 0
                else "downloaded_structural_qa_failed"
            ),
            "sha256_dedup_status": "external_exact_hash_inventory_complete",
            "perceptual_hash_status": "pending",
            "internal_cross_dedup_status": "pending",
            "usage_status": "downloaded",
            "local_raw_path": str(config.raw_dataset_root),
            "notes": (
                "Controlled v1 COCO Segmentation export downloaded. Version contains generated/augmented "
                "images (3 outputs per training example); training acceptance remains pending bbox/mask QA, "
                "perceptual dedup, internal cross-dedup, and lineage review."
            ),
        }
    )
    return proposal


def run_controlled_intake(
    config: ControlledIntakeConfig,
    *,
    archive_path: Path,
    project_evidence_path: Path | None = None,
    version_evidence_path: Path | None = None,
    evidence_fetcher: Callable[[str, Path], None] = _default_evidence_fetcher,
    now_utc: str | None = None,
) -> dict[str, Any]:
    """Run one immutable, staged, controlled external dataset intake."""

    archive_path = archive_path.resolve()
    if not archive_path.is_file():
        raise DatasetIntakeError(f"archive not found: {archive_path}")
    if archive_path.suffix.lower() != ".zip":
        raise DatasetIntakeError("controlled intake requires a ZIP archive")
    if config.raw_dataset_root.exists() or config.metadata_root.exists():
        raise DatasetIntakeError(
            "target already exists; do not overwrite or rerun without a separate rollback/promotion gate"
        )

    if (project_evidence_path is None) != (version_evidence_path is None):
        raise DatasetIntakeError(
            "both project and version evidence files are required when using local evidence"
        )
    local_evidence_paths: tuple[Path, Path] | None = None
    if project_evidence_path is not None and version_evidence_path is not None:
        resolved_project_evidence = project_evidence_path.resolve()
        resolved_version_evidence = version_evidence_path.resolve()
        if not resolved_project_evidence.is_file():
            raise DatasetIntakeError(f"project evidence file not found: {resolved_project_evidence}")
        if not resolved_version_evidence.is_file():
            raise DatasetIntakeError(f"version evidence file not found: {resolved_version_evidence}")
        local_evidence_paths = (resolved_project_evidence, resolved_version_evidence)

    registry_row = load_registry_row(config.registry_csv, config.dataset_id)
    now_utc = now_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    timestamp = now_utc.replace("-", "").replace(":", "").replace("T", "_").replace("Z", "")

    raw_parent = config.raw_dataset_root.parent
    metadata_parent = config.metadata_root.parent
    raw_parent.mkdir(parents=True, exist_ok=True)
    metadata_parent.mkdir(parents=True, exist_ok=True)
    raw_staging = raw_parent / f"_staging_{config.dataset_id}_{timestamp}"
    metadata_staging = metadata_parent / f"_staging_{config.dataset_id}_{timestamp}"
    raw_promoted = False

    if raw_staging.exists() or metadata_staging.exists():
        raise DatasetIntakeError("staging directory already exists")

    try:
        download_dir = raw_staging / "00_download"
        extracted_dir = raw_staging / "01_extracted_export"
        quarantine_dir = raw_staging / "99_quarantine"
        evidence_dir = metadata_staging / "license_evidence"
        for directory in (download_dir, extracted_dir, quarantine_dir, evidence_dir):
            directory.mkdir(parents=True, exist_ok=True)

        archive_copy = download_dir / archive_path.name
        shutil.copy2(archive_path, archive_copy)
        if sha256_file(archive_copy) != sha256_file(archive_path):
            raise DatasetIntakeError("archive copy SHA256 mismatch")

        project_html = evidence_dir / "roboflow_project_page.html"
        version_html = evidence_dir / "roboflow_dataset_v1_page.html"
        evidence_source_mode = "live_fetch"
        if local_evidence_paths is None:
            evidence_fetcher(config.project_url, project_html)
            evidence_fetcher(config.version_url, version_html)
        else:
            evidence_source_mode = "local_reviewed_snapshot"
            shutil.copy2(local_evidence_paths[0], project_html)
            shutil.copy2(local_evidence_paths[1], version_html)
        _verify_evidence(config, project_html, version_html)

        archive_rows = safe_extract_zip(archive_copy, extracted_dir)
        inspection = inspect_coco_export(
            extracted_dir,
            expected_classes=config.expected_classes,
            archive_rows=archive_rows,
        )
        summary = dict(inspection.summary)
        summary.update(
            {
                "dataset_id": config.dataset_id,
                "dataset_version": config.dataset_version,
                "export_format": config.export_format,
                "lineage_status": config.lineage_status,
                "reported_project_image_count": config.reported_project_image_count,
                "reported_version_image_count": config.reported_version_image_count,
                "reported_version_count_delta": (
                    summary["image_record_count"] - config.reported_version_image_count
                ),
                "training_acceptance": "NOT_YET_APPROVED",
                "downloaded_at_utc": now_utc,
            }
        )
        gate_classification = (
            "EXTERNAL_DATASET_INTAKE_VERIFIED"
            if not inspection.errors
            else "EXTERNAL_DATASET_INTAKE_AUDIT_REQUIRED"
        )

        _write_csv(
            metadata_staging / "intake_errors.csv",
            [{"error": error} for error in inspection.errors],
            ["error"],
        )

        _write_csv(metadata_staging / "archive_inventory.csv", inspection.archive_rows)
        _write_csv(metadata_staging / "image_inventory.csv", inspection.image_rows)
        _write_csv(metadata_staging / "annotation_inventory.csv", inspection.annotation_rows)
        _write_csv(metadata_staging / "bbox_quality_report.csv", inspection.annotation_rows)
        _write_csv(
            metadata_staging / "class_mapping.csv",
            [
                {
                    "dataset_id": config.dataset_id,
                    "original_class": original_class,
                    "mapped_class": config.mapped_class,
                    "mapping_status": "approved_for_future_conversion",
                    "yolo_label_created": "no",
                }
                for original_class in config.expected_classes
            ],
        )

        archive_hash = sha256_file(archive_copy)
        manifest_row = {
            "dataset_id": config.dataset_id,
            "provider": config.provider,
            "dataset_version": config.dataset_version,
            "source_project_url": config.project_url,
            "source_version_url": config.version_url,
            "license": config.license_name,
            "license_url": config.license_url,
            "license_verified": "yes",
            "evidence_source_mode": evidence_source_mode,
            "project_evidence_sha256": sha256_file(project_html),
            "version_evidence_sha256": sha256_file(version_html),
            "export_format": config.export_format,
            "lineage_status": config.lineage_status,
            "archive_source_path": str(archive_path),
            "archive_stored_path": str(config.raw_dataset_root / "00_download" / archive_path.name),
            "archive_sha256": archive_hash,
            "archive_size_bytes": archive_copy.stat().st_size,
            "downloaded_at_utc": now_utc,
            "image_record_count": summary["image_record_count"],
            "annotation_count": summary["annotation_count"],
            "valid_bbox_count": summary["valid_bbox_count"],
            "invalid_bbox_count": summary["invalid_bbox_count"],
            "invalid_segmentation_count": summary["invalid_segmentation_count"],
            "exact_duplicate_group_count": summary["exact_duplicate_group_count"],
            "exact_duplicate_image_count": summary["exact_duplicate_image_count"],
            "usage_status": (
                "downloaded_pending_audit"
                if not inspection.errors
                else "downloaded_quarantined_for_qa"
            ),
            "qa_error_count": len(inspection.errors),
            "training_acceptance": "NOT_YET_APPROVED",
        }
        _write_csv(metadata_staging / "download_manifest.csv", [manifest_row])

        license_markdown = f"""# License and Version Evidence — {config.dataset_id}\n\n- Checked at (UTC): {now_utc}\n- Project URL: {config.project_url}\n- Dataset version URL: {config.version_url}\n- License shown on project page: {config.license_name}\n- License reference: {config.license_url}\n- Project image count shown: {config.reported_project_image_count}\n- Version image count shown: {config.reported_version_image_count}\n- Version lineage: generated/augmented v1; 3 outputs per training example\n- Export format requested: {config.export_format}\n- Training acceptance: NOT_YET_APPROVED\n\nThe downloaded v1 export must not be described as an unaugmented/original-only payload.\n"""
        (metadata_staging / "license_evidence.md").write_text(license_markdown, encoding="utf-8")

        proposal = _build_registry_update_proposal(
            registry_row,
            config=config,
            summary=summary,
            now_utc=now_utc,
        )
        _write_csv(
            metadata_staging / "registry_update_proposal.csv",
            [proposal],
            list(pd.read_csv(config.registry_csv, nrows=0, encoding="utf-8-sig").columns),
        )

        verification = {
            "gate_classification": gate_classification,
            "dataset_id": config.dataset_id,
            "archive_sha256": archive_hash,
            "archive_copy_verified": True,
            "license_evidence_verified": True,
            "evidence_source_mode": evidence_source_mode,
            "project_evidence_sha256": sha256_file(project_html),
            "version_evidence_sha256": sha256_file(version_html),
            "summary": summary,
            "error_count": len(inspection.errors),
            "raw_target": str(config.raw_dataset_root),
            "metadata_target": str(config.metadata_root),
            "yolo_labels_created": False,
            "dataset_split_created": False,
            "model_training_executed": False,
        }
        (metadata_staging / "intake_verification.json").write_text(
            json.dumps(verification, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        raw_staging.rename(config.raw_dataset_root)
        raw_promoted = True
        metadata_staging.rename(config.metadata_root)

        final_archive = config.raw_dataset_root / "00_download" / archive_path.name
        if sha256_file(final_archive) != archive_hash:
            raise DatasetIntakeError("post-promotion archive SHA256 mismatch")
        final_verification = json.loads(
            (config.metadata_root / "intake_verification.json").read_text(encoding="utf-8")
        )
        if final_verification.get("gate_classification") != gate_classification:
            raise DatasetIntakeError("post-promotion verification status mismatch")

        return {
            "gate_classification": gate_classification,
            "raw_dataset_root": config.raw_dataset_root,
            "metadata_root": config.metadata_root,
            "archive_sha256": archive_hash,
            "summary": summary,
        }
    except Exception:
        if config.metadata_root.exists():
            shutil.rmtree(config.metadata_root, ignore_errors=True)
        if raw_promoted and config.raw_dataset_root.exists():
            shutil.rmtree(config.raw_dataset_root, ignore_errors=True)
        shutil.rmtree(raw_staging, ignore_errors=True)
        shutil.rmtree(metadata_staging, ignore_errors=True)
        raise
