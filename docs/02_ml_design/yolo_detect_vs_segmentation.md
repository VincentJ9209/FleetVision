# YOLO Detect vs Segmentation

| 項目 | YOLO Detect | YOLO Segmentation |
|---|---|---|
| 標註方式 | Bounding box | Polygon / mask |
| 標註速度 | 快 | 慢 |
| 訓練難度 | 中低 | 中高 |
| 輸出 | 損傷方框 | 損傷輪廓 |
| 適合階段 | MVP / 第一版 | 進階版 |
| 對小刮痕 | 可能較粗略 | 較精細 |

## 建議路線

```text
v001: YOLOv8 Detect + damage
v002: YOLOv8 Detect + hard negative 補強
v003: 視需要升級 YOLOv8 Segmentation
```
