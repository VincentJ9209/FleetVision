"""Canonical COCO and group-safe split balance QA for FleetVision Phase 04.5F."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import statistics
import tempfile
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


PLAN_REQUIRED_COLUMNS = {
    "record_id",
    "canonical_source_key",
    "original_split",
    "assigned_split",
    "family_image_count",
    "is_family_medoid",
    "include_in_model_dataset",
    "plan_role",
    "image_id",
    "relative_image_path",
    "sha256",
    "width",
    "height",
}


class AnnotationQaError(RuntimeError):
    """Raised when a structural annotation or split-plan Gate fails."""


@dataclass(frozen=True)
class AnnotationQaConfig:
    """Resolved canonical annotation QA configuration."""

    dataset_id: str
    project_root: Path
    canonical_coco_root: Path
    annotation_filename: str
    splits: tuple[str, ...]
    class_mapping_path: Path
    class_mapping_sha256: str
    split_plan_zip_sha256: str
    canonical_coco_sha256: dict[str, str]
    canonical_id: int
    canonical_name: str
    canonical_supercategory: str
    expected_source_images: int
    expected_source_annotations: int
    expected_source_families: int
    expected_family_leakage: int
    expected_model_included_images: int
    expected_excluded_variants: int
    expected_per_split_model_images: dict[str, int]
    review_sample_size: int


@dataclass(frozen=True)
class PlanEvidence:
    """Verified group-safe split-plan evidence."""

    rows: list[dict[str, str]]
    summary: dict[str, Any]
    path: Path
    sha256: str
    family_count: int
    family_leakage_count: int
    included_count: int
    excluded_count: int
    split_source_counts: dict[str, int]
    split_included_counts: dict[str, int]


@dataclass(frozen=True)
class CocoSplit:
    """Validated canonical COCO split."""

    split: str
    path: Path
    sha256: str
    images: list[dict[str, Any]]
    annotations: list[dict[str, Any]]
    categories: list[dict[str, Any]]
    image_by_file: dict[str, dict[str, Any]]
    annotations_by_image: dict[int, list[dict[str, Any]]]
    category_by_id: dict[int, str]


@dataclass(frozen=True)
class AnnotationQaResult:
    """Formal annotation QA outcome."""

    classification: str
    output_root: Path
    source_images: int
    source_annotations: int
    model_included_images: int
    excluded_correlated_eval_variants: int
    source_families: int
    family_leakage_count: int
    invalid_bbox_count: int
    unresolved_plan_to_coco_joins: int
    unannotated_included_images: int
    annotation_count_inconsistent_families: int
    targeted_visual_review_items: int


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise AnnotationQaError(f"invalid integer {label}: {value!r}")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise AnnotationQaError(f"invalid integer {label}: {value!r}") from exc


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise AnnotationQaError(f"invalid number {label}: {value!r}")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise AnnotationQaError(f"invalid number {label}: {value!r}") from exc
    if not math.isfinite(result):
        raise AnnotationQaError(f"non-finite number {label}: {value!r}")
    return result


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _pct(count: int, total: int) -> float:
    return round(100.0 * count / total, 6) if total else 0.0


def _sha256_contract(value: Any, label: str) -> str:
    result = str(value).strip().upper()
    if len(result) != 64 or any(character not in "0123456789ABCDEF" for character in result):
        raise AnnotationQaError(f"{label} must be 64 hexadecimal characters")
    return result


def load_annotation_qa_config(
    config_path: Path,
    *,
    project_root: Path,
) -> AnnotationQaConfig:
    """Load the canonical-only QA contract."""

    if not config_path.is_file():
        raise AnnotationQaError(f"config not found: {config_path}")
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise AnnotationQaError(f"invalid QA YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise AnnotationQaError("QA config root must be a mapping")
    expected_top = {
        "dataset_id",
        "canonical_coco_root",
        "annotation_filename",
        "splits",
        "class_mapping_path",
        "class_mapping_sha256",
        "split_plan_zip_sha256",
        "canonical_coco_sha256",
        "canonical_category",
        "expected",
        "review_sample_size",
    }
    if set(data) != expected_top:
        raise AnnotationQaError(
            f"QA config keys invalid: missing={sorted(expected_top-set(data))} unknown={sorted(set(data)-expected_top)}"
        )
    canonical = data["canonical_category"]
    expected = data["expected"]
    if not isinstance(canonical, dict) or set(canonical) != {"id", "name", "supercategory"}:
        raise AnnotationQaError("canonical_category keys are invalid")
    expected_keys = {
        "source_images",
        "source_annotations",
        "source_families",
        "family_leakage",
        "model_included_images",
        "excluded_correlated_eval_variants",
        "per_split_model_images",
    }
    if not isinstance(expected, dict) or set(expected) != expected_keys:
        raise AnnotationQaError("expected keys are invalid")
    splits = data["splits"]
    if not isinstance(splits, list) or not splits or len(splits) != len(set(splits)):
        raise AnnotationQaError("splits must be a unique non-empty list")
    split_model = expected["per_split_model_images"]
    if not isinstance(split_model, dict) or set(split_model) != set(splits):
        raise AnnotationQaError("per_split_model_images must match splits")
    canonical_hashes = data["canonical_coco_sha256"]
    if not isinstance(canonical_hashes, dict) or set(canonical_hashes) != set(splits):
        raise AnnotationQaError("canonical_coco_sha256 keys must match splits")
    root = project_root.resolve()

    def resolve(value: Any, label: str) -> Path:
        if not isinstance(value, str) or not value.strip():
            raise AnnotationQaError(f"{label} must be a non-empty path")
        path = Path(value)
        return (path if path.is_absolute() else root / path).resolve()

    canonical_root = resolve(data["canonical_coco_root"], "canonical_coco_root")
    try:
        canonical_root.relative_to((root / "dataset/02_interim").resolve())
    except ValueError as exc:
        raise AnnotationQaError("canonical_coco_root must be under dataset/02_interim") from exc
    mapping_hash = _sha256_contract(data["class_mapping_sha256"], "class_mapping_sha256")
    return AnnotationQaConfig(
        dataset_id=str(data["dataset_id"]).strip(),
        project_root=root,
        canonical_coco_root=canonical_root,
        annotation_filename=str(data["annotation_filename"]).strip(),
        splits=tuple(str(value) for value in splits),
        class_mapping_path=resolve(data["class_mapping_path"], "class_mapping_path"),
        class_mapping_sha256=mapping_hash,
        split_plan_zip_sha256=_sha256_contract(
            data["split_plan_zip_sha256"], "split_plan_zip_sha256"
        ),
        canonical_coco_sha256={
            split: _sha256_contract(
                canonical_hashes[split], f"canonical_coco_sha256.{split}"
            )
            for split in splits
        },
        canonical_id=_integer(canonical["id"], "canonical_category.id"),
        canonical_name=str(canonical["name"]).strip(),
        canonical_supercategory=str(canonical["supercategory"]).strip(),
        expected_source_images=_integer(expected["source_images"], "source_images"),
        expected_source_annotations=_integer(expected["source_annotations"], "source_annotations"),
        expected_source_families=_integer(expected["source_families"], "source_families"),
        expected_family_leakage=_integer(expected["family_leakage"], "family_leakage"),
        expected_model_included_images=_integer(expected["model_included_images"], "model_included_images"),
        expected_excluded_variants=_integer(expected["excluded_correlated_eval_variants"], "excluded_correlated_eval_variants"),
        expected_per_split_model_images={key: _integer(value, key) for key, value in split_model.items()},
        review_sample_size=_integer(data["review_sample_size"], "review_sample_size"),
    )


def _read_csv_bytes(payload: bytes) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline=""))
    if reader.fieldnames is None:
        raise AnnotationQaError("ZIP CSV has no header")
    return list(reader.fieldnames), [dict(row) for row in reader]


def verify_plan_zip(plan_zip: Path, config: AnnotationQaConfig) -> PlanEvidence:
    """Verify the immutable 04.5F-7 ZIP and its exact family assignment."""

    if not plan_zip.is_file():
        raise AnnotationQaError(f"split-plan ZIP missing: {plan_zip}")
    actual_zip_hash = sha256_file(plan_zip)
    if actual_zip_hash != config.split_plan_zip_sha256:
        raise AnnotationQaError(
            "split-plan ZIP does not match approved SHA256: "
            f"expected={config.split_plan_zip_sha256} actual={actual_zip_hash}"
        )
    try:
        archive = zipfile.ZipFile(plan_zip)
    except zipfile.BadZipFile as exc:
        raise AnnotationQaError(f"invalid split-plan ZIP: {plan_zip}") from exc
    with archive:
        bad = archive.testzip()
        if bad:
            raise AnnotationQaError(f"split-plan ZIP CRC failure: {bad}")
        required = {
            "gate_result.json",
            "evidence_manifest.csv",
            "group_safe_split_evidence/image_split_plan.csv",
            "group_safe_split_evidence/group_safe_split_plan_summary.json",
        }
        names = set(archive.namelist())
        missing = sorted(required - names)
        if missing:
            raise AnnotationQaError(f"split-plan ZIP missing entries: {missing}")
        gate = json.loads(archive.read("gate_result.json").decode("utf-8-sig"))
        if gate.get("outcome") != "PASS" or gate.get("classification") != "GROUP_SAFE_SPLIT_PLAN_CREATED_PENDING_ANNOTATION_QA":
            raise AnnotationQaError("split-plan Gate is not the accepted pending-QA result")
        manifest_columns, manifest_rows = _read_csv_bytes(archive.read("evidence_manifest.csv"))
        if manifest_columns != ["relative_path", "size_bytes", "sha256"]:
            raise AnnotationQaError("split-plan manifest schema mismatch")
        for row in manifest_rows:
            name = row["relative_path"]
            if name not in names:
                raise AnnotationQaError(f"manifest entry missing from ZIP: {name}")
            payload = archive.read(name)
            if len(payload) != _integer(row["size_bytes"], f"{name}.size"):
                raise AnnotationQaError(f"manifest size mismatch: {name}")
            if hashlib.sha256(payload).hexdigest().upper() != row["sha256"].strip().upper():
                raise AnnotationQaError(f"manifest SHA256 mismatch: {name}")
        plan_columns, rows = _read_csv_bytes(
            archive.read("group_safe_split_evidence/image_split_plan.csv")
        )
        missing_columns = sorted(PLAN_REQUIRED_COLUMNS - set(plan_columns))
        if missing_columns:
            raise AnnotationQaError(f"split plan missing columns: {missing_columns}")
        summary = json.loads(
            archive.read(
                "group_safe_split_evidence/group_safe_split_plan_summary.json"
            ).decode("utf-8-sig")
        )

    if len(rows) != config.expected_source_images:
        raise AnnotationQaError(
            f"split-plan row count mismatch: expected={config.expected_source_images} actual={len(rows)}"
        )
    record_ids: set[str] = set()
    family_splits: dict[str, set[str]] = defaultdict(set)
    split_source_counts: Counter[str] = Counter()
    split_included_counts: Counter[str] = Counter()
    included = 0
    for row in rows:
        record_id = row["record_id"].strip()
        family = row["canonical_source_key"].strip()
        original = row["original_split"].strip()
        assigned = row["assigned_split"].strip()
        if not record_id or record_id in record_ids:
            raise AnnotationQaError(f"duplicate or empty record_id: {record_id!r}")
        record_ids.add(record_id)
        if not family or original not in config.splits or assigned not in config.splits:
            raise AnnotationQaError(f"invalid family/split in plan: {record_id}")
        family_splits[family].add(assigned)
        split_source_counts[assigned] += 1
        if _truthy(row["include_in_model_dataset"]):
            included += 1
            split_included_counts[assigned] += 1
    leakage = sum(len(values) != 1 for values in family_splits.values())
    if leakage != config.expected_family_leakage:
        raise AnnotationQaError(
            f"family leakage mismatch: expected={config.expected_family_leakage} actual={leakage}"
        )
    if len(family_splits) != config.expected_source_families:
        raise AnnotationQaError(
            f"family count mismatch: expected={config.expected_source_families} actual={len(family_splits)}"
        )
    excluded = len(rows) - included
    if included != config.expected_model_included_images or excluded != config.expected_excluded_variants:
        raise AnnotationQaError(
            f"model inclusion counts mismatch: included={included} excluded={excluded}"
        )
    if dict(split_included_counts) != config.expected_per_split_model_images:
        raise AnnotationQaError(
            f"per-split model image counts mismatch: {dict(split_included_counts)}"
        )
    if summary.get("planned_model_included_image_counts") != dict(split_included_counts):
        raise AnnotationQaError("split-plan summary does not match image plan")
    return PlanEvidence(
        rows=rows,
        summary=summary,
        path=plan_zip.resolve(),
        sha256=actual_zip_hash,
        family_count=len(family_splits),
        family_leakage_count=leakage,
        included_count=included,
        excluded_count=excluded,
        split_source_counts=dict(split_source_counts),
        split_included_counts=dict(split_included_counts),
    )


def _validate_class_mapping(config: AnnotationQaConfig) -> dict[str, Any]:
    if not config.class_mapping_path.is_file():
        raise AnnotationQaError(f"class_mapping missing: {config.class_mapping_path}")
    actual_hash = sha256_file(config.class_mapping_path)
    if actual_hash != config.class_mapping_sha256:
        raise AnnotationQaError("protected class_mapping SHA256 mismatch")
    with config.class_mapping_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise AnnotationQaError("class_mapping must contain exactly one row")
    row = rows[0]
    if row.get("dataset_id", "").strip() != config.dataset_id:
        raise AnnotationQaError("class_mapping dataset_id mismatch")
    if row.get("mapped_class", "").strip() != config.canonical_name:
        raise AnnotationQaError("class_mapping canonical class mismatch")
    if row.get("yolo_label_created", "").strip().lower() != "no":
        raise AnnotationQaError("class_mapping reports YOLO labels already created")
    return {"sha256": actual_hash, "row": row}


def load_canonical_coco(config: AnnotationQaConfig) -> dict[str, CocoSplit]:
    """Load canonical COCO and require exactly one `damage` category."""

    result: dict[str, CocoSplit] = {}
    total_images = 0
    total_annotations = 0
    expected_category = {
        "id": config.canonical_id,
        "name": config.canonical_name,
        "supercategory": config.canonical_supercategory,
    }
    for split in config.splits:
        path = config.canonical_coco_root / split / config.annotation_filename
        if not path.is_file():
            raise AnnotationQaError(f"canonical COCO missing: {path}")
        actual_hash = sha256_file(path)
        if actual_hash != config.canonical_coco_sha256[split]:
            raise AnnotationQaError(
                f"canonical COCO does not match approved SHA256: split={split} "
                f"expected={config.canonical_coco_sha256[split]} actual={actual_hash}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise AnnotationQaError(f"invalid canonical COCO: {path}: {exc}") from exc
        images = payload.get("images")
        annotations = payload.get("annotations")
        categories = payload.get("categories")
        if not isinstance(images, list) or not isinstance(annotations, list) or not isinstance(categories, list):
            raise AnnotationQaError(f"invalid canonical COCO collections: {path}")
        if categories != [expected_category]:
            raise AnnotationQaError(
                f"canonical category mismatch in {split}: expected={[expected_category]} actual={categories}"
            )
        image_by_id: dict[int, dict[str, Any]] = {}
        image_by_file: dict[str, dict[str, Any]] = {}
        for image in images:
            image_id = _integer(image.get("id"), f"{split}.image.id")
            file_name = str(image.get("file_name", "")).replace("\\", "/").strip()
            width = _integer(image.get("width"), f"{split}.{image_id}.width")
            height = _integer(image.get("height"), f"{split}.{image_id}.height")
            if image_id in image_by_id or not file_name or width <= 0 or height <= 0:
                raise AnnotationQaError(f"invalid or duplicate canonical image: {split}/{image_id}")
            image_by_id[image_id] = image
            basename = Path(file_name).name
            if basename in image_by_file:
                raise AnnotationQaError(f"duplicate canonical file_name: {split}/{basename}")
            image_by_file[basename] = image
        annotations_by_image: dict[int, list[dict[str, Any]]] = defaultdict(list)
        annotation_ids: set[int] = set()
        for annotation in annotations:
            annotation_id = _integer(annotation.get("id"), f"{split}.annotation.id")
            image_id = _integer(annotation.get("image_id"), f"{split}.{annotation_id}.image_id")
            category_id = _integer(annotation.get("category_id"), f"{split}.{annotation_id}.category_id")
            if annotation_id in annotation_ids or image_id not in image_by_id:
                raise AnnotationQaError(f"invalid annotation identity/join: {split}/{annotation_id}")
            annotation_ids.add(annotation_id)
            if category_id != config.canonical_id:
                raise AnnotationQaError(f"annotation uses non-canonical category: {split}/{annotation_id}")
            bbox = annotation.get("bbox")
            if not isinstance(bbox, list) or len(bbox) != 4:
                raise AnnotationQaError(f"invalid bbox shape: {split}/{annotation_id}")
            x, y, width, height = [_number(value, "bbox") for value in bbox]
            image = image_by_id[image_id]
            image_width = _number(image["width"], "image.width")
            image_height = _number(image["height"], "image.height")
            epsilon = 1e-6
            if (
                x < -epsilon
                or y < -epsilon
                or width <= 0
                or height <= 0
                or x + width > image_width + epsilon
                or y + height > image_height + epsilon
            ):
                raise AnnotationQaError(
                    f"invalid bbox remains: {split}/{annotation_id} bbox={bbox} image={image_width}x{image_height}"
                )
            enriched = dict(annotation)
            enriched["_category_name"] = config.canonical_name
            enriched["_bbox_area_ratio"] = (width * height) / (image_width * image_height)
            enriched["_bbox_width_ratio"] = width / image_width
            enriched["_bbox_height_ratio"] = height / image_height
            annotations_by_image[image_id].append(enriched)
        total_images += len(images)
        total_annotations += len(annotations)
        result[split] = CocoSplit(
            split=split,
            path=path,
            sha256=actual_hash,
            images=images,
            annotations=annotations,
            categories=categories,
            image_by_file=image_by_file,
            annotations_by_image=annotations_by_image,
            category_by_id={config.canonical_id: config.canonical_name},
        )
    if total_images != config.expected_source_images:
        raise AnnotationQaError(
            f"canonical image total mismatch: expected={config.expected_source_images} actual={total_images}"
        )
    if total_annotations != config.expected_source_annotations:
        raise AnnotationQaError(
            f"canonical annotation total mismatch: expected={config.expected_source_annotations} actual={total_annotations}"
        )
    return result


def _match_plan(
    plan: PlanEvidence,
    datasets: dict[str, CocoSplit],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    joined: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for row in plan.rows:
        split = row["original_split"].strip()
        file_name = Path(row["relative_image_path"].replace("\\", "/")).name
        image = datasets[split].image_by_file.get(file_name)
        if image is None:
            unresolved.append(
                {
                    "record_id": row["record_id"],
                    "original_split": split,
                    "relative_image_path": row["relative_image_path"],
                    "lookup_file_name": file_name,
                }
            )
            continue
        if _integer(row["width"], "plan.width") != _integer(image["width"], "coco.width") or _integer(row["height"], "plan.height") != _integer(image["height"], "coco.height"):
            raise AnnotationQaError(f"plan-to-COCO dimension mismatch: {row['record_id']}")
        image_id = _integer(image["id"], "image.id")
        joined.append(
            {
                **row,
                "coco_image_id": image_id,
                "coco_file_name": image["file_name"],
                "_annotations": datasets[split].annotations_by_image.get(image_id, []),
            }
        )
    return joined, unresolved


def _analyse(
    joined: list[dict[str, Any]],
    plan: PlanEvidence,
    config: AnnotationQaConfig,
) -> dict[str, Any]:
    if len(joined) != config.expected_source_images:
        raise AnnotationQaError(
            f"plan-to-COCO join count mismatch: expected={config.expected_source_images} actual={len(joined)}"
        )
    included = [row for row in joined if _truthy(row["include_in_model_dataset"])]
    excluded = [row for row in joined if not _truthy(row["include_in_model_dataset"])]
    image_rows: list[dict[str, Any]] = []
    bbox_rows: list[dict[str, Any]] = []
    unannotated: list[dict[str, Any]] = []
    family_annotation_counts: dict[str, list[int]] = defaultdict(list)
    for row in joined:
        annotations = row["_annotations"]
        family = row["canonical_source_key"]
        family_annotation_counts[family].append(len(annotations))
        image_summary = {
            "record_id": row["record_id"],
            "canonical_source_key": family,
            "original_split": row["original_split"],
            "assigned_split": row["assigned_split"],
            "include_in_model_dataset": _truthy(row["include_in_model_dataset"]),
            "plan_role": row["plan_role"],
            "annotation_count": len(annotations),
            "category_names": config.canonical_name if annotations else "",
            "relative_image_path": row["relative_image_path"],
            "coco_file_name": row["coco_file_name"],
        }
        image_rows.append(image_summary)
        if image_summary["include_in_model_dataset"] and not annotations:
            unannotated.append(image_summary)
        for annotation in annotations:
            bbox = annotation["bbox"]
            bbox_rows.append(
                {
                    "record_id": row["record_id"],
                    "canonical_source_key": family,
                    "original_split": row["original_split"],
                    "assigned_split": row["assigned_split"],
                    "include_in_model_dataset": _truthy(row["include_in_model_dataset"]),
                    "annotation_id": annotation["id"],
                    "category_name": annotation["_category_name"],
                    "bbox_x": bbox[0],
                    "bbox_y": bbox[1],
                    "bbox_width": bbox[2],
                    "bbox_height": bbox[3],
                    "bbox_area_ratio": annotation["_bbox_area_ratio"],
                    "bbox_width_ratio": annotation["_bbox_width_ratio"],
                    "bbox_height_ratio": annotation["_bbox_height_ratio"],
                    "relative_image_path": row["relative_image_path"],
                }
            )
    if len(bbox_rows) != config.expected_source_annotations:
        raise AnnotationQaError(
            f"joined annotation count mismatch: expected={config.expected_source_annotations} actual={len(bbox_rows)}"
        )
    if unannotated:
        raise AnnotationQaError(
            f"annotation missing for included images: count={len(unannotated)}"
        )
    inconsistent = [
        {
            "canonical_source_key": family,
            "variant_count": len(counts),
            "annotation_count_min": min(counts),
            "annotation_count_max": max(counts),
            "annotation_count_unique_values": "|".join(str(value) for value in sorted(set(counts))),
            "annotation_count_consistent": len(set(counts)) == 1,
        }
        for family, counts in family_annotation_counts.items()
        if len(set(counts)) > 1
    ]
    inconsistent.sort(
        key=lambda row: (
            -(row["annotation_count_max"] - row["annotation_count_min"]),
            row["canonical_source_key"],
        )
    )
    included_bbox = [row for row in bbox_rows if row["include_in_model_dataset"]]
    split_summaries: list[dict[str, Any]] = []
    for split in config.splits:
        source = [row for row in image_rows if row["assigned_split"] == split]
        model = [row for row in source if row["include_in_model_dataset"]]
        boxes = [row for row in included_bbox if row["assigned_split"] == split]
        positive = sum(row["annotation_count"] > 0 for row in model)
        negative = len(model) - positive
        area = [float(row["bbox_area_ratio"]) for row in boxes]
        box_counts = [int(row["annotation_count"]) for row in model]
        split_summaries.append(
            {
                "assigned_split": split,
                "source_family_count": len({row["canonical_source_key"] for row in source}),
                "source_image_count": len(source),
                "model_included_image_count": len(model),
                "excluded_correlated_variant_count": len(source) - len(model),
                "positive_image_count": positive,
                "negative_image_count": negative,
                "positive_image_percent": _pct(positive, len(model)),
                "bbox_count": len(boxes),
                "bbox_per_included_image_mean": round(statistics.mean(box_counts), 6) if box_counts else 0.0,
                "bbox_per_positive_image_mean": round(len(boxes) / positive, 6) if positive else 0.0,
                "bbox_area_ratio_p05": round(_quantile(area, 0.05), 8),
                "bbox_area_ratio_p50": round(_quantile(area, 0.50), 8),
                "bbox_area_ratio_p95": round(_quantile(area, 0.95), 8),
                "small_bbox_count_lt_1pct": sum(value < 0.01 for value in area),
                "large_bbox_count_gt_50pct": sum(value > 0.50 for value in area),
            }
        )
    smallest = sorted(
        included_bbox,
        key=lambda row: (float(row["bbox_area_ratio"]), row["record_id"], int(row["annotation_id"])),
    )[: config.review_sample_size]
    largest = sorted(
        included_bbox,
        key=lambda row: (-float(row["bbox_area_ratio"]), row["record_id"], int(row["annotation_id"])),
    )[: config.review_sample_size]
    included_positive = sum(bool(row["_annotations"]) for row in included)
    included_negative = len(included) - included_positive
    decision = {
        "dataset_id": config.dataset_id,
        "classification": "ANNOTATION_QA_STRUCTURALLY_READY_FOR_TARGETED_VISUAL_REVIEW",
        "source_image_count": len(joined),
        "model_included_image_count": len(included),
        "excluded_correlated_eval_variant_count": len(excluded),
        "source_annotation_count": len(bbox_rows),
        "model_included_annotation_count": len(included_bbox),
        "included_positive_image_count": included_positive,
        "included_negative_image_count": included_negative,
        "source_family_count": plan.family_count,
        "family_leakage_count": plan.family_leakage_count,
        "annotation_count_inconsistent_family_count": len(inconsistent),
        "unannotated_included_image_count": len(unannotated),
        "unresolved_plan_to_coco_join_count": 0,
        "invalid_bbox_count": 0,
        "mapped_class": config.canonical_name,
        "yolo_class_count": 1,
        "split_summaries": split_summaries,
        "targeted_visual_review": {
            "smallest_bbox_sample_count": len(smallest),
            "largest_bbox_sample_count": len(largest),
            "unannotated_included_image_count": len(unannotated),
            "annotation_count_inconsistent_family_count": len(inconsistent),
        },
        "current_plan_status": "READY_FOR_TARGETED_VISUAL_REVIEW",
        "training_acceptance": "NOT_YET_APPROVED",
        "model_feasibility": "FEASIBLE_PENDING_TARGETED_VISUAL_LABEL_QA",
        "recommended_next_step": (
            "Complete targeted visual review of extreme bbox samples and annotation-count-inconsistent families; "
            "only then decide whether training_acceptance may advance."
        ),
    }
    return {
        "decision": decision,
        "image_rows": image_rows,
        "bbox_rows": included_bbox,
        "unannotated": unannotated,
        "inconsistent": inconsistent,
        "smallest": smallest,
        "largest": largest,
        "split_summaries": split_summaries,
    }


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


def _create_manifest(root: Path) -> None:
    rows = [
        {
            "relative_path": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "evidence_manifest.csv"
    ]
    _write_csv(root / "evidence_manifest.csv", rows, ["relative_path", "size_bytes", "sha256"])


def _validate_output_root(output_root: Path, config: AnnotationQaConfig) -> Path:
    resolved = output_root.resolve()
    protected_roots = [
        config.project_root / "dataset/00_catalog",
        config.project_root / "dataset/01_raw",
        config.canonical_coco_root,
        config.canonical_coco_root.parent / "cleaned_coco",
        config.project_root / "outputs/metadata/external_assets",
        config.project_root / "outputs/metadata/external_dedup",
    ]
    for protected in protected_roots:
        protected = protected.resolve()
        if resolved == protected or protected in resolved.parents:
            raise AnnotationQaError(f"QA output_root is under a protected path: {resolved}")
    return resolved


def run_annotation_split_balance_qa(
    config: AnnotationQaConfig,
    *,
    plan_zip: Path,
    output_root: Path,
    now_utc: str | None = None,
) -> AnnotationQaResult:
    """Run canonical annotation and immutable group-safe split-plan QA."""

    output_root = _validate_output_root(output_root, config)
    if output_root.exists():
        raise AnnotationQaError(f"QA output already exists: {output_root}")
    plan = verify_plan_zip(plan_zip, config)
    mapping = _validate_class_mapping(config)
    datasets = load_canonical_coco(config)
    joined, unresolved = _match_plan(plan, datasets)
    if unresolved:
        raise AnnotationQaError(
            f"unresolved plan-to-COCO joins: count={len(unresolved)}"
        )
    analysis = _analyse(joined, plan, config)

    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=output_root.parent))
    try:
        decision = dict(analysis["decision"])
        decision["created_at_utc"] = now_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        _write_json(staging / "annotation_and_split_balance_decision.json", decision)
        split_columns = [
            "assigned_split",
            "source_family_count",
            "source_image_count",
            "model_included_image_count",
            "excluded_correlated_variant_count",
            "positive_image_count",
            "negative_image_count",
            "positive_image_percent",
            "bbox_count",
            "bbox_per_included_image_mean",
            "bbox_per_positive_image_mean",
            "bbox_area_ratio_p05",
            "bbox_area_ratio_p50",
            "bbox_area_ratio_p95",
            "small_bbox_count_lt_1pct",
            "large_bbox_count_gt_50pct",
        ]
        _write_csv(staging / "planned_split_annotation_summary.csv", analysis["split_summaries"], split_columns)
        image_columns = [
            "record_id",
            "canonical_source_key",
            "original_split",
            "assigned_split",
            "include_in_model_dataset",
            "plan_role",
            "annotation_count",
            "category_names",
            "relative_image_path",
            "coco_file_name",
        ]
        _write_csv(staging / "image_annotation_plan_audit.csv", analysis["image_rows"], image_columns)
        _write_csv(staging / "unannotated_included_images.csv", analysis["unannotated"], image_columns)
        inconsistent_columns = [
            "canonical_source_key",
            "variant_count",
            "annotation_count_min",
            "annotation_count_max",
            "annotation_count_unique_values",
            "annotation_count_consistent",
        ]
        _write_csv(staging / "annotation_count_inconsistent_families.csv", analysis["inconsistent"], inconsistent_columns)
        bbox_columns = [
            "record_id",
            "canonical_source_key",
            "original_split",
            "assigned_split",
            "include_in_model_dataset",
            "annotation_id",
            "category_name",
            "bbox_x",
            "bbox_y",
            "bbox_width",
            "bbox_height",
            "bbox_area_ratio",
            "bbox_width_ratio",
            "bbox_height_ratio",
            "relative_image_path",
        ]
        _write_csv(staging / "smallest_bbox_review_sample.csv", analysis["smallest"], bbox_columns)
        _write_csv(staging / "largest_bbox_review_sample.csv", analysis["largest"], bbox_columns)
        _write_json(
            staging / "input_evidence.json",
            {
                "split_plan_zip": {"path": str(plan.path), "sha256": plan.sha256},
                "class_mapping": mapping,
                "canonical_coco": {
                    split: {
                        "path": str(dataset.path),
                        "sha256": dataset.sha256,
                        "image_count": len(dataset.images),
                        "annotation_count": len(dataset.annotations),
                        "categories": dataset.categories,
                    }
                    for split, dataset in datasets.items()
                },
                "safety": {
                    "project_modified": False,
                    "registry_modified": False,
                    "raw_dataset_modified": False,
                    "cleaned_coco_modified": False,
                    "production_deduplication_modified": False,
                    "group_safe_assignment_modified": False,
                    "yolo_dataset_created": False,
                    "model_training_started": False,
                },
            },
        )
        _create_manifest(staging)
        os.replace(staging, output_root)
    except Exception as exc:
        if staging.exists():
            import shutil

            shutil.rmtree(staging, ignore_errors=True)
        if isinstance(exc, AnnotationQaError):
            raise
        raise AnnotationQaError(f"QA evidence promotion failed: {exc}") from exc

    decision = analysis["decision"]
    targeted = decision["targeted_visual_review"]
    return AnnotationQaResult(
        classification=decision["classification"],
        output_root=output_root,
        source_images=decision["source_image_count"],
        source_annotations=decision["source_annotation_count"],
        model_included_images=decision["model_included_image_count"],
        excluded_correlated_eval_variants=decision["excluded_correlated_eval_variant_count"],
        source_families=decision["source_family_count"],
        family_leakage_count=decision["family_leakage_count"],
        invalid_bbox_count=decision["invalid_bbox_count"],
        unresolved_plan_to_coco_joins=decision["unresolved_plan_to_coco_join_count"],
        unannotated_included_images=decision["unannotated_included_image_count"],
        annotation_count_inconsistent_families=decision["annotation_count_inconsistent_family_count"],
        targeted_visual_review_items=(
            targeted["smallest_bbox_sample_count"]
            + targeted["largest_bbox_sample_count"]
            + targeted["unannotated_included_image_count"]
            + targeted["annotation_count_inconsistent_family_count"]
        ),
    )
