from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping, MutableMapping, Sequence
from zoneinfo import ZoneInfo

from fleetvision.review.severity_scope_review_mapping import (
    CONFIDENCE_LABELS,
    GROUP_LABELS,
    OPERABILITY_LABELS,
    REASON_LABELS,
    STATUS_LABELS,
    ScopeMappingValidationError,
    ScopeReviewSelection,
    derive_canonical_scope_fields,
    notes_required,
)
from fleetvision.review.severity_scope_review_package import (
    ScopeSourceCase,
    VerifiedScopePackage,
    discover_latest_f1_workspace,
    load_scope_review_app_config,
    load_verified_scope_package,
)
from fleetvision.review.severity_scope_review_state import (
    ScopeProgressCounts,
    ScopeReviewStateStore,
    StoredScopeReview,
)


FILTER_LABELS: Mapping[str, str] = {
    "all": "全部案例",
    "pending": "尚未完成",
    "reviewed": "已完成",
    "needs_adjudication": "待裁決",
    "low_confidence": "低信心",
    "catastrophic": "災難性範圍外",
}

DISPLAY_MODE_LABELS: Mapping[str, str] = {
    "compare": "左右比較",
    "original": "只看原圖",
    "overlay": "只看 Overlay",
}

PENDING_CASE_SELECTION_KEY = "_pending_scope_case_selection"


@dataclass(frozen=True)
class ScopeReviewRuntime:
    package: VerifiedScopePackage
    store: ScopeReviewStateStore
    case_by_id: Mapping[str, ScopeSourceCase]


@dataclass(frozen=True)
class ScopeCaseViewModel:
    case_index: int
    total_cases: int
    review_case_id: str
    image_id: str
    auto_error_category: str
    auto_error_detail_ids: str
    error_disposition: str
    primary_root_cause: str
    recommended_action: str
    retraining_priority: str
    original_path: Path
    overlay_path: Path
    review_status: str
    revision: int


@dataclass(frozen=True)
class SaveScopeReviewResult:
    stored_review: StoredScopeReview
    backup_path: Path | None
    progress: ScopeProgressCounts


def next_case_id(
    case_ids: Sequence[str],
    current_case_id: str,
    *,
    direction: int = 1,
) -> str:
    if not case_ids:
        raise ValueError("case_ids 不可空白")
    if current_case_id not in case_ids:
        return case_ids[0]
    index = case_ids.index(current_case_id)
    target = max(0, min(len(case_ids) - 1, index + direction))
    return case_ids[target]


def queue_case_selection(
    state: MutableMapping[str, object],
    case_id: str,
) -> None:
    state[PENDING_CASE_SELECTION_KEY] = case_id


def apply_pending_case_selection(
    state: MutableMapping[str, object],
    selector_key: str,
    case_ids: Sequence[str],
    fallback_case_id: str,
) -> str:
    if not case_ids:
        raise ValueError("case_ids 不可空白")
    fallback = fallback_case_id if fallback_case_id in case_ids else case_ids[0]
    pending = state.pop(PENDING_CASE_SELECTION_KEY, None)
    if isinstance(pending, str) and pending in case_ids:
        state[selector_key] = pending
    current = state.get(selector_key)
    if not isinstance(current, str) or current not in case_ids:
        state[selector_key] = fallback
    return str(state[selector_key])


def backup_due(successful_save_count: int, interval: int) -> bool:
    if interval <= 0:
        raise ValueError("backup interval 必須是正整數")
    return successful_save_count > 0 and successful_save_count % interval == 0


def case_widget_key(field: str, review_case_id: str) -> str:
    """Return a stable widget key isolated to one review case."""

    field_value = str(field).strip()
    case_value = str(review_case_id).strip()
    if not field_value or not case_value:
        raise ValueError("field 與 review_case_id 不可空白")
    return f"{field_value}:{case_value}"


def runtime_session_identity(
    config_path: Path,
    project_root: Path,
    f1_workspace_root: Path,
) -> str:
    """Return the session-state identity for one verified F1 workspace."""

    return "|".join(
        (
            str(config_path.resolve()),
            str(project_root.resolve()),
            str(f1_workspace_root.resolve()),
        )
    )


