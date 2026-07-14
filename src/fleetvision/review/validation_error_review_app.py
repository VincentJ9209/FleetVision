from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Mapping, MutableMapping, Sequence
from zoneinfo import ZoneInfo

import streamlit as st

from fleetvision.review.validation_error_review_mapping import (
    ACTION_LABELS,
    ANNOTATION_LABELS,
    DEFECT_LABELS,
    OUTCOME_ACTION_OPTIONS,
    OUTCOME_LABELS,
    OUTCOME_REASON_OPTIONS,
    PRIORITY_LABELS,
    REASON_LABELS,
    MappingValidationError,
    ReviewSelection,
    default_selection,
    derive_canonical_fields,
)
from fleetvision.review.validation_error_review_package import (
    ReviewAppConfig,
    SourceCase,
    VerifiedSourcePackage,
    load_review_app_config,
    load_verified_source_package,
)
from fleetvision.review.validation_error_review_state import (
    ProgressCounts,
    ReviewStateStore,
    StoredReview,
)


FILTER_LABELS: Mapping[str, str] = {
    "all": "全部案例",
    "pending": "尚未完成",
    "reviewed": "已完成",
    "needs_adjudication": "待裁決",
    "high_priority": "高優先",
    "annotation_issues": "標註問題",
}

DISPLAY_MODE_LABELS: Mapping[str, str] = {
    "compare": "左右比較",
    "original": "只看原圖",
    "overlay": "只看 Overlay",
}

PENDING_CASE_SELECTION_KEY = "_pending_case_selection"


AUTO_CATEGORY_OUTCOMES: Mapping[str, str] = {
    "false_negative": "model_miss",
    "missed_prediction": "model_miss",
    "ground_truth_error": "model_miss",
    "false_positive": "model_false_positive",
    "background_false_positive": "model_false_positive",
    "prediction_error": "model_false_positive",
    "localization_error": "localization_error",
    "duplicate_prediction": "duplicate_prediction",
    "annotation_issue": "annotation_issue",
}


@dataclass(frozen=True)
class ReviewRuntime:
    config: ReviewAppConfig
    package: VerifiedSourcePackage
    store: ReviewStateStore
    case_by_id: Mapping[str, SourceCase]


@dataclass(frozen=True)
class CaseViewModel:
    case_index: int
    total_cases: int
    review_case_id: str
    image_id: str
    auto_error_category: str
    auto_error_detail_ids: str
    gt_count: int
    prediction_count: int
    max_prediction_confidence: float
    best_iou: float
    threshold_candidate: float
    threshold_designation: str
    original_path: Path
    overlay_path: Path
    review_status: str
    revision: int


@dataclass(frozen=True)
class SaveReviewResult:
    stored_review: StoredReview
    backup_path: Path | None
    progress: ProgressCounts


def suggest_outcome(auto_error_category: str) -> str:
    """Choose a safe editable starting outcome from the automatic category."""

    normalized = str(auto_error_category).strip().lower()
    return AUTO_CATEGORY_OUTCOMES.get(normalized, "model_miss")


def annotation_quality_options(outcome: str) -> tuple[str, ...]:
    if outcome == "annotation_issue":
        return ("defect_suspected",)
    if outcome == "invalid_image":
        return ("not_applicable",)
    if outcome == "ambiguous":
        return ("questionable", "not_applicable")
    return ("correct", "questionable", "not_applicable")


def priority_options(outcome: str) -> tuple[str, ...]:
    if outcome in {"annotation_issue", "invalid_image", "ambiguous"}:
        return ("not_applicable",)
    if outcome == "threshold_tradeoff":
        return ("low", "not_applicable")
    return ("low", "medium", "high")


def visible_fields(
    *,
    outcome: str,
    reason: str,
    annotation_quality: str,
    recommended_action: str,
    priority: str,
) -> set[str]:
    """Return the progressive-disclosure fields required by one draft."""

    fields = {
        "reason",
        "annotation_quality",
        "recommended_action",
        "retraining_priority",
    }
    if outcome == "annotation_issue" or annotation_quality == "defect_suspected":
        fields.add("annotation_defect_type")
    if (
        outcome in {"annotation_issue", "ambiguous"}
        or priority == "high"
        or "other" in {reason, recommended_action}
    ):
        fields.add("review_notes")
    return fields


