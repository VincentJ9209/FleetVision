# Phase 04.5L — Validation Error Human Review

## 1. 目的

Phase 04.5L 對 Phase 04.5K 產生的 130 個 validation error cases 進行人工複核。

本階段採用：

- Excel Workbook：人工操作介面。
- Canonical CSV：正式人工複核成果。
- Validator：唯一品質 Gate。
- Correction proposal：只記錄 annotation defect 建議，不修改 GT。

## 2. 不可跨越的邊界

- 僅可使用 validation evidence。
- 不讀取 test split。
- 不重新執行模型 inference。
- 不修改 canonical COCO、raw dataset、Registry、固定 split 或 GT。
- 不開始 training／fine-tuning。
- `0.20` 僅為 `BALANCED_VALIDATION_THRESHOLD_CANDIDATE`，不是 deployment threshold。
- `retraining_status=NOT_YET_APPROVED`。
- `deployment_acceptance=NOT_YET_APPROVED`。
- Workbook、CSV、review images 與 reports 預設不 commit。

## 3. 程式檔案

```text
configs/data/validation_error_human_review_config.yaml
src/fleetvision/data/validation_error_human_review.py
scripts/phase04_5_prepare_validation_error_human_review.py
scripts/phase04_5_export_validation_error_human_review.py
scripts/phase04_5_validate_validation_error_human_review.py
scripts/phase04_5_summarize_validation_error_human_review.py
tests/test_validation_error_human_review.py
```

## 4. 輸入契約

`--source-root` 必須是已驗證 04.5K ZIP 的解壓根目錄，保留原始相對路徑：

```text
04_5K_gate_result.json
records/
├── validation_predictions.csv
└── validation_ground_truth.csv
review/
└── validation_error_review_worklist.csv
manifest/
├── phase_04_5k_artifact_manifest.csv
└── phase_04_5k_checksums.sha256
```

Prepare Gate 會逐檔確認：

- source-root artifacts 與核准 ZIP 中的成員 byte-identical。
- artifact manifest 與 checksum ledger 均吻合。
- Gate classification、validation-only flags 與 168／325／20,566 counts 完全符合。
- 任何路徑層級出現 `test` 都會 fail-closed。

`--source-zip` 必須是：

```text
04_5K_20260713_114517_02a146be_ZIP_LOG.zip
```

SHA256 必須是：

```text
4D54D2BD1DA9D4B4067B9B91001291E8A1FB3691D1F4CB4D4FFCDEED78872F89
```

`--validation-images-dir` 必須只包含固定 validation images；不得指向 test。

## 5. 建立人工複核套件

```powershell
$python = ".\.venv\Scripts\python.exe"

& $python scripts/phase04_5_prepare_validation_error_human_review.py `
  --config configs/data/validation_error_human_review_config.yaml `
  --project-root . `
  --source-root "<04.5K extracted artifact directory>" `
  --source-zip "<04_5K_20260713_114517_02a146be_ZIP_LOG.zip>" `
  --validation-images-dir "<validation-only image directory>" `
  --batch-id "phase04_5l_20260713_v1"
```

此指令：

- 驗證 source ZIP filename、SHA256、CRC 與安全 member paths。
- 驗證 source-root artifacts、04.5K manifest、checksum ledger 與 ZIP bytes 一致。
- 驗證 168 validation images、325 GT instances、20,566 raw predictions 與 130 個唯一 review cases。
- 複製 130 張 validation 原圖至 review package。
- 由既有 04.5K prediction／GT CSV 繪製 130 張 overlay；不重新推論。
- 建立 Workbook、source manifest、asset manifest 與 checksums。
- 若 batch 目錄已存在，直接停止，不覆寫。

## 6. Workbook 操作

Workbook 包含：

1. `Instructions`
2. `Review_Cases`
3. `Option_Lists`
4. `Manifest`
5. `Progress_Summary`

`Review_Cases`：

- 藍色欄位為受保護 source identity，不可修改。
- 黃色欄位為人工輸入欄位。
- 每列同時嵌入原圖與 overlay。
- `review_status` 最終必須全部為 `reviewed`。
- annotation defect 只能填寫 correction proposal；不得直接改 annotation。

## 7. 匯出 canonical CSV

```powershell
& $python scripts/phase04_5_export_validation_error_human_review.py `
  --config configs/data/validation_error_human_review_config.yaml `
  --project-root . `
  --workbook "outputs/metadata/phase_04_5l/phase04_5l_20260713_v1/workbook/validation_error_human_review.xlsx" `
  --output-csv "outputs/metadata/phase_04_5l/phase04_5l_20260713_v1/canonical/validation_error_human_review.csv"
```

Exporter 會在 promotion 前驗證：

- row count 與唯一 identity。
- controlled values。
- source fingerprints。
- reviewed completeness。
- annotation correction semantic rules。
- UTF-8-SIG round-trip。
- no-overwrite。

## 8. Validator Gate

```powershell
& $python scripts/phase04_5_validate_validation_error_human_review.py `
  --config configs/data/validation_error_human_review_config.yaml `
  --project-root . `
  --canonical-csv "outputs/metadata/phase_04_5l/phase04_5l_20260713_v1/canonical/validation_error_human_review.csv" `
  --workbook "outputs/metadata/phase_04_5l/phase04_5l_20260713_v1/workbook/validation_error_human_review.xlsx" `
  --batch-root "outputs/metadata/phase_04_5l/phase04_5l_20260713_v1" `
  --report-json "outputs/metadata/phase_04_5l/phase04_5l_20260713_v1/reports/validation_report.json" `
  --errors-csv "outputs/metadata/phase_04_5l/phase04_5l_20260713_v1/reports/validation_errors.csv"
```

PASS classification：

```text
VALIDATION_ERROR_HUMAN_REVIEW_VERIFIED
```

PASS 仍不代表 retraining 或 deployment 已獲核准。

## 9. 產生 summary 與 improvement queue

只有 Validator PASS 後才執行：

```powershell
& $python scripts/phase04_5_summarize_validation_error_human_review.py `
  --config configs/data/validation_error_human_review_config.yaml `
  --project-root . `
  --canonical-csv "outputs/metadata/phase_04_5l/phase04_5l_20260713_v1/canonical/validation_error_human_review.csv" `
  --batch-root "outputs/metadata/phase_04_5l/phase04_5l_20260713_v1"
```

輸出：

```text
canonical/annotation_correction_proposals.csv
reports/review_summary.json
reports/review_summary.md
reports/data_improvement_action_queue.csv
reports/data_improvement_action_summary.csv
```

`annotation_correction_proposals.csv` 固定：

```text
proposal_status=PROPOSED_NOT_APPLIED
```

不包含修改後 bbox geometry，也不套用任何 GT 變更。

## 10. 實作驗證

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
$env:PYTHONDONTWRITEBYTECODE = "1"
& $python -m pytest -p no:cacheprovider tests/test_validation_error_human_review.py -q

# Installer 使用 in-memory compile 檢查，不在 repository 產生 __pycache__。
& $python scripts/phase04_5_prepare_validation_error_human_review.py --help
& $python scripts/phase04_5_export_validation_error_human_review.py --help
& $python scripts/phase04_5_validate_validation_error_human_review.py --help
& $python scripts/phase04_5_summarize_validation_error_human_review.py --help
```

不得在本 Gate 內建立正式 Workbook、commit 或 push。
