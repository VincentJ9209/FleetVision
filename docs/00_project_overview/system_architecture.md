# 系統架構

## 第一版系統流程

```text
原始圖片
  ↓
metadata 建立與品質檢查
  ↓
人工分類：外觀 / 車內 / 低品質 / 無關
  ↓
車損 bbox 標註
  ↓
YOLOv8 Detect 訓練
  ↓
模型推論
  ↓
PostgreSQL 儲存結果
  ↓
Dashboard 展示
  ↓
人工覆核與錯誤分析
```

## 未來擴充流程

```text
借車照片 pickup
還車照片 return
  ↓
同車、同角度配對
  ↓
YOLO 偵測車損 bbox
  ↓
IoU / 位置 / confidence 比對
  ↓
判斷：無新增 / 既有損傷 / 疑似新增 / 需人工覆核
```
