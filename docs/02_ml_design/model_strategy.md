# 模型策略

## 第一版：YOLOv8 Detect

第一版採用 YOLOv8 Detect，單一類別 `damage`。

理由：

- bbox 標註速度較快。
- 較適合專題 MVP。
- 可輸出車損位置與信心分數。
- 後續可用於 Dashboard 與人工覆核。

## 不建議第一版直接做 Segmentation

Segmentation 標註成本較高，需要 polygon / mask。若目前時間與人力有限，應先用 Detect 跑通完整流程。

## 不建議第一版直接做索賠分類

`claimable_damage` 樣本偏少，且索賠涉及業務規則。第一版應先偵測可見車損，後續再建立索賠候選規則。
