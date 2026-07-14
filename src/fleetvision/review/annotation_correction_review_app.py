from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping, MutableMapping, Sequence
from zoneinfo import ZoneInfo

from fleetvision.review.annotation_correction_review_mapping import (
    BBoxCoordinates,
    DECISION_LABELS,
    OPERATION_LABELS,
    STATUS_LABELS,
    CorrectionMappingValidationError,
    CorrectionReviewSelection,
    derive_canonical_correction_fields,
)
from fleetvision.review.annotation_correction_review_package import (
    CorrectionSourceCase,
    VerifiedCorrectionReviewPackage,
    load_correction_review_config,
    load_verified_correction_review_package,
)
from fleetvision.review.annotation_correction_review_state import (
    CorrectionProgressCounts,
    CorrectionReviewStateStore,
    StoredCorrectionReview,
)

FILTER_LABELS: Mapping[str, str] = {
    "all": "全部案例",
    "pending": "尚未完成",
    "reviewed": "已完成",
    "needs_adjudication": "待裁決",
}
DISPLAY_MODE_LABELS: Mapping[str, str] = {
    "compare": "四圖比較",
    "original": "原圖",
    "gt": "GT Overlay",
    "pred": "Prediction Overlay",
    "combined": "Combined Overlay",
}
PENDING_CASE_SELECTION_KEY = "_pending_correction_case_selection"


@dataclass(frozen=True)
class CorrectionReviewRuntime:
    package: VerifiedCorrectionReviewPackage
    store: CorrectionReviewStateStore
    case_by_id: Mapping[str, CorrectionSourceCase]


@dataclass(frozen=True)
class CorrectionCaseViewModel:
    case_index: int
    total_cases: int
    correction_case_id: str
    review_case_id: str
    image_id: str
    original_annotation_defect_type: str
    original_review_notes: str
    original_path: Path
    gt_overlay_path: Path
    prediction_overlay_path: Path
    combined_overlay_path: Path
    gt_bbox_rows: tuple[Mapping[str, object], ...]
    prediction_bbox_rows: tuple[Mapping[str, object], ...]
    review_status: str
    revision: int


@dataclass(frozen=True)
class SaveCorrectionReviewResult:
    stored_review: StoredCorrectionReview
    backup_path: Path
    progress: CorrectionProgressCounts


def next_case_id(case_ids: Sequence[str], current_case_id: str, *, direction: int = 1) -> str:
    if not case_ids:
        raise ValueError("case_ids 不可空白")
    if current_case_id not in case_ids:
        return case_ids[0]
    index = case_ids.index(current_case_id)
    target = max(0, min(len(case_ids) - 1, index + direction))
    return case_ids[target]


def queue_case_selection(state: MutableMapping[str, object], case_id: str) -> None:
    state[PENDING_CASE_SELECTION_KEY] = case_id


