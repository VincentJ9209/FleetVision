from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from fleetvision.review.validation_error_review_mapping import (
    ACTION_LABELS,
    ANNOTATION_LABELS,
    DEFECT_LABELS,
    OUTCOME_ACTION_OPTIONS,
    OUTCOME_DEFAULTS,
    OUTCOME_LABELS,
    OUTCOME_REASON_OPTIONS,
    PRIORITY_LABELS,
    REASON_LABELS,
    MappingValidationError,
    ReviewSelection,
    default_selection,
    derive_canonical_fields,
)


NOW = datetime(2026, 7, 14, 2, 30, tzinfo=timezone.utc)


def test_small_damage_miss_maps_to_completed_canonical_fields() -> None:
    result = derive_canonical_fields(
        ReviewSelection(
            outcome="model_miss",
            reason="missed_small_damage",
            annotation_quality="correct",
            recommended_action="add_positive_sample",
            retraining_priority="medium",
        ),
        reviewer="Vincent",
        reviewed_at=NOW,
    )

    assert result.review_status == "reviewed"
    assert result.error_disposition == "confirmed_model_error"
    assert result.primary_root_cause == "missed_small_damage"
    assert result.secondary_root_cause == "none"
    assert result.annotation_quality == "correct"
    assert result.annotation_defect_type == "none"
    assert result.recommended_action == "add_positive_sample"
    assert result.retraining_priority == "medium"
    assert result.correction_proposal_required == "no"
    assert result.reviewer == "Vincent"
    assert result.reviewed_at_utc == "2026-07-14T02:30:00+00:00"


def test_annotation_defect_requires_specific_type_and_notes() -> None:
    with pytest.raises(MappingValidationError, match="標註缺陷類型"):
        derive_canonical_fields(
            ReviewSelection(
                outcome="annotation_issue",
                reason="annotation_missing",
                annotation_quality="defect_suspected",
                annotation_defect_type="none",
                recommended_action="create_annotation_correction_proposal",
                retraining_priority="not_applicable",
                review_notes="",
            ),
            reviewer="Vincent",
            reviewed_at=NOW,
        )


def test_high_priority_requires_notes() -> None:
    with pytest.raises(MappingValidationError, match="高優先"):
        derive_canonical_fields(
            ReviewSelection(
                outcome="model_false_positive",
                reason="background_false_positive",
                annotation_quality="correct",
                recommended_action="add_hard_negative",
                retraining_priority="high",
            ),
            reviewer="Vincent",
            reviewed_at=NOW,
        )


def test_ambiguous_case_is_saved_for_adjudication() -> None:
    result = derive_canonical_fields(
        ReviewSelection(
            outcome="ambiguous",
            reason="ambiguous_visual_evidence",
            annotation_quality="questionable",
            recommended_action="investigate_image_quality",
            retraining_priority="not_applicable",
            review_notes="反光與細刮痕無法可靠區分。",
        ),
        reviewer="Vincent",
        reviewed_at=NOW,
    )

    assert result.review_status == "needs_adjudication"
    assert result.error_disposition == "ambiguous_case"
    assert result.primary_root_cause == "ambiguous_visual_evidence"


def test_outcome_rejects_irrelevant_reason() -> None:
    with pytest.raises(MappingValidationError, match="模型誤報不可使用此主要原因"):
        derive_canonical_fields(
            ReviewSelection(
                outcome="model_false_positive",
                reason="missed_small_damage",
                annotation_quality="correct",
                recommended_action="add_hard_negative",
                retraining_priority="medium",
            ),
            reviewer="Vincent",
            reviewed_at=NOW,
        )


def test_outcome_rejects_irrelevant_action() -> None:
    with pytest.raises(MappingValidationError, match="門檻取捨不可使用此改善方向"):
        derive_canonical_fields(
            ReviewSelection(
                outcome="threshold_tradeoff",
                reason="weak_visual_signal",
                annotation_quality="correct",
                recommended_action="add_positive_sample",
                retraining_priority="low",
            ),
            reviewer="Vincent",
            reviewed_at=NOW,
        )


def test_every_outcome_has_a_scoped_valid_default() -> None:
    for outcome in OUTCOME_LABELS:
        selection = default_selection(outcome)
        assert selection.reason in OUTCOME_REASON_OPTIONS[outcome]
        assert selection.recommended_action in OUTCOME_ACTION_OPTIONS[outcome]
        result = derive_canonical_fields(
            selection,
            reviewer="Vincent",
            reviewed_at=NOW,
        )
        expected_status = (
            "needs_adjudication" if outcome == "ambiguous" else "reviewed"
        )
        assert result.review_status == expected_status


def test_all_generated_codes_are_approved_by_canonical_config() -> None:
    config_path = Path("configs/data/validation_error_human_review_config.yaml")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    options = raw["options"]

    assert {defaults.error_disposition for defaults in OUTCOME_DEFAULTS.values()} <= set(
        options["error_disposition"]
    )
    assert set(REASON_LABELS) <= set(options["primary_root_cause"])
    assert {"none", *REASON_LABELS.keys()} <= set(options["secondary_root_cause"])
    assert set(ANNOTATION_LABELS) <= set(options["annotation_quality"])
    assert set(DEFECT_LABELS) <= set(options["annotation_defect_type"])
    assert set(ACTION_LABELS) <= set(options["recommended_action"])
    assert set(PRIORITY_LABELS) <= set(options["retraining_priority"])
    assert {"pending", "reviewed", "needs_adjudication"} <= set(
        options["review_status"]
    )
    assert {"no", "yes"} <= set(options["correction_proposal_required"])
