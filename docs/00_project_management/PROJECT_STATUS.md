# FleetVision Project Status

> 更新原則：每次正式 checkpoint 後更新。
> 基準日期：2026-07-12

## 1. 當前 Phase

- 前一主 Phase：Phase 04 — Pilot Human Review and Reviewed Dataset — **COMPLETED**
- 主 Phase：Phase 04.5 — External Dataset Intake and Audit — **IN PROGRESS**
- 已完成 Gate：Phase 04C／04D／04E 全流程；Phase 04.5 Registry／License／download capture；raw structural QA；non-destructive bbox clipping verification；Registry promotion／post-execute recovery；Registry commit／push checkpoint
- 當前 checkpoint：`17e2c915421a8f6bacacba87c01b3d09d55c62f6`
- 下一功能 Gate：Phase 04.5F — Deduplication preflight

## 2. 已完成項目

- Phase 01 Metadata catalog
- Phase 02 Review queue
- Phase 03 Human review schema／Validator
- Phase 03.5 Auto prelabel pilot（已封存）
- Pilot worklist builder
- Human review validator
- Excel review interface／exporter
- Human review guide PDF
- Multi-reviewer package builder／merger
- Vincent／Allison 250／250 deterministic assignment
- Collaboration artifacts `.gitignore`
- Phase 04C portable image link 與 dropdown compatibility 驗證
- Phase 04D Vincent 250／250、Allison 250／250，共 500／500 人工審核
- 兩份完成版 canonical Workbook 凍結快照與 SHA256 manifest
- Phase 04E Verified Freeze（`NEW_FREEZE_VERIFIED`）
- Phase 04E Formal Merge Preflight（`FORMAL_MERGE_PREFLIGHT_PASS`）
- Phase 04E Formal Merge（`FORMAL_MERGE_VERIFIED`）
- Phase 04E Schema Promotion（`SCHEMA_PROMOTION_VERIFIED`）
- Phase 04E Reviewed Dataset Build（`REVIEWED_DATASET_BUILD_VERIFIED`）
- Annotation candidates list 與 distribution／quality summary
- Phase 04.5 Roboflow Dataset ID：`rf_car_damage_seg_v1`
- License／source／version／download lineage 已登錄
- Raw intake：11,675 images；22,019 annotations；21,616 valid bbox；403 invalid overflow bbox；0 invalid segmentation；0 missing images
- 403 個 overflow bbox 已採非破壞式 interim clipping；interim 22,019 valid bbox、0 invalid bbox
- Registry promotion：`REAL_REGISTRY_PROMOTION_VERIFIED`
- Recovery：`POST_EXECUTE_VERIFICATION_RECOVERED`
- Registry SHA256：`314b30242ed5ed4bce995bca9a2cae3c4cfa3b7aa89a7374e8dd531fe3193052`
- Registry commit／push：`17e2c915421a8f6bacacba87c01b3d09d55c62f6`
- 91 regression tests passed；11 promotion fields、19 identity fields、12 protected v2 fields verified
- `training_acceptance=NOT_YET_APPROVED`

## 3. Phase 04C／04D 完成狀態

### Excel Workbook Compatibility

已完成並驗證：

- `open_image` 改用 Excel `HYPERLINK(...)` 公式
- 六組 Excel list Data Validation 改用 workbook-scoped named ranges，指向隱藏的 `選項清單`
- `calcMode = auto`
- `fullCalcOnLoad = True`
- `forceFullCalc = True`
- `calcOnSave = True`
- TEMP Vincent／Allison Package build PASS
- Excel COM 驗收 PASS
- Allison 實際 Excel 工作流程完成

驗證結果：Targeted 6 passed；Merger regression 6 passed；Exporter regression 10 passed；Full 112 passed, 1 skipped。

### Human Review Completion and Freeze

- Vincent：250／250 完成
- Allison：250／250 完成
- 合計：500／500 完成
- 兩份完成版 canonical Workbook 均已建立凍結快照與 SHA256 manifest
- 正式人工成果未被 Builder 修正流程覆蓋

### Phase 04E — Formal Merge, Schema Promotion, and Reviewed Dataset Build

#### Formal Merge（`FORMAL_MERGE_VERIFIED`）

