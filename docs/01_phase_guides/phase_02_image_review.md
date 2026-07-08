# Phase 02：Image Review Builder

## 目的

根據 Phase 01 產生的 metadata 建立人工圖片覆核清單，讓後續人工審查可以依優先順序標記照片類型、角度、是否為外觀照片、是否有可見車損與嚴重度。

本階段只建立 review queue，不建立 Streamlit UI，不搬移圖片，不建立 YOLO labels，也不訓練模型。

## 輸入

```text
outputs/metadata/image_metadata.csv
```

Phase 01 metadata 必須包含下列欄位：

```text
image_id,source_bucket,original_path,filename,extension,file_size_bytes,width,height,aspect_ratio,is_readable,created_at,modified_at,notes
```

若缺少必要欄位，Phase 02 CLI 應停止並提示先重新執行 Phase 01。

## 輸出

```text
dataset/02_interim/03_review_queue/review_queue.csv
outputs/metadata/review_queue_summary.csv
```

這些 CSV 是可重建的本機輸出，不應提交到 GitHub。

## Review Queue 欄位

`review_queue.csv` 包含：

```text
review_id
image_id
source_bucket
original_path
filename
extension
file_size_bytes
width
height
aspect_ratio
is_readable
created_at
modified_at
notes
quality_status
brightness
blur_score
photo_type_review
angle_review
is_exterior_review
has_visible_damage_review
severity_review
review_status
reviewer
review_notes
priority
priority_reason
```

預設人工覆核欄位：

```text
photo_type_review = unknown
angle_review = unknown
is_exterior_review = unknown
has_visible_damage_review = unknown
severity_review = unknown
review_status = pending
reviewer = <empty>
review_notes = <empty>
```

## Priority 規則

預設優先順序：

```text
02_claimable_damage: 10
03_minor_damage: 20
01_general_fleet: 30
unknown source_bucket: 90
```

若 `is_readable = False`，圖片保留在 queue 中，但 `quality_status = unreadable`，並加上 `unreadable_priority_offset = 100`，讓不可讀圖片排到較低優先順序。

## CLI

建議從專案根目錄執行：

```bash
python scripts/phase02_build_review_queue.py
python scripts/phase02_build_review_queue.py --max-rows 100
python scripts/phase02_build_review_queue.py --input outputs/metadata/image_metadata.csv --output dataset/02_interim/03_review_queue/review_queue.csv
python scripts/phase02_build_review_queue.py --config configs/data/review_queue_config.yaml --project-root .
```

設定檔：

```text
configs/data/review_queue_config.yaml
```

## 驗收標準

- 可從 Phase 01 metadata 建立 `review_queue.csv`。
- 可輸出 `review_queue_summary.csv`。
- review queue 欄位完整且排序穩定。
- 不可讀圖片不會讓程式中斷，會被標記為 `quality_status = unreadable`。
- 測試使用 synthetic metadata，不依賴真實 dataset。
- 不修改 `dataset/01_raw/`。

## 驗收指令

```bash
python scripts/phase00_init_project.py --validate
pytest
python scripts/phase02_build_review_queue.py --max-rows 100
```

## 本階段不要做

- 不要修改、移動或刪除 `dataset/01_raw/`。
- 不要建立 YOLO labels。
- 不要訓練模型。
- 不要修改 Phase 01 core logic。
- 不要假設 `--max-images-per-source` 存在。
- 不要把 generated CSV outputs commit 到 GitHub。
- 不要沿用舊的 `irent-damage-detection` 架構。

## 下一步

完成 Phase 02 queue builder 後，下一個獨立任務可建立人工審查 UI 或人工審查結果彙整流程，例如：

```text
dataset/00_catalog/image_review_labels.csv
dataset/00_catalog/exterior_image_list.csv
```