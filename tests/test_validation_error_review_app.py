from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fleetvision.review.validation_error_review_app import (
    annotation_quality_options,
    backup_due,
    build_case_view_model,
    load_review_runtime,
    next_case_id,
    priority_options,
    save_review_selection,
    selection_for_case,
    suggest_outcome,
    visible_fields,
)
from fleetvision.review.validation_error_review_mapping import (
    ReviewSelection,
)
from review_app_fixtures import (
    create_review_package,
    write_app_config,
)


NOW = datetime(2026, 7, 14, 5, 0, tzinfo=timezone.utc)


def _runtime(tmp_path: Path):
    project_root, batch_root, frozen_zip = create_review_package(
        tmp_path,
        case_count=12,
    )
    config_path = write_app_config(
        tmp_path,
        project_root,
        batch_root,
        frozen_zip,
        case_count=12,
    )
    runtime = load_review_runtime(
        config_path,
        project_root,
        workspace_override=tmp_path / "ui_workspace",
    )
    return runtime


def test_auto_category_suggests_editable_outcome() -> None:
    assert suggest_outcome("false_negative") == "model_miss"
    assert (
        suggest_outcome("false_positive")
        == "model_false_positive"
    )
    assert suggest_outcome("unknown") == "model_miss"


def test_simple_model_miss_uses_minimal_fields() -> None:
    assert visible_fields(
        outcome="model_miss",
        reason="missed_small_damage",
        annotation_quality="correct",
        recommended_action="add_positive_sample",
        priority="medium",
    ) == {
        "reason",
        "annotation_quality",
        "recommended_action",
        "retraining_priority",
    }


def test_complex_cases_expand_only_required_fields() -> None:
    fields = visible_fields(
        outcome="annotation_issue",
        reason="annotation_missing",
        annotation_quality="defect_suspected",
        recommended_action=(
            "create_annotation_correction_proposal"
        ),
        priority="not_applicable",
    )
    assert {
        "annotation_defect_type",
        "review_notes",
    } <= fields

    assert annotation_quality_options(
        "annotation_issue"
    ) == ("defect_suspected",)
    assert priority_options(
        "annotation_issue"
    ) == ("not_applicable",)


def test_high_priority_or_other_requires_notes() -> None:
    assert "review_notes" in visible_fields(
        outcome="model_false_positive",
        reason="background_false_positive",
        annotation_quality="correct",
        recommended_action="add_hard_negative",
        priority="high",
    )
    assert "review_notes" in visible_fields(
        outcome="model_miss",
        reason="other",
        annotation_quality="correct",
        recommended_action="add_positive_sample",
        priority="medium",
    )


def test_navigation_is_bounded() -> None:
    case_ids = ["a", "b", "c"]
    assert next_case_id(case_ids, "a", direction=-1) == "a"
    assert next_case_id(case_ids, "a", direction=1) == "b"
    assert next_case_id(case_ids, "c", direction=1) == "c"
    assert next_case_id(case_ids, "missing", direction=1) == "a"


def test_backup_schedule_is_deterministic() -> None:
    assert backup_due(10, 10) is True
    assert backup_due(20, 10) is True
    assert backup_due(9, 10) is False
    assert backup_due(0, 10) is False


def test_runtime_save_resume_and_tenth_save_backup(
    tmp_path: Path,
) -> None:
    runtime = _runtime(tmp_path)
    assert len(runtime.package.cases) == 12
    assert runtime.store.progress().pending == 12

    selection = ReviewSelection(
        outcome="model_miss",
        reason="missed_small_damage",
        annotation_quality="correct",
        recommended_action="add_positive_sample",
        retraining_priority="medium",
    )
    last_result = None
    for case in runtime.package.cases[:10]:
        last_result = save_review_selection(
            runtime,
            case.review_case_id,
            selection,
            reviewed_at=NOW,
        )

    assert last_result is not None
    assert last_result.backup_path is not None
    assert last_result.backup_path.is_file()
    assert last_result.progress.reviewed == 10
    assert last_result.progress.pending == 2
    assert runtime.store.successful_save_count() == 10

    first_case = runtime.package.cases[0]
    restored = selection_for_case(runtime.store, first_case)
    assert restored == selection

    view = build_case_view_model(runtime, first_case)
    assert view.review_status == "reviewed"
    assert view.revision == 1
    assert view.original_path.is_file()
    assert view.overlay_path.is_file()
