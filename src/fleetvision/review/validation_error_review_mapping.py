from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Mapping, Sequence


class MappingValidationError(ValueError):
    """Raised when simplified UI input cannot form a valid canonical review."""


OUTCOME_LABELS: Mapping[str, str] = {
    "model_miss": "模型漏檢",
    "model_false_positive": "模型誤報",
    "localization_error": "模型框不準",
    "duplicate_prediction": "重複預測",
    "annotation_issue": "標註有問題",
    "threshold_tradeoff": "門檻取捨",
    "invalid_image": "圖片無效",
    "ambiguous": "無法判斷",
}

REASON_LABELS: Mapping[str, str] = {
    "missed_small_damage": "損傷太小",
    "weak_visual_signal": "損傷不明顯",
    "difficult_lighting_or_reflection": "反光或光線干擾",
    "occlusion_or_crop": "遮擋或裁切",
    "localization_error": "模型框位置不準",
    "duplicate_prediction": "同一損傷重複框選",
    "background_false_positive": "正常背景被誤判",
    "annotation_missing": "標註漏標",
    "annotation_inaccurate_bbox": "標註框不準",
    "ambiguous_visual_evidence": "影像證據不足",
    "invalid_or_low_quality_image": "圖片無效或品質太差",
    "other": "其他",
}

ANNOTATION_LABELS: Mapping[str, str] = {
    "correct": "正確",
    "questionable": "有疑問",
    "defect_suspected": "明確有問題",
    "not_applicable": "無法評估",
}

DEFECT_LABELS: Mapping[str, str] = {
    "none": "無",
    "missing_bbox": "漏標",
    "extra_bbox": "多標",
    "inaccurate_bbox": "標註框不準",
    "wrong_damage_scope": "損傷範圍不合理",
    "ambiguous_annotation": "標註規則不明確",
    "invalid_image_assignment": "圖片配錯",
    "other": "其他",
}

ACTION_LABELS: Mapping[str, str] = {
    "no_action": "不處理",
    "add_hard_negative": "增加困難負樣本",
    "add_positive_sample": "增加正樣本",
    "improve_annotation_guideline": "改善標註規範",
    "create_annotation_correction_proposal": "提出標註修正建議",
    "investigate_preprocessing": "檢查影像前處理",
    "investigate_image_quality": "檢查圖片品質",
    "adjust_model_strategy": "調整模型策略",
    "threshold_analysis_only": "僅進行門檻分析",
    "exclude_invalid_image_proposal": "提出排除無效圖片建議",
    "other": "其他",
}

PRIORITY_LABELS: Mapping[str, str] = {
    "not_applicable": "不適用",
    "low": "低",
    "medium": "中",
    "high": "高",
}

OUTCOME_REASON_OPTIONS: Mapping[str, Sequence[str]] = {
    "model_miss": (
        "missed_small_damage",
        "weak_visual_signal",
        "difficult_lighting_or_reflection",
        "occlusion_or_crop",
        "other",
    ),
    "model_false_positive": (
        "background_false_positive",
        "difficult_lighting_or_reflection",
        "weak_visual_signal",
        "other",
    ),
    "localization_error": (
        "localization_error",
        "difficult_lighting_or_reflection",
        "occlusion_or_crop",
        "other",
    ),
    "duplicate_prediction": (
        "duplicate_prediction",
        "localization_error",
        "other",
    ),
    "annotation_issue": (
        "annotation_missing",
        "annotation_inaccurate_bbox",
        "other",
    ),
    "threshold_tradeoff": (
        "weak_visual_signal",
        "missed_small_damage",
        "difficult_lighting_or_reflection",
        "other",
    ),
    "invalid_image": (
        "invalid_or_low_quality_image",
        "occlusion_or_crop",
        "other",
    ),
    "ambiguous": (
        "ambiguous_visual_evidence",
        "difficult_lighting_or_reflection",
        "weak_visual_signal",
        "invalid_or_low_quality_image",
        "other",
    ),
}

