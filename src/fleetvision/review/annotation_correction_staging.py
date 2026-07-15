from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import re
import shutil
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont

from fleetvision.review.annotation_correction_promotion_contract import (
    CocoDocument,
    Phase04_5NConfig,
    PromotionContractError,
    ReviewedProposal,
    SourceAccessLedger,
    canonical_json_bytes,
    load_coco_document,
    load_phase04_5n_config,
    resolve_canonical_validation_coco,
    sha256_file,
    verify_completed_review_workspace,
)


class AnnotationMappingError(ValueError):
    """Raised when reviewed geometry cannot map to one canonical annotation."""


@dataclass(frozen=True)
class AbsoluteXYXY:
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class CocoXYWH:
    x: float
    y: float
    width: float
    height: float

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass(frozen=True)
class LocalGtRecord:
    bbox_id: str
    box: AbsoluteXYXY


@dataclass(frozen=True)
class NativeAnnotationMapping:
    phase04_5m_review_case_id: str
    correction_case_id: str
    proposal_fingerprint: str
    source_split: str
    image_id: str
    local_gt_bbox_id: str
    native_image_id: int
    native_annotation_id: int
    native_category_id: int
    before_bbox_xywh: tuple[float, float, float, float]
    before_bbox_xyxy: tuple[float, float, float, float]
    before_area: float
    after_bbox_xywh: tuple[float, float, float, float]
    after_bbox_xyxy: tuple[float, float, float, float]
    after_area: float


@dataclass(frozen=True)
class CorrectionDiffRow:
    schema_version: str
    phase04_5m_review_case_id: str
    correction_case_id: str
    proposal_fingerprint: str
    source_split: str
    image_id: str
    native_coco_image_id: int
    native_coco_annotation_id: int
    native_category_id: int
    before_bbox_xywh: tuple[float, float, float, float]
    before_bbox_xyxy: tuple[float, float, float, float]
    before_area: float
    after_bbox_xywh: tuple[float, float, float, float]
    after_bbox_xyxy: tuple[float, float, float, float]
    after_area: float
    changed_fields: tuple[str, ...]
    source_coco_sha256: str
    staged_coco_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "phase04_5m_review_case_id": self.phase04_5m_review_case_id,
            "correction_case_id": self.correction_case_id,
            "proposal_fingerprint": self.proposal_fingerprint,
            "source_split": self.source_split,
            "image_id": self.image_id,
            "native_coco_image_id": self.native_coco_image_id,
            "native_coco_annotation_id": self.native_coco_annotation_id,
            "native_category_id": self.native_category_id,
            "before_bbox_xywh": _compact_json(self.before_bbox_xywh),
            "before_bbox_xyxy": _compact_json(self.before_bbox_xyxy),
            "before_area": self.before_area,
            "after_bbox_xywh": _compact_json(self.after_bbox_xywh),
            "after_bbox_xyxy": _compact_json(self.after_bbox_xyxy),
            "after_area": self.after_area,
            "changed_fields": _compact_json(self.changed_fields),
            "source_coco_sha256": self.source_coco_sha256,
            "staged_coco_sha256": self.staged_coco_sha256,
        }


@dataclass(frozen=True)
class SemanticValidationResult:
    passed: bool
    proposal_count: int
    mapped_annotation_count: int
    changed_annotation_count: int
    changed_annotation_ids: tuple[int, ...]
    changed_fields: tuple[str, ...]
    image_count_delta: int
    annotation_count_delta: int
    category_count_delta: int
    image_id_set_unchanged: bool
    annotation_id_set_unchanged: bool
    category_id_set_unchanged: bool
    non_target_annotations_unchanged: bool
    category_definitions_unchanged: bool


@dataclass(frozen=True)
class StagedCocoBuild:
    payload: dict[str, object]
    mappings: tuple[NativeAnnotationMapping, ...]
    diff_rows: tuple[CorrectionDiffRow, ...]
    validation: SemanticValidationResult

    @property
    def changed_annotation_ids(self) -> tuple[int, ...]:
        return self.validation.changed_annotation_ids


class StagedCocoValidationError(ValueError):
    """Raised when staged COCO semantics violate the N1 contract."""


class StagedWorkspaceError(RuntimeError):
    """Raised when an N1 staging workspace cannot be prepared safely."""


@dataclass(frozen=True)
class OverlayArtifacts:
    before: Path
    after: Path
    combined: Path


@dataclass(frozen=True)
class PreparedStagedCorrectionWorkspace:
    workspace_root: Path
    gate_result_path: Path
    source_coco_sha256: str
    staged_coco_sha256: str
    changed_annotation_ids: tuple[int, ...]


_LOCAL_ID = re.compile(r"^gt_(\d+)$", re.IGNORECASE)


