# Phase 04.5B：Roboflow 外部資料受控下載與 Intake

## 目的

本 Gate 僅允許下載並稽核 registry 中已標記 `approved_for_download` 的單一來源：

```text
rf_car_damage_seg_v1
```

來源為 Roboflow Universe `Car-Damage detection` v1。該版本頁顯示 11,685 張 generated images，並套用每筆 training example 輸出 3 份的 augmentation；因此不得把此匯出稱為 4,869 張原始／未增強資料。

## 下載格式

在 Roboflow Universe v1 頁面選擇：

```text
Download Dataset → COCO Segmentation → Download ZIP
```

不要把 API key、下載 URL query string 或登入資訊寫入 Repository、聊天、log 或 manifest。

## CLI

```powershell
.\.venv\Scripts\python.exe -B scripts/phase04_5_intake_external_dataset.py `
  --archive "C:\Users\<user>\Downloads\<roboflow-export>.zip"
```

## 正式輸出

```text
dataset/01_raw/99_external/roboflow/rf_car_damage_seg_v1/
├── 00_download/
├── 01_extracted_export/
└── 99_quarantine/

outputs/metadata/external_assets/roboflow/rf_car_damage_seg_v1/
├── archive_inventory.csv
├── image_inventory.csv
├── annotation_inventory.csv
├── bbox_quality_report.csv
├── intake_errors.csv
├── class_mapping.csv
├── download_manifest.csv
├── license_evidence.md
├── license_evidence/
├── registry_update_proposal.csv
└── intake_verification.json
```

## 安全邊界

- 原始 ZIP 以 byte-for-byte copy 保存並計算 SHA256。
- ZIP extraction 阻擋 path traversal、absolute path 與 symlink。
- 保留 COCO segmentation 原始格式，不建立 YOLO labels。
- `Car-Damage -> damage` 只寫入 mapping proposal，不執行轉換。
- 任何 bbox／segmentation／image reference 問題都寫入 QA report；資料仍保持 `NOT_YET_APPROVED`。
- 不建立 dataset split，不執行模型訓練。
- 本工具不直接修改 tracked registry；成功後由下一個獨立 Gate promotion `registry_update_proposal.csv`。
