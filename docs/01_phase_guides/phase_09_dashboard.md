# Phase 09：Streamlit Dashboard

## 目的

將模型結果轉成可展示、可檢查、可溝通的產品雛形。

## 必要功能

1. 總覽指標。
2. 圖片列表。
3. 車損 bbox 視覺化。
4. confidence 門檻篩選。
5. 資料來源篩選。
6. 人工覆核清單。
7. FP / FN 錯誤案例展示。

## 展示備援

Dashboard 應支援兩種資料來源：

1. PostgreSQL 正式模式。
2. CSV demo fallback 模式。

現場發表時建議使用 demo fallback，降低環境風險。
