# FleetVision Phase 04.5L Local Review App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一個 Vincent 單人使用的本機繁體中文 Streamlit 審核介面，讓 130 個 Phase 04.5L validation-error cases 可用大圖、少量中文選項、自動儲存及自動 canonical mapping 完成審核，最後產生可通過既有 Exporter／Validator 的 completed Workbook。

**Architecture:** 應用程式分為四個純後端邊界與一個薄 UI：中文選項映射、凍結來源 package 驗證、SQLite 狀態儲存、completed Workbook 匯出，以及 Streamlit 單案例介面。原始正式 package 全程唯讀；所有進度與輸出寫入 repository 外部 workspace。UI 不直接操作 canonical schema，而是把中文選擇送入 mapping engine，再由既有 Phase 04.5L semantic validator 作最終裁決。

**Tech Stack:** Python 3.10+、Streamlit、SQLite `sqlite3`、PyYAML、OpenPyXL 3.1.5、Pandas、Pytest、Windows PowerShell 5.1。

## Global Constraints

- Repository root：`G:\Project\FleetVision`。
- Branch：`main`。
- 規劃基準 commit：`99136e9b5ef445ec10cb0999bf42648fcd1cff8b`。
- 原始正式 review batch：`G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1`。
- 原始 Workbook SHA256：`5DC9C1FDA69865D36C60EACB90A0AEA0FC9F4B263F30281723BB0E1172549DE5`。
- Frozen package ZIP SHA256：`6D6243FE8F3E12910C03A5EDCFF178CE20B180473EED43DED2B36301A877B42A`。
- Workspace：`G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_review_workspace`。
- Reviewer 固定為 `Vincent`。
- Timezone 固定為 `Asia/Taipei`，儲存值必須是 offset-aware ISO 8601。
- 一次只支援一個本機 Streamlit server 與單一操作者。
- 原始 batch、原始 Workbook、frozen ZIP、GT、canonical COCO、Registry、raw dataset、fixed split 均不得修改。
- 不讀取 test split、不重新 inference、不開始 training／fine-tuning。
- `0.20` 僅為 `BALANCED_VALIDATION_THRESHOLD_CANDIDATE`，不得視為 deployment threshold。
- Workspace、SQLite、logs、backups、completed Workbook 與其他執行輸出不得 commit。
- Git 最終狀態只能 clean，或只保留 `?? outputs/metadata/external_assets/`。
- 禁止 `git add .`、`git add -A`、`git reset --hard`、`git clean`。
- Codex 與 Cursor Agent 維持停用，除非使用者日後明確重新授權。
- 第一版不實作登入、多人同步、雲端部署、bbox 編輯、行動版或強制鍵盤快捷鍵。
- `streamlit` 已存在於 `pyproject.toml`，本計畫不新增第三方相依套件。

---

## File Structure

### Create

- `configs/data/validation_error_review_app_config.yaml`
  - 單人本機 app 路徑、固定 hashes、reviewer、timezone、backup 與 export 設定。
- `src/fleetvision/review/__init__.py`
  - review package 公開介面。
- `src/fleetvision/review/validation_error_review_mapping.py`
  - 中文 UI 選項、條件規則與 canonical mapping。
- `src/fleetvision/review/validation_error_review_package.py`
  - app config 載入、正式 package 完整性驗證與 source cases 建立。
- `src/fleetvision/review/validation_error_review_state.py`
  - SQLite schema、transactional save、導航狀態、進度統計與 backup。
- `src/fleetvision/review/validation_error_review_export.py`
  - no-overwrite completed Workbook 匯出與 semantic validation。
- `src/fleetvision/review/validation_error_review_app.py`
  - Streamlit UI 與 view-model。
- `scripts/phase04_5_run_validation_error_review_app.py`
  - 啟動 Streamlit 的 Python wrapper。
- `scripts/phase04_5_export_validation_error_review_app_workbook.py`
  - 匯出 completed Workbook 的 CLI。
- `scripts/phase04_5_launch_validation_error_review_app.ps1`
  - Windows PowerShell 5.1 啟動器。
- `tests/review_app_fixtures.py`
  - 共享測試 fixture。
- `tests/test_validation_error_review_mapping.py`
- `tests/test_validation_error_review_package.py`
- `tests/test_validation_error_review_state.py`
- `tests/test_validation_error_review_export.py`
- `tests/test_validation_error_review_app.py`
- `docs/01_phase_guides/phase_04_5_validation_error_review_app.md`

### Modify

- `.gitignore`
  - 忽略 repository 內意外產生的 review-app SQLite、JSONL、backup 與 completed Workbook。
- `requirements.txt`
  - 不新增 dependency；只確認與 `pyproject.toml` 的既有 `streamlit` 相容，不應有變更。
- `src/fleetvision/data/validation_error_human_review.py`
  - 原則上不修改；只有既有 public interface 缺少必要 export 時，才允許增加不改變行為的 `__all__` 或薄 wrapper，且必須新增 regression test。

---

### Task 1: 中文選項 Mapping 與 App Config

**Files:**
- Create: `configs/data/validation_error_review_app_config.yaml`
- Create: `src/fleetvision/review/__init__.py`
- Create: `src/fleetvision/review/validation_error_review_mapping.py`
- Test: `tests/test_validation_error_review_mapping.py`

**Interfaces:**
- Consumes:
  - `fleetvision.data.validation_error_human_review.HUMAN_COLUMNS`
  - 現有 controlled values from `configs/data/validation_error_human_review_config.yaml`
- Produces:
  - `ReviewSelection`
  - `CanonicalReviewFields`
  - `MappingValidationError`
  - `OUTCOME_LABELS`
  - `REASON_LABELS`
  - `ANNOTATION_LABELS`
  - `ACTION_LABELS`
  - `PRIORITY_LABELS`
  - `derive_canonical_fields(selection, reviewer, reviewed_at)`

- [ ] **Step 1: Write the failing mapping tests**

Create `tests/test_validation_error_review_mapping.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from fleetvision.review.validation_error_review_mapping import (
    MappingValidationError,
    ReviewSelection,
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
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_error_review_mapping.py -q
```

Expected:

```text
ERROR collecting tests/test_validation_error_review_mapping.py
ModuleNotFoundError: No module named 'fleetvision.review'
```

- [ ] **Step 3: Add the app config**

Create `configs/data/validation_error_review_app_config.yaml`:

```yaml
schema_version: "1"

source:
  batch_root: G:/Project/FleetVision_Review_Packages/Phase04_5L/phase04_5l_20260714_v1
  workbook_relative_path: workbook/validation_error_human_review.xlsx
  workbook_sha256: 5DC9C1FDA69865D36C60EACB90A0AEA0FC9F4B263F30281723BB0E1172549DE5
  frozen_zip_path: G:/Project/FleetVision_Review_Packages/Phase04_5L/phase04_5l_20260714_v1_PACKAGE.zip
  frozen_zip_sha256: 6D6243FE8F3E12910C03A5EDCFF178CE20B180473EED43DED2B36301A877B42A
  expected_case_count: 130
  canonical_config_path: configs/data/validation_error_human_review_config.yaml

workspace:
  root: G:/Project/FleetVision_Review_Packages/Phase04_5L/phase04_5l_20260714_v1_review_workspace
  reviewer: Vincent
  timezone: Asia/Taipei
  backup_every_successful_saves: 10
  backup_retention: 20
  completed_workbook_name: validation_error_human_review_completed.xlsx
```

- [ ] **Step 4: Implement the mapping module**

Create `src/fleetvision/review/__init__.py`:

```python
"""Local human-review utilities for FleetVision."""
```

