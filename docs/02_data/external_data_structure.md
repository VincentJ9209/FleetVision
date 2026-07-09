# FleetVision External Data Structure

## 目的

此文件定義 FleetVision 納入外部資料集與免費模型時的資料結構。

原則：外部資料只能進入 `99_external` 或 `external_*` 區域，不得直接混入 FleetVision 內部 raw data。

---

## 外部 raw data

```text
dataset/01_raw/99_external/
├── kaggle/
├── roboflow/
└── huggingface/
```

用途：存放未轉換前的外部資料來源。

---

## 外部 YOLO labels raw

```text
dataset/04_annotations/external_yolo_labels_raw/
├── kaggle/
├── roboflow/
└── huggingface/
```

用途：存放已轉成 YOLO txt 格式的外部 bbox labels。

---

## 外部 metadata / audit outputs

```text
outputs/metadata/external_assets/
├── kaggle/
├── roboflow/
└── huggingface/
```

用途：存放外部資料 audit、下載紀錄、格式檢查與轉換摘要。

---

## 外部訓練資料版本

```text
dataset/05_yolo/v002_damage_detect_external_pretrain/
dataset/05_yolo/v003_damage_detect_mixed_finetune/
```

建議用途：

| 版本 | 用途 |
|---|---|
| `v002_damage_detect_external_pretrain` | 外部資料 baseline / pretrain |
| `v003_damage_detect_mixed_finetune` | 外部資料 + FleetVision fine-tune |

FleetVision holdout evaluation 不得混入外部資料。

---

## Git 規則

不要 commit：

```text
dataset/01_raw/99_external/
dataset/04_annotations/external_yolo_labels_raw/
dataset/05_yolo/
outputs/metadata/external_assets/
```

可以 commit：

```text
configs/data/external_asset_scout_config.yaml
docs/01_phase_guides/phase_03_6_external_asset_scout.md
docs/02_data/external_data_structure.md
scripts/phase03_6_external_asset_scout.py
src/fleetvision/data/external_asset_scout.py
tests/test_external_asset_scout.py
```
