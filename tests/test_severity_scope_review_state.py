from __future__ import annotations

from datetime import datetime, timezone

from fleetvision.review.severity_scope_review_mapping import (
    ScopeReviewSelection,
    derive_canonical_scope_fields,
)
from fleetvision.review.severity_scope_review_state import ScopeReviewStateStore
from scope_review_app_fixtures import create_scope_package


def test_state_save_resume_progress_and_backup(tmp_path) -> None:
    fixture = create_scope_package(tmp_path, case_count=3)
    package = fixture.package
    store = ScopeReviewStateStore(
        package.app_workspace_root,
        backup_retention=3,
    )
    store.initialize(package)
    assert store.progress().pending == 3

    selection = ScopeReviewSelection()
    for case in package.cases[:2]:
        canonical = derive_canonical_scope_fields(
            selection,
            status="reviewed",
            reviewer="Vincent",
            reviewed_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        )
        store.save_review(case.review_case_id, selection, canonical)

    progress = store.progress()
    assert progress.reviewed == 2
    assert progress.pending == 1
    assert store.successful_save_count() == 2
    backup = store.create_backup()
    assert backup.is_file()
    assert store.event_log_path.is_file()

    reopened = ScopeReviewStateStore(
        package.app_workspace_root,
        backup_retention=3,
    )
    reopened.initialize(package)
    restored = reopened.get_review(package.cases[0].review_case_id)
    assert restored is not None
    assert restored.canonical_fields["scope_review_status"] == "reviewed"


def test_filters_are_deterministic(tmp_path) -> None:
    fixture = create_scope_package(tmp_path, case_count=2)
    package = fixture.package
    store = ScopeReviewStateStore(package.app_workspace_root, backup_retention=3)
    store.initialize(package)

    selection = ScopeReviewSelection(
        scope_group="OUT_OF_SCOPE_CATASTROPHIC",
        scope_reason="catastrophic_collision",
        operability="non_drivable_or_likely_non_drivable",
        scope_confidence="low",
        scope_reviewer_notes="車體大範圍變形",
    )
    canonical = derive_canonical_scope_fields(
        selection,
        status="reviewed",
        reviewer="Vincent",
        reviewed_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
    )
    store.save_review(package.cases[0].review_case_id, selection, canonical)

    assert store.case_ids("catastrophic") == (package.cases[0].review_case_id,)
    assert store.case_ids("low_confidence") == (package.cases[0].review_case_id,)
    assert store.case_ids("pending") == (package.cases[1].review_case_id,)
