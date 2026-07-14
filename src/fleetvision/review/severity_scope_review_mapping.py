from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Mapping


class ScopeMappingValidationError(ValueError):
    """Raised when a scope-review selection violates the approved contract."""


STATUS_LABELS: Mapping[str, str] = {
    "reviewed": "已完成",
    "needs_adjudication": "待裁決",
}

GROUP_LABELS: Mapping[str, str] = {
    "IN_SCOPE_LIGHT_MODERATE": "範圍內：輕度／中度外觀損傷",
    "BOUNDARY_HEAVY_DAMAGE": "邊界案例：重度外觀損傷",
    "OUT_OF_SCOPE_CATASTROPHIC": "範圍外：災難性／車體完整性受損",
}

REASON_LABELS: Mapping[str, str] = {
    "light_surface_damage": "輕微表面損傷",
    "moderate_external_damage": "中度外觀損傷",
    "heavy_external_damage": "重度外觀損傷",
    "structural_damage": "疑似結構性損傷",
    "catastrophic_collision": "災難性碰撞",
    "extensive_multi_panel_damage": "大範圍多鈑件損傷",
    "vehicle_integrity_compromised": "車體完整性可能受損",
    "insufficient_visual_evidence": "影像證據不足",
    "other": "其他",
}

OPERABILITY_LABELS: Mapping[str, str] = {
    "drivable_or_likely_drivable": "可行駛或可能可行駛",
    "uncertain": "無法確定",
    "non_drivable_or_likely_non_drivable": "不可行駛或可能不可行駛",
}

CONFIDENCE_LABELS: Mapping[str, str] = {
    "high": "高",
    "medium": "中",
    "low": "低",
}

CONTROLLED_OPTIONS: Mapping[str, tuple[str, ...]] = {
    "scope_review_status": tuple(STATUS_LABELS),
    "scope_group": tuple(GROUP_LABELS),
    "scope_reason": tuple(REASON_LABELS),
    "operability": tuple(OPERABILITY_LABELS),
    "scope_confidence": tuple(CONFIDENCE_LABELS),
}

CATASTROPHIC_REASONS = {
    "structural_damage",
    "catastrophic_collision",
    "extensive_multi_panel_damage",
    "vehicle_integrity_compromised",
}


@dataclass(frozen=True)
class ScopeReviewSelection:
    scope_group: str = "IN_SCOPE_LIGHT_MODERATE"
    scope_reason: str = "light_surface_damage"
    operability: str = "drivable_or_likely_drivable"
    scope_confidence: str = "high"
    scope_reviewer_notes: str = ""


@dataclass(frozen=True)
class CanonicalScopeFields:
    scope_review_status: str
    scope_group: str
    scope_reason: str
    operability: str
    scope_confidence: str
    scope_reviewer_notes: str
    scope_reviewer: str
    scope_reviewed_at_utc: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _normalize(value: object) -> str:
    return str(value or "").strip()


def notes_required(selection: ScopeReviewSelection, status: str) -> bool:
    """Return whether the current decision requires an explanatory note."""

    return (
        status == "needs_adjudication"
        or selection.scope_confidence == "low"
        or selection.scope_reason in {"other", "insufficient_visual_evidence"}
        or (
            selection.scope_group == "OUT_OF_SCOPE_CATASTROPHIC"
            and selection.operability == "drivable_or_likely_drivable"
        )
    )


def validate_selection(selection: ScopeReviewSelection, status: str) -> None:
    """Validate one UI selection against the approved scope semantics."""

    normalized_status = _normalize(status)
    values = {
        "scope_review_status": normalized_status,
        "scope_group": _normalize(selection.scope_group),
        "scope_reason": _normalize(selection.scope_reason),
        "operability": _normalize(selection.operability),
        "scope_confidence": _normalize(selection.scope_confidence),
    }
    for key, value in values.items():
        if value not in CONTROLLED_OPTIONS[key]:
            raise ScopeMappingValidationError(
                f"{key}={value!r} 不是核准的 controlled value"
            )

    notes = _normalize(selection.scope_reviewer_notes)
    if notes_required(selection, normalized_status) and not notes:
        raise ScopeMappingValidationError("此判定必須填寫具體說明")

    if selection.scope_group == "OUT_OF_SCOPE_CATASTROPHIC":
        if selection.scope_reason not in CATASTROPHIC_REASONS:
            raise ScopeMappingValidationError(
                "範圍外災難性案例必須使用核准的 catastrophic reason"
            )

    if (
        selection.scope_group == "IN_SCOPE_LIGHT_MODERATE"
        and selection.scope_reason
        in {"catastrophic_collision", "vehicle_integrity_compromised"}
    ):
        raise ScopeMappingValidationError(
            "輕度／中度範圍內案例不可使用災難性碰撞或車體完整性受損原因"
        )

    if selection.scope_reason == "insufficient_visual_evidence":
        if selection.scope_confidence != "low":
            raise ScopeMappingValidationError(
                "影像證據不足必須搭配低信心程度"
            )


def derive_canonical_scope_fields(
    selection: ScopeReviewSelection,
    *,
    status: str,
    reviewer: str,
    reviewed_at: datetime,
) -> CanonicalScopeFields:
    """Validate and convert a UI selection into canonical scope fields."""

    validate_selection(selection, status)
    reviewer_value = _normalize(reviewer)
    if not reviewer_value:
        raise ScopeMappingValidationError("reviewer 不可空白")
    if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
        raise ScopeMappingValidationError("reviewed_at 必須包含時區")

    return CanonicalScopeFields(
        scope_review_status=_normalize(status),
        scope_group=_normalize(selection.scope_group),
        scope_reason=_normalize(selection.scope_reason),
        operability=_normalize(selection.operability),
        scope_confidence=_normalize(selection.scope_confidence),
        scope_reviewer_notes=_normalize(selection.scope_reviewer_notes),
        scope_reviewer=reviewer_value,
        scope_reviewed_at_utc=reviewed_at.isoformat(),
    )