def load_scope_review_runtime(
    config_path: Path,
    project_root: Path,
    *,
    f1_workspace_root: Path | None = None,
) -> ScopeReviewRuntime:
    config = load_scope_review_app_config(config_path, project_root)
    root = (
        discover_latest_f1_workspace(config)
        if f1_workspace_root is None
        else f1_workspace_root.resolve()
    )
    package = load_verified_scope_package(config, root)
    store = ScopeReviewStateStore(
        package.app_workspace_root,
        backup_retention=config.backup_retention,
    )
    store.initialize(package)
    return ScopeReviewRuntime(
        package=package,
        store=store,
        case_by_id={case.review_case_id: case for case in package.cases},
    )


def selection_for_case(
    store: ScopeReviewStateStore,
    case: ScopeSourceCase,
) -> ScopeReviewSelection:
    stored = store.get_review(case.review_case_id)
    if stored is None:
        return ScopeReviewSelection()
    try:
        return ScopeReviewSelection(**dict(stored.selection))
    except TypeError as exc:
        raise ScopeMappingValidationError(
            f"既有 scope-review 狀態欄位不相容：{case.review_case_id}"
        ) from exc


def status_for_case(
    store: ScopeReviewStateStore,
    case: ScopeSourceCase,
) -> str:
    stored = store.get_review(case.review_case_id)
    if stored is None:
        return "pending"
    return str(stored.canonical_fields["scope_review_status"])


def build_case_view_model(
    runtime: ScopeReviewRuntime,
    case: ScopeSourceCase,
) -> ScopeCaseViewModel:
    stored = runtime.store.get_review(case.review_case_id)
    return ScopeCaseViewModel(
        case_index=case.case_index,
        total_cases=len(runtime.package.cases),
        review_case_id=case.review_case_id,
        image_id=case.image_id,
        auto_error_category=case.auto_error_category,
        auto_error_detail_ids=case.auto_error_detail_ids,
        error_disposition=case.error_disposition,
        primary_root_cause=case.primary_root_cause,
        recommended_action=case.recommended_action,
        retraining_priority=case.retraining_priority,
        original_path=case.original_path,
        overlay_path=case.overlay_path,
        review_status="pending" if stored is None else str(
            stored.canonical_fields["scope_review_status"]
        ),
        revision=0 if stored is None else stored.revision,
    )


def save_scope_review_selection(
    runtime: ScopeReviewRuntime,
    review_case_id: str,
    selection: ScopeReviewSelection,
    *,
    status: str,
    reviewed_at: datetime | None = None,
) -> SaveScopeReviewResult:
    timestamp = reviewed_at or datetime.now(
        ZoneInfo(runtime.package.config.timezone)
    )
    canonical = derive_canonical_scope_fields(
        selection,
        status=status,
        reviewer=runtime.package.config.reviewer,
        reviewed_at=timestamp,
    )
    stored = runtime.store.save_review(review_case_id, selection, canonical)
    successful_save_count = runtime.store.successful_save_count()
    backup_path = None
    if backup_due(
        successful_save_count,
        runtime.package.config.backup_every_successful_saves,
    ):
        backup_path = runtime.store.create_backup()
    return SaveScopeReviewResult(
        stored_review=stored,
        backup_path=backup_path,
        progress=runtime.store.progress(),
    )


