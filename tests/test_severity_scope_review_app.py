from __future__ import annotations

from datetime import datetime, timezone

from fleetvision.review.severity_scope_review_app import (
    apply_pending_case_selection,
    backup_due,
    case_widget_key,
    build_case_view_model,
    next_case_id,
    queue_case_selection,
    runtime_session_identity,
    save_scope_review_selection,
    selection_for_case,
)
from fleetvision.review.severity_scope_review_mapping import ScopeReviewSelection
from fleetvision.review.severity_scope_review_state import ScopeReviewStateStore
from scope_review_app_fixtures import create_scope_package


def test_navigation_is_bounded_and_queued() -> None:
    case_ids = ["a", "b", "c"]
    assert next_case_id(case_ids, "a", direction=-1) == "a"
    assert next_case_id(case_ids, "a", direction=1) == "b"
    assert next_case_id(case_ids, "c", direction=1) == "c"

    state: dict[str, object] = {"selector": "a"}
    queue_case_selection(state, "b")
    assert apply_pending_case_selection(
        state,
        "selector",
        case_ids,
        "a",
    ) == "b"


def test_backup_schedule_is_deterministic() -> None:
    assert backup_due(10, 10) is True
    assert backup_due(20, 10) is True
    assert backup_due(9, 10) is False


def test_widget_keys_are_case_specific() -> None:
    assert case_widget_key("scope_group", "scope-001") == (
        "scope_group:scope-001"
    )
    assert case_widget_key("scope_group", "scope-002") != (
        case_widget_key("scope_group", "scope-001")
    )


def test_runtime_session_identity_is_path_specific(tmp_path) -> None:
    first = runtime_session_identity(
        tmp_path / "config.yaml",
        tmp_path / "project",
        tmp_path / "f1-a",
    )
    second = runtime_session_identity(
        tmp_path / "config.yaml",
        tmp_path / "project",
        tmp_path / "f1-b",
    )
    assert first != second
    assert first == runtime_session_identity(
        tmp_path / "config.yaml",
        tmp_path / "project",
        tmp_path / "f1-a",
    )


def test_save_scope_review_uses_sqlite_and_automatic_backup(tmp_path) -> None:
    fixture = create_scope_package(tmp_path, case_count=2)
    package = fixture.package
    store = ScopeReviewStateStore(package.app_workspace_root, backup_retention=3)
    store.initialize(package)
    runtime = type(
        "Runtime",
        (),
        {
            "package": package,
            "store": store,
            "case_by_id": {case.review_case_id: case for case in package.cases},
        },
    )()

    first = package.cases[0]
    assert selection_for_case(store, first) == ScopeReviewSelection()
    result = save_scope_review_selection(
        runtime,
        first.review_case_id,
        ScopeReviewSelection(),
        status="reviewed",
        reviewed_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
    )
    assert result.progress.reviewed == 1
    assert result.backup_path is None

    second = package.cases[1]
    result = save_scope_review_selection(
        runtime,
        second.review_case_id,
        ScopeReviewSelection(),
        status="reviewed",
        reviewed_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
    )
    assert result.progress.reviewed == 2
    assert result.backup_path is not None
    assert build_case_view_model(runtime, first).review_status == "reviewed"
