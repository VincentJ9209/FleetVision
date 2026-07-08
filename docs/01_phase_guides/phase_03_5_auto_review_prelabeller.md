# Phase 03.5：Colab Auto Review Prelabeler

## 目的

Phase 03.5 是介於 Phase 03 與 Phase 04 之間的輔助階段。

本階段使用 Colab 對圖片做初步分類，產生 `auto_review_suggestions.csv`，再用本地 merge script 將高信心建議值填入一份新的 review label copy。

本階段不取代人工審查，不直接把任何列標成 `reviewed`，也不建立 YOLO labels、不訓練模型。

---

## 為什麼需要 Phase 03.5

目前 FleetVision 真實資料量約 27,000 多張，若完全手動判斷：

- 是否外觀圖
- 車輛角度
- 是否有可見車損
- 車損粗略程度

人工審查成本會很高。因此先用 Colab / CLIP zero-shot classification 做預分類，讓人工只需要快速確認與修正。

---

## 輸入

預設輸入：

```text
dataset/00_catalog/image_review_labels.csv
```

此檔仍是 Phase 03 的正式輸入來源。

---

## Colab 輸出

Colab notebook 會產生：

```text
outputs/metadata/auto_review_suggestions.csv
```

預期欄位：

```text
image_id
filename
original_path
suggested_photo_type_review
photo_type_confidence
suggested_angle_review
angle_confidence
suggested_has_visible_damage_review
damage_confidence
suggested_severity_review
severity_confidence
auto_review_notes
```

---

## 本地 merge 輸出

本地 script 預設產生：

```text
dataset/00_catalog/image_review_labels_auto_suggested.csv
outputs/metadata/auto_review_merge_summary.csv
```

`image_review_labels_auto_suggested.csv` 是人工審查輔助檔，不應直接視為已完成 review。

---

## 欄位策略

### `photo_type_review`

允許值：

```text
exterior
interior
low_quality
irrelevant
unknown
```

### `angle_review`

允許值：

```text
front
rear
left
right
front_left
front_right
rear_left
rear_right
unknown
```

請使用底線版本，不要使用 `front left` 這種空格版本。

### `is_exterior_review`

由規則衍生：

```text
photo_type_review = exterior -> 1
其他 -> 0
```

### `has_visible_damage_review`

由模型建議或 severity 衍生：

```text
severity_review = none -> 0
severity_review = minor / moderate / severe -> 1
```

### `review_status`

Phase 03.5 不會將任何列設為：

```text
reviewed
```

自動預標註後仍應保持：

```text
pending
```

人工確認後，才手動改成 `reviewed`。

---

## 執行流程

### 1. 在 Colab 執行 notebook

開啟：

```text
notebooks/phase03_5_auto_review_prelabeller.ipynb
```

在 Colab 中掛載 Google Drive，設定 FleetVision 專案路徑，執行 notebook，產生：

```text
outputs/metadata/auto_review_suggestions.csv
```

### 2. 回到本機 merge

```powershell
python scripts/phase03_5_merge_auto_suggestions.py
```

若要指定路徑：

```powershell
python scripts/phase03_5_merge_auto_suggestions.py `
  --input dataset\00_catalog\image_review_labels.csv `
  --suggestions outputs\metadata\auto_review_suggestions.csv `
  --output dataset\00_catalog\image_review_labels_auto_suggested.csv
```

### 3. 人工確認

打開：

```text
dataset/00_catalog/image_review_labels_auto_suggested.csv
```

人工檢查並修正預標註欄位。

完成審查的列，才把：

```text
review_status
```

改成：

```text
reviewed
```

### 4. 另存為正式 Phase 03 輸入

人工確認後，再覆蓋或另存成：

```text
dataset/00_catalog/image_review_labels.csv
```

建議使用 CSV UTF-8。

### 5. 驗證

```powershell
python scripts/phase03_validate_review_labels.py --input dataset\00_catalog\image_review_labels.csv
```

驗證通過後再跑 Phase 04。

---

## 注意事項

- `auto_review_suggestions.csv` 是 generated output，不建議 commit。
- `image_review_labels_auto_suggested.csv` 是 generated working file，不建議 commit。
- 不要把 Colab 自動分類視為最終人工審查。
- 小刮痕、車身局部瑕疵、嚴重度判斷需要人工確認。
- 若使用 `front_left` 等新角度值，請確認 `configs/data/review_label_schema.yaml` 已同步允許這些值。
