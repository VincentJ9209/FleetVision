# Phase 04.5D-1：External Dataset Registry v2 Schema Migration

## 背景與目的

`rf_car_damage_seg_v1` 的 Raw COCO audit 為 21,616 筆 valid bbox、403 筆 invalid bbox；完成受控 clipping 後，Interim 為 22,019 筆 valid、0 筆 invalid。Registry v1 只有單一 bbox 狀態欄位，無法同時保存 Raw 與 Interim lineage，因此本 Gate 建立 30 欄至 42 欄的 append-only migration adapter。

本 Gate 只開發、測試與 dry-run adapter，正式 Registry migration 尚未執行。

## Schema v2

既有 30 欄在 Phase 04.5D-1 全部 immutable：不得刪除、重新命名、調整順序或修改任何既有值。右側依序新增：

1. `registry_schema_version`
2. `lineage_status`
3. `bbox_count_valid_raw`
4. `bbox_count_invalid_raw`
5. `bbox_quality_status_raw`
6. `bbox_repair_count`
7. `bbox_count_valid_interim`
8. `bbox_count_invalid_interim`
9. `bbox_quality_status_interim`
10. `bbox_repair_status`
11. `local_interim_path`
12. `training_acceptance`

所有列設定 `registry_schema_version = 2`；只有 `rf_car_damage_seg_v1` 寫入其餘 configured values。其他資料列的新欄位保持空字串，列順序不變。`training_acceptance` 維持 `NOT_YET_APPROVED`。

## CLI

預設 dry-run：

```powershell
.\.venv\Scripts\python.exe scripts/phase04_5_migrate_external_dataset_registry_v2.py `
  --config configs/data/external_dataset_registry_v2_migration_config.yaml `
  --project-root . `
  --dry-run
```

`--dry-run` 與 `--execute` mutually exclusive；未指定時仍為 dry-run。只有後續正式 promotion Gate 才可對真實 Registry 使用 `--execute`。

## 安全與失敗邊界

- V1 migration 前必須符合 config 的 exact 30-column schema 與 input SHA256。
- Exact 42-column v2 會先驗證欄位順序、target 唯一性、target values 與 non-target 空值規則；完全正確才回報 already applied。
- Partial v2、錯序／額外欄位、duplicate headers、target missing／duplicate 或 configured value mismatch 全部 fail closed。
- Dry-run 只在記憶體產生 proposed bytes，不建立 temporary file。
- Execute 使用 Registry 同目錄 temporary file、flush、`os.fsync()` 與 `os.replace()`，並清除失敗殘留。
- 保留 UTF-8／BOM、LF／CRLF、CSV quoting、multiline cell、existing values 與 row order。
- Config 與 Registry path 不得逃離 project root；`local_interim_path` 必須使用 project-relative POSIX path。

## 本 Gate 不執行的工作

- 不套用既有 `registry_update_proposal.csv` 的 11 個舊欄位修改。
- 不修改 Raw、Interim 或 `outputs/metadata/external_assets/`。
- 不建立 YOLO labels、dataset split 或模型訓練。
- 不將外部資料標記為可訓練；維持 `NOT_YET_APPROVED`。

下一 Gate 是正式 Registry v2 dry-run 與 migration execution verification，不是 training。
