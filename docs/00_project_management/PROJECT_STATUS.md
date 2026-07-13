# FleetVision Project Status

> 更新原則：每次正式 checkpoint 後更新。
> 基準日期：2026-07-13

## 1. 當前 Phase

- 前一主 Phase：Phase 04 — Pilot Human Review and Reviewed Dataset — **COMPLETED**
- 主 Phase：Phase 04.5 — External Dataset Intake, Controlled Baseline, and Audit — **IN PROGRESS**
- Current technical Phase：**Phase 04.5L — Validation Error Human Review**
- Latest completed technical Gate：**04.5L-2C Implementation Closure**
- Outcome：PASS
- Classification：VALIDATION_ERROR_HUMAN_REVIEW_IMPLEMENTATION_VERIFIED
- Repository base checkpoint：25e104bcf997699cd3cf573b813059612616ca2e
- Implementation files：8
- Formal review Workbook：尚未建立
- Test split read：false
- Annotation modified：false
- Training／fine-tuning：未執行
- Retraining status：NOT_YET_APPROVED
- Deployment acceptance：NOT_YET_APPROVED
- Next authorized Gate after commit/push verification：**04.5L-3 Review Package Preparation Audit**

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
- Production deduplication：39,335 hash success；0 hash errors；0 exact duplicate groups；33,844 external／external perceptual candidates
- Group-safe split plan：1,677 families；family leakage 0；train 9,334／valid 168／test 168；total 9,670；excluded correlated variants 2,005
- Source category diagnosis：三個 split 皆有 category `damage-`（id 0，0 annotations）及 `Car-Damage`（id 1，22,019 annotations）；無 mixed-category image、無第三種 category
- Canonical COCO：唯一 category `{id: 0, name: damage, supercategory: damage}`；11,675 images／22,019 annotations；bbox geometry checksum preserved；source cleaned COCO byte-identical
- Annotation／split balance QA：18,246 model-included annotations；invalid bbox 0；unresolved joins 0；unannotated included images 0；annotation-count-inconsistent families 0
- Targeted visual-review workload：smallest bbox 200＋largest bbox 200，共 400 items

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
- R-004：首個外部資料集已完成 dedup、group-safe plan、canonicalization 與 structural annotation QA，但 targeted visual label QA／lineage acceptance review 尚未完成，仍不得進入 train
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
- `81758ca feat: add phase 04.5F deduplication audit`
- `b2bcf00 fix: disable low-precision cross-source perceptual dedup`

## 6. 下一個正式執行順序

### Phase 04.5 — External Dataset Intake and Audit（IN PROGRESS）

已完成：

1. Roboflow candidate／License／source lineage 登錄
2. Download、version capture、raw inventory
3. Raw bbox／segmentation structural QA
4. 403 個 overflow bbox 的 non-destructive interim clipping 與驗證
5. Class mapping metadata：`Car-Damage -> damage`
6. Registry promotion、post-execute recovery、commit／push checkpoint
7. Production exact／perceptual deduplication
8. Group-safe source-family split plan
9. `Car-Damage`／`damage-` -> `damage` canonical COCO
10. Canonical annotation／bbox／split balance structural QA

下一功能 Gate：

1. 400 項 targeted visual bbox review
2. Targeted review finding resolution（若有）
3. Lineage acceptance review
4. Phase 04.5G acceptance report

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

<!-- PHASE_04_5J_04_5K_RECOVERY_20260713 -->

## 8. Phase 04.5J–04.5K Recovery Addendum（2026-07-13）

本 Addendum 是目前有效狀態；上方 Phase 04.5F 舊狀態保留作歷史紀錄。

### 已完成 Gate

- Phase 04.5J：`PASS`
- Classification：`CONTROLLED_COLAB_BASELINE_TRAINING_COMPLETED`
- Final ZIP：`04_5J_20260713_082857_6c719a70_ZIP_LOG.zip`
- ZIP SHA256：`98F0A04301FD08862941CB9033E23A932929F646494EE5917CD043DE3A815CEB`
- Model：YOLOv8s Detect，single class `damage`
- Training：33 epochs；best epoch 13；early stopping
- Validation best：P 0.4868／R 0.3508／mAP50 0.3516／mAP50-95 0.1620
- Test：P 0.5423／R 0.3883／mAP50 0.3804／mAP50-95 0.1756
- `best.pt` SHA256：`90A880513A42EF2DB1373902D98FF09D1756AB7A8A4EEA6A7AA231D4020B77BF`
- `last.pt` SHA256：`9D97A7053CA4400F45E9365C3FB9BFBE3EFFF20E6F3D37A403EC505186B386AC`