def next_case_id(
    case_ids: Sequence[str],
    current_case_id: str,
    *,
    direction: int = 1,
) -> str:
    """Return the adjacent case without wrapping beyond either boundary."""

    if not case_ids:
        raise ValueError("case_ids cannot be empty")
    if current_case_id not in case_ids:
        return case_ids[0]
    current_index = case_ids.index(current_case_id)
    target_index = max(
        0,
        min(len(case_ids) - 1, current_index + direction),
    )
    return case_ids[target_index]


def queue_case_selection(
    state: MutableMapping[str, object],
    case_id: str,
) -> None:
    """Queue a selector change for the next Streamlit rerun."""

    state[PENDING_CASE_SELECTION_KEY] = case_id


def apply_pending_case_selection(
    state: MutableMapping[str, object],
    selector_key: str,
    case_ids: Sequence[str],
    fallback_case_id: str,
) -> str:
    """Apply queued navigation before the selector widget is instantiated."""

    if not case_ids:
        raise ValueError("case_ids cannot be empty")

    fallback = (
        fallback_case_id
        if fallback_case_id in case_ids
        else case_ids[0]
    )
    pending = state.pop(PENDING_CASE_SELECTION_KEY, None)
    if isinstance(pending, str) and pending in case_ids:
        state[selector_key] = pending

    current = state.get(selector_key)
    if not isinstance(current, str) or current not in case_ids:
        state[selector_key] = fallback

    return str(state[selector_key])


def backup_due(successful_save_count: int, interval: int) -> bool:
    if interval <= 0:
        raise ValueError("backup interval must be positive")
    return (
        successful_save_count > 0
        and successful_save_count % interval == 0
    )


def _new_selection_for_case(case: SourceCase) -> ReviewSelection:
    outcome = suggest_outcome(case.auto_error_category)
    selection = default_selection(outcome)
    if outcome in {"annotation_issue", "ambiguous"}:
        selection = replace(selection, review_notes="")
    return selection


def selection_for_case(
    store: ReviewStateStore,
    case: SourceCase,
) -> ReviewSelection:
    stored = store.get_review(case.review_case_id)
    if stored is None:
        return _new_selection_for_case(case)
    try:
        return ReviewSelection(**dict(stored.selection))
    except TypeError as exc:
        raise MappingValidationError(
            f"既有審核狀態欄位不相容：{case.review_case_id}"
        ) from exc


def build_case_view_model(
    runtime: ReviewRuntime,
    case: SourceCase,
) -> CaseViewModel:
    stored = runtime.store.get_review(case.review_case_id)
    return CaseViewModel(
        case_index=case.case_index,
        total_cases=len(runtime.package.cases),
        review_case_id=case.review_case_id,
        image_id=case.image_id,
        auto_error_category=case.auto_error_category,
        auto_error_detail_ids=case.auto_error_detail_ids,
        gt_count=case.gt_count,
        prediction_count=case.prediction_count,
        max_prediction_confidence=case.max_prediction_confidence,
        best_iou=case.best_iou,
        threshold_candidate=case.threshold_candidate,
        threshold_designation=case.threshold_designation,
        original_path=case.original_path,
        overlay_path=case.overlay_path,
        review_status=(
            "pending"
            if stored is None
            else str(stored.canonical_fields["review_status"])
        ),
        revision=0 if stored is None else stored.revision,
    )


def load_review_runtime(
    config_path: Path,
    project_root: Path,
    *,
    workspace_override: Path | None = None,
) -> ReviewRuntime:
    """Verify the frozen package and initialize one pinned local workspace."""

    project_root = project_root.resolve()
    config = load_review_app_config(config_path, project_root)
    package = load_verified_source_package(config)

    if workspace_override is not None:
        override = workspace_override.resolve()
        config = replace(config, workspace_root=override)
        package = replace(package, config=config)

    store = ReviewStateStore(
        config.workspace_root,
        backup_retention=config.backup_retention,
    )
    store.initialize(package)
    return ReviewRuntime(
        config=config,
        package=package,
        store=store,
        case_by_id={
            case.review_case_id: case
            for case in package.cases
        },
    )


@st.cache_resource(show_spinner=False)
def _cached_runtime(
    config_path: str,
    project_root: str,
    workspace_override: str,
) -> ReviewRuntime:
    override = (
        Path(workspace_override)
        if workspace_override
        else None
    )
    return load_review_runtime(
        Path(config_path),
        Path(project_root),
        workspace_override=override,
    )


