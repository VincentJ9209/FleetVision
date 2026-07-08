# Phase 05：YOLOv8 Detect 訓練

## 目的

在 Colab 使用 GPU 訓練第一版可見車損偵測模型。

## 建議設定

```text
model: yolov8s.pt
task: detect
class: damage
imgsz: 640
epochs: 50-100
```

## 輸入

```text
dataset/05_yolo/v001_damage_detect/data.yaml
```

## 輸出

```text
models/yolo_damage_v001/best.pt
models/yolo_damage_v001/last.pt
outputs/evaluation/v001/
```

## 注意

`imgsz=640` 不代表要手動把原圖硬拉成 640x640。原圖應保留，讓 YOLO 訓練流程自行處理 resize / padding。

## 驗收標準

- Colab 可完成訓練。
- 有 `best.pt`。
- 有 metrics 與 sample predictions。
- 能在未見過的測試圖片上推論。
