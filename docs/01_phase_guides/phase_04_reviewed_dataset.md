# Phase 04：Reviewed Dataset Builder

## 目的

Phase 04 將 Phase 03 驗證通過的人工覆核結果轉換成後續標註準備用的 CSV 清單。

本階段只處理 CSV，不讀取圖片內容、不複製圖片、不移動圖片、不建立 YOLO labels、不建立 YOLO dataset，也不訓練模型。

---

## 輸入

預設輸入：

```text
dataset/00_catalog/image_review_labels.csv
```

此檔案應先通過 Phase 03 驗證：

```bash
python scripts/phase03_validate_review_labels.py --input dataset/00_catalog/image_review_labels.csv
```

---

## 輸入欄位

Phase 04 預期欄位沿用 Phase 03 schema：

```text
review_id
image_id
source_bucket
original_path
filename
photo_type_review
angle_review
is_exterior_review
has_visible_damage_review
severity_review
review_status
reviewer
review_notes
```

若缺少必要欄位，Phase 04 會 fail fast，提示先修正 review labels CSV。

---

## 輸出

預設輸出：

```text
dataset/03_reviewed/exterior/exterior_image_list.csv
dataset/03_reviewed/low_quality/low_quality_image_list.csv
dataset/03_reviewed/irrelevant/irrelevant_image_list.csv
dataset/04_annotations/annotation_candidates.csv
outputs/metadata/reviewed_dataset_summary.csv
```

這些都是 generated local outputs，不建議 commit 到 GitHub。

---

## 分流規則

預設只處理：

```text
review_status = reviewed
```

### Exterior list

輸出到：

```text
dataset/03_reviewed/exterior/exterior_image_list.csv
```

條件：

```text
photo_type_review = exterior
is_exterior_review = 1
```

### Low quality list

輸出到：

```text
dataset/03_reviewed/low_quality/low_quality_image_list.csv
```

條件：

```text
photo_type_review = low_quality
```

### Irrelevant list

輸出到：

```text
dataset/03_reviewed/irrelevant/irrelevant_image_list.csv
```

條件：

```text
photo_type_review = irrelevant
```

### Annotation candidates

輸出到：

```text
dataset/04_annotations/annotation_candidates.csv
```

條件：

```text
photo_type_review = exterior
is_exterior_review = 1
has_visible_damage_review = 1
```

額外欄位：

```text
candidate_reason = visible_damage_reviewed
```

`severity_review` 只作為後續排序與分析 metadata，不是 YOLO class。

---

## CLI

顯示說明：

```bash
python scripts/phase04_build_reviewed_dataset.py --help
```

使用預設設定：

```bash
python scripts/phase04_build_reviewed_dataset.py
```

指定設定檔：

```bash
python scripts/phase04_build_reviewed_dataset.py --config configs/data/reviewed_dataset_config.yaml
```

指定輸入：

```bash
python scripts/phase04_build_reviewed_dataset.py --input dataset/00_catalog/image_review_labels.csv
```

指定輸出：

```bash
python scripts/phase04_build_reviewed_dataset.py --exterior-output dataset/03_reviewed/exterior/exterior_image_list.csv
python scripts/phase04_build_reviewed_dataset.py --low-quality-output dataset/03_reviewed/low_quality/low_quality_image_list.csv
python scripts/phase04_build_reviewed_dataset.py --irrelevant-output dataset/03_reviewed/irrelevant/irrelevant_image_list.csv
python scripts/phase04_build_reviewed_dataset.py --annotation-candidates-output dataset/04_annotations/annotation_candidates.csv
python scripts/phase04_build_reviewed_dataset.py --summary-output outputs/metadata/reviewed_dataset_summary.csv
```

---

## 驗收指令

```bash
python scripts/phase00_init_project.py --validate
pytest
python scripts/phase04_build_reviewed_dataset.py --help
```

若已有真實且通過 Phase 03 驗證的 labels CSV：

```bash
python scripts/phase03_validate_review_labels.py --input dataset/00_catalog/image_review_labels.csv
python scripts/phase04_build_reviewed_dataset.py --input dataset/00_catalog/image_review_labels.csv
```

---

## 本階段不要做

- 不要修改 `dataset/01_raw/`。
- 不要複製或移動圖片。
- 不要建立 YOLO labels。
- 不要建立 `dataset/05_yolo/`。
- 不要訓練模型。
- 不要判斷索賠責任。
- 不要把 `minor` / `claimable` 當成 YOLO class。
- 不要 commit generated CSV outputs。

---

## 下一階段銜接

Phase 04 輸出的 `annotation_candidates.csv` 是後續 bbox annotation preparation 的候選清單。

下一階段才會規劃人工 bbox 標註流程與標註格式，不會在 Phase 04 產生 YOLO labels。