def save_review_selection(
    runtime: ReviewRuntime,
    review_case_id: str,
    selection: ReviewSelection,
    *,
    reviewed_at: datetime | None = None,
) -> SaveReviewResult:
    """Map, validate, save, and optionally create the scheduled backup."""

    timestamp = reviewed_at or datetime.now(
        ZoneInfo(runtime.config.timezone)
    )
    canonical = derive_canonical_fields(
        selection,
        reviewer=runtime.config.reviewer,
        reviewed_at=timestamp,
    )
    stored = runtime.store.save_review(
        review_case_id,
        selection,
        canonical,
    )

    successful_save_count = runtime.store.successful_save_count()
    backup_path = None
    if backup_due(
        successful_save_count,
        runtime.config.backup_every_successful_saves,
    ):
        backup_path = runtime.store.create_backup()

    return SaveReviewResult(
        stored_review=stored,
        backup_path=backup_path,
        progress=runtime.store.progress(),
    )


def _case_label(runtime: ReviewRuntime, case_id: str) -> str:
    case = runtime.case_by_id[case_id]
    stored = runtime.store.get_review(case_id)
    status = (
        "未完成"
        if stored is None
        else (
            "已完成"
            if stored.canonical_fields["review_status"] == "reviewed"
            else "待裁決"
        )
    )
    return f"{case.case_index:03d}｜{status}｜{case.image_id}"


def _seed_widget(
    key: str,
    value: str,
    *,
    allowed: Sequence[str] | None = None,
) -> None:
    if key not in st.session_state:
        st.session_state[key] = value
    if (
        allowed is not None
        and st.session_state[key] not in allowed
    ):
        st.session_state[key] = value


def _show_flash_message() -> None:
    message = st.session_state.pop("_review_flash_message", "")
    if message:
        st.success(message)


def _render_images(view: CaseViewModel) -> None:
    mode = st.radio(
        "圖片顯示方式",
        list(DISPLAY_MODE_LABELS),
        format_func=DISPLAY_MODE_LABELS.get,
        horizontal=True,
        key=f"{view.review_case_id}:display_mode",
    )
    if mode == "compare":
        left, right = st.columns(2)
        with left:
            st.image(
                str(view.original_path),
                caption="原始圖片",
                use_container_width=True,
            )
        with right:
            st.image(
                str(view.overlay_path),
                caption="GT／模型 Overlay",
                use_container_width=True,
            )
    elif mode == "original":
        st.image(
            str(view.original_path),
            caption="原始圖片",
            use_container_width=True,
        )
    else:
        st.image(
            str(view.overlay_path),
            caption="GT／模型 Overlay",
            use_container_width=True,
        )


def _render_progress(progress: ProgressCounts) -> None:
    columns = st.columns(5)
    columns[0].metric("總案例", progress.total)
    columns[1].metric("已完成", progress.reviewed)
    columns[2].metric("未完成", progress.pending)
    columns[3].metric("待裁決", progress.needs_adjudication)
    columns[4].metric("標註問題", progress.annotation_issues)
    ratio = (
        progress.reviewed / progress.total
        if progress.total
        else 0.0
    )
    st.progress(
        ratio,
        text=f"最終完成進度：{progress.reviewed}/{progress.total}",
    )


def _render_case_metadata(view: CaseViewModel) -> None:
    with st.expander("案例與模型資訊", expanded=False):
        st.write(
            {
                "review_case_id": view.review_case_id,
                "圖片": view.image_id,
                "系統初步分類": view.auto_error_category,
                "錯誤明細": view.auto_error_detail_ids,
                "GT 數量": view.gt_count,
                "Prediction 數量": view.prediction_count,
                "最高 confidence": (
                    f"{view.max_prediction_confidence:.6f}"
                ),
                "最佳 IoU": f"{view.best_iou:.6f}",
                "驗證門檻候選": (
                    f"{view.threshold_candidate:.2f}"
                ),
                "門檻定位": view.threshold_designation,
                "目前狀態": view.review_status,
                "儲存版本": view.revision,
            }
        )
        st.caption(
            "0.20 僅為 validation threshold candidate，"
            "不是部署門檻。"
        )