Create `src/fleetvision/review/validation_error_review_mapping.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Mapping


class MappingValidationError(ValueError):
    """Raised when simplified UI input cannot form a valid canonical review."""


OUTCOME_LABELS: Mapping[str, str] = {
    "model_miss": "模型漏檢",
    "model_false_positive": "模型誤報",
    "localization_error": "模型框不準",
    "duplicate_prediction": "重複預測",
    "annotation_issue": "標註有問題",
    "threshold_tradeoff": "門檻取捨",
    "invalid_image": "圖片無效",
    "ambiguous": "無法判斷",
}

REASON_LABELS: Mapping[str, str] = {
    "missed_small_damage": "損傷太小",
    "weak_visual_signal": "損傷不明顯",
    "difficult_lighting_or_reflection": "反光或光線干擾",
    "occlusion_or_crop": "遮擋或裁切",
    "localization_error": "模型框位置不準",
    "duplicate_prediction": "同一損傷重複框選",
    "background_false_positive": "正常背景被誤判",
    "annotation_missing": "標註漏標",
    "annotation_inaccurate_bbox": "標註框不準",
    "ambiguous_visual_evidence": "影像證據不足",
    "invalid_or_low_quality_image": "圖片無效或品質太差",
    "other": "其他",
}

ANNOTATION_LABELS: Mapping[str, str] = {
    "correct": "正確",
    "questionable": "有疑問",
    "defect_suspected": "明確有問題",
    "not_applicable": "無法評估",
}

DEFECT_LABELS: Mapping[str, str] = {
    "none": "無",
    "missing_bbox": "漏標",
    "extra_bbox": "多標",
    "inaccurate_bbox": "標註框不準",
    "wrong_damage_scope": "損傷範圍不合理",
    "ambiguous_annotation": "標註規則不明確",
    "invalid_image_assignment": "圖片配錯",
    "other": "其他",
}

ACTION_LABELS: Mapping[str, str] = {
    "no_action": "不處理",
    "add_hard_negative": "增加困難負樣本",
    "add_positive_sample": "增加正樣本",
    "improve_annotation_guideline": "改善標註規範",
    "create_annotation_correction_proposal": "提出標註修正建議",
    "investigate_preprocessing": "檢查影像前處理",
    "investigate_image_quality": "檢查圖片品質",
    "adjust_model_strategy": "調整模型策略",
    "threshold_analysis_only": "僅進行門檻分析",
    "exclude_invalid_image_proposal": "提出排除無效圖片建議",
    "other": "其他",
}

PRIORITY_LABELS: Mapping[str, str] = {
    "not_applicable": "不適用",
    "low": "低",
    "medium": "中",
    "high": "高",
}

OUTCOME_DEFAULTS: Mapping[str, tuple[str, str, str]] = {
    "model_miss": ("confirmed_model_error", "missed_small_damage", "add_positive_sample"),
    "model_false_positive": (
        "confirmed_model_error",
        "background_false_positive",
        "add_hard_negative",
    ),
    "localization_error": (
        "confirmed_model_error",
        "localization_error",
        "adjust_model_strategy",
    ),
    "duplicate_prediction": (
        "confirmed_model_error",
        "duplicate_prediction",
        "adjust_model_strategy",
    ),
    "annotation_issue": (
        "annotation_issue",
        "annotation_missing",
        "create_annotation_correction_proposal",
    ),
    "threshold_tradeoff": (
        "expected_threshold_tradeoff",
        "weak_visual_signal",
        "threshold_analysis_only",
    ),
    "invalid_image": (
        "invalid_review_case",
        "invalid_or_low_quality_image",
        "exclude_invalid_image_proposal",
    ),
    "ambiguous": (
        "ambiguous_case",
        "ambiguous_visual_evidence",
        "investigate_image_quality",
    ),
}


@dataclass(frozen=True)
class ReviewSelection:
    outcome: str
    reason: str
    annotation_quality: str
    recommended_action: str
    retraining_priority: str
    annotation_defect_type: str = "none"
    secondary_reason: str = "none"
    review_notes: str = ""


@dataclass(frozen=True)
class CanonicalReviewFields:
    review_status: str
    error_disposition: str
    primary_root_cause: str
    secondary_root_cause: str
    annotation_quality: str
    annotation_defect_type: str
    recommended_action: str
    retraining_priority: str
    correction_proposal_required: str
    reviewer: str
    reviewed_at_utc: str
    review_notes: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def _require_known(value: str, allowed: Mapping[str, str], field_name: str) -> None:
    if value not in allowed:
        raise MappingValidationError(f"{field_name} 不是允許值：{value}")


def derive_canonical_fields(
    selection: ReviewSelection,
    *,
    reviewer: str,
    reviewed_at: datetime,
) -> CanonicalReviewFields:
    _require_known(selection.outcome, OUTCOME_LABELS, "主要結果")
    _require_known(selection.reason, REASON_LABELS, "主要原因")
    _require_known(selection.annotation_quality, ANNOTATION_LABELS, "標註品質")
    _require_known(selection.annotation_defect_type, DEFECT_LABELS, "標註缺陷類型")
    _require_known(selection.recommended_action, ACTION_LABELS, "改善方向")
    _require_known(selection.retraining_priority, PRIORITY_LABELS, "優先程度")

    if not reviewer.strip():
        raise MappingValidationError("審核者不可空白")
    if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
        raise MappingValidationError("審核時間必須包含時區")

    default_disposition, default_reason, default_action = OUTCOME_DEFAULTS[selection.outcome]
    primary_reason = selection.reason or default_reason
    action = selection.recommended_action or default_action
    notes = selection.review_notes.strip()

    if selection.retraining_priority == "high" and not notes:
        raise MappingValidationError("高優先案例必須填寫說明")

    defect = selection.annotation_quality == "defect_suspected"
    if defect:
        if selection.annotation_defect_type == "none":
            raise MappingValidationError("明確有標註問題時必須選擇標註缺陷類型")
        if not notes:
            raise MappingValidationError("標註缺陷必須填寫具體說明")
        if action != "create_annotation_correction_proposal":
            raise MappingValidationError("標註缺陷必須提出標註修正建議")
    else:
        if selection.annotation_defect_type != "none":
            raise MappingValidationError("標註沒有明確缺陷時，缺陷類型必須為無")
        if action == "create_annotation_correction_proposal":
            raise MappingValidationError("只有明確標註缺陷才能提出修正建議")

    if "other" in {
        selection.reason,
        selection.annotation_defect_type,
        action,
    } and not notes:
        raise MappingValidationError("選擇其他時必須填寫說明")

    status = "needs_adjudication" if selection.outcome == "ambiguous" else "reviewed"
    correction_required = "yes" if defect else "no"

    return CanonicalReviewFields(
        review_status=status,
        error_disposition=default_disposition,
        primary_root_cause=primary_reason,
        secondary_root_cause=selection.secondary_reason,
        annotation_quality=selection.annotation_quality,
        annotation_defect_type=selection.annotation_defect_type,
        recommended_action=action,
        retraining_priority=selection.retraining_priority,
        correction_proposal_required=correction_required,
        reviewer=reviewer.strip(),
        reviewed_at_utc=reviewed_at.isoformat(),
        review_notes=notes,
    )
```

- [ ] **Step 5: Run tests and confirm GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_error_review_mapping.py -q
```

Expected:

```text
4 passed
```

- [ ] **Step 6: Commit Task 1**

```powershell
git add -- `
  configs/data/validation_error_review_app_config.yaml `
  src/fleetvision/review/__init__.py `
  src/fleetvision/review/validation_error_review_mapping.py `
  tests/test_validation_error_review_mapping.py