def _finite_float(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise AnnotationMappingError(f"{label} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise AnnotationMappingError(f"{label} must be a finite number") from exc
    if not math.isfinite(result):
        raise AnnotationMappingError(f"{label} must be a finite number")
    return result


def _canonical_local_id(value: object) -> str:
    text = str(value).strip().lower()
    match = _LOCAL_ID.fullmatch(text)
    if match is None:
        raise AnnotationMappingError(f"invalid local bbox ID: {value!r}")
    return f"gt_{int(match.group(1)):03d}"


def _validate_positive_box(box: AbsoluteXYXY, label: str) -> None:
    values = (box.x1, box.y1, box.x2, box.y2)
    if not all(math.isfinite(value) for value in values):
        raise AnnotationMappingError(f"{label} coordinates must be finite")
    if box.x2 <= box.x1 or box.y2 <= box.y1:
        raise AnnotationMappingError(f"{label} width and height must be positive")


def _validate_box_bounds(
    box: AbsoluteXYXY,
    *,
    width: int,
    height: int,
    label: str,
) -> None:
    _validate_positive_box(box, label)
    if box.x1 < 0 or box.y1 < 0 or box.x2 > width or box.y2 > height:
        raise AnnotationMappingError(
            f"{label} is outside image bounds {width}x{height}: {box!r}"
        )


def xyxy_to_coco_xywh(box: AbsoluteXYXY) -> CocoXYWH:
    _validate_positive_box(box, "bbox")
    return CocoXYWH(
        x=float(box.x1),
        y=float(box.y1),
        width=float(box.x2 - box.x1),
        height=float(box.y2 - box.y1),
    )


def _coco_xywh_to_xyxy(value: object, label: str) -> AbsoluteXYXY:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise AnnotationMappingError(f"{label} must contain four coordinates")
    x, y, width, height = (
        _finite_float(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    )
    if width <= 0 or height <= 0:
        raise AnnotationMappingError(f"{label} width and height must be positive")
    return AbsoluteXYXY(x1=x, y1=y, x2=x + width, y2=y + height)


def parse_local_gt_records(value: str) -> tuple[LocalGtRecord, ...]:
    try:
        payload = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise AnnotationMappingError("source_gt_bbox_records_json is invalid") from exc
    if not isinstance(payload, list):
        raise AnnotationMappingError("source_gt_bbox_records_json must be a list")

    records: list[LocalGtRecord] = []
    seen: set[str] = set()
    for index, raw in enumerate(payload):
        if not isinstance(raw, Mapping):
            raise AnnotationMappingError(f"local bbox record[{index}] must be an object")
        bbox_id = _canonical_local_id(raw.get("bbox_id"))
        if bbox_id in seen:
            raise AnnotationMappingError(f"duplicate local bbox ID: {bbox_id}")
        seen.add(bbox_id)
        box = AbsoluteXYXY(
            x1=_finite_float(raw.get("x1"), f"local bbox {bbox_id}.x1"),
            y1=_finite_float(raw.get("y1"), f"local bbox {bbox_id}.y1"),
            x2=_finite_float(raw.get("x2"), f"local bbox {bbox_id}.x2"),
            y2=_finite_float(raw.get("y2"), f"local bbox {bbox_id}.y2"),
        )
        _validate_positive_box(box, f"local bbox {bbox_id}")
        records.append(LocalGtRecord(bbox_id=bbox_id, box=box))
    return tuple(records)


def parse_replacement_bbox(value: str) -> AbsoluteXYXY:
    try:
        payload = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise AnnotationMappingError("replacement_bbox_coordinates_json is invalid") from exc
    if not isinstance(payload, Mapping):
        raise AnnotationMappingError("replacement bbox must be an object")
    required = {"x1", "y1", "x2", "y2"}
    if set(payload) != required:
        raise AnnotationMappingError(
            "replacement bbox must contain exactly x1/y1/x2/y2"
        )
    box = AbsoluteXYXY(
        x1=_finite_float(payload["x1"], "replacement.x1"),
        y1=_finite_float(payload["y1"], "replacement.y1"),
        x2=_finite_float(payload["x2"], "replacement.x2"),
        y2=_finite_float(payload["y2"], "replacement.y2"),
    )
    _validate_positive_box(box, "replacement bbox")
    return box


def _parse_target_ids(value: str) -> tuple[str, ...]:
    try:
        payload = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise AnnotationMappingError("target_gt_bbox_ids_json is invalid") from exc
    if not isinstance(payload, list):
        raise AnnotationMappingError("target_gt_bbox_ids_json must be a list")
    return tuple(_canonical_local_id(item) for item in payload)


def _parse_source_dimension(source_row: Mapping[str, str], key: str) -> int:
    raw = source_row.get(key)
    try:
        value = int(str(raw))
    except (TypeError, ValueError) as exc:
        raise AnnotationMappingError(f"source {key} must be a positive integer") from exc
    if value <= 0:
        raise AnnotationMappingError(f"source {key} must be a positive integer")
    return value


def _coordinates_match(
    first: AbsoluteXYXY,
    second: AbsoluteXYXY,
    *,
    tolerance: float,
) -> bool:
    return all(
        abs(left - right) <= tolerance
        for left, right in zip(
            (first.x1, first.y1, first.x2, first.y2),
            (second.x1, second.y1, second.x2, second.y2),
            strict=True,
        )
    )


def map_reviewed_proposal_to_native_annotation(
    proposal: ReviewedProposal,
    source_row: Mapping[str, str],
    coco: CocoDocument,
    *,
    tolerance: float,
) -> NativeAnnotationMapping:
    tolerance_value = _finite_float(tolerance, "tolerance")
    if tolerance_value < 0:
        raise AnnotationMappingError("tolerance must be non-negative")
    if proposal.correction_operation != "RESIZE_OR_REDRAW_BBOX":
        raise AnnotationMappingError(
            "correction operation must be RESIZE_OR_REDRAW_BBOX"
        )
    if proposal.source_split != "valid":
        raise AnnotationMappingError("proposal source_split must be valid")

    image = coco.images_by_file_name.get(proposal.image_id)
    if image is None:
        raise AnnotationMappingError(
            f"canonical image filename is missing: {proposal.image_id}"
        )

    source_contract_checks = {
        "review_case_id": proposal.review_case_id,
        "correction_case_id": proposal.correction_case_id,
        "image_id": proposal.image_id,
        "source_split": proposal.source_split,
        "source_case_fingerprint": proposal.source_case_fingerprint,
        "gt_bbox_records_json": proposal.source_gt_bbox_records_json,
    }
    for key, expected in source_contract_checks.items():
        if source_row.get(key) != expected:
            raise AnnotationMappingError(
                f"source row {key} mismatch for {proposal.review_case_id}"
            )

    image_id = image.get("id")
    width = image.get("width")
    height = image.get("height")
    if not isinstance(image_id, int) or isinstance(image_id, bool):
        raise AnnotationMappingError("canonical image ID must be an integer")
    if not isinstance(width, int) or not isinstance(height, int):
        raise AnnotationMappingError("canonical image dimensions must be integers")
    source_width = _parse_source_dimension(source_row, "image_width")
    source_height = _parse_source_dimension(source_row, "image_height")
    if (width, height) != (source_width, source_height):
        raise AnnotationMappingError(
            "source/canonical image dimension mismatch: "
            f"source={source_width}x{source_height}, canonical={width}x{height}"
        )

    local_records = parse_local_gt_records(proposal.source_gt_bbox_records_json)
    target_ids = _parse_target_ids(proposal.target_gt_bbox_ids_json)
    if len(target_ids) != 1:
        raise AnnotationMappingError("exactly one local target bbox ID is required")
    local_by_id = {record.bbox_id: record for record in local_records}
    local_target = local_by_id.get(target_ids[0])
    if local_target is None:
        raise AnnotationMappingError(f"unknown local target bbox ID: {target_ids[0]}")
    _validate_box_bounds(
        local_target.box,
        width=width,
        height=height,
        label=f"local bbox {local_target.bbox_id}",
    )

    replacement = parse_replacement_bbox(proposal.replacement_bbox_coordinates_json)
    _validate_box_bounds(
        replacement,
        width=width,
        height=height,
        label="replacement bbox",
    )

    damage_categories = [
        category_id
        for category_id, category in coco.categories_by_id.items()
        if category.get("name") == "damage"
    ]
    if len(damage_categories) != 1:
        raise AnnotationMappingError(
            f"canonical damage category resolution requires exactly one ID; found {len(damage_categories)}"
        )
    category_id = damage_categories[0]

    matches: list[tuple[int, Mapping[str, object], AbsoluteXYXY]] = []
    for annotation_id, annotation in coco.annotations_by_id.items():
        if annotation.get("image_id") != image_id:
            continue
        if annotation.get("category_id") != category_id:
            continue
        native_box = _coco_xywh_to_xyxy(
            annotation.get("bbox"),
            f"annotation {annotation_id} bbox",
        )
        if _coordinates_match(
            native_box,
            local_target.box,
            tolerance=tolerance_value,
        ):
            matches.append((annotation_id, annotation, native_box))

    if not matches:
        raise AnnotationMappingError(
            f"zero native annotations match local bbox {local_target.bbox_id}"
        )
    if len(matches) > 1:
        raise AnnotationMappingError(
            f"multiple native annotations match local bbox {local_target.bbox_id}"
        )

    annotation_id, annotation, before_box = matches[0]
    before_xywh = _coco_xywh_to_xyxy(
        annotation.get("bbox"),
        f"annotation {annotation_id} bbox",
    )
    before_coco = xyxy_to_coco_xywh(before_xywh)
    before_area = _finite_float(
        annotation.get("area"),
        f"annotation {annotation_id} area",
    )
    if before_area <= 0:
        raise AnnotationMappingError(
            f"annotation {annotation_id} area must be positive"
        )
    after_coco = xyxy_to_coco_xywh(replacement)

    return NativeAnnotationMapping(
        phase04_5m_review_case_id=proposal.review_case_id,
        correction_case_id=proposal.correction_case_id,
        proposal_fingerprint=proposal.proposal_fingerprint,
        source_split=proposal.source_split,
        image_id=proposal.image_id,
        local_gt_bbox_id=local_target.bbox_id,
        native_image_id=image_id,
        native_annotation_id=annotation_id,
        native_category_id=category_id,
        before_bbox_xywh=(
            before_coco.x,
            before_coco.y,
            before_coco.width,
            before_coco.height,
        ),
        before_bbox_xyxy=(
            before_box.x1,
            before_box.y1,
            before_box.x2,
            before_box.y2,
        ),
        before_area=before_area,
        after_bbox_xywh=(
            after_coco.x,
            after_coco.y,
            after_coco.width,
            after_coco.height,
        ),
        after_bbox_xyxy=(
            replacement.x1,
            replacement.y1,
            replacement.x2,
            replacement.y2,
        ),
        after_area=after_coco.area,
    )



def require_distinct_native_annotation_mappings(
    mappings: tuple[NativeAnnotationMapping, ...],
) -> tuple[NativeAnnotationMapping, ...]:
    annotation_ids = tuple(mapping.native_annotation_id for mapping in mappings)
    if len(set(annotation_ids)) != len(annotation_ids):
        raise AnnotationMappingError(
            f"native annotation IDs must be distinct: {annotation_ids!r}"
        )
    return mappings

def apply_reviewed_geometry(
    annotation: Mapping[str, object],
    box: AbsoluteXYXY,
) -> dict[str, object]:
    replacement = xyxy_to_coco_xywh(box)
    changed = copy.deepcopy(dict(annotation))
    changed["bbox"] = [
        replacement.x,
        replacement.y,
        replacement.width,
        replacement.height,
    ]
    changed["area"] = replacement.area

    original = dict(annotation)
    changed_keys = {
        key
        for key in set(original) | set(changed)
        if original.get(key) != changed.get(key)
    }
    if changed_keys != {"bbox", "area"}:
        raise AnnotationMappingError(
            "geometry changed-key set must equal {'bbox', 'area'}; "
            f"got {sorted(changed_keys)!r}"
        )
    return changed


_SHA256_RE = re.compile(r"^[0-9A-Fa-f]{64}$")


def _compact_json(value: object) -> str:
    return json.dumps(
        list(value) if isinstance(value, tuple) else value,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def _validated_sha256(value: object, label: str) -> str:
    text = str(value).strip()
    if _SHA256_RE.fullmatch(text) is None:
        raise StagedCocoValidationError(f"{label} must be a 64-character SHA256")
    return text.upper()


def normalized_json_value(value: object) -> object:
    """Return a key-order-neutral, list-order-preserving, type-sensitive value."""

    if isinstance(value, Mapping):
        return (
            "dict",
            tuple(
                (str(key), normalized_json_value(item))
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            ),
        )
    if isinstance(value, list):
        return ("list", tuple(normalized_json_value(item) for item in value))
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, int):
        return ("int", value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return ("float", repr(value))
        return ("float", value.hex())
    if isinstance(value, str):
        return ("str", value)
    raise StagedCocoValidationError(
        f"unsupported JSON value type: {type(value).__name__}"
    )


def _require_coco_array(
    payload: Mapping[str, object],
    key: str,
) -> list[dict[str, object]]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise StagedCocoValidationError(f"staged COCO {key} must be a list")
    result: list[dict[str, object]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise StagedCocoValidationError(
                f"staged COCO {key}[{index}] must be an object"
            )
        result.append(dict(item))
    return result


def _index_unique_ids(
    records: list[dict[str, object]],
    label: str,
) -> tuple[dict[int, dict[str, object]], tuple[int, ...]]:
    indexed: dict[int, dict[str, object]] = {}
    ordered: list[int] = []
    for index, record in enumerate(records):
        record_id = record.get("id")
        if isinstance(record_id, bool) or not isinstance(record_id, int):
            raise StagedCocoValidationError(
                f"{label}[{index}] ID must be an integer"
            )
        if record_id in indexed:
            raise StagedCocoValidationError(
                f"duplicate {label[:-1]} ID: {record_id}"
            )
        indexed[record_id] = record
        ordered.append(record_id)
    return indexed, tuple(ordered)


def _changed_keys(
    source: Mapping[str, object],
    staged: Mapping[str, object],
) -> tuple[str, ...]:
    changed: list[str] = []
    for key in set(source) | set(staged):
        if (key in source) != (key in staged):
            changed.append(key)
            continue
        if normalized_json_value(source[key]) != normalized_json_value(staged[key]):
            changed.append(key)
    return tuple(sorted(changed))


def _close(left: float, right: float, tolerance: float) -> bool:
    return abs(left - right) <= tolerance


def _validate_target_geometry(
    *,
    staged_annotation: Mapping[str, object],
    source_annotation: Mapping[str, object],
    mapping: NativeAnnotationMapping,
    images_by_id: Mapping[int, Mapping[str, object]],
    allowed_fields: tuple[str, ...],
    tolerance: float,
) -> tuple[str, ...]:
    changed = _changed_keys(source_annotation, staged_annotation)
    if changed != allowed_fields:
        raise StagedCocoValidationError(
            f"unexpected changed fields for annotation "
            f"{mapping.native_annotation_id}: {changed!r}"
        )

    if source_annotation.get("image_id") != mapping.native_image_id:
        raise StagedCocoValidationError("mapping/source native image ID mismatch")
    if source_annotation.get("category_id") != mapping.native_category_id:
        raise StagedCocoValidationError("mapping/source native category ID mismatch")

    try:
        source_box = _coco_xywh_to_xyxy(
            source_annotation.get("bbox"),
            f"source annotation {mapping.native_annotation_id} bbox",
        )
        source_xywh = xyxy_to_coco_xywh(source_box)
    except AnnotationMappingError as exc:
        raise StagedCocoValidationError(str(exc)) from exc
    if not all(
        _close(actual, expected, tolerance)
        for actual, expected in zip(
            (
                source_xywh.x,
                source_xywh.y,
                source_xywh.width,
                source_xywh.height,
            ),
            mapping.before_bbox_xywh,
            strict=True,
        )
    ):
        raise StagedCocoValidationError("mapping before bbox does not match source")
    try:
        source_area = _finite_float(
            source_annotation.get("area"),
            f"source annotation {mapping.native_annotation_id} area",
        )
    except AnnotationMappingError as exc:
        raise StagedCocoValidationError(str(exc)) from exc
    if not _close(source_area, mapping.before_area, tolerance):
        raise StagedCocoValidationError("mapping before area does not match source")

    try:
        staged_box = _coco_xywh_to_xyxy(
            staged_annotation.get("bbox"),
            f"staged annotation {mapping.native_annotation_id} bbox",
        )
        staged_xywh = xyxy_to_coco_xywh(staged_box)
        staged_area = _finite_float(
            staged_annotation.get("area"),
            f"staged annotation {mapping.native_annotation_id} area",
        )
    except AnnotationMappingError as exc:
        raise StagedCocoValidationError(str(exc)) from exc
    if staged_area <= 0:
        raise StagedCocoValidationError(
            f"staged annotation {mapping.native_annotation_id} area must be positive"
        )

    image = images_by_id.get(mapping.native_image_id)
    if image is None:
        raise StagedCocoValidationError("target annotation image is missing")
    width = image.get("width")
    height = image.get("height")
    if (
        isinstance(width, bool)
        or isinstance(height, bool)
        or not isinstance(width, int)
        or not isinstance(height, int)
        or width <= 0
        or height <= 0
    ):
        raise StagedCocoValidationError("target image dimensions are invalid")
    try:
        _validate_box_bounds(
            staged_box,
            width=width,
            height=height,
            label=f"staged annotation {mapping.native_annotation_id}",
        )
    except AnnotationMappingError as exc:
        raise StagedCocoValidationError(str(exc)) from exc

    bbox_matches = all(
        _close(actual, expected, tolerance)
        for actual, expected in zip(
            (
                staged_xywh.x,
                staged_xywh.y,
                staged_xywh.width,
                staged_xywh.height,
            ),
            mapping.after_bbox_xywh,
            strict=True,
        )
    )
    area_matches = (
        _close(staged_area, mapping.after_area, tolerance)
        and _close(staged_area, staged_xywh.area, tolerance)
    )
    if not bbox_matches or not area_matches:
        raise StagedCocoValidationError(
            "target after bbox/area does not equal reviewed replacement geometry"
        )
    return changed


def validate_staged_coco(
    source: CocoDocument,
    staged_payload: dict[str, object],
    mappings: tuple[NativeAnnotationMapping, ...],
    allowed_changed_fields: tuple[str, ...],
    *,
    tolerance: float,
) -> SemanticValidationResult:
    tolerance_value = _finite_float(tolerance, "tolerance")
    if tolerance_value < 0:
        raise StagedCocoValidationError("tolerance must be non-negative")

    allowed_fields = tuple(sorted(str(item) for item in allowed_changed_fields))
    if allowed_fields != ("area", "bbox"):
        raise StagedCocoValidationError(
            "allowed changed fields must resolve exactly to ('area', 'bbox')"
        )
    if len(mappings) != 2:
        raise StagedCocoValidationError("exactly two annotation mappings are required")
    try:
        require_distinct_native_annotation_mappings(mappings)
    except AnnotationMappingError as exc:
        raise StagedCocoValidationError(str(exc)) from exc

    if not isinstance(source.payload, Mapping):
        raise StagedCocoValidationError("source COCO root must be an object")
    if not isinstance(staged_payload, Mapping):
        raise StagedCocoValidationError("staged COCO root must be an object")

    if set(source.payload) != set(staged_payload):
        raise StagedCocoValidationError("top-level COCO key set changed")
    for key in set(source.payload) - {"images", "annotations", "categories"}:
        if normalized_json_value(source.payload[key]) != normalized_json_value(
            staged_payload[key]
        ):
            raise StagedCocoValidationError(
                f"top-level COCO field changed: {key}"
            )

    source_images = _require_coco_array(source.payload, "images")
    source_annotations = _require_coco_array(source.payload, "annotations")
    source_categories = _require_coco_array(source.payload, "categories")
    staged_images = _require_coco_array(staged_payload, "images")
    staged_annotations = _require_coco_array(staged_payload, "annotations")
    staged_categories = _require_coco_array(staged_payload, "categories")

    image_count_delta = len(staged_images) - len(source_images)
    annotation_count_delta = len(staged_annotations) - len(source_annotations)
    category_count_delta = len(staged_categories) - len(source_categories)
    if image_count_delta != 0:
        raise StagedCocoValidationError("image count delta must be zero")
    if annotation_count_delta != 0:
        raise StagedCocoValidationError("annotation count delta must be zero")
    if category_count_delta != 0:
        raise StagedCocoValidationError("category count delta must be zero")

    source_image_map, source_image_order = _index_unique_ids(source_images, "images")
    staged_image_map, staged_image_order = _index_unique_ids(staged_images, "images")
    source_annotation_map, source_annotation_order = _index_unique_ids(
        source_annotations, "annotations"
    )
    staged_annotation_map, staged_annotation_order = _index_unique_ids(
        staged_annotations, "annotations"
    )
    source_category_map, source_category_order = _index_unique_ids(
        source_categories, "categories"
    )
    staged_category_map, staged_category_order = _index_unique_ids(
        staged_categories, "categories"
    )

    if set(source_image_map) != set(staged_image_map):
        raise StagedCocoValidationError("image ID set changed")
    if set(source_annotation_map) != set(staged_annotation_map):
        raise StagedCocoValidationError("annotation ID set changed")
    if set(source_category_map) != set(staged_category_map):
        raise StagedCocoValidationError("category ID set changed")
    if source_annotation_order != staged_annotation_order:
        raise StagedCocoValidationError("annotation array order changed")
    if source_image_order != staged_image_order or normalized_json_value(
        source_images
    ) != normalized_json_value(staged_images):
        raise StagedCocoValidationError("image definitions changed")
    if source_category_order != staged_category_order or normalized_json_value(
        source_categories
    ) != normalized_json_value(staged_categories):
        raise StagedCocoValidationError("category definitions changed")

    target_ids = tuple(mapping.native_annotation_id for mapping in mappings)
    target_set = set(target_ids)
    changed_ids = tuple(
        annotation_id
        for annotation_id in source_annotation_order
        if normalized_json_value(source_annotation_map[annotation_id])
        != normalized_json_value(staged_annotation_map[annotation_id])
    )
    changed_set = set(changed_ids)
    non_target_changes = changed_set - target_set
    if non_target_changes:
        raise StagedCocoValidationError(
            f"non-target annotation changed: {sorted(non_target_changes)}"
        )
    if changed_set != target_set or len(changed_ids) != 2:
        raise StagedCocoValidationError(
            f"changed annotation IDs must equal mapped targets: {changed_ids!r}"
        )

    changed_fields: set[str] = set()
    mapping_by_id = {mapping.native_annotation_id: mapping for mapping in mappings}
    for annotation_id in changed_ids:
        changed_fields.update(
            _validate_target_geometry(
                staged_annotation=staged_annotation_map[annotation_id],
                source_annotation=source_annotation_map[annotation_id],
                mapping=mapping_by_id[annotation_id],
                images_by_id=source_image_map,
                allowed_fields=allowed_fields,
                tolerance=tolerance_value,
            )
        )

    return SemanticValidationResult(
        passed=True,
        proposal_count=len(mappings),
        mapped_annotation_count=len(target_set),
        changed_annotation_count=len(changed_ids),
        changed_annotation_ids=changed_ids,
        changed_fields=tuple(sorted(changed_fields)),
        image_count_delta=image_count_delta,
        annotation_count_delta=annotation_count_delta,
        category_count_delta=category_count_delta,
        image_id_set_unchanged=True,
        annotation_id_set_unchanged=True,
        category_id_set_unchanged=True,
        non_target_annotations_unchanged=True,
        category_definitions_unchanged=True,
    )


def build_diff_rows(
    mappings: tuple[NativeAnnotationMapping, ...],
    *,
    source_coco_sha256: str,
    staged_coco_sha256: str,
) -> tuple[CorrectionDiffRow, ...]:
    if len(mappings) != 2:
        raise StagedCocoValidationError(
            "exactly two annotation mappings are required for diff rows"
        )
    try:
        require_distinct_native_annotation_mappings(mappings)
    except AnnotationMappingError as exc:
        raise StagedCocoValidationError(str(exc)) from exc
    source_hash = _validated_sha256(source_coco_sha256, "source COCO SHA256")
    staged_hash = _validated_sha256(staged_coco_sha256, "staged COCO SHA256")
    return tuple(
        CorrectionDiffRow(
            schema_version="1",
            phase04_5m_review_case_id=mapping.phase04_5m_review_case_id,
            correction_case_id=mapping.correction_case_id,
            proposal_fingerprint=mapping.proposal_fingerprint,
            source_split=mapping.source_split,
            image_id=mapping.image_id,
            native_coco_image_id=mapping.native_image_id,
            native_coco_annotation_id=mapping.native_annotation_id,
            native_category_id=mapping.native_category_id,
            before_bbox_xywh=mapping.before_bbox_xywh,
            before_bbox_xyxy=mapping.before_bbox_xyxy,
            before_area=mapping.before_area,
            after_bbox_xywh=mapping.after_bbox_xywh,
            after_bbox_xyxy=mapping.after_bbox_xyxy,
            after_area=mapping.after_area,
            changed_fields=("area", "bbox"),
            source_coco_sha256=source_hash,
            staged_coco_sha256=staged_hash,
        )
        for mapping in mappings
    )


def build_staged_coco(
    source: CocoDocument,
    mappings: tuple[NativeAnnotationMapping, ...],
    replacements: Mapping[int, AbsoluteXYXY],
    *,
    source_sha256: str,
) -> StagedCocoBuild:
    source_hash = _validated_sha256(source_sha256, "source SHA256")
    if len(mappings) != 2:
        raise StagedCocoValidationError("exactly two annotation mappings are required")
    try:
        require_distinct_native_annotation_mappings(mappings)
    except AnnotationMappingError as exc:
        raise StagedCocoValidationError(str(exc)) from exc

    target_ids = {mapping.native_annotation_id for mapping in mappings}
    replacement_ids = set(replacements)
    if replacement_ids != target_ids:
        raise StagedCocoValidationError(
            "replacement annotation IDs must equal mapped annotation IDs"
        )

    payload = copy.deepcopy(source.payload)
    if not isinstance(payload, dict):
        raise StagedCocoValidationError("source COCO root must be an object")
    annotations = payload.get("annotations")
    if not isinstance(annotations, list):
        raise StagedCocoValidationError("source COCO annotations must be a list")

    positions: dict[int, int] = {}
    for index, annotation in enumerate(annotations):
        if not isinstance(annotation, Mapping):
            raise StagedCocoValidationError(
                f"source annotation[{index}] must be an object"
            )
        annotation_id = annotation.get("id")
        if isinstance(annotation_id, bool) or not isinstance(annotation_id, int):
            raise StagedCocoValidationError("source annotation ID must be an integer")
        if annotation_id in positions:
            raise StagedCocoValidationError(
                f"duplicate annotation ID: {annotation_id}"
            )
        positions[annotation_id] = index

    for mapping in mappings:
        annotation_id = mapping.native_annotation_id
        if annotation_id not in positions:
            raise StagedCocoValidationError(
                f"mapped annotation is missing from source: {annotation_id}"
            )
        annotations[positions[annotation_id]] = apply_reviewed_geometry(
            annotations[positions[annotation_id]],
            replacements[annotation_id],
        )

    validation = validate_staged_coco(
        source,
        payload,
        mappings,
        ("bbox", "area"),
        tolerance=0.0,
    )
    staged_hash = hashlib.sha256(canonical_json_bytes(payload)).hexdigest().upper()
    diff_rows = build_diff_rows(
        mappings,
        source_coco_sha256=source_hash,
        staged_coco_sha256=staged_hash,
    )
    return StagedCocoBuild(
        payload=payload,
        mappings=mappings,
        diff_rows=diff_rows,
        validation=validation,
    )




BEFORE_COLOR = (255, 165, 0)
AFTER_COLOR = (0, 200, 0)
COMBINED_BEFORE_COLOR = (255, 80, 80)
COMBINED_AFTER_COLOR = (80, 220, 120)
LINE_WIDTH = 4
JPEG_QUALITY = 95
JPEG_SUBSAMPLING = 0

_TIMESTAMP_RE = re.compile(r"^\d{8}_\d{9}$")
_MANIFEST_FIELDS = ("relative_path", "size_bytes", "sha256")
_SOURCE_COPY_MAP = (
    (
        "exports/annotation_correction_proposals_reviewed.csv",
        "source/annotation_correction_proposals_reviewed.csv",
    ),
    (
        "exports/annotation_correction_proposals_reviewed.json",
        "source/annotation_correction_proposals_reviewed.json",
    ),
    (
        "exports/correction_review_export_result.json",
        "source/correction_review_export_result.json",
    ),
    ("source/source_contract.json", "source/source_contract.json"),
    ("source/source_manifest.csv", "source/source_manifest.csv"),
)


def _workspace_timestamp(value: str | None) -> str:
    timestamp = value
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S%f")[:-3]
    if _TIMESTAMP_RE.fullmatch(timestamp) is None:
        raise StagedWorkspaceError(
            "timestamp must match yyyyMMdd_HHmmssfff"
        )
    return timestamp


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_csv(
    path: Path,
    rows: Iterable[Mapping[str, object]],
    fieldnames: Iterable[str],
) -> None:
    names = tuple(fieldnames)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=names)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in names})


def _read_csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return tuple(dict(row) for row in csv.DictReader(handle))
    except (OSError, csv.Error) as exc:
        raise StagedWorkspaceError(f"cannot read CSV {path}: {exc}") from exc


def _safe_workspace_member(root: Path, relative_text: str, label: str) -> Path:
    relative = Path(relative_text.replace("\\", "/"))
    if (
        not relative_text.strip()
        or relative.is_absolute()
        or relative.drive
        or ".." in relative.parts
    ):
        raise StagedWorkspaceError(f"{label} is not a safe relative path")
    base = root.resolve()
    candidate = (base / relative).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise StagedWorkspaceError(f"{label} escapes workspace root") from exc
    return candidate


def _preflight_original_images(
    completed_review_root: Path,
) -> tuple[dict[str, str], ...]:
    source_csv = (
        completed_review_root / "source/correction_review_source.csv"
    ).resolve()
    rows = _read_csv_rows(source_csv)
    if not rows:
        raise StagedWorkspaceError("correction review source CSV is empty")
    for row in rows:
        relative = row.get("original_image_relpath", "")
        original = _safe_workspace_member(
            completed_review_root,
            relative,
            "original_image_relpath",
        )
        if not original.is_file():
            raise StagedWorkspaceError(
                f"authoritative original image is missing: {relative}"
            )
    return rows


def _fingerprint_file_tree(root: Path) -> str:
    digest = hashlib.sha256()
    resolved = root.resolve()
    if not resolved.exists():
        digest.update(b"ABSENT")
        return digest.hexdigest().upper()
    if not resolved.is_dir():
        raise StagedWorkspaceError(
            f"protected external assets path is not a directory: {resolved}"
        )
    files = sorted(
        (path for path in resolved.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(resolved).as_posix(),
    )
    digest.update(f"FILES:{len(files)}\n".encode("utf-8"))
    for path in files:
        relative = path.relative_to(resolved).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.stat().st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest().upper()


def _bbox_text(values: tuple[float, float, float, float]) -> str:
    return "[" + ",".join(f"{value:.3f}" for value in values) + "]"


def _draw_overlay(
    source: Image.Image,
    *,
    mapping: NativeAnnotationMapping,
    before_color: tuple[int, int, int] | None,
    after_color: tuple[int, int, int] | None,
) -> Image.Image:
    image = source.copy().convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    if before_color is not None:
        draw.rectangle(
            mapping.before_bbox_xyxy,
            outline=before_color,
            width=LINE_WIDTH,
        )
    if after_color is not None:
        draw.rectangle(
            mapping.after_bbox_xyxy,
            outline=after_color,
            width=LINE_WIDTH,
        )

    width, height = image.size
    lines = (
        (
            f"case={mapping.phase04_5m_review_case_id} "
            f"ann={mapping.native_annotation_id} image={width}x{height}"
        ),
        f"before={_bbox_text(mapping.before_bbox_xyxy)}",
        f"after={_bbox_text(mapping.after_bbox_xyxy)}",
    )
    panel_height = 48
    draw.rectangle((0, 0, width, panel_height), fill=(0, 0, 0))
    y = 2
    for line in lines:
        draw.text((4, y), line, fill=(255, 255, 255), font=font)
        y += 15
    return image


def _save_deterministic_jpeg(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        path,
        format="JPEG",
        quality=JPEG_QUALITY,
        subsampling=JPEG_SUBSAMPLING,
        optimize=False,
        progressive=False,
        exif=b"",
    )


def render_annotation_overlays(
    original_image: Path,
    mapping: NativeAnnotationMapping,
    output_root: Path,
) -> OverlayArtifacts:
    original = Path(original_image).resolve()
    if not original.is_file():
        raise StagedWorkspaceError(
            f"authoritative original image is missing: {original}"
        )
    try:
        with Image.open(original) as opened:
            opened.load()
            source = opened.convert("RGB")
    except (OSError, ValueError) as exc:
        raise StagedWorkspaceError(
            f"cannot read authoritative original image: {original}"
        ) from exc

    before = output_root / "before" / f"{mapping.correction_case_id}.jpg"
    after = output_root / "after" / f"{mapping.correction_case_id}.jpg"
    combined = output_root / "combined" / f"{mapping.correction_case_id}.jpg"

    _save_deterministic_jpeg(
        _draw_overlay(
            source,
            mapping=mapping,
            before_color=BEFORE_COLOR,
            after_color=None,
        ),
        before,
    )
    _save_deterministic_jpeg(
        _draw_overlay(
            source,
            mapping=mapping,
            before_color=None,
            after_color=AFTER_COLOR,
        ),
        after,
    )
    _save_deterministic_jpeg(
        _draw_overlay(
            source,
            mapping=mapping,
            before_color=COMBINED_BEFORE_COLOR,
            after_color=COMBINED_AFTER_COLOR,
        ),
        combined,
    )
    return OverlayArtifacts(before=before, after=after, combined=combined)


def _mapping_row(mapping: NativeAnnotationMapping) -> dict[str, object]:
    return {
        "phase04_5m_review_case_id": mapping.phase04_5m_review_case_id,
        "correction_case_id": mapping.correction_case_id,
        "proposal_fingerprint": mapping.proposal_fingerprint,
        "source_split": mapping.source_split,
        "image_id": mapping.image_id,
        "local_gt_bbox_id": mapping.local_gt_bbox_id,
        "native_coco_image_id": mapping.native_image_id,
        "native_coco_annotation_id": mapping.native_annotation_id,
        "native_category_id": mapping.native_category_id,
        "before_bbox_xywh": _compact_json(mapping.before_bbox_xywh),
        "before_bbox_xyxy": _compact_json(mapping.before_bbox_xyxy),
        "before_area": mapping.before_area,
        "after_bbox_xywh": _compact_json(mapping.after_bbox_xywh),
        "after_bbox_xyxy": _compact_json(mapping.after_bbox_xyxy),
        "after_area": mapping.after_area,
    }


def _diff_json_row(row: CorrectionDiffRow) -> dict[str, object]:
    return {
        "schema_version": row.schema_version,
        "phase04_5m_review_case_id": row.phase04_5m_review_case_id,
        "correction_case_id": row.correction_case_id,
        "proposal_fingerprint": row.proposal_fingerprint,
        "source_split": row.source_split,
        "image_id": row.image_id,
        "native_coco_image_id": row.native_coco_image_id,
        "native_coco_annotation_id": row.native_coco_annotation_id,
        "native_category_id": row.native_category_id,
        "before_bbox_xywh": list(row.before_bbox_xywh),
        "before_bbox_xyxy": list(row.before_bbox_xyxy),
        "before_area": row.before_area,
        "after_bbox_xywh": list(row.after_bbox_xywh),
        "after_bbox_xyxy": list(row.after_bbox_xyxy),
        "after_area": row.after_area,
        "changed_fields": list(row.changed_fields),
        "source_coco_sha256": row.source_coco_sha256,
        "staged_coco_sha256": row.staged_coco_sha256,
    }


def _write_diff_markdown(
    path: Path,
    rows: tuple[CorrectionDiffRow, ...],
) -> None:
    lines = [
        "# Phase 04.5N Staged Annotation Correction Diff",
        "",
        "| Review case | Correction case | Native annotation | Before xywh | After xywh | Changed fields |",
        "|---|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                (
                    row.phase04_5m_review_case_id,
                    row.correction_case_id,
                    str(row.native_coco_annotation_id),
                    _compact_json(row.before_bbox_xywh),
                    _compact_json(row.after_bbox_xywh),
                    _compact_json(row.changed_fields),
                )
            )
            + " |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _manifest_rows(
    workspace_root: Path,
    relative_paths: Iterable[str],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for relative in sorted(set(relative_paths)):
        member = _safe_workspace_member(
            workspace_root,
            relative,
            "manifest relative_path",
        )
        if not member.is_file():
            raise StagedWorkspaceError(
                f"manifest member does not exist: {relative}"
            )
        rows.append(
            {
                "relative_path": relative,
                "size_bytes": member.stat().st_size,
                "sha256": sha256_file(member),
            }
        )
    return tuple(rows)


def _verify_manifest_rows(
    workspace_root: Path,
    rows: Iterable[Mapping[str, object]],
) -> None:
    for row in rows:
        relative = str(row.get("relative_path", ""))
        member = _safe_workspace_member(
            workspace_root,
            relative,
            "manifest relative_path",
        )
        if not member.is_file():
            raise StagedWorkspaceError(f"missing manifest member: {relative}")
        if member.stat().st_size != int(row.get("size_bytes", -1)):
            raise StagedWorkspaceError(
                f"manifest size mismatch: {relative}"
            )
        if sha256_file(member) != str(row.get("sha256", "")).upper():
            raise StagedWorkspaceError(
                f"manifest sha256 mismatch: {relative}"
            )


def _expected_workspace_files(
    mappings: tuple[NativeAnnotationMapping, ...],
) -> set[str]:
    files = {
        destination for _source, destination in _SOURCE_COPY_MAP
    }
    files.update(
        {
            "canonical_snapshot/canonical_validation_coco.json",
            "canonical_snapshot/canonical_source_contract.json",
            "staged/staged_corrected_validation_coco.json",
            "diff/annotation_correction_mapping.csv",
            "diff/annotation_correction_diff.csv",
            "diff/annotation_correction_diff.json",
            "diff/annotation_correction_diff.md",
            "evidence/semantic_validation.json",
            "evidence/workspace_manifest.csv",
            "evidence/SHA256SUMS.csv",
            "evidence/gate_result.json",
        }
    )
    for mapping in mappings:
        for category in ("before", "after", "combined"):
            files.add(
                f"overlays/{category}/{mapping.correction_case_id}.jpg"
            )
    return files


def _actual_workspace_files(workspace_root: Path) -> set[str]:
    return {
        path.relative_to(workspace_root).as_posix()
        for path in workspace_root.rglob("*")
        if path.is_file()
    }


def _write_blocked_result(
    *,
    config: Phase04_5NConfig,
    requested_timestamp: str,
    failed_stage: str,
    error: BaseException,
    canonical_source_sha256: str | None,
) -> Path:
    blocked_root = config.n1_workspace_base_root / "_blocked_results"
    blocked_root.mkdir(parents=True, exist_ok=True)
    unique = uuid.uuid4().hex
    path = blocked_root / (
        f"phase04_5n_staging_blocked_{requested_timestamp}_{unique}.json"
    )
    payload = {
        "schema_version": "1",
        "gate_id": "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS",
        "outcome": "BLOCKED",
        "classification": "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_BLOCKED",
        "requested_timestamp": requested_timestamp,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "failed_stage": failed_stage,
        "exception_type": type(error).__name__,
        "exception_message": str(error),
        "canonical_source_sha256": canonical_source_sha256,
        "canonical_source_modified": False,
        "test_split_read": False,
        "model_inference_executed": False,
        "dataset_modified": False,
        "registry_modified": False,
        "fixed_splits_modified": False,
        "training_started": False,
        "retraining_status": "NOT_YET_APPROVED",
        "deployment_acceptance": "NOT_YET_APPROVED",
    }
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(
                payload,
                handle,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            handle.write("\n")
    except OSError as exc:
        raise StagedWorkspaceError(
            f"failed to write BLOCKED evidence after {error}: {exc}"
        ) from exc
    return path


def prepare_staged_correction_workspace(
    config: Phase04_5NConfig,
    completed_review_root: Path,
    *,
    timestamp: str | None = None,
) -> PreparedStagedCorrectionWorkspace:
    requested_timestamp = _workspace_timestamp(timestamp)
    completed_root = Path(completed_review_root).resolve()
    base_root = config.n1_workspace_base_root.resolve()
    prefix = config.n1_workspace_prefix
    final_root = base_root / f"{prefix}_{requested_timestamp}"
    staging_root = base_root / f".{prefix}_{requested_timestamp}.staging"
    protected_root = (
        config.project_root / "outputs/metadata/external_assets"
    ).resolve()

    failed_stage = "preflight"
    canonical_source_sha256: str | None = None
    base_root.mkdir(parents=True, exist_ok=True)

    try:
        if final_root.exists():
            raise StagedWorkspaceError(
                f"final workspace already exists: {final_root}"
            )
        if staging_root.exists():
            raise StagedWorkspaceError(
                f"staging workspace already exists: {staging_root}"
            )

        failed_stage = "preflight_original_images"
        source_rows = _preflight_original_images(completed_root)

        failed_stage = "verify_predecessor"
        verified = verify_completed_review_workspace(config, completed_root)

        failed_stage = "resolve_canonical_source"
        canonical_source = resolve_canonical_validation_coco(config)
        canonical_source_sha256 = canonical_source.sha256
        protected_before = _fingerprint_file_tree(protected_root)

        failed_stage = "load_canonical_source"
        ledger = SourceAccessLedger()
        coco = load_coco_document(canonical_source, ledger)

        source_by_case = {
            row.get("review_case_id", ""): row for row in source_rows
        }
        if len(source_by_case) != len(source_rows):
            raise StagedWorkspaceError(
                "source rows contain duplicate or missing review_case_id"
            )

        failed_stage = "map_annotations"
        mappings = tuple(
            map_reviewed_proposal_to_native_annotation(
                proposal,
                source_by_case[proposal.review_case_id],
                coco,
                tolerance=config.coordinate_tolerance_pixels,
            )
            for proposal in verified.proposals
        )
        require_distinct_native_annotation_mappings(mappings)
        replacements = {
            mapping.native_annotation_id: AbsoluteXYXY(
                *mapping.after_bbox_xyxy
            )
            for mapping in mappings
        }

        failed_stage = "build_staged_coco"
        build = build_staged_coco(
            coco,
            mappings,
            replacements,
            source_sha256=canonical_source.sha256,
        )

        staging_root.mkdir()
        for directory in (
            "source",
            "canonical_snapshot",
            "staged",
            "diff",
            "overlays/before",
            "overlays/after",
            "overlays/combined",
            "evidence",
        ):
            (staging_root / directory).mkdir(parents=True, exist_ok=True)

        failed_stage = "copy_predecessor_evidence"
        for source_relative, destination_relative in _SOURCE_COPY_MAP:
            source_path = _safe_workspace_member(
                completed_root,
                source_relative,
                "predecessor source path",
            )
            destination_path = _safe_workspace_member(
                staging_root,
                destination_relative,
                "workspace destination path",
            )
            shutil.copy2(source_path, destination_path)

        failed_stage = "snapshot_canonical_source"
        canonical_snapshot = (
            staging_root
            / "canonical_snapshot/canonical_validation_coco.json"
        )
        shutil.copy2(canonical_source.path, canonical_snapshot)
        if sha256_file(canonical_snapshot) != canonical_source.sha256:
            raise StagedWorkspaceError(
                "canonical snapshot sha256 does not match source"
            )
        canonical_contract = {
            "schema_version": "1",
            "canonical_source_relative_path": (
                canonical_source.relative_path.as_posix()
            ),
            "canonical_source_size_bytes": canonical_source.size_bytes,
            "canonical_source_sha256": canonical_source.sha256,
            "canonical_source_split": canonical_source.split,
            "canonical_source_image_count": len(coco.images_by_id),
            "canonical_source_annotation_count": len(coco.annotations_by_id),
            "canonical_source_category_count": len(coco.categories_by_id),
            "canonical_source_schema_summary": {
                "root_keys": sorted(coco.payload),
                "category_definitions": list(
                    coco.categories_by_id.values()
                ),
            },
        }
        _write_json(
            staging_root
            / "canonical_snapshot/canonical_source_contract.json",
            canonical_contract,
        )

        failed_stage = "write_staged_coco"
        staged_path = (
            staging_root
            / "staged"
            / config.staged_coco_name
        )
        staged_path.write_bytes(canonical_json_bytes(build.payload))
        staged_sha256 = sha256_file(staged_path)
        if staged_sha256 != build.diff_rows[0].staged_coco_sha256:
            raise StagedWorkspaceError(
                "staged COCO sha256 does not match semantic build"
            )

        failed_stage = "write_diff_evidence"
        mapping_rows = tuple(_mapping_row(mapping) for mapping in mappings)
        _write_csv(
            staging_root / "diff/annotation_correction_mapping.csv",
            mapping_rows,
            tuple(mapping_rows[0]),
        )
        diff_csv_rows = tuple(row.as_dict() for row in build.diff_rows)
        _write_csv(
            staging_root / "diff/annotation_correction_diff.csv",
            diff_csv_rows,
            tuple(diff_csv_rows[0]),
        )
        _write_json(
            staging_root / "diff/annotation_correction_diff.json",
            {
                "schema_version": "1",
                "correction_count": len(build.diff_rows),
                "corrections": [
                    _diff_json_row(row) for row in build.diff_rows
                ],
            },
        )
        _write_diff_markdown(
            staging_root / "diff/annotation_correction_diff.md",
            build.diff_rows,
        )
        semantic_payload = asdict(build.validation)
        _write_json(
            staging_root / "evidence/semantic_validation.json",
            semantic_payload,
        )

        failed_stage = "render_overlays"
        source_rows_by_case = {
            row["review_case_id"]: row for row in source_rows
        }
        for mapping in mappings:
            source_row = source_rows_by_case[
                mapping.phase04_5m_review_case_id
            ]
            original = _safe_workspace_member(
                completed_root,
                source_row["original_image_relpath"],
                "original image path",
            )
            render_annotation_overlays(
                original,
                mapping,
                staging_root / "overlays",
            )

        failed_stage = "verify_source_stability"
        if sha256_file(canonical_source.path) != canonical_source.sha256:
            raise StagedWorkspaceError(
                "canonical source sha256 drift detected during N1 staging"
            )
        if _fingerprint_file_tree(protected_root) != protected_before:
            raise StagedWorkspaceError(
                "protected external assets fingerprint changed during N1 staging"
            )

        failed_stage = "write_gate_result"
        gate_result = {
            "schema_version": "1",
            "gate_id": "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS",
            "outcome": "PASS",
            "classification": config.n1_gate_classification,
            "generated_timestamp": requested_timestamp,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "predecessor_workspace": str(verified.workspace_root),
            "predecessor_review_case_ids": list(
                verified.review_case_ids
            ),
            "proposal_count": len(verified.proposals),
            "mapped_annotation_count": len(mappings),
            "changed_annotation_count": (
                build.validation.changed_annotation_count
            ),
            "changed_native_annotation_ids": list(
                build.validation.changed_annotation_ids
            ),
            "image_count_delta": build.validation.image_count_delta,
            "annotation_count_delta": (
                build.validation.annotation_count_delta
            ),
            "category_count_delta": build.validation.category_count_delta,
            "canonical_source_relative_path": (
                canonical_source.relative_path.as_posix()
            ),
            "canonical_source_sha256": canonical_source.sha256,
            "staged_coco_sha256": staged_sha256,
            "canonical_source_modified": False,
            "test_split_read": ledger.test_split_read,
            "model_inference_executed": False,
            "dataset_modified": False,
            "registry_modified": False,
            "fixed_splits_modified": False,
            "training_started": False,
            "retraining_status": "NOT_YET_APPROVED",
            "deployment_acceptance": "NOT_YET_APPROVED",
        }
        gate_result_path = staging_root / "evidence/gate_result.json"
        _write_json(gate_result_path, gate_result)

        failed_stage = "write_and_verify_manifests"
        content_paths = sorted(
            _actual_workspace_files(staging_root)
            - {
                "evidence/workspace_manifest.csv",
                "evidence/SHA256SUMS.csv",
            }
        )
        workspace_rows = _manifest_rows(staging_root, content_paths)
        workspace_manifest_path = (
            staging_root / "evidence/workspace_manifest.csv"
        )
        _write_csv(
            workspace_manifest_path,
            workspace_rows,
            _MANIFEST_FIELDS,
        )
        _verify_manifest_rows(staging_root, workspace_rows)

        checksum_paths = sorted(
            _actual_workspace_files(staging_root)
            - {"evidence/SHA256SUMS.csv"}
        )
        checksum_rows = _manifest_rows(staging_root, checksum_paths)
        checksum_path = staging_root / "evidence/SHA256SUMS.csv"
        _write_csv(
            checksum_path,
            checksum_rows,
            _MANIFEST_FIELDS,
        )
        _verify_manifest_rows(staging_root, checksum_rows)

        expected_files = _expected_workspace_files(mappings)
        actual_files = _actual_workspace_files(staging_root)
        if actual_files != expected_files:
            missing = sorted(expected_files - actual_files)
            extra = sorted(actual_files - expected_files)
            raise StagedWorkspaceError(
                f"workspace inventory mismatch; missing={missing}, extra={extra}"
            )

        failed_stage = "final_source_stability"
        if sha256_file(canonical_source.path) != canonical_source.sha256:
            raise StagedWorkspaceError(
                "canonical source sha256 drift detected before final rename"
            )
        if _fingerprint_file_tree(protected_root) != protected_before:
            raise StagedWorkspaceError(
                "protected external assets fingerprint changed before final rename"
            )

        failed_stage = "atomic_final_rename"
        os.replace(staging_root, final_root)
        final_gate_result = final_root / "evidence/gate_result.json"
        return PreparedStagedCorrectionWorkspace(
            workspace_root=final_root,
            gate_result_path=final_gate_result,
            source_coco_sha256=canonical_source.sha256,
            staged_coco_sha256=staged_sha256,
            changed_annotation_ids=build.validation.changed_annotation_ids,
        )
    except Exception as exc:
        if staging_root.exists():
            shutil.rmtree(staging_root)
        if isinstance(exc, StagedWorkspaceError):
            wrapped = exc
        elif isinstance(
            exc,
            (
                PromotionContractError,
                AnnotationMappingError,
                StagedCocoValidationError,
                OSError,
                csv.Error,
                json.JSONDecodeError,
            ),
        ):
            wrapped = StagedWorkspaceError(str(exc))
        else:
            wrapped = StagedWorkspaceError(str(exc))
        _write_blocked_result(
            config=config,
            requested_timestamp=requested_timestamp,
            failed_stage=failed_stage,
            error=exc,
            canonical_source_sha256=canonical_source_sha256,
        )
        raise wrapped from exc


def _cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build and validate a staged Phase 04.5N annotation correction "
            "workspace without modifying canonical annotations."
        )
    )
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--completed-review-workspace", required=True, type=Path
    )
    parser.add_argument("--timestamp", required=True)
    return parser


