# Phase 08：批次推論與結果入庫

## 目的

將模型推論結果轉成可查詢、可展示、可追蹤的資料流程。

## 流程

```text
圖片資料夾
  ↓
YOLOv8 model predict
  ↓
predictions.csv
  ↓
PostgreSQL damage_predictions
  ↓
Dashboard
```

## prediction 欄位

| 欄位 | 說明 |
|---|---|
| image_id | 圖片 ID |
| model_version | 模型版本 |
| class_name | damage |
| confidence | 信心分數 |
| x1, y1, x2, y2 | bbox 座標 |
| image_width, image_height | 原圖尺寸 |
| created_at | 推論時間 |

## 驗收標準

- 有 detections 的圖片能輸出 bbox。
- 無 detections 的圖片也要保留紀錄或清楚處理。
- 推論結果可寫入 PostgreSQL。
