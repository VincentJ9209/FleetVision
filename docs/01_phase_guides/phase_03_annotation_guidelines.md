# Phase 03：Review Label Schema and Validation

## 目的

建立人工審查後的 review labels CSV 規格，並提供 validator 檢查欄位、允許值與基本一致性規則。

本階段只驗證 CSV，不讀取真實圖片，不修改 `dataset/01_raw/`，不建立 YOLO labels，不建立 YOLO dataset，也不訓練模型。

## 輸入

預設驗證人工建立或工具匯出的 labels CSV：

```text
dataset/00_catalog/image_review_labels.csv
```

此檔案不是由 Phase 03 自動產生；Phase 03 只負責驗證。

## Review Label 欄位

CSV 必須包含：

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

Identity 欄位不可空白：

```text
review_id
image_id
source_bucket
original_path
filename
```

## 允許值

```text
photo_type_review:
  exterior, interior, low_quality, irrelevant, unknown

angle_review:
  left_front, left_rear, right_front, right_rear, other, unknown

is_exterior_review:
  0, 1, unknown

has_visible_damage_review:
  0, 1, unknown

severity_review:
  minor, claimable, unknown

review_status:
  pending, reviewed, needs_followup, skipped
```

`severity_review` 是人工審查 metadata，不是 YOLO 類別。第一版 YOLO 仍只使用單一類別 `damage`。

## Validation 規則

- 必要欄位必須存在。
- Identity 欄位不可空白。
- Enum 欄位必須完全符合允許值。
- `review_status = reviewed` 時，`reviewer` 不可空白。
- `photo_type_review = exterior` 時，`is_exterior_review` 必須為 `1`。
- `photo_type_review` 為 `interior`、`low_quality`、`irrelevant` 時，`is_exterior_review` 必須為 `0`。
- `has_visible_damage_review = 0` 時，`severity_review` 必須為 `unknown`。
- `has_visible_damage_review = 1` 時，`severity_review` 可為 `minor`、`claimable` 或 `unknown`，因為嚴重度可能需要後續覆核。
- `review_id` 不可重複。
- `image_id` 不可重複。

## 設定檔

```text
configs/data/review_label_schema.yaml
```

設定檔定義：

- 預設 input / summary / errors 路徑
- required columns
- identity columns
- allowed values
- unique columns

## CLI

從專案根目錄執行：

```bash
python scripts/phase03_validate_review_labels.py --help
python scripts/phase03_validate_review_labels.py
python scripts/phase03_validate_review_labels.py --input dataset/00_catalog/image_review_labels.csv
python scripts/phase03_validate_review_labels.py --schema configs/data/review_label_schema.yaml
python scripts/phase03_validate_review_labels.py --report outputs/metadata/review_label_validation_summary.csv
python scripts/phase03_validate_review_labels.py --errors outputs/metadata/review_label_validation_errors.csv
python scripts/phase03_validate_review_labels.py --project-root .
```

Exit code：

```text
0: validation 通過
1: CSV 有 validation errors
2: input / schema 缺失或設定不可讀
```

## 輸出

預設輸出：

```text
outputs/metadata/review_label_validation_summary.csv
outputs/metadata/review_label_validation_errors.csv
```

這些是 generated local outputs，不應 commit 到 GitHub。

## 驗收指令

```bash
python scripts/phase00_init_project.py --validate
pytest
python scripts/phase03_validate_review_labels.py --help
```

若已有人工 labels CSV，可額外執行：

```bash
python scripts/phase03_validate_review_labels.py --input dataset/00_catalog/image_review_labels.csv
```

## 本階段不要做

- 不要修改 `dataset/01_raw/`。
- 不要建立 YOLO labels。
- 不要建立 YOLO dataset。
- 不要訓練模型。
- 不要修改 Phase 01 或 Phase 02 core logic。
- 不要把 `minor` / `claimable` 當成 YOLO 第一版類別。
- 不要 commit generated CSV outputs。
- 不要沿用舊的 `irent-damage-detection` 架構。