def _render_review_controls(
    runtime: ReviewRuntime,
    case: SourceCase,
    case_ids: Sequence[str],
) -> None:
    initial = selection_for_case(runtime.store, case)
    prefix = case.review_case_id

    outcome_key = f"{prefix}:outcome"
    _seed_widget(outcome_key, initial.outcome)
    outcome = st.radio(
        "主要判斷",
        list(OUTCOME_LABELS),
        format_func=OUTCOME_LABELS.get,
        horizontal=True,
        key=outcome_key,
    )

    defaults = default_selection(outcome)
    reason_options = tuple(OUTCOME_REASON_OPTIONS[outcome])
    action_options = tuple(OUTCOME_ACTION_OPTIONS[outcome])
    quality_options = annotation_quality_options(outcome)
    retraining_options = priority_options(outcome)

    reason_key = f"{prefix}:reason"
    quality_key = f"{prefix}:annotation_quality"
    action_key = f"{prefix}:recommended_action"
    priority_key = f"{prefix}:retraining_priority"

    _seed_widget(
        reason_key,
        (
            initial.reason
            if initial.outcome == outcome
            else defaults.reason
        ),
        allowed=reason_options,
    )
    _seed_widget(
        quality_key,
        (
            initial.annotation_quality
            if initial.outcome == outcome
            else defaults.annotation_quality
        ),
        allowed=quality_options,
    )
    _seed_widget(
        action_key,
        (
            initial.recommended_action
            if initial.outcome == outcome
            else defaults.recommended_action
        ),
        allowed=action_options,
    )
    _seed_widget(
        priority_key,
        (
            initial.retraining_priority
            if initial.outcome == outcome
            else defaults.retraining_priority
        ),
        allowed=retraining_options,
    )

    first, second = st.columns(2)
    with first:
        reason = st.selectbox(
            "主要原因",
            reason_options,
            format_func=REASON_LABELS.get,
            key=reason_key,
        )
        annotation_quality = st.selectbox(
            "標註品質",
            quality_options,
            format_func=ANNOTATION_LABELS.get,
            key=quality_key,
        )
    with second:
        recommended_action = st.selectbox(
            "改善方向",
            action_options,
            format_func=ACTION_LABELS.get,
            key=action_key,
        )
        retraining_priority = st.selectbox(
            "重新訓練優先度",
            retraining_options,
            format_func=PRIORITY_LABELS.get,
            key=priority_key,
        )

    fields = visible_fields(
        outcome=outcome,
        reason=reason,
        annotation_quality=annotation_quality,
        recommended_action=recommended_action,
        priority=retraining_priority,
    )

    defect_type = "none"
    if "annotation_defect_type" in fields:
        defect_options = tuple(
            key
            for key in DEFECT_LABELS
            if key != "none"
        )
        defect_key = f"{prefix}:annotation_defect_type"
        initial_defect = (
            initial.annotation_defect_type
            if initial.outcome == outcome
            else defaults.annotation_defect_type
        )
        if initial_defect == "none":
            initial_defect = defect_options[0]
        _seed_widget(
            defect_key,
            initial_defect,
            allowed=defect_options,
        )
        defect_type = st.selectbox(
            "標註問題類型",
            defect_options,
            format_func=DEFECT_LABELS.get,
            key=defect_key,
        )

    notes = ""
    if "review_notes" in fields:
        notes_key = f"{prefix}:review_notes"
        _seed_widget(
            notes_key,
            (
                initial.review_notes
                if initial.outcome == outcome
                else ""
            ),
        )
        notes = st.text_area(
            "判斷說明",
            key=notes_key,
            placeholder=(
                "請具體說明影像依據、標註問題或高優先原因。"
            ),
            height=100,
        )

    selection = ReviewSelection(
        outcome=outcome,
        reason=reason,
        annotation_quality=annotation_quality,
        annotation_defect_type=defect_type,
        recommended_action=recommended_action,
        retraining_priority=retraining_priority,
        review_notes=notes,
    )

    save_column, save_next_column, status_column = st.columns(
        [1, 1, 2]
    )
    save_only = save_column.button(
        "儲存本筆",
        type="primary",
        use_container_width=True,
        key=f"{prefix}:save",
    )
    save_next = save_next_column.button(
        "儲存並下一筆",
        use_container_width=True,
        key=f"{prefix}:save_next",
    )
    with status_column:
        stored = runtime.store.get_review(case.review_case_id)
        if stored is None:
            st.info("目前尚未儲存。")
        else:
            status_label = (
                "已完成"
                if stored.canonical_fields["review_status"] == "reviewed"
                else "待裁決"
            )
            st.info(
                f"目前狀態：{status_label}｜revision {stored.revision}"
            )

    if save_only or save_next:
        try:
            next_id = next_case_id(
                case_ids,
                case.review_case_id,
                direction=1,
            )
            result = save_review_selection(
                runtime,
                case.review_case_id,
                selection,
            )
            target_case_id = (
                next_id if save_next else case.review_case_id
            )
            runtime.store.set_last_viewed(target_case_id)
            if save_next:
                queue_case_selection(
                    st.session_state,
                    target_case_id,
                )
            backup_text = (
                f"；已建立備份 {result.backup_path.name}"
                if result.backup_path is not None
                else ""
            )
            st.session_state["_review_flash_message"] = (
                f"已儲存 {case.image_id}{backup_text}"
            )
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def render_review_app(runtime: ReviewRuntime) -> None:
    st.set_page_config(
        page_title="FleetVision 04.5L 中文人工複核",
        layout="wide",
    )
    st.title("FleetVision 04.5L 中文人工複核")
    st.caption(
        "單人本機審核｜來源 package 唯讀｜"
        "不讀 test｜不重新 inference｜不修改 annotation"
    )
    _show_flash_message()

    progress = runtime.store.progress()
    _render_progress(progress)

    filter_key = "review_filter"
    _seed_widget(filter_key, "all", allowed=tuple(FILTER_LABELS))
    filter_name = st.sidebar.selectbox(
        "案例篩選",
        list(FILTER_LABELS),
        format_func=FILTER_LABELS.get,
        key=filter_key,
    )
    case_ids = runtime.store.list_case_ids(filter_name)

    if not case_ids:
        st.warning("目前篩選條件下沒有案例。")
        if st.button("切換至全部案例"):
            st.session_state[filter_key] = "all"
            st.rerun()
        return

    last_viewed = runtime.store.get_last_viewed()
    if last_viewed not in case_ids:
        last_viewed = case_ids[0]
        runtime.store.set_last_viewed(last_viewed)

    selector_key = f"case_selector:{filter_name}"
    apply_pending_case_selection(
        st.session_state,
        selector_key,
        case_ids,
        last_viewed,
    )
    _seed_widget(
        selector_key,
        last_viewed,
        allowed=case_ids,
    )
    selected_case_id = st.sidebar.selectbox(
        "跳至案例",
        case_ids,
        format_func=lambda case_id: _case_label(
            runtime,
            case_id,
        ),
        key=selector_key,
    )
    runtime.store.set_last_viewed(selected_case_id)

    previous_column, next_column = st.sidebar.columns(2)
    if previous_column.button(
        "上一筆",
        use_container_width=True,
    ):
        target_case_id = next_case_id(
            case_ids,
            selected_case_id,
            direction=-1,
        )
        runtime.store.set_last_viewed(target_case_id)
        queue_case_selection(
            st.session_state,
            target_case_id,
        )
        st.rerun()
    if next_column.button(
        "下一筆",
        use_container_width=True,
    ):
        target_case_id = next_case_id(
            case_ids,
            selected_case_id,
            direction=1,
        )
        runtime.store.set_last_viewed(target_case_id)
        queue_case_selection(
            st.session_state,
            target_case_id,
        )
        st.rerun()

    case = runtime.case_by_id[selected_case_id]
    view = build_case_view_model(runtime, case)

    st.subheader(
        f"案例 {view.case_index}/{view.total_cases}｜{view.image_id}"
    )
    _render_images(view)
    _render_case_metadata(view)
    st.divider()
    _render_review_controls(runtime, case, case_ids)

    st.divider()
    st.caption(
        "TEST_SPLIT_READ: NO｜MODEL_INFERENCE_EXECUTED: NO｜"
        "ANNOTATION_MODIFIED: NO｜TRAINING_STARTED: NO"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=(
            "configs/data/"
            "validation_error_review_app_config.yaml"
        ),
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--workspace-root",
        default="",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main(
    config_path: Path,
    project_root: Path,
    *,
    workspace_override: Path | None = None,
) -> None:
    runtime = _cached_runtime(
        str(config_path),
        str(project_root.resolve()),
        (
            str(workspace_override.resolve())
            if workspace_override is not None
            else ""
        ),
    )
    render_review_app(runtime)


if __name__ == "__main__":
    arguments = parse_args()
    main(
        Path(arguments.config),
        Path(arguments.project_root),
        workspace_override=(
            Path(arguments.workspace_root)
            if arguments.workspace_root
            else None
        ),
    )
