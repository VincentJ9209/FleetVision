# Phase 04.5C：External COCO BBox Repair

## 問題背景

Roboflow `rf_car_damage_seg_v1` v1 COCO export 在唯讀 audit 後發現 403 筆 invalid bbox，全部屬於右或下邊界 overflow：

| Split | Invalid bbox |
| ----- | -----------: |
| train |          351 |
| valid |           40 |
| test  |           12 |
| Total |          403 |

原因分布：

- `exceeds_image_width`：263
- `exceeds_image_height`：147
- 同時超出右、下：7（unique invalid annotation 仍為 403）

不存在 negative origin、nonpositive size、malformed bbox、missing image、invalid segmentation 等其他問題。

## 修復策略

採用 **clipping** 而非刪除 annotation，因為：

1. 保留全部 22,019 筆 annotation identity 與 segmentation mask。
2. overflow 通常來自 augmentation 邊界裁切誤差，clipping 可恢復可用 bbox。
3. 不重新計算 `area`、不修改 segmentation polygon／RLE。

修復公式：

```python
old_x2 = x + width
old_y2 = y + height
new_x2 = min(old_x2, image_width)
new_y2 = min(old_y2, image_height)
new_width = new_x2 - x
new_height = new_y2 - y
```

只允許修復 `exceeds_image_width` 與 `exceeds_image_height`。任何其他 invalid reason 會使整個 Gate **BLOCKED**。

## Raw immutable 原則

- 只讀取 `dataset/01_raw/99_external/roboflow/rf_car_damage_seg_v1/01_extracted_export`
- 不修改 raw JSON、不複製 11,675 張圖片
- 執行前後驗證 input annotation SHA256 不變

## 輸出架構

```text
dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1/
├── cleaned_coco/
│   ├── train/_annotations.coco.json
│   ├── valid/_annotations.coco.json
│   └── test/_annotations.coco.json
├── bbox_repair_log.csv
├── bbox_repair_summary.csv
└── cleaned_annotation_manifest.csv
```

Cleaned JSON 保留原始 `file_name`。Manifest 記錄 `raw_image_root`，使後續 converter 以：

```text
cleaned annotation JSON + raw split image root
```

作為輸入。

## Config

```text
configs/data/external_coco_bbox_repair_config.yaml
```

## CLI

```powershell
.\.venv\Scripts\python.exe -B scripts/phase04_5_repair_external_coco_bbox.py `
  --config configs/data/external_coco_bbox_repair_config.yaml
```

成功 Gate：

```text
EXTERNAL_COCO_BBOX_REPAIR_VERIFIED
```

## 驗收標準

- 403 repaired、0 dropped、22,019 output annotations、0 invalid_after
- raw input SHA256 不變
- segmentation、area、IDs 與其他欄位不變
- staging 失敗不得留下部分正式輸出
- 預設 no-overwrite

## Rollback／No-overwrite

`repair_policy.allow_overwrite: false` 時，若 `output_root` 已存在則 BLOCKED。正式執行使用 staging directory 與 atomic promotion。

## 安全邊界

- 不建立 YOLO labels
- 不建立 dataset split
- 不執行模型訓練
- Registry 維持 `NOT_YET_APPROVED`
- annotation candidates 與本工具無關；本工具處理外部 Roboflow COCO export

## 狀態

本 guide 記錄 adapter 與驗收標準。正式 repair 尚未在本輪執行。
