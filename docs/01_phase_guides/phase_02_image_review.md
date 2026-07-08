# Phase 02：圖片人工分類

## 目的

將混合車況照片分成外觀、車內、低品質、無關與未知，避免用不相關照片訓練車損模型。

## 分類類別

```text
exterior
interior
low_quality
irrelevant
unknown
```

## 推薦流程

1. 從 metadata 中抽出未審查圖片。
2. 用 Streamlit 建立人工審查工具。
3. 每張圖標記 photo_type。
4. 寫入 `image_review_labels.csv`。
5. 產生 `exterior_image_list.csv`。

## 輸出

```text
dataset/00_catalog/image_review_labels.csv
dataset/00_catalog/exterior_image_list.csv
```

## 驗收標準

- 外觀照片可被清楚篩選。
- 低品質照片可被標記。
- 分類結果可追蹤，不直接覆蓋原始圖片。