def _labelled_options(labels: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(labels)


def _index_of(options: Sequence[str], value: str) -> int:
    try:
        return options.index(value)
    except ValueError:
        return 0


def render_app(
    config_path: Path,
    project_root: Path,
    *,
    f1_workspace_root: Path | None = None,
) -> None:
    """Render the Traditional Chinese Streamlit scope-review interface."""

    import streamlit as st

    st.set_page_config(
        page_title="FleetVision 車損範圍人工審核",
        page_icon="🚗",
        layout="wide",
    )
    st.title("FleetVision｜車損嚴重度範圍人工審核")
    st.caption(
        "本介面只處理 validation-only 的 130 筆 severity-scope 判定；"
        "不讀取 test、不重新推論、不修改標註或資料集，也不開始訓練。"
    )

    resolved_project_root = project_root.resolve()
    resolved_config_path = (
        config_path
        if config_path.is_absolute()
        else resolved_project_root / config_path
    ).resolve()
    app_config = load_scope_review_app_config(
        resolved_config_path,
        resolved_project_root,
    )
    resolved_f1_workspace = (
        discover_latest_f1_workspace(app_config)
        if f1_workspace_root is None
        else f1_workspace_root.resolve()
    )
    identity = runtime_session_identity(
        resolved_config_path,
        resolved_project_root,
        resolved_f1_workspace,
    )
    runtime_key = "_severity_scope_review_runtime"
    identity_key = "_severity_scope_review_runtime_identity"
    if st.session_state.get(identity_key) != identity:
        with st.spinner("正在驗證 F1 evidence 與 130 筆預覽資產…"):
            st.session_state[runtime_key] = load_scope_review_runtime(
                resolved_config_path,
                resolved_project_root,
                f1_workspace_root=resolved_f1_workspace,
            )
        st.session_state[identity_key] = identity
    runtime = st.session_state[runtime_key]
    progress = runtime.store.progress()

    metric_columns = st.columns(4)
    metric_columns[0].metric("總案例", progress.total)
    metric_columns[1].metric("已完成", progress.reviewed)
    metric_columns[2].metric("尚未完成", progress.pending)
    metric_columns[3].metric("待裁決", progress.needs_adjudication)
    st.progress(0.0 if progress.total == 0 else progress.reviewed / progress.total)

    with st.sidebar:
        st.header("審核導覽")
        filter_name = st.selectbox(
            "篩選案例",
            options=tuple(FILTER_LABELS),
            format_func=lambda value: FILTER_LABELS[value],
        )
        case_ids = list(runtime.store.case_ids(filter_name))
        if not case_ids:
            st.success("此篩選條件目前沒有案例。")
            return
        fallback = runtime.store.last_viewed_case_id() or case_ids[0]
        selector_key = f"scope_case_selector:{filter_name}"
        selected = apply_pending_case_selection(
            st.session_state,
            selector_key,
            case_ids,
            fallback,
        )
        selected = st.selectbox(
            "選擇案例",
            options=case_ids,
            index=case_ids.index(selected),
            key=selector_key,
        )
        display_mode = st.radio(
            "圖片顯示",
            options=tuple(DISPLAY_MODE_LABELS),
            format_func=lambda value: DISPLAY_MODE_LABELS[value],
        )
        st.info(
            "儲存會寫入本機 SQLite 並保留事件紀錄；每 10 次成功儲存自動備份。"
        )

    case = runtime.case_by_id[selected]
    view = build_case_view_model(runtime, case)
    st.subheader(
        f"案例 {view.case_index}/{view.total_cases}｜{view.review_case_id}"
    )
    st.caption(
        f"狀態：{view.review_status}｜修訂：{view.revision}｜image_id：{view.image_id}"
    )

    if display_mode == "compare":
        left, right = st.columns(2)
        left.image(str(view.original_path), caption="原圖", use_container_width=True)
        right.image(str(view.overlay_path), caption="Overlay", use_container_width=True)
    elif display_mode == "original":
        st.image(str(view.original_path), caption="原圖", use_container_width=True)
    else:
        st.image(str(view.overlay_path), caption="Overlay", use_container_width=True)

    with st.expander("查看既有 validation-error 人工審核資訊", expanded=False):
        st.write(
            {
                "自動錯誤類別": view.auto_error_category,
                "錯誤細節 ID": view.auto_error_detail_ids,
                "人工錯誤處置": view.error_disposition,
                "主要根因": view.primary_root_cause,
                "建議動作": view.recommended_action,
                "重新訓練優先度": view.retraining_priority,
            }
        )

    selection = selection_for_case(runtime.store, case)
    group_options = _labelled_options(GROUP_LABELS)
    reason_options = _labelled_options(REASON_LABELS)
    operability_options = _labelled_options(OPERABILITY_LABELS)
    confidence_options = _labelled_options(CONFIDENCE_LABELS)

    st.markdown("### 本次 Scope 判定")
    group = st.selectbox(
        "範圍群組",
        options=group_options,
        index=_index_of(group_options, selection.scope_group),
        format_func=lambda value: GROUP_LABELS[value],
        key=case_widget_key("scope_group", selected),
    )
    reason = st.selectbox(
        "判定原因",
        options=reason_options,
        index=_index_of(reason_options, selection.scope_reason),
        format_func=lambda value: REASON_LABELS[value],
        key=case_widget_key("scope_reason", selected),
    )
    operability = st.selectbox(
        "可行駛性",
        options=operability_options,
        index=_index_of(operability_options, selection.operability),
        format_func=lambda value: OPERABILITY_LABELS[value],
        key=case_widget_key("operability", selected),
    )
    confidence = st.selectbox(
        "信心程度",
        options=confidence_options,
        index=_index_of(confidence_options, selection.scope_confidence),
        format_func=lambda value: CONFIDENCE_LABELS[value],
        key=case_widget_key("scope_confidence", selected),
    )
    draft = ScopeReviewSelection(
        scope_group=group,
        scope_reason=reason,
        operability=operability,
        scope_confidence=confidence,
        scope_reviewer_notes=selection.scope_reviewer_notes,
    )
    require_notes = notes_required(draft, "reviewed")
    notes = st.text_area(
        "判定說明" + ("（目前判定必填）" if require_notes else "（特定情況必填）"),
        value=selection.scope_reviewer_notes,
        height=120,
        placeholder="說明影像證據、邊界判斷或待裁決原因。",
        key=case_widget_key("scope_reviewer_notes", selected),
    )
    draft = ScopeReviewSelection(
        scope_group=group,
        scope_reason=reason,
        operability=operability,
        scope_confidence=confidence,
        scope_reviewer_notes=notes,
    )

    previous_col, save_col, next_col, adjudication_col = st.columns(4)
    if previous_col.button("← 上一筆", use_container_width=True):
        queue_case_selection(
            st.session_state,
            next_case_id(case_ids, selected, direction=-1),
        )
        st.rerun()

    if save_col.button("儲存本筆", type="primary", use_container_width=True):
        try:
            result = save_scope_review_selection(
                runtime,
                selected,
                draft,
                status="reviewed",
            )
        except ScopeMappingValidationError as exc:
            st.error(str(exc))
        else:
            st.success(
                f"已儲存。進度 {result.progress.reviewed}/{result.progress.total}。"
            )
            if result.backup_path is not None:
                st.info(f"已建立備份：{result.backup_path.name}")
            st.rerun()

    if next_col.button("儲存並下一筆 →", type="primary", use_container_width=True):
        try:
            result = save_scope_review_selection(
                runtime,
                selected,
                draft,
                status="reviewed",
            )
        except ScopeMappingValidationError as exc:
            st.error(str(exc))
        else:
            target = next_case_id(case_ids, selected, direction=1)
            queue_case_selection(st.session_state, target)
            if result.backup_path is not None:
                st.toast(f"已建立備份：{result.backup_path.name}")
            st.rerun()

    if adjudication_col.button("標記待裁決", use_container_width=True):
        try:
            result = save_scope_review_selection(
                runtime,
                selected,
                draft,
                status="needs_adjudication",
            )
        except ScopeMappingValidationError as exc:
            st.error(str(exc))
        else:
            st.warning(
                f"已標記待裁決；目前待裁決 {result.progress.needs_adjudication} 筆。"
            )
            st.rerun()

    st.divider()
    st.caption(
        "完成條件：已完成 130、尚未完成 0、待裁決 0。"
        "達成後使用受控 exporter 產生 completed scope Workbook；Excel 不作為 live review state。"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--config",
        default="configs/data/severity_scope_review_app_config.yaml",
    )
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--f1-workspace-root", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    render_app(
        Path(args.config),
        Path(args.project_root),
        f1_workspace_root=(
            Path(args.f1_workspace_root) if args.f1_workspace_root else None
        ),
    )


if __name__ == "__main__":
    main()
