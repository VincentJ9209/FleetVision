from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from fleetvision.review.validation_error_review_mapping import (
    ReviewSelection,
    derive_canonical_fields,
)
from fleetvision.review.validation_error_review_package import (
    load_review_app_config,
    load_verified_source_package,
)
from fleetvision.review.validation_error_review_state import (
    ReviewStateError,
    ReviewStateStore,
)
from review_app_fixtures import (
    create_review_package,
    write_app_config,
)


NOW = datetime(2026, 7, 14, 3, 0, tzinfo=timezone.utc)


def _prepared(
    tmp_path: Path,
    *,
    backup_retention: int = 20,
):
    project_root, batch_root, frozen_zip = create_review_package(
        tmp_path
    )
    config_path = write_app_config(
        tmp_path,
        project_root,
        batch_root,
        frozen_zip,
    )
    config = load_review_app_config(config_path, project_root)
    package = load_verified_source_package(config)
    store = ReviewStateStore(
        config.workspace_root,
        backup_retention=backup_retention,
    )
    store.initialize(package)
    return package, store


def _model_miss(priority: str = "medium"):
    notes = "重要案例。" if priority == "high" else ""
    selection = ReviewSelection(
        outcome="model_miss",
        reason="missed_small_damage",
        annotation_quality="correct",
        recommended_action="add_positive_sample",
        retraining_priority=priority,
        review_notes=notes,
    )
    canonical = derive_canonical_fields(
        selection,
        reviewer="Vincent",
        reviewed_at=NOW,
    )
    return selection, canonical


def _annotation_issue():
    selection = ReviewSelection(
        outcome="annotation_issue",
        reason="annotation_missing",
        annotation_quality="defect_suspected",
        annotation_defect_type="missing_bbox",
        recommended_action="create_annotation_correction_proposal",
        retraining_priority="not_applicable",
        review_notes="原始標註疑似漏標。",
    )
    canonical = derive_canonical_fields(
        selection,
        reviewer="Vincent",
        reviewed_at=NOW,
    )
    return selection, canonical


def test_initialize_save_reload_and_progress(tmp_path: Path) -> None:
    package, store = _prepared(tmp_path)
    case_id = package.cases[0].review_case_id
    selection, canonical = _model_miss()

    saved = store.save_review(case_id, selection, canonical)
    reloaded = store.get_review(case_id)
    progress = store.progress()

    assert saved.revision == 1
    assert reloaded is not None
    assert reloaded.selection["outcome"] == "model_miss"
    assert reloaded.canonical_fields["review_status"] == "reviewed"
    assert progress.total == 2
    assert progress.reviewed == 1
    assert progress.pending == 1
    assert progress.needs_adjudication == 0
    assert store.successful_save_count() == 1
    assert store.database_integrity_check() == "ok"


def test_second_save_increments_revision_and_audit_event_ids(
    tmp_path: Path,
) -> None:
    package, store = _prepared(tmp_path)
    case_id = package.cases[0].review_case_id
    selection, canonical = _model_miss()

    first = store.save_review(case_id, selection, canonical)
    second = store.save_review(case_id, selection, canonical)

    assert first.revision == 1
    assert second.revision == 2
    events = [
        json.loads(line)
        for line in store.event_log_path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    assert [event["event_id"] for event in events] == [1, 2]
    assert [event["revision"] for event in events] == [1, 2]


def test_progress_filters_include_priority_and_annotation_issue(
    tmp_path: Path,
) -> None:
    package, store = _prepared(tmp_path)
    first_id = package.cases[0].review_case_id
    second_id = package.cases[1].review_case_id

    selection, canonical = _model_miss(priority="high")
    store.save_review(first_id, selection, canonical)
    selection, canonical = _annotation_issue()
    store.save_review(second_id, selection, canonical)

    progress = store.progress()
    assert progress.reviewed == 2
    assert progress.high_priority == 1
    assert progress.annotation_issues == 1
    assert store.list_case_ids("high_priority") == [first_id]
    assert store.list_case_ids("annotation_issues") == [second_id]
    assert store.list_case_ids("pending") == []


def test_last_viewed_is_persisted_and_unknown_case_is_blocked(
    tmp_path: Path,
) -> None:
    package, store = _prepared(tmp_path)
    second_id = package.cases[1].review_case_id

    store.set_last_viewed(second_id)
    assert store.get_last_viewed() == second_id

    with pytest.raises(ReviewStateError, match="unknown review_case_id"):
        store.set_last_viewed("missing")


def test_reopen_is_idempotent_but_identity_mismatch_is_blocked(
    tmp_path: Path,
) -> None:
    package, store = _prepared(tmp_path)
    store.initialize(package)

    changed_config = replace(
        package.config,
        reviewer="Another Reviewer",
    )
    changed_package = replace(package, config=changed_config)

    with pytest.raises(
        ReviewStateError,
        match="workspace identity",
    ):
        store.initialize(changed_package)


def test_source_case_mismatch_is_blocked(tmp_path: Path) -> None:
    package, store = _prepared(tmp_path)
    changed_case = replace(
        package.cases[0],
        source_case_fingerprint="F" * 64,
    )
    changed_package = replace(
        package,
        cases=(changed_case, *package.cases[1:]),
    )

    with pytest.raises(
        ReviewStateError,
        match="source cases",
    ):
        store.initialize(changed_package)


def test_reviewer_mismatch_and_unknown_save_are_blocked(
    tmp_path: Path,
) -> None:
    package, store = _prepared(tmp_path)
    selection, canonical = _model_miss()
    wrong_reviewer = replace(canonical, reviewer="Other")

    with pytest.raises(ReviewStateError, match="reviewer"):
        store.save_review(
            package.cases[0].review_case_id,
            selection,
            wrong_reviewer,
        )

    with pytest.raises(ReviewStateError, match="unknown review_case_id"):
        store.save_review("missing", selection, canonical)


def test_online_backup_is_valid_and_retention_is_enforced(
    tmp_path: Path,
) -> None:
    _, store = _prepared(tmp_path, backup_retention=3)

    backups = [store.create_backup() for _ in range(5)]
    retained = sorted(
        store.backup_dir.glob("review_state_*.sqlite3")
    )

    assert len(retained) == 3
    assert backups[-1] in retained
    assert backups[0] not in retained

    for backup in retained:
        connection = sqlite3.connect(backup)
        try:
            assert (
                connection.execute(
                    "PRAGMA integrity_check"
                ).fetchone()[0]
                == "ok"
            )
            assert (
                connection.execute(
                    "SELECT COUNT(*) FROM review_cases"
                ).fetchone()[0]
                == 2
            )
        finally:
            connection.close()


def test_workspace_can_be_removed_after_store_operations(
    tmp_path: Path,
) -> None:
    package, store = _prepared(tmp_path)
    selection, canonical = _model_miss()
    store.save_review(
        package.cases[0].review_case_id,
        selection,
        canonical,
    )
    store.create_backup()

    workspace = store.workspace_root
    import shutil

    shutil.rmtree(workspace)
    assert not workspace.exists()
