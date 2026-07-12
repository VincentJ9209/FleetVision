# Phase 04.5F 外部資料集圖片去重稽核

## 目的與邊界

本工具針對 `rf_car_damage_seg_v1` 建立可重現的 SHA256、pHash、dHash 稽核，以及 external／external、internal／external 候選比對。工具只產生人工複核候選，不會自動拒絕圖片，也不會修改 Registry、原始圖片、interim 資料、人工成果或 internal holdout。

本 Gate 完成後，`training_acceptance` 仍維持 `NOT_YET_APPROVED`。在 Phase 04.5G lineage acceptance review 正式通過前，不得建立 YOLO labels、資料切分或開始訓練。

## 輸入

- 內部 canonical metadata：`outputs/metadata/image_metadata.csv`
- 外部受保護 inventory：`outputs/metadata/external_assets/roboflow/rf_car_damage_seg_v1/image_inventory.csv`
- 外部唯讀圖片根目錄：`dataset/01_raw/99_external/roboflow/rf_car_damage_seg_v1`
- 設定：`configs/data/external_dataset_deduplication_config.yaml`

所有路徑、schema、record ID、圖片存在性、可讀性、尺寸及外部 SHA256 都採 fail-closed 驗證。輸出 CSV 僅記錄 repository-relative POSIX path，不寫入絕對路徑。

## 雜湊演算法

- SHA256：以設定的 chunk size 串流讀取，輸出固定 64 位大寫十六進位字串。
- dHash：Pillow 灰階後縮放為 `(hash_size + 1) × hash_size`，比較水平方向相鄰像素，輸出固定寬度大寫十六進位字串。
- pHash：Pillow 灰階後縮放為 `(hash_size × 4) × (hash_size × 4)`，轉成 NumPy `float32`，使用 `cv2.dct`，取左上角低頻區塊，計算中位數時排除 DC coefficient，再產生固定寬度大寫十六進位字串。

## 候選索引

工具不執行 O(N²) 全配對。pHash 依 `phash_hamming_distance_max + 1` 切成連續 bands，各 band 寬度總和等於完整 hash bit width。每筆 record 只和至少共享一個 `(band_index, band_value)` 的既有 record 比較，再依序套用：

1. scope 開關；
2. exact match 排除；
3. pHash Hamming distance；
4. dHash Hamming distance；
5. aspect-ratio relative difference。

相同 pair 只會出現一次，左右 record 採字典序。若任一 record 的索引候選數超過 `max_candidates_per_record`，工具會失敗，不截斷結果。

## 執行模式

預設為 preflight，只讀取並驗證設定與兩份 inventory schema／identity，不計算全資料集 image hashes，也不建立 production output：

```powershell
python scripts/phase04_5_audit_external_dataset_deduplication.py `
  --config configs/data/external_dataset_deduplication_config.yaml
```

正式執行會讀取圖片並在 staging 內完成所有 CSV 與 verification JSON，全部成功後才原子 promotion：

```powershell
python scripts/phase04_5_audit_external_dataset_deduplication.py `
  --config configs/data/external_dataset_deduplication_config.yaml `
  --execute
```

既有輸出預設不可覆寫。覆寫必須同時提供：

```powershell
--execute --overwrite
```

失敗時不 promotion 部分正常輸出；hash／integrity 或 candidate overflow 失敗會依設定在 staging 保留 `deduplication_errors.csv` 證據。

## 正式輸出

只有 `--execute` 可在 `outputs/metadata/external_dedup/roboflow/rf_car_damage_seg_v1/` 建立：

- `image_hash_inventory.csv`
- `exact_duplicate_groups.csv`
- `exact_duplicate_members.csv`
- `perceptual_duplicate_candidates.csv`
- `deduplication_summary.csv`
- `deduplication_verification.json`
- `deduplication_errors.csv`

Exact group 與 perceptual candidate 均標記 `requires_review`。候選結果必須由人工審查，不能直接推導資料拒絕、damage severity、保險理賠責任或訓練接受狀態。

## CLI exit codes

- `0`：preflight 或 execute 成功。
- `2`：設定、schema 或輸入 preflight 錯誤。
- `3`：圖片讀取、雜湊或完整性錯誤。
- `4`：候選數 overflow。
- `5`：staging 寫入或 output promotion 錯誤。

CLI 最後一行固定輸出 compact JSON，供 PowerShell 或自動化流程判讀。

## 安全檢查

- `dataset/01_raw/` 與 `dataset/02_interim/` 僅讀取。
- `outputs/metadata/external_assets/` 僅讀取，不 stage、不 commit。
- 不修改 `dataset/00_catalog/external_dataset_registry.csv`，不產生 Registry proposal。
- 不建立 labels、`dataset/05_yolo/`、train／validation／test split 或模型輸出。
- 測試只使用 `pytest tmp_path` 與 Pillow 產生的小型圖片 fixture。
