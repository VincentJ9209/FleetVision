# Phase 03：車損標註

## 目的

建立 YOLOv8 Detect 可訓練的車損 bounding box 標註資料。

## 第一版類別

```text
0: damage
```

## 應標註

- 刮傷
- 擦傷
- 凹陷
- 撞傷
- 掉漆
- 破裂
- 明顯外觀損傷

## 不建議標註

- 反光
- 車門縫
- 陰影
- 水痕
- 污漬，除非專案明確定義為車況異常
- 模糊到無法判斷的位置

## 標註資料放置

```text
dataset/04_annotations/
├── cvat_exports/
├── labelstudio_exports/
├── yolo_labels_raw/
└── annotation_versions/
```

## 驗收標準

- 所有明確車損圖都有 bbox。
- 正常圖可作為 negative sample。
- 標註規則文件存在。
- YOLO label 格式檢查通過。
