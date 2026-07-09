# Phase 03.6：External Asset Scout

## 目的

Phase 03.6 用來盤點 Kaggle、Roboflow、Hugging Face 或其他公開資料集 / 免費模型，判斷是否可納入 FleetVision 後續訓練或預標註流程。

本階段只做 registry、資料夾結構與可用性評估，不登入外部平台、不下載大量資料、不呼叫外部 API、不訓練模型。

---

## 為什麼要新增這一階段

目前 FleetVision 內部資料嚴重不平衡：一般車況很多，明顯車損與輕微車損較少。外部資料可用來補足 damage bbox 訓練樣本，但必須先檢查授權、格式、類別定義與 domain gap。

外部資料不可直接混入主資料集，必須先經過 External Asset Scout 與後續 External Dataset Intake。

---

## 輸出

預設 registry：

```text
dataset/00_catalog/external_asset_registry.csv
```

預設 summary：

```text
outputs/metadata/external_asset_scout_summary.csv
```

registry 欄位：

```text
asset_id
source_name
platform
url_or_slug
license
dataset_size
task_type
annotation_format
classes
image_count
has_bbox
has_yolo_format
can_map_to_damage
can_use_for_training
can_use_for_prelabel
risk_notes
decision
reviewer
last_checked_at
```

---

## 新增資料結構

本階段會初始化下列本地資料夾：

```text
dataset/01_raw/99_external/
├── kaggle/
├── roboflow/
└── huggingface/

dataset/04_annotations/external_yolo_labels_raw/
├── kaggle/
├── roboflow/
└── huggingface/

outputs/metadata/external_assets/
├── kaggle/
├── roboflow/
└── huggingface/

dataset/05_yolo/v002_damage_detect_external_pretrain/
dataset/05_yolo/v003_damage_detect_mixed_finetune/
```

這些資料夾是本地 generated/data working areas，不應 commit 大量資料。

---

## CLI

初始化資料夾與 registry template：

```bash
python scripts/phase03_6_external_asset_scout.py
```

初始化並驗證 registry：

```bash
python scripts/phase03_6_external_asset_scout.py --validate
```

若要重建空白 registry template：

```bash
python scripts/phase03_6_external_asset_scout.py --overwrite
```

---

## 判斷規則

外部資料至少要回答：

| 問題 | 說明 |
|---|---|
| 授權是否清楚 | license 必須人工確認 |
| 是否有 bbox | YOLO Detect 訓練需要 bbox |
| 是否可轉成 YOLO | 最好已有 YOLO 格式或可轉換 |
| 類別能否 mapping 到 damage | 不要直接沿用 minor / claimable 為 YOLO class |
| 是否適合 FleetVision 場景 | 注意 insurance / crash / repair shop domain gap |
| 是否可用於 prelabel | 免費模型可先當 teacher / prelabeler |

---

## 決策欄位

`decision` 建議值：

```text
pending
approved_for_download
rejected
downloaded
audited
converted
```

只有 `approved_for_download` 的資料才進入 Phase 06.0 External Dataset Intake。

---

## 注意事項

- 不要把 Kaggle / Roboflow API key 貼到 ChatGPT 或 Codex。
- 不要讓 Codex 下載或列印大量資料內容。
- Kaggle / Roboflow 下載應在 Cursor、Colab 或本機 shell 執行。
- 外部資料可以用於 train / pretrain，但不能污染 FleetVision holdout evaluation。
