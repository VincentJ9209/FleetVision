# Phase 04.5F 外部 COCO 類別正規化與 Annotation QA

## 根因與正式決策

Roboflow source COCO 的三個 split 都包含兩個 taxonomy entries：

- `damage-`：category id 0，0 annotations；source supercategory placeholder。
- `Car-Damage`：category id 1，22,019 annotations；supercategory 為 `damage-`。

沒有 annotation 使用不同 category 表示同一張圖，沒有第三種 category。`damage-` 不是不同語意的標註類別，而是 Roboflow taxonomy 命名漂移。因此 source aliases `Car-Damage` 與 `damage-` 正規化為唯一 canonical class：

```text
id: 0
name: damage
supercategory: damage
```

## 安全邊界

- `dataset/01_raw/` 不修改。
- `cleaned_coco` 保持 byte-for-byte 不變。
- canonical output 獨立寫入 `dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1/canonical_coco`。
- 使用 staging＋atomic promotion；既有 output 預設不可覆寫。
- unknown category fail-closed。
- annotation／image IDs、bbox、area、segmentation、iscrowd、licenses、info 與其他 metadata 保留。
- 不建立 YOLO labels、不 materialize split、不訓練模型、不修改 Registry／protected assets／production dedup。

## Canonicalization

Dry-run：

```powershell
python scripts/phase04_5_normalize_external_coco_categories.py `
  --config configs/data/external_coco_category_normalization_config.yaml
```

正式建立：

```powershell
python scripts/phase04_5_normalize_external_coco_categories.py `
  --config configs/data/external_coco_category_normalization_config.yaml `
  --execute
```

輸出包含三份 canonical COCO、`canonicalization_split_audit.csv`、`canonicalization_verification.json` 與 header-only error report。

## Canonical-only Annotation／Split Balance QA

QA 必須讀取既有、manifest 驗證的 04.5F-7 group-safe split-plan ZIP。它不重新分配 family：

```powershell
python scripts/phase04_5_validate_external_annotation_split_balance.py `
  --config configs/data/external_annotation_split_balance_qa_config.yaml `
  --split-plan-zip <04_5F-7_ZIP_LOG.zip>
```

Canonical QA 只允許 `damage`。`Car-Damage` 或 `damage-` 出現在 canonical input 時立即阻擋。

## 已驗證結果

| Split | Families | Source images | Model images | Excluded variants | Positive／negative | Bboxes |
|---|---:|---:|---:|---:|---:|---:|
| train | 1,341 | 9,334 | 9,334 | 0 | 9,334／0 | 17,607 |
| valid | 168 | 1,171 | 168 | 1,003 | 168／0 | 329 |
| test | 168 | 1,170 | 168 | 1,002 | 168／0 | 310 |

總計：11,675 source images、22,019 source annotations、9,670 model-included images、18,246 model-included annotations、2,005 excluded correlated variants、family leakage 0、invalid bbox 0、unresolved joins 0、unannotated included images 0、annotation-count-inconsistent families 0。

Targeted visual review 包含最小 bbox 200 項與最大 bbox 200 項，共 400 項。結構 Gate 為 `ANNOTATION_QA_STRUCTURALLY_READY_FOR_TARGETED_VISUAL_REVIEW`；在人工視覺 QA 完成前，`training_acceptance` 維持 `NOT_YET_APPROVED`。
