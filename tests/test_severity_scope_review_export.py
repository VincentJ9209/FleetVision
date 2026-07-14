from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from fleetvision.review.severity_scope_review_export import (
    ScopeCompletedWorkbookExportError,
    export_completed_scope_workbook,
)
from fleetvision.review.severity_scope_review_mapping import (
    ScopeReviewSelection,
    derive_canonical_scope_fields,
)
from fleetvision.review.severity_scope_review_state import ScopeReviewStateStore
from scope_review_app_fixtures import create_scope_package


def _complete_all(package, store) -> None:
    selection = ScopeReviewSelection()
    for case in package.cases:
        canonical = derive_canonical_scope_fields(
            selection,
            status="reviewed",
            reviewer="Vincent",
            reviewed_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        )
        store.save_review(case.review_case_id, selection, canonical)


def test_export_requires_complete_state(tmp_path) -> None:
    fixture = create_scope_package(tmp_path, case_count=2)
    package = fixture.package
    store = ScopeReviewStateStore(package.app_workspace_root, backup_retention=3)
    store.initialize(package)
    with pytest.raises(ScopeCompletedWorkbookExportError, match="130/130 reviewed"):
        export_completed_scope_workbook(package, store)


def test_export_is_transactional_no_overwrite_and_preserves_source(
    tmp_path,
    monkeypatch,
) -> None:
    fixture = create_scope_package(tmp_path, case_count=2)
    package = fixture.package
    store = ScopeReviewStateStore(package.app_workspace_root, backup_retention=3)
    store.initialize(package)
    _complete_all(package, store)

    monkeypatch.setattr(
        "fleetvision.review.severity_scope_review_export.load_findings_config",
        lambda *_args, **_kwargs: SimpleNamespace(expected_case_count=2),
    )
    monkeypatch.setattr(
        "fleetvision.review.severity_scope_review_export.validate_scope_dataframe",
        lambda *_args, **_kwargs: SimpleNamespace(
            passed=True,
            issue_count=0,
            issues=(),
            counts={"reviewed": 2, "pending": 0, "needs_adjudication": 0},
        ),
    )

    source_hash_before = package.template_workbook_sha256
    result = export_completed_scope_workbook(package, store)
    assert result.output_path.is_file()
    assert result.result_path.is_file()
    assert result.backup_path.is_file()
    assert package.template_workbook_sha256 == source_hash_before

    with pytest.raises(ScopeCompletedWorkbookExportError, match="already exists"):
        export_completed_scope_workbook(package, store)
