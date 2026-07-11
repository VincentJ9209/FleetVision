# Phase 04E：Human Review Schema Promotion

## 目的

將已通過正式 Merge 驗證的 `human_*` 人工審核欄位，轉換為既有 Reviewed Dataset Builder 使用的 canonical review 欄位。

此步驟：

- 不修改正式 Merge CSV。
- 不修改既有 Reviewed Dataset Builder。
- 不建立 Reviewed Dataset。
- 不修改 `dataset/01_raw/`。
- 只建立新的 canonical promoted CSV 與驗證／provenance 報告。

## 輸入

```text
outputs/manual_review/collaboration/pilot500_human_review_results_collaboration.csv
```

## 輸出

```text
outputs/manual_review/collaboration/pilot500_review_labels_canonical.csv
outputs/metadata/pilot500_review_schema_promotion_summary.csv
outputs/metadata/pilot500_review_schema_promotion_errors.csv
outputs/metadata/pilot500_review_schema_promotion_manifest.csv
```

## 欄位映射

| Formal Merge 欄位 | Canonical 欄位 |
|---|---|
| `human_photo_type_review` | `photo_type_review` |
| `human_angle_review` | `angle_review` |
| `human_is_exterior_review` | `is_exterior_review` |
| `human_has_visible_damage_review` | `has_visible_damage_review` |
| `human_severity_review` | `severity_review` |
| `human_review_status` | `review_status` |
| `human_reviewer` | `reviewer` |
| `human_reviewed_at` | `reviewed_at` |
| `human_review_notes` | `review_notes` |

Identity 欄位 `review_id`、`image_id`、`source_bucket`、`original_path`、`filename` 必須逐值保持不變，資料列順序亦不得改變。

## 執行

從 Repository 根目錄：

```powershell
python -B scripts/phase04_promote_human_review_schema.py
```

第一次正式執行不得加入 `--overwrite`。若任一正式輸出已存在，工具會停止，避免覆蓋既有 promoted artifact。

## 成功 Gate

```text
Gate classification: SCHEMA_PROMOTION_VERIFIED
Promotion: rows=500, unique_review_ids=500, reviewed=500, pending=0, validation_errors=0, mapping_mismatches=0
FORMAL_MERGE_INPUT_MODIFIED: NO
EXISTING_BUILDER_MODIFIED: NO
REVIEWED_DATASET_BUILD_EXECUTED: NO
STOPPED_BEFORE_REVIEWED_DATASET_BUILD_GATE
```

通過後，下一個獨立 Gate 才能使用 promoted CSV 執行 Reviewed Dataset Builder。