### Phase 04.5K 完成 Gate

- Phase：`04.5K Baseline Error Analysis`
- Outcome：`PASS`
- Classification：`VALIDATION_ERROR_ANALYSIS_AND_THRESHOLD_CANDIDATES_COMPLETED`
- Final ZIP：`04_5K_20260713_114517_02a146be_ZIP_LOG.zip`
- ZIP SHA256：`4D54D2BD1DA9D4B4067B9B91001291E8A1FB3691D1F4CB4D4FFCDEED78872F89`
- Validation images／GT：168／325
- Raw predictions：20,566
- Candidate thresholds：high-recall `0.05`／balanced `0.20`／high-precision `0.80`
- Balanced candidate metrics：P `0.409396`／R `0.375385`／F1 `0.391653`
- Detailed errors：379
- Human-review cases：130
- Representative overlays：60
- Data-improvement priority categories：6
- Test set used for tuning：`false`
- Test set read：`false`
- Training started in 04.5K：`false`
- Annotation modified：`false`
- Deployment acceptance：`NOT_YET_APPROVED`

### 當前 Gate

- 工作：人工複核 130 個 validation error cases
- 目的：確認 no-detection、low-confidence miss、localization error、background false positive 與 duplicate prediction 的真實原因
- 輸出：資料改善優先順序、annotation／data-quality findings、是否需要重新訓練的正式建議
- Model state：04.5J baseline training 已完成；目前沒有 training／fine-tuning 正在執行
- Retraining status：`NOT_YET_APPROVED`

### 強制邊界

- Test set 已正式評估一次，禁止再用於 threshold tuning、候選選擇或資料改善排序。
- 後續人工複核只使用 04.5K validation error artifacts。
- 未完成複核與資料改善決策前，不重新訓練、不 fine-tune、不修改固定 split。
- `0.20` 只能標記為 balanced `VALIDATION_THRESHOLD_CANDIDATE`，不得宣告 deployment threshold。

<!-- FLEETVISION-MANAGED:CURRENT-STATE:BEGIN -->
## Machine-readable state

~~~yaml
schema_version: 1
project: FleetVision
repository_root: "G:\Project\FleetVision"
branch: main
repository_base_head: "25e104bcf997699cd3cf573b813059612616ca2e"
repository_base_subject: "docs(governance): adopt repository-backed project state"
technical_phase: "04.5L"
technical_gate: "04.5L-2C"
technical_gate_outcome: "PASS"
technical_classification: "VALIDATION_ERROR_HUMAN_REVIEW_IMPLEMENTATION_VERIFIED"
implementation_files_created: 8
implementation_evidence_zip_sha256: "1151664A258C1DB4F01B16C900279F976F9EAEF3FFCC74D98F97EB87A804B07C"
focused_tests: "exit_code_0"
full_tests: "exit_code_0"
formal_workbook_created: false
test_split_read: false
annotation_modified: false
training_started: false
retraining_status: "NOT_YET_APPROVED"
deployment_acceptance: "NOT_YET_APPROVED"
worktree_policy: "CLEAN_OR_PROTECTED_UNTRACKED_ONLY"
protected_untracked_path: "outputs/metadata/external_assets/"
next_authorized_action: "04.5L-3_REVIEW_PACKAGE_PREPARATION_AUDIT"
updated_at: "2026-07-14T00:13:18+08:00"
~~~

## Current checkpoint

- Technical phase: **04.5L — Validation Error Human Review**
- Latest completed technical Gate: **04.5L-2C Implementation Closure**
- Outcome: **PASS**
- Classification: **VALIDATION_ERROR_HUMAN_REVIEW_IMPLEMENTATION_VERIFIED**
- Repository base checkpoint: 25e104bcf997699cd3cf573b813059612616ca2e
- Formal review Workbook created: **NO**
- Test split read: **NO**
- Training started: **NO**
- Next authorized action after remote verification: **04.5L-3 Review Package Preparation Audit**
<!-- FLEETVISION-MANAGED:CURRENT-STATE:END -->