git commit -m "feat: add local review mapping rules"
```

---

### Task 2: 凍結來源 Package 驗證與 Source Case Loader

**Files:**
- Create: `src/fleetvision/review/validation_error_review_package.py`
- Create: `tests/review_app_fixtures.py`
- Create: `tests/test_validation_error_review_package.py`

**Interfaces:**
- Consumes:
  - `fleetvision.data.validation_error_human_review.read_workbook_dataframe`
  - `fleetvision.data.validation_error_human_review.sha256_file`
  - Task 1 config path
- Produces:
  - `ReviewAppConfig`
  - `SourceCase`
  - `VerifiedSourcePackage`
  - `load_review_app_config(config_path, project_root)`
  - `load_verified_source_package(config)`

- [ ] **Step 1: Write fixture and failing package tests**

Create `tests/review_app_fixtures.py`:

```python
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from openpyxl import Workbook


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def create_review_package(tmp_path: Path, case_count: int = 2) -> tuple[Path, Path]:
    batch_root = tmp_path / "batch_001"
    original_dir = batch_root / "assets/original"
    overlay_dir = batch_root / "assets/overlay"
    workbook_dir = batch_root / "workbook"
    manifest_dir = batch_root / "manifest"

    original_dir.mkdir(parents=True)
    overlay_dir.mkdir(parents=True)
    workbook_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Review_Cases"
    headers = [
        "Original Preview",
        "Overlay Preview",
        "schema_version",
        "review_batch_id",
        "review_case_id",
        "source_04_5k_zip_sha256",
        "source_case_fingerprint",
        "image_id",
        "image_filename",
        "auto_error_category",
        "auto_error_detail_ids",
        "error_case_count",
        "ground_truth_error_count",
        "prediction_error_count",
        "gt_count",
        "prediction_count",
        "max_prediction_confidence",
        "best_iou",
        "threshold_candidate",
        "threshold_designation",
        "original_image_relpath",
        "overlay_image_relpath",
        "review_status",
        "error_disposition",
        "primary_root_cause",
        "secondary_root_cause",
        "annotation_quality",
        "annotation_defect_type",
        "recommended_action",
        "retraining_priority",
        "correction_proposal_required",
        "reviewer",
        "reviewed_at_utc",
        "review_notes",
    ]
    sheet.append(headers)

    for index in range(case_count):
        image_id = f"case_{index:03d}.jpg"
        original = original_dir / image_id
        overlay = overlay_dir / f"review_{index:03d}.jpg"
        original.write_bytes(b"original-" + bytes([index]))
        overlay.write_bytes(b"overlay-" + bytes([index]))
        sheet.append(
            [
                "",
                "",
                "1",
                "batch_001",
                f"review_{index:03d}",
                "A" * 64,
                f"{index:064X}",
                image_id,
                image_id,
                "false_negative",
                "false_negative",
                "1",
                "1",
                "1",
                "1",
                "0",
                "0.10",
                "0.00",
                "0.20",
                "BALANCED_VALIDATION_THRESHOLD_CANDIDATE",
                f"assets/original/{image_id}",
                f"assets/overlay/review_{index:03d}.jpg",
                "pending",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )

    for name in ("Instructions", "Option_Lists", "Manifest", "Progress_Summary"):
        workbook.create_sheet(name)
    workbook._sheets = [
        workbook["Instructions"],
        workbook["Review_Cases"],
        workbook["Option_Lists"],
        workbook["Manifest"],
        workbook["Progress_Summary"],
    ]

    workbook_path = workbook_dir / "validation_error_human_review.xlsx"
    workbook.save(workbook_path)

    source_manifest = {
        "gate_id": "04.5L-PREP",
        "classification": "VALIDATION_ERROR_HUMAN_REVIEW_PACKAGE_PREPARED",
        "review_batch_id": "batch_001",
        "case_count": case_count,
        "test_split_read": False,
        "model_inference_executed": False,
        "annotation_modified": False,
        "training_started": False,
    }
    (manifest_dir / "source_manifest.json").write_text(
        json.dumps(source_manifest),
        encoding="utf-8",
    )

    rows: list[dict[str, str]] = []
    for path in sorted(candidate for candidate in batch_root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(batch_root).as_posix()
        rows.append(
            {
                "relative_path": relative,
                "size_bytes": str(path.stat().st_size),
                "sha256": sha256_file(path),
            }
        )

    with (manifest_dir / "asset_manifest.csv").open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["relative_path", "size_bytes", "sha256"],
        )
        writer.writeheader()
        writer.writerows(rows)

    checksum_rows = [
        path
        for path in sorted(candidate for candidate in batch_root.rglob("*") if candidate.is_file())
        if path.name != "checksums.sha256"
    ]
    (manifest_dir / "checksums.sha256").write_text(
        "\n".join(
            f"{sha256_file(path)}  {path.relative_to(batch_root).as_posix()}"
            for path in checksum_rows
        )
        + "\n",
        encoding="utf-8",
    )

    frozen_zip = tmp_path / "batch_001_PACKAGE.zip"
    with zipfile.ZipFile(frozen_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(candidate for candidate in batch_root.rglob("*") if candidate.is_file()):
            archive.write(path, arcname=path.relative_to(batch_root.parent).as_posix())

    return batch_root, frozen_zip


def write_app_config(
    tmp_path: Path,
    batch_root: Path,
    frozen_zip: Path,
    *,
    workbook_sha256: str,
    frozen_zip_sha256: str,
    case_count: int = 2,
) -> Path:
    workspace = tmp_path / "workspace"
    config_path = tmp_path / "review_app.yaml"
    config_path.write_text(
        "\n".join(
            [
                'schema_version: "1"',
                "source:",
                f"  batch_root: {batch_root.as_posix()}",
                "  workbook_relative_path: workbook/validation_error_human_review.xlsx",
                f"  workbook_sha256: {workbook_sha256}",
                f"  frozen_zip_path: {frozen_zip.as_posix()}",
                f"  frozen_zip_sha256: {frozen_zip_sha256}",
                f"  expected_case_count: {case_count}",
                "  canonical_config_path: configs/data/validation_error_human_review_config.yaml",
                "workspace:",
                f"  root: {workspace.as_posix()}",
                "  reviewer: Vincent",
                "  timezone: Asia/Taipei",
                "  backup_every_successful_saves: 10",
                "  backup_retention: 20",
                "  completed_workbook_name: validation_error_human_review_completed.xlsx",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return config_path
```

Create `tests/test_validation_error_review_package.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from fleetvision.review.validation_error_review_package import (
    PackageVerificationError,
    load_review_app_config,
    load_verified_source_package,
)
from review_app_fixtures import create_review_package, sha256_file, write_app_config


def test_verified_package_loads_source_cases(tmp_path: Path) -> None:
    batch_root, frozen_zip = create_review_package(tmp_path)
    workbook = batch_root / "workbook/validation_error_human_review.xlsx"
    config_path = write_app_config(
        tmp_path,
        batch_root,
        frozen_zip,
        workbook_sha256=sha256_file(workbook),
        frozen_zip_sha256=sha256_file(frozen_zip),
    )

    config = load_review_app_config(config_path, tmp_path)
    package = load_verified_source_package(config)

    assert package.batch_root == batch_root.resolve()
    assert len(package.cases) == 2
    assert package.cases[0].case_index == 1
    assert package.cases[0].review_case_id == "review_000"
    assert package.cases[0].original_path.is_file()
    assert package.cases[0].overlay_path.is_file()


def test_workbook_hash_mismatch_blocks_startup(tmp_path: Path) -> None:
    batch_root, frozen_zip = create_review_package(tmp_path)
    config_path = write_app_config(
        tmp_path,
        batch_root,
        frozen_zip,
        workbook_sha256="0" * 64,
        frozen_zip_sha256=sha256_file(frozen_zip),
    )
    config = load_review_app_config(config_path, tmp_path)

    with pytest.raises(PackageVerificationError, match="Workbook SHA256"):
        load_verified_source_package(config)


def test_test_path_is_forbidden(tmp_path: Path) -> None:
    test_root = tmp_path / "test"
    test_root.mkdir()
    batch_root, frozen_zip = create_review_package(test_root)
    workbook = batch_root / "workbook/validation_error_human_review.xlsx"
    config_path = write_app_config(
        tmp_path,
        batch_root,
        frozen_zip,
        workbook_sha256=sha256_file(workbook),
        frozen_zip_sha256=sha256_file(frozen_zip),
    )
    config = load_review_app_config(config_path, tmp_path)

    with pytest.raises(PackageVerificationError, match="test split"):
        load_verified_source_package(config)
```

- [ ] **Step 2: Run focused tests and confirm RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_error_review_package.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'fleetvision.review.validation_error_review_package'
```

- [ ] **Step 3: Implement verified package loading**

Create `src/fleetvision/review/validation_error_review_package.py`:

```python
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from fleetvision.data.validation_error_human_review import (
    read_workbook_dataframe,
    sha256_file,
)


class PackageVerificationError(RuntimeError):
    """Raised when the frozen review package cannot be trusted."""


@dataclass(frozen=True)
class ReviewAppConfig:
    schema_version: str
    project_root: Path
    batch_root: Path
    workbook_relative_path: str
    workbook_sha256: str
    frozen_zip_path: Path
    frozen_zip_sha256: str
    expected_case_count: int
    canonical_config_path: Path
    workspace_root: Path
    reviewer: str
    timezone: str
    backup_every_successful_saves: int
    backup_retention: int
    completed_workbook_name: str

    @property
    def workbook_path(self) -> Path:
        return self.batch_root / self.workbook_relative_path


@dataclass(frozen=True)
class SourceCase:
    case_index: int
    review_case_id: str
    source_case_fingerprint: str
    image_id: str
    auto_error_category: str
    gt_count: int
    prediction_count: int
    max_prediction_confidence: float
    best_iou: float
    original_relpath: str
    overlay_relpath: str
    original_path: Path
    overlay_path: Path


@dataclass(frozen=True)
class VerifiedSourcePackage:
    config: ReviewAppConfig
    batch_root: Path
    workbook_path: Path
    cases: tuple[SourceCase, ...]


def _resolve(project_root: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def _assert_not_test_path(path: Path, label: str) -> None:
    if any(part.lower() == "test" for part in path.parts):
        raise PackageVerificationError(f"{label} may not reference test split: {path}")


def load_review_app_config(config_path: Path, project_root: Path) -> ReviewAppConfig:
    resolved_config = _resolve(project_root, str(config_path))
    raw = yaml.safe_load(resolved_config.read_text(encoding="utf-8")) or {}
    source = raw["source"]
    workspace = raw["workspace"]

    config = ReviewAppConfig(
        schema_version=str(raw["schema_version"]),
        project_root=project_root.resolve(),
        batch_root=_resolve(project_root, str(source["batch_root"])),
        workbook_relative_path=str(source["workbook_relative_path"]),
        workbook_sha256=str(source["workbook_sha256"]).upper(),
        frozen_zip_path=_resolve(project_root, str(source["frozen_zip_path"])),
        frozen_zip_sha256=str(source["frozen_zip_sha256"]).upper(),
        expected_case_count=int(source["expected_case_count"]),
        canonical_config_path=_resolve(project_root, str(source["canonical_config_path"])),
        workspace_root=_resolve(project_root, str(workspace["root"])),
        reviewer=str(workspace["reviewer"]).strip(),
        timezone=str(workspace["timezone"]).strip(),
        backup_every_successful_saves=int(workspace["backup_every_successful_saves"]),
        backup_retention=int(workspace["backup_retention"]),
        completed_workbook_name=str(workspace["completed_workbook_name"]).strip(),
    )

    for label, digest in (
        ("workbook_sha256", config.workbook_sha256),
        ("frozen_zip_sha256", config.frozen_zip_sha256),
    ):
        if len(digest) != 64 or any(character not in "0123456789ABCDEF" for character in digest):
            raise PackageVerificationError(f"{label} must be 64 uppercase hex characters")
    if config.expected_case_count <= 0:
        raise PackageVerificationError("expected_case_count must be positive")
    if not config.reviewer:
        raise PackageVerificationError("reviewer is required")
    if config.backup_every_successful_saves <= 0 or config.backup_retention <= 0:
        raise PackageVerificationError("backup settings must be positive")
    if not config.completed_workbook_name.lower().endswith(".xlsx"):
        raise PackageVerificationError("completed_workbook_name must end with .xlsx")
    return config


def _verify_manifest(batch_root: Path) -> None:
    manifest_path = batch_root / "manifest/asset_manifest.csv"
    checksum_path = batch_root / "manifest/checksums.sha256"
    if not manifest_path.is_file() or not checksum_path.is_file():
        raise PackageVerificationError("manifest or checksums are missing")

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    seen: set[str] = set()
    for row in rows:
        relative = row["relative_path"].replace("\\", "/")
        if relative in seen:
            raise PackageVerificationError(f"duplicate manifest path: {relative}")
        seen.add(relative)
        path = batch_root / PurePosixPath(relative)
        if not path.is_file():
            raise PackageVerificationError(f"manifest file missing: {relative}")
        if str(path.stat().st_size) != row["size_bytes"].strip():
            raise PackageVerificationError(f"manifest size mismatch: {relative}")
        if sha256_file(path) != row["sha256"].strip().upper():
            raise PackageVerificationError(f"manifest SHA256 mismatch: {relative}")

    for raw_line in checksum_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        digest, relative = line.split(maxsplit=1)
        path = batch_root / PurePosixPath(relative.replace("\\", "/"))
        if not path.is_file() or sha256_file(path) != digest.upper():
            raise PackageVerificationError(f"checksum mismatch: {relative}")


def load_verified_source_package(config: ReviewAppConfig) -> VerifiedSourcePackage:
    _assert_not_test_path(config.batch_root, "batch_root")
    _assert_not_test_path(config.workbook_path, "workbook_path")
    if not config.batch_root.is_dir():
        raise PackageVerificationError(f"batch root not found: {config.batch_root}")
    if not config.workbook_path.is_file():
        raise PackageVerificationError(f"Workbook not found: {config.workbook_path}")
    if sha256_file(config.workbook_path) != config.workbook_sha256:
        raise PackageVerificationError("Workbook SHA256 mismatch")
    if not config.frozen_zip_path.is_file():
        raise PackageVerificationError(f"frozen ZIP not found: {config.frozen_zip_path}")
    if sha256_file(config.frozen_zip_path) != config.frozen_zip_sha256:
        raise PackageVerificationError("frozen ZIP SHA256 mismatch")

    source_manifest_path = config.batch_root / "manifest/source_manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    expected_manifest = {
        "classification": "VALIDATION_ERROR_HUMAN_REVIEW_PACKAGE_PREPARED",
        "case_count": config.expected_case_count,
        "test_split_read": False,
        "model_inference_executed": False,
        "annotation_modified": False,
        "training_started": False,
    }
    for key, expected in expected_manifest.items():
        if source_manifest.get(key) != expected:
            raise PackageVerificationError(
                f"source manifest mismatch: {key}={source_manifest.get(key)!r}"
            )

    _verify_manifest(config.batch_root)
    frame = read_workbook_dataframe(config.workbook_path)
    if len(frame) != config.expected_case_count:
        raise PackageVerificationError(
            f"case count mismatch: expected={config.expected_case_count} actual={len(frame)}"
        )
    if frame["review_case_id"].nunique(dropna=False) != len(frame):
        raise PackageVerificationError("review_case_id must be unique")

    cases: list[SourceCase] = []
    for index, row in enumerate(frame.to_dict(orient="records"), start=1):
        original_relpath = row["original_image_relpath"].replace("\\", "/")
        overlay_relpath = row["overlay_image_relpath"].replace("\\", "/")
        original_path = config.batch_root / PurePosixPath(original_relpath)
        overlay_path = config.batch_root / PurePosixPath(overlay_relpath)
        if not original_path.is_file() or not overlay_path.is_file():
            raise PackageVerificationError(f"review assets missing for {row['review_case_id']}")
        cases.append(
            SourceCase(
                case_index=index,
                review_case_id=row["review_case_id"],
                source_case_fingerprint=row["source_case_fingerprint"],
                image_id=row["image_id"],
                auto_error_category=row["auto_error_category"],
                gt_count=int(row["gt_count"]),
                prediction_count=int(row["prediction_count"]),
                max_prediction_confidence=float(row["max_prediction_confidence"]),
                best_iou=float(row["best_iou"]),
                original_relpath=original_relpath,
                overlay_relpath=overlay_relpath,
                original_path=original_path,
                overlay_path=overlay_path,
            )
        )

    return VerifiedSourcePackage(
        config=config,
        batch_root=config.batch_root,
        workbook_path=config.workbook_path,
        cases=tuple(cases),
    )
```

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_error_review_package.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit Task 2**

```powershell
git add -- `
  src/fleetvision/review/validation_error_review_package.py `
  tests/review_app_fixtures.py `
  tests/test_validation_error_review_package.py

git commit -m "feat: verify local review source package"
```

---

### Task 3: SQLite State Store、Progress 與 Backup

**Files:**
- Create: `src/fleetvision/review/validation_error_review_state.py`
- Create: `tests/test_validation_error_review_state.py`

**Interfaces:**
- Consumes:
  - `VerifiedSourcePackage`
  - `ReviewSelection`
  - `CanonicalReviewFields`
- Produces:
  - `WorkspaceIdentity`
  - `StoredReview`
  - `ProgressCounts`
  - `ReviewStateStore.initialize(package)`
  - `ReviewStateStore.save_review(...)`
  - `ReviewStateStore.get_review(review_case_id)`
  - `ReviewStateStore.list_case_ids(filter_name)`
  - `ReviewStateStore.progress()`
  - `ReviewStateStore.set_last_viewed(review_case_id)`
  - `ReviewStateStore.get_last_viewed()`
  - `ReviewStateStore.create_backup()`

- [ ] **Step 1: Write failing state tests**

Create `tests/test_validation_error_review_state.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fleetvision.review.validation_error_review_mapping import (
    ReviewSelection,
    derive_canonical_fields,
)
from fleetvision.review.validation_error_review_package import (
    load_review_app_config,
    load_verified_source_package,
)
from fleetvision.review.validation_error_review_state import ReviewStateStore
from review_app_fixtures import create_review_package, sha256_file, write_app_config


def _store(tmp_path: Path) -> tuple[ReviewStateStore, str]:
    batch_root, frozen_zip = create_review_package(tmp_path)
    workbook = batch_root / "workbook/validation_error_human_review.xlsx"
    config_path = write_app_config(
        tmp_path,
        batch_root,
        frozen_zip,
        workbook_sha256=sha256_file(workbook),
        frozen_zip_sha256=sha256_file(frozen_zip),
    )
    config = load_review_app_config(config_path, tmp_path)
    package = load_verified_source_package(config)
    store = ReviewStateStore(config.workspace_root, backup_retention=20)
    store.initialize(package)
    return store, package.cases[0].review_case_id


def test_save_reload_and_progress(tmp_path: Path) -> None:
    store, review_case_id = _store(tmp_path)
    selection = ReviewSelection(
        outcome="model_miss",
        reason="missed_small_damage",
        annotation_quality="correct",
        recommended_action="add_positive_sample",
        retraining_priority="medium",
    )
    canonical = derive_canonical_fields(
        selection,
        reviewer="Vincent",
        reviewed_at=datetime(2026, 7, 14, 3, 0, tzinfo=timezone.utc),
    )

    saved = store.save_review(review_case_id, selection, canonical)
    reloaded = store.get_review(review_case_id)
    progress = store.progress()

    assert saved.revision == 1
    assert reloaded is not None
    assert reloaded.canonical_fields["review_status"] == "reviewed"
    assert progress.reviewed == 1
    assert progress.pending == 1


def test_workspace_identity_mismatch_is_blocked(tmp_path: Path) -> None:
    store, _ = _store(tmp_path)
    database_path = store.database_path

    with database_path.open("ab") as handle:
        handle.write(b"tamper")

    assert database_path.is_file()


def test_backup_is_created_and_retention_is_enforced(tmp_path: Path) -> None:
    store, _ = _store(tmp_path)

    for _ in range(22):
        store.create_backup()

    backups = sorted(store.backup_dir.glob("review_state_*.sqlite3"))
    assert len(backups) == 20
```

- [ ] **Step 2: Run focused tests and confirm RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_error_review_state.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'fleetvision.review.validation_error_review_state'
```

- [ ] **Step 3: Implement the state store**

Create `src/fleetvision/review/validation_error_review_state.py`:

```python
from __future__ import annotations

import json
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from fleetvision.review.validation_error_review_mapping import (
    CanonicalReviewFields,
    ReviewSelection,
)
from fleetvision.review.validation_error_review_package import VerifiedSourcePackage


class ReviewStateError(RuntimeError):
    """Raised when local review state is inconsistent or unsafe."""


@dataclass(frozen=True)
class StoredReview:
    review_case_id: str
    selection: dict[str, str]
    canonical_fields: dict[str, str]
    revision: int
    saved_at_utc: str


@dataclass(frozen=True)
class ProgressCounts:
    total: int
    reviewed: int
    pending: int
    needs_adjudication: int
    high_priority: int
    annotation_issues: int


class ReviewStateStore:
    def __init__(self, workspace_root: Path, *, backup_retention: int) -> None:
        self.workspace_root = workspace_root.resolve()
        self.state_dir = self.workspace_root / "state"
        self.backup_dir = self.workspace_root / "backups"
        self.export_dir = self.workspace_root / "exports"
        self.log_dir = self.workspace_root / "app_logs"
        self.database_path = self.state_dir / "review_state.sqlite3"
        self.event_log_path = self.state_dir / "review_events.jsonl"
        self.backup_retention = backup_retention

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self, package: VerifiedSourcePackage) -> None:
        for path in (self.state_dir, self.backup_dir, self.export_dir, self.log_dir):
            path.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS workspace_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS review_cases (
                    review_case_id TEXT PRIMARY KEY,
                    case_index INTEGER NOT NULL UNIQUE,
                    source_case_fingerprint TEXT NOT NULL,
                    image_id TEXT NOT NULL,
                    ui_selection_json TEXT NOT NULL DEFAULT '{}',
                    canonical_fields_json TEXT NOT NULL DEFAULT '{}',
                    review_status TEXT NOT NULL DEFAULT 'pending',
                    revision INTEGER NOT NULL DEFAULT 0,
                    saved_at_utc TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS export_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    output_path TEXT NOT NULL UNIQUE,
                    sha256 TEXT NOT NULL,
                    exported_at_utc TEXT NOT NULL
                );
                """
            )
            identity = {
                "schema_version": package.config.schema_version,
                "batch_root": str(package.batch_root),
                "workbook_sha256": package.config.workbook_sha256,
                "frozen_zip_sha256": package.config.frozen_zip_sha256,
                "expected_case_count": str(package.config.expected_case_count),
                "reviewer": package.config.reviewer,
            }
            existing = {
                row["key"]: row["value"]
                for row in connection.execute("SELECT key, value FROM workspace_metadata")
            }
            if existing and existing != identity:
                raise ReviewStateError("workspace identity does not match source package")
            if not existing:
                connection.executemany(
                    "INSERT INTO workspace_metadata(key, value) VALUES(?, ?)",
                    identity.items(),
                )

            for case in package.cases:
                connection.execute(
                    """
                    INSERT INTO review_cases(
                        review_case_id,
                        case_index,
                        source_case_fingerprint,
                        image_id
                    )
                    VALUES(?, ?, ?, ?)
                    ON CONFLICT(review_case_id) DO NOTHING
                    """,
                    (
                        case.review_case_id,
                        case.case_index,
                        case.source_case_fingerprint,
                        case.image_id,
                    ),
                )

    def save_review(
        self,
        review_case_id: str,
        selection: ReviewSelection,
        canonical: CanonicalReviewFields,
    ) -> StoredReview:
        saved_at = datetime.now(timezone.utc).isoformat()
        selection_json = json.dumps(asdict(selection), ensure_ascii=False, sort_keys=True)
        canonical_json = json.dumps(
            canonical.as_dict(),
            ensure_ascii=False,
            sort_keys=True,
        )
        with self._connect() as connection:
            row = connection.execute(
                "SELECT revision FROM review_cases WHERE review_case_id = ?",
                (review_case_id,),
            ).fetchone()
            if row is None:
                raise ReviewStateError(f"unknown review_case_id: {review_case_id}")
            revision = int(row["revision"]) + 1
            connection.execute(
                """
                UPDATE review_cases
                SET ui_selection_json = ?,
                    canonical_fields_json = ?,
                    review_status = ?,
                    revision = ?,
                    saved_at_utc = ?
                WHERE review_case_id = ?
                """,
                (
                    selection_json,
                    canonical_json,
                    canonical.review_status,
                    revision,
                    saved_at,
                    review_case_id,
                ),
            )

        event = {
            "event": "review_saved",
            "review_case_id": review_case_id,
            "revision": revision,
            "saved_at_utc": saved_at,
            "review_status": canonical.review_status,
        }
        with self.event_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

        return StoredReview(
            review_case_id=review_case_id,
            selection=json.loads(selection_json),
            canonical_fields=json.loads(canonical_json),
            revision=revision,
            saved_at_utc=saved_at,
        )

    def get_review(self, review_case_id: str) -> StoredReview | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT review_case_id, ui_selection_json, canonical_fields_json,
                       revision, saved_at_utc
                FROM review_cases
                WHERE review_case_id = ?
                """,
                (review_case_id,),
            ).fetchone()
        if row is None or int(row["revision"]) == 0:
            return None
        return StoredReview(
            review_case_id=row["review_case_id"],
            selection=json.loads(row["ui_selection_json"]),
            canonical_fields=json.loads(row["canonical_fields_json"]),
            revision=int(row["revision"]),
            saved_at_utc=row["saved_at_utc"],
        )

    def progress(self) -> ProgressCounts:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT review_status, canonical_fields_json FROM review_cases"
            ).fetchall()
        reviewed = 0
        pending = 0
        needs_adjudication = 0
        high_priority = 0
        annotation_issues = 0
        for row in rows:
            status = row["review_status"]
            canonical = json.loads(row["canonical_fields_json"])
            reviewed += int(status == "reviewed")
            pending += int(status == "pending")
            needs_adjudication += int(status == "needs_adjudication")
            high_priority += int(canonical.get("retraining_priority") == "high")
            annotation_issues += int(canonical.get("annotation_quality") == "defect_suspected")
        return ProgressCounts(
            total=len(rows),
            reviewed=reviewed,
            pending=pending,
            needs_adjudication=needs_adjudication,
            high_priority=high_priority,
            annotation_issues=annotation_issues,
        )

    def list_case_ids(self, filter_name: str = "all") -> list[str]:
        queries = {
            "all": "SELECT review_case_id FROM review_cases ORDER BY case_index",
            "pending": (
                "SELECT review_case_id FROM review_cases "
                "WHERE review_status = 'pending' ORDER BY case_index"
            ),
            "reviewed": (
                "SELECT review_case_id FROM review_cases "
                "WHERE review_status = 'reviewed' ORDER BY case_index"
            ),
            "needs_adjudication": (
                "SELECT review_case_id FROM review_cases "
                "WHERE review_status = 'needs_adjudication' ORDER BY case_index"
            ),
        }
        if filter_name not in queries:
            raise ReviewStateError(f"unsupported filter: {filter_name}")
        with self._connect() as connection:
            return [
                row["review_case_id"]
                for row in connection.execute(queries[filter_name]).fetchall()
            ]

    def set_last_viewed(self, review_case_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO app_state(key, value)
                VALUES('last_viewed_case_id', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (review_case_id,),
            )

    def get_last_viewed(self) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_state WHERE key = 'last_viewed_case_id'"
            ).fetchone()
        return None if row is None else str(row["value"])

    def create_backup(self) -> Path:
        if not self.database_path.is_file():
            raise ReviewStateError("state database does not exist")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output = self.backup_dir / f"review_state_{timestamp}.sqlite3"
        shutil.copy2(self.database_path, output)
        backups = sorted(self.backup_dir.glob("review_state_*.sqlite3"))
        for stale in backups[:-self.backup_retention]:
            stale.unlink()
        return output
```

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_error_review_state.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit Task 3**

```powershell
git add -- `
  src/fleetvision/review/validation_error_review_state.py `
  tests/test_validation_error_review_state.py

git commit -m "feat: persist local review progress"
```

---

### Task 4: Completed Workbook Exporter

**Files:**
- Create: `src/fleetvision/review/validation_error_review_export.py`
- Create: `tests/test_validation_error_review_export.py`

**Interfaces:**
- Consumes:
  - `VerifiedSourcePackage`
  - `ReviewStateStore`
  - `HUMAN_COLUMNS`
  - `read_workbook_dataframe`
  - `validate_canonical_dataframe`
- Produces:
  - `CompletedWorkbookExport`
  - `export_completed_workbook(package, store)`

- [ ] **Step 1: Write failing exporter tests**

Create `tests/test_validation_error_review_export.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from openpyxl import load_workbook

from fleetvision.data.validation_error_human_review import read_workbook_dataframe
from fleetvision.review.validation_error_review_export import (
    CompletedWorkbookExportError,
    export_completed_workbook,
)
from fleetvision.review.validation_error_review_mapping import (
    ReviewSelection,
    derive_canonical_fields,
)
from fleetvision.review.validation_error_review_package import (
    load_review_app_config,
    load_verified_source_package,
)
from fleetvision.review.validation_error_review_state import ReviewStateStore
from review_app_fixtures import create_review_package, sha256_file, write_app_config


def _prepared(tmp_path: Path):
    batch_root, frozen_zip = create_review_package(tmp_path)
    workbook = batch_root / "workbook/validation_error_human_review.xlsx"
    config_path = write_app_config(
        tmp_path,
        batch_root,
        frozen_zip,
        workbook_sha256=sha256_file(workbook),
        frozen_zip_sha256=sha256_file(frozen_zip),
    )
    config = load_review_app_config(config_path, tmp_path)
    package = load_verified_source_package(config)
    store = ReviewStateStore(config.workspace_root, backup_retention=20)
    store.initialize(package)
    return package, store


def test_export_is_blocked_while_pending_cases_exist(tmp_path: Path) -> None:
    package, store = _prepared(tmp_path)

    with pytest.raises(CompletedWorkbookExportError, match="130/130 reviewed"):
        export_completed_workbook(package, store)


def test_completed_workbook_preserves_source_fields(tmp_path: Path) -> None:
    package, store = _prepared(tmp_path)
    for case in package.cases:
        selection = ReviewSelection(
            outcome="model_miss",
            reason="missed_small_damage",
            annotation_quality="correct",
            recommended_action="add_positive_sample",
            retraining_priority="medium",
        )
        canonical = derive_canonical_fields(
            selection,
            reviewer="Vincent",
            reviewed_at=datetime(2026, 7, 14, 4, 0, tzinfo=timezone.utc),
        )
        store.save_review(case.review_case_id, selection, canonical)

    before = read_workbook_dataframe(package.workbook_path)
    result = export_completed_workbook(package, store)
    after = read_workbook_dataframe(result.output_path)

    assert result.output_path.is_file()
    assert result.row_count == 2
    assert set(after["review_status"]) == {"reviewed"}
    assert before["source_case_fingerprint"].tolist() == after["source_case_fingerprint"].tolist()

    workbook = load_workbook(result.output_path)
    assert workbook.sheetnames == [
        "Instructions",
        "Review_Cases",
        "Option_Lists",
        "Manifest",
        "Progress_Summary",
    ]


def test_completed_workbook_refuses_overwrite(tmp_path: Path) -> None:
    package, store = _prepared(tmp_path)
    for case in package.cases:
        selection = ReviewSelection(
            outcome="model_miss",
            reason="missed_small_damage",
            annotation_quality="correct",
            recommended_action="add_positive_sample",
            retraining_priority="medium",
        )
        canonical = derive_canonical_fields(
            selection,
            reviewer="Vincent",
            reviewed_at=datetime(2026, 7, 14, 4, 0, tzinfo=timezone.utc),
        )
        store.save_review(case.review_case_id, selection, canonical)

    export_completed_workbook(package, store)
    with pytest.raises(CompletedWorkbookExportError, match="overwrite"):
        export_completed_workbook(package, store)
```

- [ ] **Step 2: Run focused tests and confirm RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_error_review_export.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'fleetvision.review.validation_error_review_export'
```

- [ ] **Step 3: Implement no-overwrite completed Workbook export**

Create `src/fleetvision/review/validation_error_review_export.py`:

```python
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook

from fleetvision.data.validation_error_human_review import (
    HUMAN_COLUMNS,
    load_config,
    read_workbook_dataframe,
    sha256_file,
    validate_canonical_dataframe,
)
from fleetvision.review.validation_error_review_package import VerifiedSourcePackage
from fleetvision.review.validation_error_review_state import ReviewStateStore


class CompletedWorkbookExportError(RuntimeError):
    """Raised when completed Workbook export is unsafe or incomplete."""


@dataclass(frozen=True)
class CompletedWorkbookExport:
    output_path: Path
    sha256: str
    row_count: int
    exported_at_utc: str


def export_completed_workbook(
    package: VerifiedSourcePackage,
    store: ReviewStateStore,
) -> CompletedWorkbookExport:
    progress = store.progress()
    if (
        progress.reviewed != progress.total
        or progress.pending != 0
        or progress.needs_adjudication != 0
    ):
        raise CompletedWorkbookExportError(
            f"completed Workbook requires 130/130 reviewed; "
            f"reviewed={progress.reviewed} pending={progress.pending} "
            f"needs_adjudication={progress.needs_adjudication}"
        )

    if sha256_file(package.workbook_path) != package.config.workbook_sha256:
        raise CompletedWorkbookExportError("source Workbook SHA256 changed")

    output_path = store.export_dir / package.config.completed_workbook_name
    if output_path.exists():
        raise CompletedWorkbookExportError(
            f"completed Workbook overwrite is forbidden: {output_path}"
        )

    store.create_backup()
    temporary_path = output_path.with_suffix(".staging.xlsx")
    if temporary_path.exists():
        raise CompletedWorkbookExportError(
            f"staging Workbook already exists: {temporary_path}"
        )

    shutil.copy2(package.workbook_path, temporary_path)
    try:
        workbook = load_workbook(temporary_path, read_only=False, data_only=False)
        sheet = workbook["Review_Cases"]
        headers = {str(cell.value): cell.column for cell in sheet[1]}
        row_by_case_id = {
            str(sheet.cell(row=row_index, column=headers["review_case_id"]).value): row_index
            for row_index in range(2, sheet.max_row + 1)
        }

        for case in package.cases:
            stored = store.get_review(case.review_case_id)
            if stored is None:
                raise CompletedWorkbookExportError(
                    f"missing stored review: {case.review_case_id}"
                )
            row_index = row_by_case_id[case.review_case_id]
            for column in HUMAN_COLUMNS:
                sheet.cell(
                    row=row_index,
                    column=headers[column],
                    value=stored.canonical_fields[column],
                )

        workbook.save(temporary_path)
        frame = read_workbook_dataframe(temporary_path)
        canonical_config = load_config(
            package.config.canonical_config_path,
            package.config.project_root,
        )
        validation = validate_canonical_dataframe(
            frame,
            canonical_config,
            require_complete=True,
            batch_root=package.batch_root,
        )
        if not validation.passed:
            codes = ", ".join(issue["error_code"] for issue in validation.issues[:10])
            raise CompletedWorkbookExportError(
                f"completed Workbook semantic validation failed: {codes}"
            )

        source_frame = read_workbook_dataframe(package.workbook_path)
        if (
            source_frame["source_case_fingerprint"].tolist()
            != frame["source_case_fingerprint"].tolist()
        ):
            raise CompletedWorkbookExportError("source identity changed during export")

        temporary_path.replace(output_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    exported_at = datetime.now(timezone.utc).isoformat()
    digest = sha256_file(output_path)
    with store._connect() as connection:
        connection.execute(
            """
            INSERT INTO export_history(output_path, sha256, exported_at_utc)
            VALUES(?, ?, ?)
            """,
            (str(output_path), digest, exported_at),
        )

    return CompletedWorkbookExport(
        output_path=output_path,
        sha256=digest,
        row_count=len(package.cases),
        exported_at_utc=exported_at,
    )
```

- [ ] **Step 4: Run exporter and existing Phase 04.5L tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_validation_error_review_export.py `
  tests/test_validation_error_human_review.py `
  -q
```

Expected:

```text
all selected tests passed
```

- [ ] **Step 5: Commit Task 4**

```powershell
git add -- `
  src/fleetvision/review/validation_error_review_export.py `
  tests/test_validation_error_review_export.py

git commit -m "feat: export completed local review workbook"
```

---

### Task 5: Streamlit 單案例中文 UI

**Files:**
- Create: `src/fleetvision/review/validation_error_review_app.py`
- Create: `tests/test_validation_error_review_app.py`

**Interfaces:**
- Consumes:
  - `ReviewAppConfig`
  - `VerifiedSourcePackage`
  - `ReviewStateStore`
  - Task 1 label dictionaries and mapping
- Produces:
  - `CaseViewModel`
  - `build_case_view_model(case, stored_review)`
  - `visible_fields(outcome, annotation_quality, priority)`
  - `main(config_path, project_root)`

- [ ] **Step 1: Write failing view-model tests**

Create `tests/test_validation_error_review_app.py`:

```python
from __future__ import annotations

from fleetvision.review.validation_error_review_app import visible_fields


def test_normal_model_miss_uses_simple_fields() -> None:
    assert visible_fields(
        outcome="model_miss",
        annotation_quality="correct",
        priority="medium",
    ) == {
        "reason",
        "annotation_quality",
        "recommended_action",
        "retraining_priority",
    }


def test_annotation_issue_expands_defect_and_notes() -> None:
    assert visible_fields(
        outcome="annotation_issue",
        annotation_quality="defect_suspected",
        priority="not_applicable",
    ) == {
        "reason",
        "annotation_quality",
        "annotation_defect_type",
        "recommended_action",
        "retraining_priority",
        "review_notes",
    }


def test_high_priority_requires_notes_field() -> None:
    assert "review_notes" in visible_fields(
        outcome="model_false_positive",
        annotation_quality="correct",
        priority="high",
    )
```

- [ ] **Step 2: Run focused tests and confirm RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_error_review_app.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'fleetvision.review.validation_error_review_app'
```

- [ ] **Step 3: Implement the thin Streamlit UI**

Create `src/fleetvision/review/validation_error_review_app.py`:

```python
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

from fleetvision.review.validation_error_review_mapping import (
    ACTION_LABELS,
    ANNOTATION_LABELS,
    DEFECT_LABELS,
    OUTCOME_DEFAULTS,
    OUTCOME_LABELS,
    PRIORITY_LABELS,
    REASON_LABELS,
    ReviewSelection,
    derive_canonical_fields,
)
from fleetvision.review.validation_error_review_package import (
    SourceCase,
    load_review_app_config,
    load_verified_source_package,
)
from fleetvision.review.validation_error_review_state import ReviewStateStore, StoredReview


@dataclass(frozen=True)
class CaseViewModel:
    case_index: int
    review_case_id: str
    image_id: str
    auto_error_category: str
    gt_count: int
    prediction_count: int
    max_prediction_confidence: float
    best_iou: float
    original_path: Path
    overlay_path: Path


def build_case_view_model(case: SourceCase) -> CaseViewModel:
    return CaseViewModel(
        case_index=case.case_index,
        review_case_id=case.review_case_id,
        image_id=case.image_id,
        auto_error_category=case.auto_error_category,
        gt_count=case.gt_count,
        prediction_count=case.prediction_count,
        max_prediction_confidence=case.max_prediction_confidence,
        best_iou=case.best_iou,
        original_path=case.original_path,
        overlay_path=case.overlay_path,
    )


def visible_fields(
    *,
    outcome: str,
    annotation_quality: str,
    priority: str,
) -> set[str]:
    fields = {
        "reason",
        "annotation_quality",
        "recommended_action",
        "retraining_priority",
    }
    if outcome == "annotation_issue" or annotation_quality == "defect_suspected":
        fields.update({"annotation_defect_type", "review_notes"})
    if outcome == "ambiguous" or priority == "high":
        fields.add("review_notes")
    return fields


def _select_by_label(
    label: str,
    values: dict[str, str],
    *,
    index: int = 0,
    key: str,
) -> str:
    options = list(values)
    selected = st.selectbox(
        label,
        options,
        index=index,
        format_func=lambda value: values[value],
        key=key,
    )
    return str(selected)


def main(config_path: Path, project_root: Path) -> None:
    st.set_page_config(
        page_title="FleetVision 04.5L 中文人工複核",
        layout="wide",
    )

    config = load_review_app_config(config_path, project_root)
    package = load_verified_source_package(config)
    store = ReviewStateStore(
        config.workspace_root,
        backup_retention=config.backup_retention,
    )
    store.initialize(package)

    case_by_id = {case.review_case_id: case for case in package.cases}
    filter_name = st.sidebar.selectbox(
        "案例篩選",
        ["all", "pending", "reviewed", "needs_adjudication"],
        format_func={
            "all": "全部",
            "pending": "未審核",
            "reviewed": "已完成",
            "needs_adjudication": "待裁決",
        }.get,
    )
    case_ids = store.list_case_ids(filter_name)
    if not case_ids:
        st.info("目前篩選條件下沒有案例。")
        return

    last_viewed = store.get_last_viewed()
    default_index = case_ids.index(last_viewed) if last_viewed in case_ids else 0
    selected_case_id = st.sidebar.selectbox(
        "跳至案例",
        case_ids,
        index=default_index,
        format_func=lambda value: (
            f"{case_by_id[value].case_index:03d}｜{case_by_id[value].image_id}"
        ),
    )
    store.set_last_viewed(selected_case_id)

    case = case_by_id[selected_case_id]
    view = build_case_view_model(case)
    progress = store.progress()

    st.title("FleetVision 04.5L 中文人工複核")
    st.caption(
        f"案例 {view.case_index} / {progress.total}｜"
        f"已完成 {progress.reviewed}｜"
        f"待裁決 {progress.needs_adjudication}｜"
        f"未審核 {progress.pending}"
    )

    display_mode = st.radio(
        "圖片顯示",
        ["compare", "original", "overlay"],
        horizontal=True,
        format_func={
            "compare": "左右比較",
            "original": "只看原圖",
            "overlay": "只看 Overlay",
        }.get,
    )
    if display_mode == "compare":
        left, right = st.columns(2)
        left.image(str(view.original_path), caption="原始圖片", use_container_width=True)
        right.image(str(view.overlay_path), caption="GT／模型 Overlay", use_container_width=True)
    elif display_mode == "original":
        st.image(str(view.original_path), caption="原始圖片", use_container_width=True)
    else:
        st.image(str(view.overlay_path), caption="GT／模型 Overlay", use_container_width=True)

    with st.expander("案例資訊", expanded=False):
        st.write(
            {
                "圖片": view.image_id,
                "系統初步分類": view.auto_error_category,
                "GT 數量": view.gt_count,
                "Prediction 數量": view.prediction_count,
                "最高 confidence": f"{view.max_prediction_confidence:.4f}",
                "最佳 IoU": f"{view.best_iou:.4f}",
                "Threshold": "0.20（validation candidate，非部署門檻）",
            }
        )

    stored = store.get_review(selected_case_id)
    initial = stored.selection if stored is not None else {}

    with st.form("review_form", clear_on_submit=False):
        outcome_options = list(OUTCOME_LABELS)
        outcome = st.radio(
            "主要結果",
            outcome_options,
            index=outcome_options.index(initial.get("outcome", "model_miss")),
            format_func=OUTCOME_LABELS.get,
        )

        default_disposition, default_reason, default_action = OUTCOME_DEFAULTS[outcome]
        reason = _select_by_label(
            "主要原因",
            dict(REASON_LABELS),
            index=list(REASON_LABELS).index(initial.get("reason", default_reason)),
            key=f"{selected_case_id}_reason",
        )
        annotation_quality = _select_by_label(
            "標註品質",
            dict(ANNOTATION_LABELS),
            index=list(ANNOTATION_LABELS).index(
                initial.get(
                    "annotation_quality",
                    "defect_suspected" if outcome == "annotation_issue" else "correct",
                )
            ),
            key=f"{selected_case_id}_annotation_quality",
        )
        recommended_action = _select_by_label(
            "改善方向",
            dict(ACTION_LABELS),
            index=list(ACTION_LABELS).index(
                initial.get("recommended_action", default_action)
            ),
            key=f"{selected_case_id}_recommended_action",
        )
        retraining_priority = _select_by_label(
            "優先程度",
            dict(PRIORITY_LABELS),
            index=list(PRIORITY_LABELS).index(
                initial.get(
                    "retraining_priority",
                    "not_applicable"
                    if outcome in {"annotation_issue", "invalid_image", "ambiguous"}
                    else "medium",
                )
            ),
            key=f"{selected_case_id}_priority",
        )

        fields = visible_fields(
            outcome=outcome,
            annotation_quality=annotation_quality,
            priority=retraining_priority,
        )
        annotation_defect_type = "none"
        if "annotation_defect_type" in fields:
            annotation_defect_type = _select_by_label(
                "標註問題類型",
                dict(DEFECT_LABELS),
                index=list(DEFECT_LABELS).index(
                    initial.get("annotation_defect_type", "missing_bbox")
                ),
                key=f"{selected_case_id}_defect",
            )

        review_notes = initial.get("review_notes", "")
        if "review_notes" in fields:
            review_notes = st.text_area(
                "判斷說明",
                value=review_notes,
                key=f"{selected_case_id}_notes",
            )

        save_only = st.form_submit_button("儲存")
        save_next = st.form_submit_button("儲存並下一筆")

    if save_only or save_next:
        selection = ReviewSelection(
            outcome=outcome,
            reason=reason,
            annotation_quality=annotation_quality,
            annotation_defect_type=annotation_defect_type,
            recommended_action=recommended_action,
            retraining_priority=retraining_priority,
            review_notes=review_notes,
        )
        try:
            canonical = derive_canonical_fields(
                selection,
                reviewer=config.reviewer,
                reviewed_at=datetime.now(ZoneInfo(config.timezone)),
            )
            store.save_review(selected_case_id, selection, canonical)
            progress_after = store.progress()
            successful_saves = progress_after.reviewed + progress_after.needs_adjudication
            if successful_saves > 0 and (
                successful_saves % config.backup_every_successful_saves == 0
            ):
                store.create_backup()
            st.success("已儲存。")
            if save_next:
                current_position = case_ids.index(selected_case_id)
                next_position = min(current_position + 1, len(case_ids) - 1)
                store.set_last_viewed(case_ids[next_position])
                st.rerun()
        except Exception as exc:
            st.error(str(exc))

    st.divider()
    st.caption(
        "TEST_SPLIT_READ: NO｜MODEL_INFERENCE_EXECUTED: NO｜"
        "ANNOTATION_MODIFIED: NO｜TRAINING_STARTED: NO"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/data/validation_error_review_app_config.yaml",
    )
    parser.add_argument("--project-root", default=".")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    main(Path(arguments.config), Path(arguments.project_root).resolve())
```

- [ ] **Step 4: Run view-model tests and import smoke**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_error_review_app.py -q

.\.venv\Scripts\python.exe -c "import fleetvision.review.validation_error_review_app as app; print(app.__name__)"
```

Expected:

```text
3 passed
fleetvision.review.validation_error_review_app
```

- [ ] **Step 5: Commit Task 5**

```powershell
git add -- `
  src/fleetvision/review/validation_error_review_app.py `
  tests/test_validation_error_review_app.py

git commit -m "feat: add Chinese local review interface"
```

---

### Task 6: CLI、PowerShell Launcher、Docs、Ignore Rules 與 End-to-End Verification

**Files:**
- Create: `scripts/phase04_5_run_validation_error_review_app.py`
- Create: `scripts/phase04_5_export_validation_error_review_app_workbook.py`
- Create: `scripts/phase04_5_launch_validation_error_review_app.ps1`
- Create: `docs/01_phase_guides/phase_04_5_validation_error_review_app.md`
- Modify: `.gitignore`
- Test: all Task 1–5 tests plus existing repository suite

**Interfaces:**
- Consumes:
  - `validation_error_review_app.main`
  - `export_completed_workbook`
  - default app config path
- Produces:
  - PowerShell 5.1 launch command
  - export CLI
  - operator guide
  - final controlled implementation classification

- [ ] **Step 1: Create the Python Streamlit launcher**

Create `scripts/phase04_5_run_validation_error_review_app.py`:

```python
"""Launch FleetVision Phase 04.5L local review app through Streamlit."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = (
    PROJECT_ROOT
    / "src/fleetvision/review/validation_error_review_app.py"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/data/validation_error_review_app_config.yaml",
    )
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--headless", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_PATH),
        "--browser.gatherUsageStats=false",
        f"--server.headless={'true' if args.headless else 'false'}",
        "--",
        "--config",
        str(args.config),
        "--project-root",
        str(args.project_root),
    ]
    return subprocess.call(command, cwd=PROJECT_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Create the completed Workbook export CLI**

Create `scripts/phase04_5_export_validation_error_review_app_workbook.py`:

```python
"""Export a completed Workbook from FleetVision local review state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fleetvision.review.validation_error_review_export import (  # noqa: E402
    export_completed_workbook,
)
from fleetvision.review.validation_error_review_package import (  # noqa: E402
    load_review_app_config,
    load_verified_source_package,
)
from fleetvision.review.validation_error_review_state import ReviewStateStore  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/data/validation_error_review_app_config.yaml",
    )
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    config = load_review_app_config(Path(args.config), project_root)
    package = load_verified_source_package(config)
    store = ReviewStateStore(
        config.workspace_root,
        backup_retention=config.backup_retention,
    )
    store.initialize(package)
    result = export_completed_workbook(package, store)

    print("Gate classification: LOCAL_REVIEW_APP_COMPLETED_WORKBOOK_EXPORTED")
    print(f"Completed Workbook: {result.output_path}")
    print(f"Completed Workbook SHA256: {result.sha256}")
    print(f"Review cases: {result.row_count}")
    print("TEST_SPLIT_READ: NO")
    print("MODEL_INFERENCE_EXECUTED: NO")
    print("ANNOTATION_MODIFIED: NO")
    print("TRAINING_STARTED: NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Create the PowerShell 5.1 launcher**

Create `scripts/phase04_5_launch_validation_error_review_app.ps1`:

```powershell
#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$ProjectRoot = "G:\Project\FleetVision",
    [string]$Config = "configs/data/validation_error_review_app_config.yaml"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Launcher = Join-Path $ProjectRoot "scripts\phase04_5_run_validation_error_review_app.py"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python executable not found: $Python"
}
if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    throw "Review app launcher not found: $Launcher"
}

Push-Location -LiteralPath $ProjectRoot
try {
    & $Python $Launcher --config $Config --project-root $ProjectRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Review app exited with code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
```

- [ ] **Step 4: Add local-output ignore rules**

Append to `.gitignore`:

```gitignore
# Phase 04.5L local review app accidental in-repo outputs
**/review_state.sqlite3
**/review_state.sqlite3-wal
**/review_state.sqlite3-shm
**/review_events.jsonl
**/review_state_*.sqlite3
**/validation_error_human_review_completed.xlsx
```

- [ ] **Step 5: Write the operator guide**

Create `docs/01_phase_guides/phase_04_5_validation_error_review_app.md` with these exact sections:

```markdown
# Phase 04.5L 本機中文人工複核介面

## 目的

使用繁體中文、大尺寸原圖／Overlay 與少量條件式選項完成 130 個
validation-error cases。介面只在本機運作，不讀 test、不重新推論、不修改
annotation，也不開始 training。

## 啟動

```powershell
cd G:\Project\FleetVision

Set-ExecutionPolicy -Scope Process Bypass

.\scripts\phase04_5_launch_validation_error_review_app.ps1
```

瀏覽器未自動開啟時，使用 Streamlit 終端輸出的 Local URL。

## 每張圖片的操作

1. 先看原圖與 Overlay。
2. 選擇主要結果。
3. 確認系統帶入的主要原因、標註品質、改善方向與優先度。
4. 標註問題、高優先、無法判斷或其他案例需填寫說明。
5. 按「儲存」或「儲存並下一筆」。

## 狀態

- 未審核：尚未完成。
- 已完成：可納入 completed Workbook。
- 待裁決：必須日後返回並改成已完成。

## 中斷與恢復

關閉瀏覽器或停止 Streamlit 不會清除 SQLite 進度。重新啟動後會回到上次
檢視案例。每 10 次成功儲存建立 backup，最多保留 20 份。

## 匯出 completed Workbook

只有 130/130 已完成，且 pending 與 needs_adjudication 均為 0 時執行：

```powershell
cd G:\Project\FleetVision

.\.venv\Scripts\python.exe `
  scripts\phase04_5_export_validation_error_review_app_workbook.py
```

輸出位於：

```text
G:\Project\FleetVision_Review_Packages\Phase04_5L\
phase04_5l_20260714_v1_review_workspace\
exports\
validation_error_human_review_completed.xlsx
```

## 安全邊界

- 原始 batch、Workbook 與 frozen ZIP 不覆寫。
- 不修改 GT、canonical COCO、Registry、raw dataset 或 fixed split。
- 不讀 test split。
- 不重新 inference。
- 不開始 training／fine-tuning。
- completed Workbook 仍須通過既有 Phase 04.5L Exporter 與 Validator。
```

- [ ] **Step 6: Run CLI help and focused suite**

Run:

```powershell
.\.venv\Scripts\python.exe scripts/phase04_5_run_validation_error_review_app.py --help

.\.venv\Scripts\python.exe scripts/phase04_5_export_validation_error_review_app_workbook.py --help

.\.venv\Scripts\python.exe -m pytest `
  tests/test_validation_error_review_mapping.py `
  tests/test_validation_error_review_package.py `
  tests/test_validation_error_review_state.py `
  tests/test_validation_error_review_export.py `
  tests/test_validation_error_review_app.py `
  tests/test_validation_error_human_review.py `
  -q
```

Expected:

```text
Both CLI help commands exit 0.
All selected tests passed.
```

- [ ] **Step 7: Run full repository verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q

.\.venv\Scripts\python.exe scripts/phase00_init_project.py --validate

git diff --check
```

Expected:

```text
Full pytest suite passes with only pre-existing allowed skips.
Phase 00 validation passes.
git diff --check exits 0.
```

- [ ] **Step 8: Run a headless Streamlit startup smoke**

Run in PowerShell:

```powershell
$process = Start-Process `
  -FilePath "G:\Project\FleetVision\.venv\Scripts\python.exe" `
  -ArgumentList @(
    "scripts\phase04_5_run_validation_error_review_app.py",
    "--headless"
  ) `
  -WorkingDirectory "G:\Project\FleetVision" `
  -PassThru

Start-Sleep -Seconds 8

if ($process.HasExited) {
    throw "Streamlit smoke process exited early with code $($process.ExitCode)"
}

Stop-Process -Id $process.Id
```

Expected:

```text
The Streamlit process remains alive until explicitly stopped.
No source package file hash changes.
No test-split path is accessed.
```

- [ ] **Step 9: Verify immutable source hashes**

Run:

```powershell
Get-FileHash `
  "G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1\workbook\validation_error_human_review.xlsx" `
  -Algorithm SHA256

Get-FileHash `
  "G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_PACKAGE.zip" `
  -Algorithm SHA256
```

Expected:

```text
Workbook:
5DC9C1FDA69865D36C60EACB90A0AEA0FC9F4B263F30281723BB0E1172549DE5

Frozen ZIP:
6D6243FE8F3E12910C03A5EDCFF178CE20B180473EED43DED2B36301A877B42A
```

- [ ] **Step 10: Commit Task 6**

```powershell
git add -- `
  .gitignore `
  scripts/phase04_5_run_validation_error_review_app.py `
  scripts/phase04_5_export_validation_error_review_app_workbook.py `
  scripts/phase04_5_launch_validation_error_review_app.ps1 `
  docs/01_phase_guides/phase_04_5_validation_error_review_app.md

git commit -m "docs: add local review app operation workflow"
```

- [ ] **Step 11: Push and verify remote**

```powershell
git push origin main
git fetch origin main --prune

$local = git rev-parse HEAD
$origin = git rev-parse origin/main
$remote = (git ls-remote origin refs/heads/main).Split("`t")[0]

if ($local -ne $origin -or $local -ne $remote) {
    throw "Local, origin/main, and remote main do not match."
}

git status --short --untracked-files=normal
```

Expected final status:

```text
?? outputs/metadata/external_assets/
```

Expected implementation classification:

```text
LOCAL_REVIEW_APP_IMPLEMENTED_TESTED_COMMITTED_AND_REMOTE_VERIFIED
```

Expected safety declarations:

```text
TEST_SPLIT_READ: NO
MODEL_INFERENCE_EXECUTED: NO
ANNOTATION_MODIFIED: NO
TRAINING_STARTED: NO
RETRAINING_STATUS: NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE: NOT_YET_APPROVED
```

---

## Plan Self-Review

### Spec Coverage

- 單人、本機、繁體中文：Tasks 1、5、6。
- 大圖與一次一案例：Task 5。
- 中文簡化選項與條件式欄位：Tasks 1、5。
- Canonical mapping 與既有 Validator 相容：Tasks 1、4。
- SQLite transaction、恢復、backup：Task 3。
- 原始 package 完整性與 fail-closed：Task 2。
- completed Workbook no-overwrite：Task 4。
- PowerShell 5.1 啟動：Task 6。
- 130/130 才可匯出：Tasks 3、4。
- 原始 hashes 不變、安全邊界與 full suite：Task 6。
- 不加入多人、登入、雲端、bbox 編輯、re-inference：Global Constraints 與 Task 6 guide。

### Type Consistency

- `ReviewSelection` 與 `CanonicalReviewFields` 由 Task 1 定義。
- `ReviewAppConfig`、`SourceCase`、`VerifiedSourcePackage` 由 Task 2 定義。
- `ReviewStateStore`、`StoredReview`、`ProgressCounts` 由 Task 3 定義。
- `CompletedWorkbookExport` 由 Task 4 定義。
- Task 4、5、6 使用的名稱與前述定義一致。

### Execution Order

Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6。不得平行跳過 dependency task；每個 Task 必須先通過 focused tests 並 commit，再開始下一個 Task。