OUTCOME_ACTION_OPTIONS: Mapping[str, Sequence[str]] = {
    "model_miss": (
        "add_positive_sample",
        "investigate_preprocessing",
        "investigate_image_quality",
        "adjust_model_strategy",
        "other",
    ),
    "model_false_positive": (
        "add_hard_negative",
        "investigate_image_quality",
        "adjust_model_strategy",
        "other",
    ),
    "localization_error": (
        "adjust_model_strategy",
        "add_positive_sample",
        "investigate_preprocessing",
        "other",
    ),
    "duplicate_prediction": (
        "adjust_model_strategy",
        "other",
    ),
    "annotation_issue": (
        "create_annotation_correction_proposal",
    ),
    "threshold_tradeoff": (
        "threshold_analysis_only",
    ),
    "invalid_image": (
        "exclude_invalid_image_proposal",
        "investigate_image_quality",
        "other",
    ),
    "ambiguous": (
        "investigate_image_quality",
        "improve_annotation_guideline",
        "other",
    ),
}


@dataclass(frozen=True)
class OutcomeDefaults:
    error_disposition: str
    primary_root_cause: str
    recommended_action: str
    annotation_quality: str
    retraining_priority: str


OUTCOME_DEFAULTS: Mapping[str, OutcomeDefaults] = {
    "model_miss": OutcomeDefaults(
        "confirmed_model_error",
        "missed_small_damage",
        "add_positive_sample",
        "correct",
        "medium",
    ),
    "model_false_positive": OutcomeDefaults(
        "confirmed_model_error",
        "background_false_positive",
        "add_hard_negative",
        "correct",
        "medium",
    ),
    "localization_error": OutcomeDefaults(
        "confirmed_model_error",
        "localization_error",
        "adjust_model_strategy",
        "correct",
        "medium",
    ),
    "duplicate_prediction": OutcomeDefaults(
        "confirmed_model_error",
        "duplicate_prediction",
        "adjust_model_strategy",
        "correct",
        "medium",
    ),
    "annotation_issue": OutcomeDefaults(
        "annotation_issue",
        "annotation_missing",
        "create_annotation_correction_proposal",
        "defect_suspected",
        "not_applicable",
    ),
    "threshold_tradeoff": OutcomeDefaults(
        "expected_threshold_tradeoff",
        "weak_visual_signal",
        "threshold_analysis_only",
        "correct",
        "low",
    ),
    "invalid_image": OutcomeDefaults(
        "invalid_review_case",
        "invalid_or_low_quality_image",
        "exclude_invalid_image_proposal",
        "not_applicable",
        "not_applicable",
    ),
    "ambiguous": OutcomeDefaults(
        "ambiguous_case",
        "ambiguous_visual_evidence",
        "investigate_image_quality",
        "questionable",
        "not_applicable",
    ),
}


@dataclass(frozen=True)
class ReviewSelection:
    outcome: str
    reason: str
    annotation_quality: str
    recommended_action: str
    retraining_priority: str
    annotation_defect_type: str = "none"
    secondary_reason: str = "none"
    review_notes: str = ""


@dataclass(frozen=True)
class CanonicalReviewFields:
    review_status: str
    error_disposition: str
    primary_root_cause: str
    secondary_root_cause: str
    annotation_quality: str
    annotation_defect_type: str
    recommended_action: str
    retraining_priority: str
    correction_proposal_required: str
    reviewer: str
    reviewed_at_utc: str
    review_notes: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _require_known(value: str, allowed: Mapping[str, str], field_name: str) -> None:
    if value not in allowed:
        raise MappingValidationError(f"{field_name}不是允許值：{value}")


def _require_scoped(
    value: str,
    allowed: Sequence[str],
    *,
    field_name: str,
    outcome: str,
) -> None:
    if value not in allowed:
        raise MappingValidationError(
            f"{OUTCOME_LABELS[outcome]}不可使用此{field_name}：{value}"
        )


