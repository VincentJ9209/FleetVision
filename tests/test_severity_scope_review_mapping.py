from __future__ import annotations

from datetime import datetime, timezone

import pytest

from fleetvision.review.severity_scope_review_mapping import (
    ScopeMappingValidationError,
    ScopeReviewSelection,
    derive_canonical_scope_fields,
    notes_required,
    validate_selection,
)


def test_simple_in_scope_selection_is_valid() -> None:
    selection = ScopeReviewSelection()
    validate_selection(selection, "reviewed")
    canonical = derive_canonical_scope_fields(
        selection,
        status="reviewed",
        reviewer="Vincent",
        reviewed_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
    )
    assert canonical.scope_review_status == "reviewed"
    assert canonical.scope_reviewer == "Vincent"
    assert canonical.scope_reviewed_at_utc.endswith("+00:00")


def test_low_confidence_and_adjudication_require_notes() -> None:
    low = ScopeReviewSelection(scope_confidence="low")
    assert notes_required(low, "reviewed") is True
    with pytest.raises(ScopeMappingValidationError, match="必須填寫"):
        validate_selection(low, "reviewed")

    adjudication = ScopeReviewSelection(scope_reviewer_notes="")
    assert notes_required(adjudication, "needs_adjudication") is True
    with pytest.raises(ScopeMappingValidationError, match="必須填寫"):
        validate_selection(adjudication, "needs_adjudication")


def test_catastrophic_group_requires_catastrophic_reason() -> None:
    selection = ScopeReviewSelection(
        scope_group="OUT_OF_SCOPE_CATASTROPHIC",
        scope_reason="moderate_external_damage",
        operability="non_drivable_or_likely_non_drivable",
    )
    with pytest.raises(ScopeMappingValidationError, match="catastrophic reason"):
        validate_selection(selection, "reviewed")


def test_insufficient_visual_evidence_requires_low_confidence_and_notes() -> None:
    selection = ScopeReviewSelection(
        scope_reason="insufficient_visual_evidence",
        scope_confidence="medium",
        scope_reviewer_notes="畫面遮蔽",
    )
    with pytest.raises(ScopeMappingValidationError, match="低信心"):
        validate_selection(selection, "reviewed")


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ScopeMappingValidationError, match="時區"):
        derive_canonical_scope_fields(
            ScopeReviewSelection(),
            status="reviewed",
            reviewer="Vincent",
            reviewed_at=datetime(2026, 7, 14),
        )
