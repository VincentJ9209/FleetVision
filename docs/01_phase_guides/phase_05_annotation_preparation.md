# Phase 05：YOLO Annotation Preparation

## 目的

Phase 05 將 Phase 04 的 `annotation_candidates.csv` 轉成 bbox 人工標註前的任務清單。

本階段只建立 CSV 任務清單與標註準備規則，不讀取圖片內容、不複製或移動圖片、不建立 YOLO labels、不建立最終 YOLO dataset，也不訓練模型。

第一版 YOLO 類別策略仍是單一類別：

```text
damage
```

`minor` / `claimable` 只作為任務優先序與分析 metadata，不是 YOLO class。

---

## 輸入

預設輸入：

```text
dataset/04_annotations/annotation_candidates.csv
```

此檔由 Phase 04 產生，代表人工審查後可進入 bbox 標註準備的候選圖片。

---

## 輸入欄位

Phase 05 預期欄位：

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
candidate_reason
```

若缺少必要欄位，程式會 fail fast，提示先檢查 Phase 04 輸出。

---

## 輸出

預設輸出：

```text
dataset/04_annotations/annotation_task_manifest.csv
outputs/metadata/annotation_task_manifest_summary.csv
```

這些是 generated local outputs，不建議 commit 到 GitHub。

---

## 任務清單欄位

`annotation_task_manifest.csv` 包含：

```text
task_id
review_id
image_id
source_bucket
original_path
filename
photo_type_review
angle_review
severity_review
candidate_reason
annotation_class
annotation_type
annotation_status
task_priority
task_notes
```

預設：

```text
annotation_class = damage
annotation_type = bbox
annotation_status = pending
```

---

## 篩選規則

Phase 05 只納入符合下列條件的列：

```text
photo_type_review = exterior
is_exterior_review = 1
has_visible_damage_review = 1
review_status = reviewed
```

預設任務優先序：

| severity_review | task_priority |
|---|---:|
| `claimable` | 10 |
| `minor` | 20 |
| `unknown` | 30 |
| other | 40 |

這只是人工標註優先序，不是模型類別。

---

## CLI

顯示說明：

```bash
python scripts/phase05_prepare_annotation_tasks.py --help
```

使用預設設定：

```bash
python scripts/phase05_prepare_annotation_tasks.py
```

指定設定檔：

```bash
python scripts/phase05_prepare_annotation_tasks.py --config configs/data/annotation_prep_config.yaml
```

指定輸入與輸出：

```bash
python scripts/phase05_prepare_annotation_tasks.py --input dataset/04_annotations/annotation_candidates.csv
python scripts/phase05_prepare_annotation_tasks.py --output dataset/04_annotations/annotation_task_manifest.csv
python scripts/phase05_prepare_annotation_tasks.py --summary-output outputs/metadata/annotation_task_manifest_summary.csv
```

---

## 驗收指令

```bash
python scripts/phase00_init_project.py --validate
pytest
python scripts/phase05_prepare_annotation_tasks.py --help
```

若已有真實 Phase 04 產出的候選清單：

```bash
python scripts/phase05_prepare_annotation_tasks.py --input dataset/04_annotations/annotation_candidates.csv
```

---

## 本階段不要做

- 不要修改 `dataset/01_raw/`。
- 不要複製或移動圖片。
- 不要建立 YOLO label `.txt`。
- 不要建立 `dataset/05_yolo/`。
- 不要訓練模型。
- 不要把 `minor` / `claimable` 當成 YOLO class。
- 不要 commit generated CSV outputs。

---

## 下一階段銜接

下一階段才會處理 bbox annotation export、YOLO label 格式轉換、train / val / test split 與 `data.yaml`。
