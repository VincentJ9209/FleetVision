# Dataset 結構規範

## 總覽

```text
dataset/
├── 00_catalog/
├── 01_raw/
├── 02_interim/
├── 03_reviewed/
├── 04_annotations/
├── 05_yolo/
└── 06_demo_samples/
```

## 00_catalog

放資料清單、Excel、metadata 與資料字典。

```text
dataset/00_catalog/raw_excels/
dataset/00_catalog/image_metadata.csv
dataset/00_catalog/image_review_labels.csv
dataset/00_catalog/annotation_summary.csv
dataset/00_catalog/data_dictionary.md
```

## 01_raw

放原始圖片，不要修改。

```text
dataset/01_raw/01_general_fleet/images/
dataset/01_raw/02_claimable_damage/images/
dataset/01_raw/03_minor_damage/images/
```

## 02_interim

放中間處理結果，可重建。

## 03_reviewed

放人工分類後資料，例如 exterior、interior、low_quality。

## 04_annotations

放 CVAT / Label Studio / YOLO raw labels 與標註版本。

## 05_yolo

放 YOLOv8 訓練資料集。

## 06_demo_samples

放現場展示與 Dashboard fallback 小樣本。
