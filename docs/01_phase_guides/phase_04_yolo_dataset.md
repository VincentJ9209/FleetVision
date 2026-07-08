# Phase 04：建立 YOLO Dataset

## 目的

將外觀圖片與標註結果整理成 YOLOv8 可訓練資料集。

## 第一版 dataset

```text
dataset/05_yolo/v001_damage_detect/
├── data.yaml
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

## data.yaml 範例

```yaml
path: dataset/05_yolo/v001_damage_detect
train: images/train
val: images/val
test: images/test

names:
  0: damage
```

## 切分原則

避免同一台車、同一來源批次、過度相似圖片同時出現在 train 與 test。若 metadata 尚不完整，至少要記錄資料切分方法與限制。

## 驗收標準

- 每張訓練圖片有對應 label 或被明確允許為 negative sample。
- label 格式為 `class x_center y_center width height`。
- 座標值介於 0 到 1。
- `data.yaml` 可被 YOLOv8 讀取。
