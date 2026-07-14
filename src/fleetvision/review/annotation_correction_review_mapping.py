from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Mapping


class CorrectionMappingValidationError(ValueError):
    """Raised when a correction-review decision violates the approved contract."""


STATUS_LABELS: Mapping[str, str] = {
    "pending": "尚未完成",
    "reviewed": "已完成",
    "needs_adjudication": "待裁決",
}

DECISION_LABELS: Mapping[str, str] = {
    "CONFIRM_GT_CORRECTION_REQUIRED": "確認需要修正 GT",
    "REJECT_CORRECTION_KEEP_CURRENT_GT": "拒絕修正，保留現有 GT",
    "NEEDS_ADJUDICATION": "需要進一步裁決",
}

OPERATION_LABELS: Mapping[str, str] = {
    "RESIZE_OR_REDRAW_BBOX": "調整或重畫 bbox",
    "REMOVE_DUPLICATE_BBOX": "移除重複 bbox",
    "REMOVE_INVALID_BBOX": "移除無效 bbox",
    "ADD_MISSING_BBOX": "新增缺漏 bbox",
    "OTHER": "其他",
    "NOT_APPLICABLE": "不適用",
}

CONTROLLED_OPTIONS: Mapping[str, tuple[str, ...]] = {
    "correction_review_status": tuple(STATUS_LABELS),
    "correction_decision": tuple(DECISION_LABELS),
    "correction_operation": tuple(OPERATION_LABELS),
}


@dataclass(frozen=True)
class BBoxCoordinates:
    x1: float
    y1: float
    x2: float
    y2: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class CorrectionReviewSelection:
    correction_review_status: str = "pending"
    correction_decision: str = "NEEDS_ADJUDICATION"
    correction_operation: str = "NOT_APPLICABLE"
    target_gt_bbox_ids: tuple[str, ...] = ()
    replacement_bbox: BBoxCoordinates | None = None
    correction_reason: str = ""


@dataclass(frozen=True)
class CanonicalCorrectionFields:
    correction_review_status: str
    correction_decision: str
    correction_operation: str
    target_gt_bbox_ids_json: str
    replacement_bbox_coordinates_json: str
    correction_reason: str
    correction_reviewer: str
    correction_reviewed_at_utc: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _normalize(value: object) -> str:
    return str(value or "").strip()


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_target_bbox_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, tuple):
        raw = list(value)
    elif isinstance(value, list):
        raw = value
    elif value in (None, ""):
        raw = []
    else:
        try:
            raw = json.loads(str(value))
        except json.JSONDecodeError as exc:
            raise CorrectionMappingValidationError("target bbox IDs 不是有效 JSON") from exc
    if not isinstance(raw, list):
        raise CorrectionMappingValidationError("target bbox IDs 必須是 JSON array")
    normalized = tuple(sorted(str(item).strip() for item in raw))
    if any(not item for item in normalized):
        raise CorrectionMappingValidationError("target bbox ID 不可空白")
    if len(normalized) != len(set(normalized)):
        raise CorrectionMappingValidationError("target bbox IDs 不可重複")
    return normalized


def parse_replacement_bbox(value: object) -> BBoxCoordinates | None:
    if value in (None, ""):
        return None
    if isinstance(value, BBoxCoordinates):
        return value
    if isinstance(value, dict):
        raw = value
    else:
        try:
            raw = json.loads(str(value))
        except json.JSONDecodeError as exc:
            raise CorrectionMappingValidationError("replacement bbox 不是有效 JSON") from exc
    if not isinstance(raw, dict) or set(raw) != {"x1", "y1", "x2", "y2"}:
        raise CorrectionMappingValidationError("replacement bbox 欄位必須為 x1/y1/x2/y2")
    try:
        box = BBoxCoordinates(*(float(raw[key]) for key in ("x1", "y1", "x2", "y2")))
    except (TypeError, ValueError) as exc:
        raise CorrectionMappingValidationError("replacement bbox 座標必須是數值") from exc
    if not all(math.isfinite(number) for number in box.as_dict().values()):
        raise CorrectionMappingValidationError("replacement bbox 座標必須是有限數值")
    return box


def _validate_bbox(box: BBoxCoordinates, image_width: int, image_height: int) -> None:
    if image_width <= 0 or image_height <= 0:
        raise CorrectionMappingValidationError("影像尺寸必須是正整數")
    if not (box.x1 < box.x2 and box.y1 < box.y2):
        raise CorrectionMappingValidationError("replacement bbox 必須滿足 x1<x2 且 y1<y2")
    if box.x1 < 0 or box.y1 < 0 or box.x2 > image_width or box.y2 > image_height:
        raise CorrectionMappingValidationError("replacement bbox 超出影像範圍")