def default_selection(outcome: str) -> ReviewSelection:
    """Return the minimal valid default selection for one simplified outcome."""

    _require_known(outcome, OUTCOME_LABELS, "主要結果")
    defaults = OUTCOME_DEFAULTS[outcome]
    notes = "需要進一步人工判斷。" if outcome == "ambiguous" else ""
    defect_type = "missing_bbox" if outcome == "annotation_issue" else "none"
    if outcome == "annotation_issue":
        notes = "明確懷疑原始標註有缺陷，僅提出修正建議。"
    return ReviewSelection(
        outcome=outcome,
        reason=defaults.primary_root_cause,
        annotation_quality=defaults.annotation_quality,
        annotation_defect_type=defect_type,
        recommended_action=defaults.recommended_action,
        retraining_priority=defaults.retraining_priority,
        review_notes=notes,
    )


def derive_canonical_fields(
    selection: ReviewSelection,
    *,
    reviewer: str,
    reviewed_at: datetime,
) -> CanonicalReviewFields:
    """Convert simplified Chinese UI choices into validated canonical values."""

    _require_known(selection.outcome, OUTCOME_LABELS, "主要結果")
    _require_known(selection.reason, REASON_LABELS, "主要原因")
    _require_known(selection.annotation_quality, ANNOTATION_LABELS, "標註品質")
    _require_known(selection.annotation_defect_type, DEFECT_LABELS, "標註缺陷類型")
    _require_known(selection.recommended_action, ACTION_LABELS, "改善方向")
    _require_known(selection.retraining_priority, PRIORITY_LABELS, "優先程度")

    if selection.secondary_reason != "none":
        _require_known(selection.secondary_reason, REASON_LABELS, "次要原因")

    _require_scoped(
        selection.reason,
        OUTCOME_REASON_OPTIONS[selection.outcome],
        field_name="主要原因",
        outcome=selection.outcome,
    )
    _require_scoped(
        selection.recommended_action,
        OUTCOME_ACTION_OPTIONS[selection.outcome],
        field_name="改善方向",
        outcome=selection.outcome,
    )

    reviewer = reviewer.strip()
    if not reviewer:
        raise MappingValidationError("審核者不可空白")
    if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
        raise MappingValidationError("審核時間必須包含時區")

    notes = selection.review_notes.strip()
    if selection.retraining_priority == "high" and not notes:
        raise MappingValidationError("高優先案例必須填寫說明")
    if selection.outcome == "ambiguous" and not notes:
        raise MappingValidationError("無法判斷的案例必須填寫說明")

    defect = selection.annotation_quality == "defect_suspected"
    if selection.outcome == "annotation_issue" and not defect:
        raise MappingValidationError("標註有問題必須設定為明確有問題")
    if defect and selection.outcome != "annotation_issue":
        raise MappingValidationError("明確標註缺陷必須選擇標註有問題")

    if defect:
        if selection.annotation_defect_type == "none":
            raise MappingValidationError("明確有標註問題時必須選擇標註缺陷類型")
        if not notes:
            raise MappingValidationError("標註缺陷必須填寫具體說明")
        if selection.recommended_action != "create_annotation_correction_proposal":
            raise MappingValidationError("標註缺陷必須提出標註修正建議")
    else:
        if selection.annotation_defect_type != "none":
            raise MappingValidationError("標註沒有明確缺陷時，缺陷類型必須為無")
        if selection.recommended_action == "create_annotation_correction_proposal":
            raise MappingValidationError("只有明確標註缺陷才能提出修正建議")

    if "other" in {
        selection.reason,
        selection.annotation_defect_type,
        selection.recommended_action,
        selection.secondary_reason,
    } and not notes:
        raise MappingValidationError("選擇其他時必須填寫說明")

    defaults = OUTCOME_DEFAULTS[selection.outcome]
    status = "needs_adjudication" if selection.outcome == "ambiguous" else "reviewed"

    return CanonicalReviewFields(
        review_status=status,
        error_disposition=defaults.error_disposition,
        primary_root_cause=selection.reason,
        secondary_root_cause=selection.secondary_reason,
        annotation_quality=selection.annotation_quality,
        annotation_defect_type=selection.annotation_defect_type,
        recommended_action=selection.recommended_action,
        retraining_priority=selection.retraining_priority,
        correction_proposal_required="yes" if defect else "no",
        reviewer=reviewer,
        reviewed_at_utc=reviewed_at.isoformat(timespec="seconds"),
        review_notes=notes,
    )
