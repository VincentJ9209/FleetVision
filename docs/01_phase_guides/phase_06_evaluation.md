# Phase 06：模型評估與錯誤分析

## 目的

找出模型的主要誤判與漏判來源，建立下一輪資料補強方向。

## 重要指標

- Precision
- Recall
- mAP50
- mAP50-95
- False Positive
- False Negative

## 常見錯誤來源

| 錯誤 | 可能原因 | 改善 |
|---|---|---|
| 反光被判為車損 | 車身高反光 | 加入反光 normal hard negatives |
| 小刮痕漏判 | 解析度不足 | 測試 imgsz 960 或補小刮痕資料 |
| 陰影被判為損傷 | 光線變化大 | 增加不同光線正常圖 |
| 水痕誤判 | 雨天 / 洗車痕 | 增加水痕負樣本 |

## 輸出

```text
outputs/error_analysis/false_positive/
outputs/error_analysis/false_negative/
outputs/evaluation/v001/metrics_summary.csv
```
