# 新增車損比對邏輯

## 現階段限制

目前尚未取得大量同一台車的借車 / 還車成對照片，因此第一版只能先建立比對規則與模擬流程，不能宣稱已完整驗證真實新增車損判斷。

## 未來比對流程

```text
pickup image detections
return image detections
  ↓
同 vehicle_id + rental_id + angle 配對
  ↓
比對 return bbox 與 pickup bbox 的 IoU
  ↓
判斷 no_new_damage / existing_damage / suspected_new_damage / review_required
```

## 規則範例

- 還車有高信心 damage，借車無對應 bbox：`suspected_new_damage`
- 還車有 damage，借車同位置有高 IoU bbox：`existing_damage`
- 還車無 damage：`no_new_damage`
- 任一圖片低品質：`review_required`