def apply_pending_case_selection(
    state: MutableMapping[str, object], selector_key: str, case_ids: Sequence[str], fallback_case_id: str
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


def case_widget_key(field: str, correction_case_id: str) -> str:
    if not str(field).strip() or not str(correction_case_id).strip():
        raise ValueError("field 與 correction_case_id 不可空白")
    return f"{field}:{correction_case_id}"


def runtime_session_identity(config_path: Path, project_root: Path, workspace_root: Path) -> str:
    return "|".join((str(config_path.resolve()), str(project_root.resolve()), str(workspace_root.resolve())))


def suggested_operation(case: CorrectionSourceCase) -> str:
    return {
        "wrong_damage_scope": "RESIZE_OR_REDRAW_BBOX",
        "extra_bbox": "REMOVE_DUPLICATE_BBOX",
    }.get(case.original_annotation_defect_type, "NOT_APPLICABLE")


def load_correction_review_runtime(
    config_path: Path, project_root: Path, *, workspace_root: Path
) -> CorrectionReviewRuntime:
    config = load_correction_review_config(config_path, project_root)
    package = load_verified_correction_review_package(config, workspace_root)
    store = CorrectionReviewStateStore(package.app_workspace_root, backup_retention=config.backup_retention)
    store.initialize(package)
    return CorrectionReviewRuntime(package, store, {case.correction_case_id: case for case in package.cases})


def selection_for_case(store: CorrectionReviewStateStore, case: CorrectionSourceCase) -> CorrectionReviewSelection:
    stored = store.get_review(case.correction_case_id)
    if stored is None:
        return CorrectionReviewSelection()
    raw = dict(stored.selection)
    bbox = raw.get("replacement_bbox")
    if isinstance(bbox, dict):
        raw["replacement_bbox"] = BBoxCoordinates(**bbox)
    targets = raw.get("target_gt_bbox_ids")
    if isinstance(targets, list):
        raw["target_gt_bbox_ids"] = tuple(targets)
    try:
        return CorrectionReviewSelection(**raw)
    except TypeError as exc:
        raise CorrectionMappingValidationError(f"既有 correction-review 狀態欄位不相容：{case.correction_case_id}") from exc


def build_case_view_model(runtime: CorrectionReviewRuntime, case: CorrectionSourceCase) -> CorrectionCaseViewModel:
    stored = runtime.store.get_review(case.correction_case_id)
    return CorrectionCaseViewModel(
        case_index=case.case_index,
        total_cases=len(runtime.package.cases),
        correction_case_id=case.correction_case_id,
        review_case_id=case.review_case_id,
        image_id=case.image_id,
        original_annotation_defect_type=case.original_annotation_defect_type,
        original_review_notes=case.original_review_notes,
        original_path=case.original_path,
        gt_overlay_path=case.gt_overlay_path,
        prediction_overlay_path=case.prediction_overlay_path,
        combined_overlay_path=case.combined_overlay_path,
        gt_bbox_rows=tuple(json.loads(case.gt_bbox_records_json)),
        prediction_bbox_rows=tuple(json.loads(case.prediction_bbox_records_json)),
        review_status="pending" if stored is None else str(stored.canonical_fields["correction_review_status"]),
        revision=0 if stored is None else stored.revision,
    )


def save_correction_review_selection(
    runtime: CorrectionReviewRuntime,
    correction_case_id: str,
    selection: CorrectionReviewSelection,
    *,
    reviewed_at: datetime | None = None,
) -> SaveCorrectionReviewResult:
    case = runtime.case_by_id[correction_case_id]
    gt_ids = tuple(row["bbox_id"] for row in json.loads(case.gt_bbox_records_json))
    timestamp = reviewed_at or datetime.now(ZoneInfo(runtime.package.config.timezone))
    canonical = derive_canonical_correction_fields(
        selection,
        reviewer=runtime.package.config.reviewer,
        reviewed_at=timestamp,
        image_width=case.image_width,
        image_height=case.image_height,
        available_gt_bbox_ids=gt_ids,
    )
    stored = runtime.store.save_review(correction_case_id, selection, canonical)
    backup = runtime.store.create_backup()
    return SaveCorrectionReviewResult(stored, backup, runtime.store.progress())


def render_app(config_path: Path, project_root: Path, *, workspace_root: Path) -> None:
    import streamlit as st

    st.set_page_config(page_title="FleetVision 標註修正提案人工複核", page_icon="🚗", layout="wide")
    st.title("FleetVision｜標註修正提案人工複核")
    st.caption("本介面只處理 validation-only 的 2 筆 annotation correction proposals；不讀取 test、不重新推論、不修改標註／資料集，也不開始訓練。")
    resolved_config = config_path if config_path.is_absolute() else project_root / config_path
    identity = runtime_session_identity(resolved_config, project_root, workspace_root)
    runtime_key = "_annotation_correction_review_runtime"
    identity_key = "_annotation_correction_review_runtime_identity"
    if st.session_state.get(identity_key) != identity:
        with st.spinner("正在驗證 Phase 04.5M package 與兩筆預覽資產…"):
            st.session_state[runtime_key] = load_correction_review_runtime(resolved_config, project_root, workspace_root=workspace_root)
        st.session_state[identity_key] = identity
    runtime: CorrectionReviewRuntime = st.session_state[runtime_key]
    progress = runtime.store.progress()
    cols = st.columns(4)
    cols[0].metric("總案例", progress.total)
    cols[1].metric("已完成", progress.reviewed)
    cols[2].metric("尚未完成", progress.pending)
    cols[3].metric("待裁決", progress.needs_adjudication)
    st.progress(0.0 if progress.total == 0 else progress.reviewed / progress.total)

    with st.sidebar:
        filter_name = st.selectbox("篩選案例", options=tuple(FILTER_LABELS), format_func=lambda value: FILTER_LABELS[value])
        case_ids = list(runtime.store.case_ids(filter_name))
        if not case_ids:
            st.success("此篩選條件目前沒有案例。")
            return
        fallback = runtime.store.last_viewed_case_id() or case_ids[0]
        selector_key = f"correction_case_selector:{filter_name}"
        selected = apply_pending_case_selection(st.session_state, selector_key, case_ids, fallback)
        selected = st.selectbox("選擇案例", options=case_ids, index=case_ids.index(selected), key=selector_key)
        display_mode = st.radio("圖片顯示", options=tuple(DISPLAY_MODE_LABELS), format_func=lambda value: DISPLAY_MODE_LABELS[value])
        st.info("儲存會寫入本機 SQLite、追加 audit event，並在每次成功儲存後建立 backup。")

    case = runtime.case_by_id[selected]
    view = build_case_view_model(runtime, case)
    st.subheader(f"案例 {view.case_index}/{view.total_cases}｜{view.review_case_id}")
    st.caption(f"狀態：{view.review_status}｜修訂：{view.revision}｜image_id：{view.image_id}")
    images = {
        "original": (view.original_path, "原圖"),
        "gt": (view.gt_overlay_path, "GT Overlay"),
        "pred": (view.prediction_overlay_path, "Prediction Overlay"),
        "combined": (view.combined_overlay_path, "Combined Overlay"),
    }
    if display_mode == "compare":
        image_cols = st.columns(4)
        for column, key in zip(image_cols, ("original", "gt", "pred", "combined")):
            path, caption = images[key]
            column.image(str(path), caption=caption, use_container_width=True)
    else:
        path, caption = images[display_mode]
        st.image(str(path), caption=caption, use_container_width=True)

    st.warning(f"原始 finding：{view.original_annotation_defect_type}｜先前備註：{view.original_review_notes}")
    left, right = st.columns(2)
    left.dataframe(list(view.gt_bbox_rows), use_container_width=True)
    right.dataframe(list(view.prediction_bbox_rows), use_container_width=True)

    current = selection_for_case(runtime.store, case)
    decision_options = tuple(DECISION_LABELS)
    operation_options = tuple(OPERATION_LABELS)
    status = st.selectbox("審核狀態", options=("reviewed", "needs_adjudication"), format_func=lambda value: STATUS_LABELS[value], key=case_widget_key("status", selected))
    decision = st.selectbox("修正決策", options=decision_options, index=decision_options.index(current.correction_decision) if current.correction_decision in decision_options else 0, format_func=lambda value: DECISION_LABELS[value], key=case_widget_key("decision", selected))
    suggestion = suggested_operation(case)
    default_operation = current.correction_operation if current.correction_review_status != "pending" else suggestion
    operation = st.selectbox("修正操作", options=operation_options, index=operation_options.index(default_operation), format_func=lambda value: OPERATION_LABELS[value], key=case_widget_key("operation", selected))
    gt_ids = tuple(str(row["bbox_id"]) for row in view.gt_bbox_rows)
    targets = tuple(st.multiselect("目標 GT bbox", options=gt_ids, default=list(current.target_gt_bbox_ids), key=case_widget_key("targets", selected)))
    bbox = current.replacement_bbox or BBoxCoordinates(0.0, 0.0, 0.0, 0.0)
    coords = st.columns(4)
    values = [coords[0].number_input("x1", value=float(bbox.x1), key=case_widget_key("x1", selected)), coords[1].number_input("y1", value=float(bbox.y1), key=case_widget_key("y1", selected)), coords[2].number_input("x2", value=float(bbox.x2), key=case_widget_key("x2", selected)), coords[3].number_input("y2", value=float(bbox.y2), key=case_widget_key("y2", selected))]
    replacement = None if operation in {"REMOVE_DUPLICATE_BBOX", "REMOVE_INVALID_BBOX", "NOT_APPLICABLE"} else BBoxCoordinates(*map(float, values))
    reason = st.text_area("修正理由", value=current.correction_reason, key=case_widget_key("reason", selected))
    if st.button("儲存此案例", type="primary", key=case_widget_key("save", selected)):
        selection = CorrectionReviewSelection(status, decision, operation, targets, replacement, reason)
        try:
            result = save_correction_review_selection(runtime, selected, selection)
        except (CorrectionMappingValidationError, KeyError) as exc:
            st.error(str(exc))
        else:
            st.success(f"已儲存 revision {result.stored_review.revision}；backup：{result.backup_path}")
            st.rerun()
    nav = st.columns(2)
    if nav[0].button("上一筆", key=case_widget_key("prev", selected)):
        queue_case_selection(st.session_state, next_case_id(case_ids, selected, direction=-1)); st.rerun()
    if nav[1].button("下一筆", key=case_widget_key("next", selected)):
        queue_case_selection(st.session_state, next_case_id(case_ids, selected, direction=1)); st.rerun()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FleetVision Phase 04.5M correction review app")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    args = parser.parse_args(argv)
    render_app(args.config, args.project_root, workspace_root=args.workspace_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
