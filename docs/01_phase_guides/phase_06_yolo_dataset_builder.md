# Phase 06：YOLO Dataset Builder

## 目的

Phase 06 將 Phase 05 的 annotation task manifest 與人工 bbox 標註後的 raw YOLO label files，整理成 YOLOv8 Detect 可訓練的 dataset 結構。

本階段採最小可行範圍：

```text
annotation_task_manifest.csv + yolo_labels_raw/*.txt
  → dataset/05_yolo/v001_damage_detect/
```

本階段不解析 CVAT 或 Label Studio 原生匯出格式。若使用 CVAT / Label Studio，請先匯出成 YOLO txt labels，再交給本 builder。

---

## 第一版模型類別策略

第一版只使用單一 YOLO class：

```text
0 = damage
```

不要把 `minor_damage` 或 `claimable_damage` 當成 YOLO class。嚴重度與索賠判斷屬於後續分析、規則與人工覆核，不是第一版偵測類別。

---

## 輸入

預設 manifest：

```text
dataset/04_annotations/annotation_task_manifest.csv
```

必要欄位：

```text
image_id
original_path
filename
```

預設 raw YOLO labels：

```text
dataset/04_annotations/yolo_labels_raw/
```

label 檔案預設以 image filename stem 對應：

```text
car_001.jpg → car_001.txt
```

每列 label 格式：

```text
class_id x_center y_center width height
```

其中：

- `class_id` 必須是 `0`
- bbox 為 normalized xywh
- `x_center`、`y_center` 範圍為 0 到 1
- `width`、`height` 範圍為大於 0 且小於等於 1

---

## 輸出

預設輸出：

```text
dataset/05_yolo/v001_damage_detect/
├── images/train/
├── images/val/
├── images/test/
├── labels/train/
├── labels/val/
├── labels/test/
└── data.yaml
```

Summary：

```text
outputs/metadata/yolo_dataset_summary.csv
```

以上都是 generated local outputs，不建議 commit 到 GitHub。

---

## CLI

```bash
python scripts/phase06_build_yolo_dataset.py --help
```

使用預設設定：

```bash
python scripts/phase06_build_yolo_dataset.py
```

指定 manifest、label 來源與輸出：

```bash
python scripts/phase06_build_yolo_dataset.py \
  --manifest dataset/04_annotations/annotation_task_manifest.csv \
  --labels-dir dataset/04_annotations/yolo_labels_raw \
  --output-root dataset/05_yolo/v001_damage_detect
```

只驗證與建立 labels，不複製 images：

```bash
python scripts/phase06_build_yolo_dataset.py --no-copy-images
```

---

## 設定檔

```text
configs/data/yolo_dataset_config.yaml
```

重點設定：

```yaml
class_names:
  - damage

split:
  train: 0.8
  val: 0.1
  test: 0.1
  seed: 42
```

---

## 驗收指令

```bash
python scripts/phase00_init_project.py --validate
pytest
python scripts/phase06_build_yolo_dataset.py --help
```

有真實人工標註後再執行：

```bash
python scripts/phase06_build_yolo_dataset.py
```

---

## 本階段不要做

- 不訓練 YOLO。
- 不跑 prediction。
- 不做索賠判斷。
- 不修改 `dataset/01_raw/`。
- 不把 `minor_damage` / `claimable_damage` 當成 YOLO class。
- 不 commit generated YOLO dataset outputs。
