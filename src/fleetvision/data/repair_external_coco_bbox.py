"""Non-destructive COCO bbox clipping adapter for FleetVision Phase 04.5C.

Reads verified Roboflow COCO exports from the isolated raw external dataset area,
clips only right/bottom bounding-box overflow, writes cleaned annotation JSON to
``dataset/02_interim``, and never modifies raw sources, registry rows, YOLO
labels, dataset splits, or training artifacts.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REQUIRED_COCO_KEYS = {"images", "annotations", "categories"}
ALLOWED_REPAIR_REASONS = frozenset({"exceeds_image_width", "exceeds_image_height"})

REPAIR_LOG_COLUMNS = [
    "dataset_id",
    "split",
    "annotation_id",
    "image_id",
    "file_name",
    "image_width",
    "image_height",
    "old_x",
    "old_y",
    "old_width",
    "old_height",
    "old_x2",
    "old_y2",
    "new_x",
    "new_y",
    "new_width",
    "new_height",
    "new_x2",
    "new_y2",
    "clipped_right",
    "clipped_bottom",
    "repair_reasons",
    "input_annotation_sha256",
    "output_annotation_sha256",
]

SUMMARY_COLUMNS = [
    "dataset_id",
    "split",
    "image_count",
    "input_annotation_count",
    "valid_before_count",
    "invalid_before_count",
    "repaired_count",
    "dropped_count",
    "output_annotation_count",
    "invalid_after_count",
    "missing_image_count",
    "unexpected_invalid_count",
]

MANIFEST_COLUMNS = [
    "dataset_id",
    "split",
    "raw_image_root",
    "input_annotation_path",
    "input_annotation_sha256",
    "output_annotation_path",
    "output_annotation_sha256",
    "image_count",
    "input_annotation_count",
    "output_annotation_count",
    "repaired_count",
    "dropped_count",
    "invalid_after_count",
    "repair_policy",
    "lineage_status",
    "training_acceptance",
    "created_at_utc",
]


class BboxRepairError(RuntimeError):
    """Raised when an external COCO bbox repair gate fails."""


@dataclass(frozen=True)
class BboxRepairConfig:
    """Resolved configuration for one external COCO bbox repair run."""

    dataset_id: str
    raw_export_root: Path
    output_root: Path
    annotation_filename: str
    splits: tuple[str, ...]
    allowed_invalid_reasons: frozenset[str]
    preserve_segmentation: bool
    preserve_area: bool
    preserve_ids: bool
    drop_annotations: bool
    fail_on_unexpected_invalid_reason: bool
    allow_overwrite: bool
    expected_total_images: int
    expected_total_annotations: int
    expected_total_repaired: int
    expected_total_dropped: int
    expected_total_invalid_after: int
    expected_per_split: dict[str, dict[str, int]]
    lineage_status: str
    training_acceptance: str
    project_root: Path


@dataclass(frozen=True)
class SplitRepairResult:
    """Per-split repair outcome before promotion."""

    split: str
    repaired_payload: dict[str, Any]
    repair_log_rows: list[dict[str, Any]]
    summary_row: dict[str, Any]
    manifest_row: dict[str, Any]
    input_annotation_sha256: str
    output_annotation_sha256: str
    input_annotation_path: Path
    output_annotation_path: Path
    raw_image_root: Path


def find_project_root(start: Path | None = None) -> Path:
    """Find the FleetVision project root from a starting path."""
    current = (start or Path.cwd()).resolve()
    markers = ["PROJECT_CONTEXT_BRIEF.md", "src/fleetvision", "configs/data"]
    for path in [current, *current.parents]:
        if all((path / marker).exists() for marker in markers):
            return path
    return current


def resolve_path(path: str | Path, project_root: Path) -> Path:
    """Resolve a project-relative path."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else project_root / candidate