- Gate：`NEW_FREEZE_VERIFIED`、`FORMAL_MERGE_PREFLIGHT_PASS`、`FORMAL_MERGE_VERIFIED`
- 合併列數：500 rows、500 unique review IDs
- reviewed：500；pending：0；validation errors：0
- Vincent／Allison overlap：0
- Frozen snapshot：`G:\Project\FleetVision_Backups\Phase04_Completed_Reviews\Frozen_500\20260711_235712`
- Formal merge provenance：`G:\Project\FleetVision_Backups\Phase04_Completed_Reviews\Formal_Merge_500\20260712_001744`
- Formal merged CSV：`outputs/manual_review/collaboration/pilot500_human_review_results_collaboration.csv`
- Input SHA256：`A88F530BB3B68E518197E476057E4B1A2A2295196E9892F9116F3F95060AF2D0`
- Formal merge logical fingerprint：`1FF38FF9E9B04481A0C0BAD724E3D9B9ADFCA4E2C92441D8A2DC7DC3D30113FD`

#### Schema Promotion（`SCHEMA_PROMOTION_VERIFIED`）

- Canonical review CSV：`outputs/manual_review/collaboration/pilot500_review_labels_canonical.csv`
- Canonical output SHA256：`0CA1E663AE2AA702AF07E7431F4FE7476ED407B12D2DF48835A5FC9BF9EA4B7A`
- rows：500；unique review IDs：500；reviewed：500；pending：0
- input validation errors：0；output validation errors：0；mapping mismatches：0
- Canonical logical fingerprint：`26074E75E8BDB0436D10FC7BE81543254C186E3FB13F9D9C66F1230DC383DD7B`
- Formal merge input 未修改

#### Reviewed Dataset Build（`REVIEWED_DATASET_BUILD_VERIFIED`）

- total：500；reviewed：500
- exterior：446；low_quality：18；irrelevant：4
- annotation_candidates：82；interior：26；unknown：6
- 正式輸出：
  - `dataset/03_reviewed/exterior/exterior_image_list.csv`
  - `dataset/03_reviewed/low_quality/low_quality_image_list.csv`
  - `dataset/03_reviewed/irrelevant/irrelevant_image_list.csv`
  - `dataset/04_annotations/annotation_candidates.csv`
  - `outputs/metadata/reviewed_dataset_summary.csv`
- Build provenance：`G:\Project\FleetVision_Backups\Phase04_Completed_Reviews\Reviewed_Dataset_Build\20260712_011049`
- 安全邊界：`dataset/01_raw` 未修改；未建立 YOLO labels、dataset split 或模型訓練

## 4. 當前重要風險

- R-001：人工結果遺失（已以凍結快照、formal merge provenance 與 SHA256 manifest 控制；後續步驟仍須維持唯讀）
- R-002：舊 Package 連結不相容（Phase 04C 已完成驗證）
- R-003：資料不平衡
- R-004：首個外部資料集已完成 intake 與 Registry promotion，但尚未通過 perceptual hash、internal cross-dedup、lineage acceptance review，仍不得進入 train
- R-005：Internal holdout 尚未凍結

## 5. 最近 Git Checkpoints

- `feat: complete phase03.5 auto prelabel pilot`
- `06efb67 feat: add phase04 pilot human review worklist`
- `bb0be16 feat: add phase04 pilot human review validator`
- `ea20ad3 feat: add phase04 Excel human review interface`
- `fix: resolve phase04 Excel image hyperlinks`
- `feat: add phase04 Excel review exporter`
- `docs: add phase04 human review guide`
- `feat: add phase04 multi-reviewer collaboration workflow`
- `chore: ignore phase04 collaboration artifacts`

- `docs: record phase04c workbook integrity fix`
- `docs: record phase04e verified freeze and formal merge`
- `49e14cf feat: add human review schema promotion adapter`
- `docs: close phase04 reviewed dataset workflow`
- `17e2c91 chore(dataset): commit verified registry promotion`

## 6. 下一個正式執行順序

### Phase 04.5 — External Dataset Intake and Audit（IN PROGRESS）

已完成：

1. Roboflow candidate／License／source lineage 登錄
2. Download、version capture、raw inventory
3. Raw bbox／segmentation structural QA
4. 403 個 overflow bbox 的 non-destructive interim clipping 與驗證
5. Class mapping metadata：`Car-Damage -> damage`
6. Registry promotion、post-execute recovery、commit／push checkpoint

下一功能 Gate：

1. Phase 04.5F deduplication preflight
2. Perceptual hash inventory
3. Internal／external exact and near-duplicate comparison
4. Lineage acceptance review
5. Phase 04.5G acceptance report

在 `training_acceptance` 正式改為 approved 前，不得建立 YOLO labels、dataset split、`dataset/05_yolo/` 或開始模型訓練。

## 7. 明確禁止事項

- 不重跑 Phase 03.5
- 不修改 `dataset/01_raw/`
- 不建立 YOLO labels
- 不建立 `dataset/05_yolo/`
- 不訓練模型
- 不下載未登錄或未確認 License 的外部資料
- 不將外部資料混入 internal test
- 不覆蓋已有人工審核結果
