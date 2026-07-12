"""Non-destructive COCO category canonicalization for FleetVision Phase 04.5F."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


SPLIT_AUDIT_COLUMNS = [
    "split",
    "source_json_sha256",
    "canonical_json_sha256",
    "source_categories_json",
    "source_category_annotation_counts_json",
    "source_category_image_counts_json",
    "alias_mapping_json",
    "unknown_categories_json",
    "images_before",
    "images_after",
    "annotations_before",
    "annotations_after",
    "bbox_checksum_before",
    "bbox_checksum_after",
    "transformation_error_count",
]
ERROR_COLUMNS = ["split", "error_code", "error_message"]


class CanonicalizationError(RuntimeError):
    """Base error for category canonicalization."""


class CanonicalizationConfigError(CanonicalizationError):
    """Invalid configuration or unsafe path."""


class CanonicalizationInputError(CanonicalizationError):
    """Invalid COCO source or unknown semantic category."""


class CanonicalizationOutputError(CanonicalizationError):
    """Staging or atomic promotion failure."""


@dataclass(frozen=True)
class CanonicalizationConfig:
    """Resolved category-normalization configuration."""

    dataset_id: str
    project_root: Path
    source_root: Path
    output_root: Path
    annotation_filename: str
    splits: tuple[str, ...]
    source_aliases: tuple[str, ...]
    source_json_sha256: dict[str, str]
    canonical_id: int
    canonical_name: str
    canonical_supercategory: str
    expected_total_images: int
    expected_total_annotations: int
    expected_per_split: dict[str, dict[str, int]]
    overwrite_existing_output: bool
    write_error_report_on_failure: bool


@dataclass(frozen=True)
class CanonicalizedPayload:
    """One canonicalized COCO payload plus preservation evidence."""

    payload: dict[str, Any]
    source_category_distribution: dict[str, int]
    source_category_image_counts: dict[str, int]
    alias_mapping: dict[str, str]
    unknown_categories: tuple[str, ...]
    images_before: int
    images_after: int
    annotations_before: int
    annotations_after: int
    bbox_checksum_before: str
    bbox_checksum_after: str


@dataclass(frozen=True)
class CanonicalizationBuildResult:
    """Compact dry-run or execution result."""

    dataset_id: str
    executed: bool
    output_root: Path
    total_images: int
    total_annotations: int
    canonical_class_count: int
    gate_classification: str


TOP_KEYS = {
    "dataset_id",
    "source_root",
    "output_root",
    "annotation_filename",
    "splits",
    "source_aliases",
    "source_json_sha256",
    "canonical_category",
    "expected",
    "execution",
}
CANONICAL_KEYS = {"id", "name", "supercategory"}
EXPECTED_KEYS = {"total_images", "total_annotations", "per_split"}
PER_SPLIT_KEYS = {"images", "annotations"}
EXECUTION_KEYS = {"overwrite_existing_output", "write_error_report_on_failure"}


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return uppercase streaming SHA256."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _validate_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing or unknown:
        raise CanonicalizationConfigError(
            f"{label} keys invalid: missing={missing}; unknown={unknown}"
        )


def _positive_int(value: Any, label: str, *, allow_zero: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CanonicalizationConfigError(f"{label} must be an integer")
    if value < 0 or (value == 0 and not allow_zero):
        raise CanonicalizationConfigError(f"{label} must be positive")
    return value


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise CanonicalizationConfigError(f"{label} must be boolean")
    return value


def _sha256_contract(value: Any, label: str) -> str:
    result = str(value).strip().upper()
    if len(result) != 64 or any(character not in "0123456789ABCDEF" for character in result):
        raise CanonicalizationConfigError(f"{label} must be 64 hexadecimal characters")
    return result


def _path(value: Any, root: Path, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CanonicalizationConfigError(f"{label} must be a non-empty path string")
    candidate = Path(value)
    return candidate if candidate.is_absolute() else root / candidate


def load_canonicalization_config(
    config_path: Path,
    *,
    project_root: Path,
) -> CanonicalizationConfig:
    """Load and strictly validate the normalization YAML."""

    if not config_path.is_file():
        raise CanonicalizationConfigError(f"config not found: {config_path}")
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise CanonicalizationConfigError(f"invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise CanonicalizationConfigError("config root must be a mapping")
    _validate_exact_keys(data, TOP_KEYS, "root")

    canonical = data["canonical_category"]
    expected = data["expected"]
    execution = data["execution"]
    if not isinstance(canonical, dict) or not isinstance(expected, dict) or not isinstance(execution, dict):
        raise CanonicalizationConfigError("nested config sections must be mappings")
    _validate_exact_keys(canonical, CANONICAL_KEYS, "canonical_category")
    _validate_exact_keys(expected, EXPECTED_KEYS, "expected")
    _validate_exact_keys(execution, EXECUTION_KEYS, "execution")

    dataset_id = data["dataset_id"]
    annotation_filename = data["annotation_filename"]
    splits = data["splits"]
    aliases = data["source_aliases"]
    source_hashes = data["source_json_sha256"]
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise CanonicalizationConfigError("dataset_id must be a non-empty string")
    if not isinstance(annotation_filename, str) or not annotation_filename.strip():
        raise CanonicalizationConfigError("annotation_filename must be a non-empty string")
    if not isinstance(splits, list) or not splits or any(not isinstance(item, str) or not item for item in splits):
        raise CanonicalizationConfigError("splits must be a non-empty list of strings")
    if len(splits) != len(set(splits)):
        raise CanonicalizationConfigError("splits must be unique")
    if not isinstance(aliases, list) or not aliases or any(not isinstance(item, str) or not item for item in aliases):
        raise CanonicalizationConfigError("source_aliases must be a non-empty list of strings")
    if len(aliases) != len(set(aliases)):
        raise CanonicalizationConfigError("source_aliases must be unique")
    if not isinstance(source_hashes, dict) or set(source_hashes) != set(splits):
        raise CanonicalizationConfigError("source_json_sha256 keys must exactly match splits")
    canonical_id = _positive_int(canonical["id"], "canonical_category.id", allow_zero=True)
    canonical_name = canonical["name"]
    canonical_supercategory = canonical["supercategory"]
    if not isinstance(canonical_name, str) or not canonical_name.strip():
        raise CanonicalizationConfigError("canonical_category.name must be non-empty")
    if not isinstance(canonical_supercategory, str) or not canonical_supercategory.strip():
        raise CanonicalizationConfigError("canonical_category.supercategory must be non-empty")

    per_split_raw = expected["per_split"]
    if not isinstance(per_split_raw, dict) or set(per_split_raw) != set(splits):
        raise CanonicalizationConfigError("expected.per_split keys must exactly match splits")
    per_split: dict[str, dict[str, int]] = {}
    for split in splits:
        values = per_split_raw[split]
        if not isinstance(values, dict):
            raise CanonicalizationConfigError(f"expected.per_split.{split} must be a mapping")
        _validate_exact_keys(values, PER_SPLIT_KEYS, f"expected.per_split.{split}")
        per_split[split] = {
            "images": _positive_int(values["images"], f"{split}.images", allow_zero=True),
            "annotations": _positive_int(values["annotations"], f"{split}.annotations", allow_zero=True),
        }

    root = project_root.resolve()
    source_root = _path(data["source_root"], root, "source_root").resolve()
    output_root = _path(data["output_root"], root, "output_root").resolve()
    approved_parent = (root / "dataset/02_interim").resolve()
    try:
        source_root.relative_to(approved_parent)
        output_root.relative_to(approved_parent)
    except ValueError as exc:
        raise CanonicalizationConfigError(
            "source_root and output_root must be under dataset/02_interim"
        ) from exc
    if source_root == output_root or source_root in output_root.parents or output_root in source_root.parents:
        raise CanonicalizationConfigError("source_root and output_root must be separate sibling trees")

    return CanonicalizationConfig(
        dataset_id=dataset_id.strip(),
        project_root=root,
        source_root=source_root,
        output_root=output_root,
        annotation_filename=annotation_filename.strip(),
        splits=tuple(splits),
        source_aliases=tuple(aliases),
        source_json_sha256={
            split: _sha256_contract(source_hashes[split], f"source_json_sha256.{split}")
            for split in splits
        },
        canonical_id=canonical_id,
        canonical_name=canonical_name.strip(),
        canonical_supercategory=canonical_supercategory.strip(),
        expected_total_images=_positive_int(expected["total_images"], "expected.total_images", allow_zero=True),
        expected_total_annotations=_positive_int(expected["total_annotations"], "expected.total_annotations", allow_zero=True),
        expected_per_split=per_split,
        overwrite_existing_output=_boolean(execution["overwrite_existing_output"], "overwrite_existing_output"),
        write_error_report_on_failure=_boolean(execution["write_error_report_on_failure"], "write_error_report_on_failure"),
    )


def _validate_collection(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key)
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise CanonicalizationInputError(f"COCO {key} must be a list of objects")
    return value


def _bbox_evidence(annotations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": annotation.get("id"),
            "image_id": annotation.get("image_id"),
            "bbox": annotation.get("bbox"),
        }
        for annotation in annotations
    ]


def canonicalize_coco_payload(
    payload: dict[str, Any],
    *,
    source_aliases: tuple[str, ...],
    canonical_id: int,
    canonical_name: str,
    canonical_supercategory: str,
) -> CanonicalizedPayload:
    """Canonicalize approved aliases while preserving all non-category data."""

    if not isinstance(payload, dict):
        raise CanonicalizationInputError("COCO root must be an object")
    images = _validate_collection(payload, "images")
    annotations = _validate_collection(payload, "annotations")
    categories = _validate_collection(payload, "categories")
    if not categories:
        raise CanonicalizationInputError("COCO categories cannot be empty")

    category_by_id: dict[Any, str] = {}
    unknown: list[str] = []
    for category in categories:
        category_id = category.get("id")
        name = str(category.get("name", "")).strip()
        if category_id in category_by_id or not name:
            raise CanonicalizationInputError(f"invalid or duplicate category: {category}")
        category_by_id[category_id] = name
        if name not in source_aliases:
            unknown.append(name)
    if unknown:
        raise CanonicalizationInputError(
            f"unknown category names: {sorted(set(unknown))}"
        )

    image_ids = [image.get("id") for image in images]
    annotation_ids = [annotation.get("id") for annotation in annotations]
    if len(image_ids) != len(set(image_ids)):
        raise CanonicalizationInputError("duplicate image IDs")
    if len(annotation_ids) != len(set(annotation_ids)):
        raise CanonicalizationInputError("duplicate annotation IDs")

    annotation_counts: Counter[str] = Counter()
    image_sets: dict[str, set[Any]] = defaultdict(set)
    for annotation in annotations:
        category_id = annotation.get("category_id")
        if category_id not in category_by_id:
            raise CanonicalizationInputError(
                f"annotation references unknown category_id: {annotation.get('id')}"
            )
        name = category_by_id[category_id]
        annotation_counts[name] += 1
        image_sets[name].add(annotation.get("image_id"))

    working = copy.deepcopy(payload)
    working["categories"] = [
        {
            "id": canonical_id,
            "name": canonical_name,
            "supercategory": canonical_supercategory,
        }
    ]
    for annotation in working["annotations"]:
        annotation["category_id"] = canonical_id

    source_bbox = _bbox_evidence(annotations)
    canonical_bbox = _bbox_evidence(working["annotations"])
    bbox_before = _sha256_json(source_bbox)
    bbox_after = _sha256_json(canonical_bbox)
    if bbox_before != bbox_after:
        raise CanonicalizationInputError("bbox geometry changed during canonicalization")
    if len(working["images"]) != len(images) or len(working["annotations"]) != len(annotations):
        raise CanonicalizationInputError("image or annotation count changed")
    for source, canonicalized in zip(annotations, working["annotations"], strict=True):
        source_without_category = {key: value for key, value in source.items() if key != "category_id"}
        canonical_without_category = {
            key: value for key, value in canonicalized.items() if key != "category_id"
        }
        if source_without_category != canonical_without_category:
            raise CanonicalizationInputError(
                f"non-category annotation data changed: annotation_id={source.get('id')}"
            )

    return CanonicalizedPayload(
        payload=working,
        source_category_distribution={
            alias: annotation_counts.get(alias, 0) for alias in source_aliases
        },
        source_category_image_counts={
            alias: len(image_sets.get(alias, set())) for alias in source_aliases
        },
        alias_mapping={alias: canonical_name for alias in source_aliases},
        unknown_categories=tuple(),
        images_before=len(images),
        images_after=len(working["images"]),
        annotations_before=len(annotations),
        annotations_after=len(working["annotations"]),
        bbox_checksum_before=bbox_before,
        bbox_checksum_after=bbox_after,
    )


def _read_payload(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CanonicalizationInputError(f"source annotation missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CanonicalizationInputError(f"invalid COCO JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CanonicalizationInputError(f"COCO root must be an object: {path}")
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _promote(staging: Path, output: Path, *, overwrite: bool) -> None:
    backup: Path | None = None
    try:
        if output.exists():
            if not overwrite:
                raise CanonicalizationOutputError(f"output already exists: {output}")
            backup = Path(tempfile.mkdtemp(prefix=f".{output.name}.backup-", dir=output.parent))
            backup.rmdir()
            os.replace(output, backup)
        os.replace(staging, output)
        if backup is not None:
            shutil.rmtree(backup, ignore_errors=True)
    except CanonicalizationOutputError:
        raise
    except Exception as exc:
        if backup is not None and backup.exists() and not output.exists():
            os.replace(backup, output)
        raise CanonicalizationOutputError(f"atomic promotion failed: {exc}") from exc


def build_canonical_coco(
    config: CanonicalizationConfig,
    *,
    execute: bool,
    overwrite: bool = False,
    now_utc: str | None = None,
) -> CanonicalizationBuildResult:
    """Validate or build deterministic canonical COCO outputs."""

    if config.output_root.exists() and execute and not overwrite:
        raise CanonicalizationOutputError(f"output already exists: {config.output_root}")

    split_results: dict[str, tuple[Path, str, dict[str, Any], CanonicalizedPayload]] = {}
    total_images = 0
    total_annotations = 0
    for split in config.splits:
        source_path = config.source_root / split / config.annotation_filename
        source_hash = sha256_file(source_path) if source_path.is_file() else ""
        if source_hash != config.source_json_sha256[split]:
            raise CanonicalizationInputError(
                f"source cleaned COCO does not match approved SHA256: split={split} "
                f"expected={config.source_json_sha256[split]} actual={source_hash or 'MISSING'}"
            )
        payload = _read_payload(source_path)
        normalized = canonicalize_coco_payload(
            payload,
            source_aliases=config.source_aliases,
            canonical_id=config.canonical_id,
            canonical_name=config.canonical_name,
            canonical_supercategory=config.canonical_supercategory,
        )
        expected = config.expected_per_split[split]
        if normalized.images_before != expected["images"]:
            raise CanonicalizationInputError(
                f"{split} image count mismatch: expected={expected['images']} actual={normalized.images_before}"
            )
        if normalized.annotations_before != expected["annotations"]:
            raise CanonicalizationInputError(
                f"{split} annotation count mismatch: expected={expected['annotations']} actual={normalized.annotations_before}"
            )
        total_images += normalized.images_before
        total_annotations += normalized.annotations_before
        split_results[split] = (source_path, source_hash, payload, normalized)

    if total_images != config.expected_total_images:
        raise CanonicalizationInputError(
            f"total image count mismatch: expected={config.expected_total_images} actual={total_images}"
        )
    if total_annotations != config.expected_total_annotations:
        raise CanonicalizationInputError(
            f"total annotation count mismatch: expected={config.expected_total_annotations} actual={total_annotations}"
        )
    if not execute:
        return CanonicalizationBuildResult(
            dataset_id=config.dataset_id,
            executed=False,
            output_root=config.output_root,
            total_images=total_images,
            total_annotations=total_annotations,
            canonical_class_count=1,
            gate_classification="COCO_CATEGORY_CANONICALIZATION_PREFLIGHT_VALIDATED",
        )

    config.output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{config.output_root.name}.staging-", dir=config.output_root.parent)
    )
    try:
        audits: list[dict[str, Any]] = []
        canonical_hashes: dict[str, str] = {}
        source_hashes: dict[str, str] = {}
        for split in config.splits:
            source_path, source_hash, payload, normalized = split_results[split]
            canonical_path = staging / split / config.annotation_filename
            _write_json(canonical_path, normalized.payload)
            canonical_hash = sha256_file(canonical_path)
            canonical_hashes[split] = canonical_hash
            source_hashes[split] = source_hash
            audits.append(
                {
                    "split": split,
                    "source_json_sha256": source_hash,
                    "canonical_json_sha256": canonical_hash,
                    "source_categories_json": json.dumps(payload["categories"], ensure_ascii=False, sort_keys=True),
                    "source_category_annotation_counts_json": json.dumps(normalized.source_category_distribution, ensure_ascii=False, sort_keys=True),
                    "source_category_image_counts_json": json.dumps(normalized.source_category_image_counts, ensure_ascii=False, sort_keys=True),
                    "alias_mapping_json": json.dumps(normalized.alias_mapping, ensure_ascii=False, sort_keys=True),
                    "unknown_categories_json": "[]",
                    "images_before": normalized.images_before,
                    "images_after": normalized.images_after,
                    "annotations_before": normalized.annotations_before,
                    "annotations_after": normalized.annotations_after,
                    "bbox_checksum_before": normalized.bbox_checksum_before,
                    "bbox_checksum_after": normalized.bbox_checksum_after,
                    "transformation_error_count": 0,
                }
            )
        _write_csv(staging / "canonicalization_split_audit.csv", audits, SPLIT_AUDIT_COLUMNS)
        _write_csv(staging / "canonicalization_errors.csv", [], ERROR_COLUMNS)
        timestamp = now_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        verification = {
            "dataset_id": config.dataset_id,
            "gate_classification": "COCO_CATEGORY_CANONICALIZATION_VERIFIED",
            "created_at_utc": timestamp,
            "source_root": config.source_root.relative_to(config.project_root).as_posix(),
            "output_root": config.output_root.relative_to(config.project_root).as_posix(),
            "source_aliases": list(config.source_aliases),
            "canonical_category": {
                "id": config.canonical_id,
                "name": config.canonical_name,
                "supercategory": config.canonical_supercategory,
            },
            "source_json_sha256": source_hashes,
            "canonical_json_sha256": canonical_hashes,
            "total_images_before": total_images,
            "total_images_after": total_images,
            "total_annotations_before": total_annotations,
            "total_annotations_after": total_annotations,
            "bbox_geometry_preserved": all(
                row["bbox_checksum_before"] == row["bbox_checksum_after"] for row in audits
            ),
            "unknown_categories": [],
            "transformation_error_count": 0,
            "source_cleaned_coco_modified": False,
            "raw_dataset_modified": False,
            "registry_modified": False,
            "protected_external_assets_modified": False,
            "production_deduplication_modified": False,
            "yolo_labels_created": False,
            "dataset_split_materialized": False,
            "model_training_started": False,
            "training_acceptance": "NOT_YET_APPROVED",
        }
        _write_json(staging / "canonicalization_verification.json", verification)
        for split, (source_path, expected_hash, _, _) in split_results.items():
            if sha256_file(source_path) != expected_hash:
                raise CanonicalizationInputError(
                    f"source cleaned COCO changed during build: split={split}"
                )
        _promote(staging, config.output_root, overwrite=overwrite)
    except CanonicalizationError:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(staging, ignore_errors=True)
        raise CanonicalizationOutputError(str(exc)) from exc

    return CanonicalizationBuildResult(
        dataset_id=config.dataset_id,
        executed=True,
        output_root=config.output_root,
        total_images=total_images,
        total_annotations=total_annotations,
        canonical_class_count=1,
        gate_classification="COCO_CATEGORY_CANONICALIZATION_VERIFIED",
    )