def _blocked_cli_payload(error: Exception) -> dict[str, object]:
    return {
        "outcome": "BLOCKED",
        "classification": (
            "PHASE_04_5N_STAGED_ANNOTATION_CORRECTIONS_BLOCKED"
        ),
        "exception_type": type(error).__name__,
        "exception_message": str(error),
        "n1_executed": False,
        "n2_executed": False,
        "canonical_source_modified": False,
        "test_split_read": False,
        "model_inference_executed": False,
        "dataset_modified": False,
        "registry_modified": False,
        "fixed_splits_modified": False,
        "training_started": False,
        "retraining_status": "NOT_YET_APPROVED",
        "deployment_acceptance": "NOT_YET_APPROVED",
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _cli_parser().parse_args(argv)
    try:
        config = load_phase04_5n_config(args.config, args.project_root)
        prepared = prepare_staged_correction_workspace(
            config,
            args.completed_review_workspace,
            timestamp=args.timestamp,
        )
        payload = json.loads(
            prepared.gate_result_path.read_text(encoding="utf-8")
        )
        payload["workspace_root"] = str(prepared.workspace_root)
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        )
        return 0
    except Exception as error:
        print(
            json.dumps(
                _blocked_cli_payload(error),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ),
            file=sys.stderr,
        )
        return 1