def to_repo_relative(path: Path, project_root: Path) -> str:
    """Return a repository-relative POSIX path string."""
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_bbox_repair_config(config_path: Path, project_root: Path | None = None) -> BboxRepairConfig:
    """Load bbox-repair YAML and resolve project-relative paths."""
    root = project_root or find_project_root(config_path.parent)
    if not config_path.is_file():
        raise BboxRepairError(f"config not found: {config_path}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    repair_policy = data.get("repair_policy", {}) or {}
    expected = data.get("expected", {}) or {}
    splits = tuple(str(value) for value in data.get("splits", []) or [])
    allowed = frozenset(
        str(value) for value in repair_policy.get("allowed_invalid_reasons", []) or []
    )

    required = ["dataset_id", "raw_export_root", "output_root", "annotation_filename"]
    missing = [key for key in required if not data.get(key)]
    if missing or not splits:
        raise BboxRepairError(f"config missing required values: {missing or ['splits']}")

    per_split_raw = expected.get("per_split", {}) or {}
    per_split = {
        str(split): {
            "images": int(values.get("images", 0)),
            "annotations": int(values.get("annotations", 0)),
            "repaired": int(values.get("repaired", 0)),
        }
        for split, values in per_split_raw.items()
    }

    return BboxRepairConfig(
        dataset_id=str(data["dataset_id"]),
        raw_export_root=resolve_path(str(data["raw_export_root"]), root),
        output_root=resolve_path(str(data["output_root"]), root),
        annotation_filename=str(data["annotation_filename"]),
        splits=splits,
        allowed_invalid_reasons=allowed,
        preserve_segmentation=bool(repair_policy.get("preserve_segmentation", True)),
        preserve_area=bool(repair_policy.get("preserve_area", True)),
        preserve_ids=bool(repair_policy.get("preserve_ids", True)),
        drop_annotations=bool(repair_policy.get("drop_annotations", False)),
        fail_on_unexpected_invalid_reason=bool(
            repair_policy.get("fail_on_unexpected_invalid_reason", True)
        ),
        allow_overwrite=bool(repair_policy.get("allow_overwrite", False)),
        expected_total_images=int(expected.get("total_images", 0)),
        expected_total_annotations=int(expected.get("total_annotations", 0)),
        expected_total_repaired=int(expected.get("total_repaired", 0)),
        expected_total_dropped=int(expected.get("total_dropped", 0)),
        expected_total_invalid_after=int(expected.get("total_invalid_after", 0)),
        expected_per_split=per_split,
        lineage_status=str(data.get("lineage_status", "")),
        training_acceptance=str(data.get("training_acceptance", "NOT_YET_APPROVED")),
        project_root=root,
    )


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return uppercase SHA256 for one file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    if not _is_number(value):
        return False
    numeric = float(value)
    return numeric == numeric and abs(numeric) != float("inf")


def classify_bbox_invalid_reasons(
    bbox: object,
    image_width: object,
    image_height: object,
) -> list[str]:
    """Return sorted invalid-reason codes for one COCO bbox; empty means valid."""
    reasons: list[str] = []

    if not isinstance(bbox, list) or len(bbox) != 4:
        return ["malformed_bbox"]

    if not all(_is_finite_number(value) for value in bbox):
        if not all(_is_number(value) for value in bbox):
            return ["non_numeric_bbox"]
        return ["non_finite_bbox"]

    if not _is_finite_number(image_width) or not _is_finite_number(image_height):
        return ["invalid_image_dimensions"]

    x, y, width, height = map(float, bbox)
    image_w = float(image_width)
    image_h = float(image_height)

    if image_w <= 0 or image_h <= 0:
        return ["invalid_image_dimensions"]
    if width <= 0:
        reasons.append("nonpositive_width")
    if height <= 0:
        reasons.append("nonpositive_height")
    if x < 0:
        reasons.append("negative_x")
    if y < 0:
        reasons.append("negative_y")
    if x + width > image_w + 1e-6:
        reasons.append("exceeds_image_width")
    if y + height > image_h + 1e-6:
        reasons.append("exceeds_image_height")

    return sorted(set(reasons))


def clip_bbox_to_image(
    bbox: list[int | float],
    image_width: int | float,
    image_height: int | float,
) -> list[int | float]:
    """Clip a COCO bbox to the image right/bottom boundaries."""
    x, y, width, height = map(float, bbox)
    old_x2 = x + width
    old_y2 = y + height
    new_x2 = min(old_x2, float(image_width))
    new_y2 = min(old_y2, float(image_height))
    new_width = new_x2 - x
    new_height = new_y2 - y
    return [x, y, new_width, new_height]


def _load_coco_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
        raise BboxRepairError(f"invalid COCO JSON: {path}") from exc
    if not isinstance(data, dict) or not REQUIRED_COCO_KEYS.issubset(data):
        raise BboxRepairError(f"COCO JSON missing required keys: {path}")
    return data


def _validate_image_files(images: list[dict[str, Any]], image_root: Path) -> int:
    """Return count of image records whose files are missing."""
    missing = 0
    for image in images:
        if not isinstance(image, dict):
            missing += 1
            continue
        file_name = str(image.get("file_name", "")).strip()
        if not file_name or not (image_root / file_name).is_file():
            missing += 1
    return missing


def _annotation_non_bbox_fields(annotation: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in annotation.items() if key != "bbox"}


def repair_coco_payload(
    payload: dict[str, Any],
    *,
    split: str,
    dataset_id: str,
    image_root: Path,
    repair_policy: BboxRepairConfig,
    input_annotation_sha256: str,
    output_annotation_sha256: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Repair one split payload and return cleaned payload plus report rows."""
    if repair_policy.drop_annotations:
        raise BboxRepairError("drop_annotations policy is not supported for Phase 04.5C")

    working = copy.deepcopy(payload)
    for collection_name in ("images", "annotations", "categories"):
        collection = working.get(collection_name)
        if not isinstance(collection, list):
            raise BboxRepairError(f"COCO {collection_name} must be a list")
        if any(not isinstance(item, dict) for item in collection):
            raise BboxRepairError(
                f"COCO {collection_name} contains non-object item"
            )

    images = working["images"]
    annotations = working["annotations"]
    image_lookup = {
        image.get("id"): image for image in images if "id" in image
    }

    missing_image_count = _validate_image_files(images, image_root)
    if missing_image_count:
        raise BboxRepairError(
            f"missing image file(s) in split={split}: count={missing_image_count}"
        )

    repair_log_rows: list[dict[str, Any]] = []
    valid_before = 0
    invalid_before = 0
    unexpected_invalid_count = 0
    repaired_count = 0

    for annotation in annotations:
        annotation_id = annotation.get("id")
        image_id = annotation.get("image_id")
        image = image_lookup.get(image_id)
        if image is None:
            raise BboxRepairError(
                f"missing image record: split={split} annotation_id={annotation_id}"
            )

        bbox = annotation.get("bbox")
        file_name = str(image.get("file_name", "")).strip()
        image_width = image.get("width")
        image_height = image.get("height")
        reasons = classify_bbox_invalid_reasons(bbox, image_width, image_height)

        if not reasons:
            valid_before += 1
            continue

        invalid_before += 1
        unexpected = [reason for reason in reasons if reason not in repair_policy.allowed_invalid_reasons]
        if unexpected:
            unexpected_invalid_count += 1
            if repair_policy.fail_on_unexpected_invalid_reason:
                raise BboxRepairError(
                    f"unexpected invalid bbox reason(s) in split={split} "
                    f"annotation_id={annotation_id}: {unexpected}"
                )
            continue

        original_fields = _annotation_non_bbox_fields(annotation)
        old_x, old_y, old_width, old_height = map(float, bbox)  # type: ignore[arg-type]
        clipped = clip_bbox_to_image(
            [old_x, old_y, old_width, old_height],
            float(image_width),  # type: ignore[arg-type]
            float(image_height),  # type: ignore[arg-type]
        )
        new_x, new_y, new_width, new_height = clipped
        new_x2 = new_x + float(new_width)
        new_y2 = new_y + float(new_height)

        if new_width <= 0 or new_height <= 0:
            raise BboxRepairError(
                f"clip produced non-positive bbox: split={split} annotation_id={annotation_id}"
            )

        after_reasons = classify_bbox_invalid_reasons(
            clipped,
            image_width,
            image_height,
        )
        if after_reasons:
            raise BboxRepairError(
                f"bbox still invalid after clip: split={split} annotation_id={annotation_id} "
                f"reasons={after_reasons}"
            )

        annotation["bbox"] = clipped
        repaired_count += 1

        if _annotation_non_bbox_fields(annotation) != original_fields:
            raise BboxRepairError(
                f"non-bbox annotation fields changed during repair: annotation_id={annotation_id}"
            )

        repair_log_rows.append(
            {
                "dataset_id": dataset_id,
                "split": split,
                "annotation_id": annotation_id,
                "image_id": image_id,
                "file_name": file_name,
                "image_width": image_width,
                "image_height": image_height,
                "old_x": old_x,
                "old_y": old_y,
                "old_width": old_width,
                "old_height": old_height,
                "old_x2": old_x + old_width,
                "old_y2": old_y + old_height,
                "new_x": new_x,
                "new_y": new_y,
                "new_width": new_width,
                "new_height": new_height,
                "new_x2": new_x2,
                "new_y2": new_y2,
                "clipped_right": "exceeds_image_width" in reasons,
                "clipped_bottom": "exceeds_image_height" in reasons,
                "repair_reasons": ",".join(reasons),
                "input_annotation_sha256": input_annotation_sha256,
                "output_annotation_sha256": output_annotation_sha256 or "",
            }
        )

    invalid_after = 0
    for annotation in annotations:
        image = image_lookup.get(annotation.get("image_id"))
        if image is None:
            invalid_after += 1
            continue
        if classify_bbox_invalid_reasons(
            annotation.get("bbox"),
            image.get("width"),
            image.get("height"),
        ):
            invalid_after += 1

    summary_row = {
        "dataset_id": dataset_id,
        "split": split,
        "image_count": len(images),
        "input_annotation_count": len(annotations),
        "valid_before_count": valid_before,
        "invalid_before_count": invalid_before,
        "repaired_count": repaired_count,
        "dropped_count": 0,
        "output_annotation_count": len(annotations),
        "invalid_after_count": invalid_after,
        "missing_image_count": missing_image_count,
        "unexpected_invalid_count": unexpected_invalid_count,
    }

    return working, repair_log_rows, summary_row


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns)
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    frame = frame[columns]
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def _validate_output_policy(output_root: Path, allow_overwrite: bool) -> None:
    if output_root.exists() and not allow_overwrite:
        raise BboxRepairError(
            f"output root already exists; explicit overwrite is required: {output_root}"
        )


def _process_split(
    config: BboxRepairConfig,
    split: str,
    *,
    created_at_utc: str,
) -> SplitRepairResult:
    raw_image_root = config.raw_export_root / split
    input_annotation_path = raw_image_root / config.annotation_filename
    if not input_annotation_path.is_file():
        raise BboxRepairError(f"input annotation JSON not found: {input_annotation_path}")

    input_hash = sha256_file(input_annotation_path)
    payload = _load_coco_json(input_annotation_path)
    output_annotation_path = (
        config.output_root / "cleaned_coco" / split / config.annotation_filename
    )

    repaired_payload, repair_log_rows, summary_row = repair_coco_payload(
        payload,
        split=split,
        dataset_id=config.dataset_id,
        image_root=raw_image_root,
        repair_policy=config,
        input_annotation_sha256=input_hash,
    )

    staging_json = Path(tempfile.mkdtemp()) / config.annotation_filename
    try:
        _write_json(staging_json, repaired_payload)
        output_hash = sha256_file(staging_json)
    finally:
        shutil.rmtree(staging_json.parent, ignore_errors=True)

    for row in repair_log_rows:
        row["output_annotation_sha256"] = output_hash

    manifest_row = {
        "dataset_id": config.dataset_id,
        "split": split,
        "raw_image_root": to_repo_relative(raw_image_root, config.project_root),
        "input_annotation_path": to_repo_relative(input_annotation_path, config.project_root),
        "input_annotation_sha256": input_hash,
        "output_annotation_path": to_repo_relative(output_annotation_path, config.project_root),
        "output_annotation_sha256": output_hash,
        "image_count": summary_row["image_count"],
        "input_annotation_count": summary_row["input_annotation_count"],
        "output_annotation_count": summary_row["output_annotation_count"],
        "repaired_count": summary_row["repaired_count"],
        "dropped_count": summary_row["dropped_count"],
        "invalid_after_count": summary_row["invalid_after_count"],
        "repair_policy": "clip_right_bottom_overflow",
        "lineage_status": config.lineage_status,
        "training_acceptance": config.training_acceptance,
        "created_at_utc": created_at_utc,
    }

    return SplitRepairResult(
        split=split,
        repaired_payload=repaired_payload,
        repair_log_rows=repair_log_rows,
        summary_row=summary_row,
        manifest_row=manifest_row,
        input_annotation_sha256=input_hash,
        output_annotation_sha256=output_hash,
        input_annotation_path=input_annotation_path,
        output_annotation_path=output_annotation_path,
        raw_image_root=raw_image_root,
    )


def _build_total_summary(
    config: BboxRepairConfig,
    split_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    totals = {
        "dataset_id": config.dataset_id,
        "split": "total",
        "image_count": 0,
        "input_annotation_count": 0,
        "valid_before_count": 0,
        "invalid_before_count": 0,
        "repaired_count": 0,
        "dropped_count": 0,
        "output_annotation_count": 0,
        "invalid_after_count": 0,
        "missing_image_count": 0,
        "unexpected_invalid_count": 0,
    }
    for row in split_rows:
        for key in totals:
            if key in {"dataset_id", "split"}:
                continue
            totals[key] += int(row[key])
    return totals


def _promote_transactionally(staged_to_final: dict[Path, Path]) -> None:
    """Promote staged files and remove every newly-created artifact on failure."""
    promoted: list[Path] = []
    created_directories: list[Path] = []
    try:
        for final_path in staged_to_final.values():
            missing_parents: list[Path] = []
            current = final_path.parent
            while not current.exists():
                missing_parents.append(current)
                current = current.parent
            for directory in reversed(missing_parents):
                directory.mkdir()
                created_directories.append(directory)

        for staged_path, final_path in staged_to_final.items():
            os.replace(staged_path, final_path)
            promoted.append(final_path)
    except Exception:
        for final_path in reversed(promoted):
            if final_path.exists():
                final_path.unlink()
        for directory in sorted(
            set(created_directories),
            key=lambda value: len(value.parts),
            reverse=True,
        ):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise


def build_external_coco_bbox_repair(
    config_path: Path,
    *,
    project_root: Path | None = None,
    now_utc: str | None = None,
) -> dict[str, Any]:
    """Run one staged, atomic external COCO bbox repair build."""
    root = project_root or find_project_root(config_path.parent)
    config = load_bbox_repair_config(config_path, root)
    _validate_output_policy(config.output_root, config.allow_overwrite)

    if not config.raw_export_root.is_dir():
        raise BboxRepairError(f"raw export root not found: {config.raw_export_root}")

    input_hashes_before = {
        split: sha256_file(config.raw_export_root / split / config.annotation_filename)
        for split in config.splits
    }

    created_at_utc = now_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if created_at_utc.endswith("+00:00"):
        created_at_utc = created_at_utc.replace("+00:00", "Z")

    split_results = [
        _process_split(config, split, created_at_utc=created_at_utc)
        for split in config.splits
    ]

    split_summary_rows = [result.summary_row for result in split_results]
    total_summary = _build_total_summary(config, split_summary_rows)
    summary_rows = split_summary_rows + [total_summary]

    for row in split_summary_rows:
        split = str(row["split"])
        expected = config.expected_per_split.get(split)
        if not expected:
            continue
        comparisons = (
            ("image_count", "images"),
            ("input_annotation_count", "annotations"),
            ("repaired_count", "repaired"),
        )
        for actual_key, expected_key in comparisons:
            expected_value = int(expected.get(expected_key, 0))
            actual_value = int(row[actual_key])
            if expected_value and actual_value != expected_value:
                raise BboxRepairError(
                    f"split={split} {actual_key} mismatch: "
                    f"expected={expected_value} actual={actual_value}"
                )

    if (
        config.expected_total_images
        and total_summary["image_count"] != config.expected_total_images
    ):
        raise BboxRepairError(
            "image_count mismatch: "
            f"expected={config.expected_total_images} "
            f"actual={total_summary['image_count']}"
        )
    repair_log_rows = [
        row for result in split_results for row in result.repair_log_rows
    ]
    manifest_rows = [result.manifest_row for result in split_results]

    if total_summary["repaired_count"] != config.expected_total_repaired:
        raise BboxRepairError(
            "repaired_count mismatch: "
            f"expected={config.expected_total_repaired} actual={total_summary['repaired_count']}"
        )
    if total_summary["dropped_count"] != config.expected_total_dropped:
        raise BboxRepairError(
            "dropped_count mismatch: "
            f"expected={config.expected_total_dropped} actual={total_summary['dropped_count']}"
        )
    if total_summary["invalid_after_count"] != config.expected_total_invalid_after:
        raise BboxRepairError(
            "invalid_after_count mismatch: "
            f"expected={config.expected_total_invalid_after} actual={total_summary['invalid_after_count']}"
        )
    if total_summary["output_annotation_count"] != config.expected_total_annotations:
        raise BboxRepairError(
            "output_annotation_count mismatch: "
            f"expected={config.expected_total_annotations} "
            f"actual={total_summary['output_annotation_count']}"
        )

    staging_parent = config.output_root.parent
    staging_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".bbox_repair_staging_{config.dataset_id}_",
        dir=staging_parent,
    ) as temporary_directory:
        staging_root = Path(temporary_directory)
        staged_to_final: dict[Path, Path] = {}

        for result in split_results:
            staged_json = (
                staging_root
                / "cleaned_coco"
                / result.split
                / config.annotation_filename
            )
            _write_json(staged_json, result.repaired_payload)
            if sha256_file(staged_json) != result.output_annotation_sha256:
                raise BboxRepairError(
                    f"staged output SHA256 mismatch for split={result.split}"
                )
            staged_to_final[staged_json] = result.output_annotation_path

        staged_log = staging_root / "bbox_repair_log.csv"
        staged_summary = staging_root / "bbox_repair_summary.csv"
        staged_manifest = staging_root / "cleaned_annotation_manifest.csv"
        _write_csv(staged_log, repair_log_rows, REPAIR_LOG_COLUMNS)
        _write_csv(staged_summary, summary_rows, SUMMARY_COLUMNS)
        _write_csv(staged_manifest, manifest_rows, MANIFEST_COLUMNS)

        staged_to_final[staged_log] = config.output_root / "bbox_repair_log.csv"
        staged_to_final[staged_summary] = config.output_root / "bbox_repair_summary.csv"
        staged_to_final[staged_manifest] = config.output_root / "cleaned_annotation_manifest.csv"

        for split, expected_hash in input_hashes_before.items():
            current_hash = sha256_file(
                config.raw_export_root / split / config.annotation_filename
            )
            if current_hash != expected_hash:
                raise BboxRepairError(
                    f"raw input annotation SHA256 changed for split={split}"
                )

        _promote_transactionally(staged_to_final)

    for split, expected_hash in input_hashes_before.items():
        current_hash = sha256_file(config.raw_export_root / split / config.annotation_filename)
        if current_hash != expected_hash:
            shutil.rmtree(config.output_root, ignore_errors=True)
            raise BboxRepairError(f"raw input annotation SHA256 changed for split={split}")

    return {
        "gate_classification": "EXTERNAL_COCO_BBOX_REPAIR_VERIFIED",
        "dataset_id": config.dataset_id,
        "summary": total_summary,
        "repair_log_rows": len(repair_log_rows),
        "manifest_rows": len(manifest_rows),
        "output_root": config.output_root,
        "raw_source_modified": False,
    }
