# Phase 04.5D-2：External Dataset Registry v2 Intake Promotion

## 目的

本 Gate 使用獨立 adapter，將受保護的
`registry_update_proposal.csv` 中已完成的 intake 結果，安全 promotion
至 `dataset/00_catalog/external_dataset_registry.csv` 的既有 30 個 legacy
欄位之一部分。

本 adapter 不重新執行 external dataset intake、bbox repair、YOLO
轉換、dataset split 或模型訓練。

## 輸入

- Registry：
  `dataset/00_catalog/external_dataset_registry.csv`
- Intake proposal：
  `outputs/metadata/external_assets/roboflow/rf_car_damage_seg_v1/registry_update_proposal.csv`
- Config：
  `configs/data/external_dataset_registry_v2_intake_promotion_config.yaml`

`outputs/metadata/external_assets/` 永久保持 untracked、read-only，不得
修改、刪除、stage 或 commit。

## 固定 promotion 欄位

Adapter 只允許 promotion 以下 11 欄：

1. `download_date`
2. `image_count_downloaded`
3. `bbox_count_reported`
4. `bbox_count_valid`
5. `accepted_image_count`
6. `rejected_image_count`
7. `bbox_quality_status`
8. `sha256_dedup_status`
9. `usage_status`
10. `local_raw_path`
11. `notes`

欄位集合是固定契約，不會依目前差異動態擴張。

## Identity 欄位

其餘 19 個 legacy 欄位必須在 Registry 與 proposal 完全一致。任何
差異都會 fail closed，避免 stale proposal 或 Registry drift：

- `dataset_id`
- `platform`
- `dataset_name`
- `source_url`
- `publisher`
- `license`
- `license_evidence_url`
- `license_verified`
- `search_date`
- `dataset_version`
- `task_type`
- `annotation_format`
- `original_classes`
- `image_count_reported`
- `mapping_to_damage`
- `domain_similarity`
- `perceptual_hash_status`
- `internal_cross_dedup_status`
- `rejection_reason`

## Registry v2 保護欄位

以下 12 欄不得由 intake proposal 修改：

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

`training_acceptance` 必須永久保持：

```text
NOT_YET_APPROVED
```

## 欄位語意

- Legacy `bbox_count_valid=21616` 是 intake 時的 Raw valid bbox 數。
- `bbox_count_valid_raw=21616` 保存 Raw QA 結果。
- `bbox_count_valid_interim=22019` 保存 clipping repair 後的 Interim 結果。
- `notes` 依 proposal 精確取代，不與舊 Registry notes 合併。
- Proposal 的 `local_raw_path` 保留既有絕對 Windows 路徑，但 adapter
  會驗證它位於 project root 內，且精確對應 config 中的
  project-relative Raw 目錄。

## CLI

### 預設 dry-run

```powershell
.\.venv\Scripts\python.exe `
  scripts/phase04_5_promote_external_dataset_registry_v2_intake.py `
  --config configs/data/external_dataset_registry_v2_intake_promotion_config.yaml `
  --project-root . `
  --dry-run
```

未指定 `--dry-run` 或 `--execute` 時仍為 dry-run。

### Execute

```powershell
.\.venv\Scripts\python.exe `
  scripts/phase04_5_promote_external_dataset_registry_v2_intake.py `
  --config configs/data/external_dataset_registry_v2_intake_promotion_config.yaml `
  --project-root . `
  --execute
```

`--dry-run` 與 `--execute` mutually exclusive。只有在獨立的正式
promotion Gate 核准後，才可對真實 Registry 使用 `--execute`。

## Dry-run 契約

Dry-run：

- 驗證 Registry 與 proposal SHA256。
- 驗證精確 42／30 欄 schema 與欄位順序。
- 驗證 Registry row count 與完整 `dataset_id` 順序符合 config。
- 驗證 target Dataset ID 在兩側唯一。
- 驗證 19 個 identity 欄位。
- 驗證 12 個 Registry v2 protected 欄位。
- 驗證 Raw path 位於 project root 且目錄存在。
- 僅在記憶體建立 proposed Registry bytes。
- 不建立 temporary file。
- 不修改 Registry、proposal、Raw、Interim 或 protected metadata。

預期 classification：

```text
EXTERNAL_DATASET_REGISTRY_V2_INTAKE_PROMOTION_DRY_RUN_VERIFIED
```

## Execute 契約

Execute 使用 Registry 同目錄 temporary file，並執行：

1. 完整 validation。
2. 寫入 temporary file。
3. `flush()`。
4. `os.fsync()`。
5. staged bytes 驗證。
6. `os.replace()` atomic replacement。
7. post-write bytes、SHA256、schema、row 與 protected fields 驗證。
8. post-write 驗證失敗時，以原 Registry bytes rollback。
9. 清除 temporary file。

預期 classification：

```text
EXTERNAL_DATASET_REGISTRY_V2_INTAKE_PROMOTION_VERIFIED
```

## Already applied

只有在 11 個 promotion 欄位全部符合 proposal，且 19 個 identity
欄位、12 個 protected v2 欄位與 schema 契約皆正確時，才能回傳：

```text
EXTERNAL_DATASET_REGISTRY_V2_INTAKE_PROMOTION_ALREADY_APPLIED
```

不得只依 `usage_status=downloaded` 判斷。

## Fail-closed 邊界

以下情況全部 BLOCKED：

- Registry 或 proposal SHA256 不符。
- 欄位缺漏、錯序、額外欄位或 duplicate headers。
- Registry row count 或 `dataset_id` 順序不符。
- target row missing 或 duplicate。
- proposal 不只一列。
- identity 欄位不一致。
- protected v2 欄位不一致。
- `training_acceptance` 不是 `NOT_YET_APPROVED`。
- `local_raw_path` 逃離 project root、不存在或不符合 configured path。
- partial promotion。
- Registry 在 validation 與 execute 之間改變。
- proposal 在 validation 與 execute 之間改變。
- atomic replacement 或 post-write verification 失敗。

Blocked classification：

```text
EXTERNAL_DATASET_REGISTRY_V2_INTAKE_PROMOTION_BLOCKED
```

## 不執行的工作

- 不修改 `dataset/01_raw/`。
- 不修改 `dataset/02_interim/`。
- 不修改 `outputs/metadata/external_assets/`。
- 不建立 YOLO labels。
- 不建立 dataset split。
- 不執行 model training。
- 不核准 training acceptance。

## Phase 邊界

Adapter implementation、tests、config 與本 guide 完成後，下一個獨立
Gate 才能對真實 inputs 執行 **dry-run**。

Dry-run 驗證通過後，仍須完成獨立驗證；不得在同一 Gate 直接執行
正式 promotion。