def validate_selection(
    selection: CorrectionReviewSelection,
    *,
    image_width: int,
    image_height: int,
    available_gt_bbox_ids: tuple[str, ...],
) -> None:
    status = _normalize(selection.correction_review_status)
    decision = _normalize(selection.correction_decision)
    operation = _normalize(selection.correction_operation)
    reason = _normalize(selection.correction_reason)
    targets = parse_target_bbox_ids(selection.target_gt_bbox_ids)
    replacement = parse_replacement_bbox(selection.replacement_bbox)

    values = {
        "correction_review_status": status,
        "correction_decision": decision,
        "correction_operation": operation,
    }
    for key, value in values.items():
        if value not in CONTROLLED_OPTIONS[key]:
            raise CorrectionMappingValidationError(f"{key}={value!r} 不是核准的 controlled value")

    available = tuple(available_gt_bbox_ids)
    unknown = [target for target in targets if target not in available]
    if unknown:
        raise CorrectionMappingValidationError(f"target GT bbox ID 不存在：{unknown}")

    if status == "pending":
        if decision != "NEEDS_ADJUDICATION" or operation != "NOT_APPLICABLE":
            raise CorrectionMappingValidationError("pending 狀態不得預先確認修正")
        if targets or replacement is not None or reason:
            raise CorrectionMappingValidationError("pending 狀態不得包含正式修正內容")
        return

    if not reason:
        raise CorrectionMappingValidationError("已審核或待裁決案例必須填寫 correction reason")

    if decision == "NEEDS_ADJUDICATION":
        if status != "needs_adjudication":
            raise CorrectionMappingValidationError("NEEDS_ADJUDICATION 必須搭配 needs_adjudication 狀態")
        if operation != "NOT_APPLICABLE" or targets or replacement is not None:
            raise CorrectionMappingValidationError("待裁決案例不得包含修正操作或 geometry")
        return

    if status != "reviewed":
        raise CorrectionMappingValidationError("final correction decision 必須搭配 reviewed 狀態")

    if decision == "REJECT_CORRECTION_KEEP_CURRENT_GT":
        if operation != "NOT_APPLICABLE":
            raise CorrectionMappingValidationError("保留現有 GT 必須使用 NOT_APPLICABLE")
        if targets or replacement is not None:
            raise CorrectionMappingValidationError("保留現有 GT 不得指定 target 或 replacement geometry")
        return

    if decision != "CONFIRM_GT_CORRECTION_REQUIRED":
        raise CorrectionMappingValidationError("未知 correction decision")
    if operation == "NOT_APPLICABLE":
        raise CorrectionMappingValidationError("確認修正時不可使用 NOT_APPLICABLE")

    if operation in {"REMOVE_DUPLICATE_BBOX", "REMOVE_INVALID_BBOX"}:
        if not targets:
            raise CorrectionMappingValidationError("移除 bbox 必須指定至少一個 target GT bbox ID")
        if replacement is not None:
            raise CorrectionMappingValidationError("移除 bbox 不得包含 replacement geometry")
        return

    if operation == "RESIZE_OR_REDRAW_BBOX":
        if len(targets) != 1:
            raise CorrectionMappingValidationError("調整或重畫 bbox 必須指定一個 target GT bbox ID")
        if replacement is None:
            raise CorrectionMappingValidationError("調整或重畫 bbox 必須提供 replacement geometry")
        _validate_bbox(replacement, image_width, image_height)
        return

    if operation == "ADD_MISSING_BBOX":
        if targets:
            raise CorrectionMappingValidationError("新增 bbox 不得指定既有 target GT bbox ID")
        if replacement is None:
            raise CorrectionMappingValidationError("新增 bbox 必須提供 replacement geometry")
        _validate_bbox(replacement, image_width, image_height)
        return

    if operation == "OTHER":
        if replacement is not None:
            _validate_bbox(replacement, image_width, image_height)
        return

    raise CorrectionMappingValidationError(f"未支援的 correction operation：{operation}")


def derive_canonical_correction_fields(
    selection: CorrectionReviewSelection,
    *,
    reviewer: str,
    reviewed_at: datetime,
    image_width: int,
    image_height: int,
    available_gt_bbox_ids: tuple[str, ...],
) -> CanonicalCorrectionFields:
    validate_selection(
        selection,
        image_width=image_width,
        image_height=image_height,
        available_gt_bbox_ids=available_gt_bbox_ids,
    )
    reviewer_value = _normalize(reviewer)
    if not reviewer_value:
        raise CorrectionMappingValidationError("reviewer 不可空白")
    if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
        raise CorrectionMappingValidationError("reviewed_at 必須包含時區")

    targets = parse_target_bbox_ids(selection.target_gt_bbox_ids)
    replacement = parse_replacement_bbox(selection.replacement_bbox)
    return CanonicalCorrectionFields(
        correction_review_status=_normalize(selection.correction_review_status),
        correction_decision=_normalize(selection.correction_decision),
        correction_operation=_normalize(selection.correction_operation),
        target_gt_bbox_ids_json=canonical_json(list(targets)),
        replacement_bbox_coordinates_json="" if replacement is None else canonical_json(replacement.as_dict()),
        correction_reason=_normalize(selection.correction_reason),
        correction_reviewer=reviewer_value,
        correction_reviewed_at_utc=reviewed_at.isoformat(),
    )


def proposal_fingerprint(
    source_case_fingerprint: str,
    canonical: CanonicalCorrectionFields,
) -> str:
    fields = canonical.as_dict()
    payload = "\x1f".join(
        [str(source_case_fingerprint).strip().upper()]
        + [fields[key] for key in fields]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()
