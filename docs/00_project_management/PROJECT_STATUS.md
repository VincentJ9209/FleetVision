# FleetVision Project Status

> 更新原則：每次正式 checkpoint 後更新。
> 基準日期：2026-07-19

## 1. 當前 Phase

- 前一主 Phase：Phase 04 — Pilot Human Review and Reviewed Dataset — **COMPLETED**
- 主 Phase：Phase 05S — Seven-day Demo Sprint and Second-stage Before/After Workflow — **IN PROGRESS**
- Current technical Phase：**Phase 05S-A2 — Implementation Plan Approved and Documented**
- Latest completed operational Gate：**Phase 05S-A2 Plan Approval and Documentation Reconciliation**
- Outcome：**PASS**
- Classification：`PHASE_05S_A2_IMPLEMENTATION_PLAN_APPROVED_AND_DOCUMENTED`
- Latest verified repository checkpoint before this A2 docs checkpoint：`6693f0d978b839713636288175cd8dca74172416`
- Repository checkpoint subject：`docs(phase05s): record approved A1 startup scope`
- Formal human review：**130／130 reviewed**
- Pending：**0**
- Needs adjudication：**0**
- Completed Workbook：**CREATED／FROZEN**
- Completed Workbook SHA256：`C9DF0A38B115406791DF03BFDC714901A66A47BE95CE0E2047E573FCC8D6FB6C`
- Logical fingerprint：`F87882E8F6DBF20B6603FC5106BE5A78BD61E4A22A6500E9586E51498B4AAC35`
- Test split read：**false**
- Model inference executed in 04.5L：**false**
- Annotation modified：**false**
- Training／fine-tuning：**未執行**
- Retraining status：`NOT_YET_APPROVED`
- Deployment acceptance：`NOT_YET_APPROVED`
- Phase 05S-A1 design：**APPROVED／RECONCILED**
- Phase 05S-A1 implementation plan：**APPROVED／REPOSITORY_TRACKED_AFTER_THIS_GATE**
- A3 implementation authorization：**NOT_GRANTED**
- `04_team` image scan：**NOT_EXECUTED**
- Next authorized Gate：**`PHASE_05S_A3_IMPLEMENTATION_AUTHORIZATION_BEFORE_CODE`**

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

<!-- PHASE_04_5L_COMPLETED_REVIEW_20260714 -->

## 9. Phase 04.5L Completed Review Addendum（2026-07-14）

本 Addendum 取代較早的「Formal review Workbook 尚未建立」與
「下一步為 Review Package Preparation Audit」等狀態敘述。歷史內容保留供追溯，
但不可覆蓋本節與下方 machine-readable current state。

### Repository-backed checkpoints

- Local review app implementation checkpoint：
  `45314caf31c4c94784757bd93212c75d2bb44262`
- Implementation classification：
  `LOCAL_REVIEW_APP_IMPLEMENTED_TESTED_COMMITTED_AND_REMOTE_VERIFIED`
- Navigation hotfix checkpoint：
  `53e742d40430e4419c1da63bca384e237578486a`
- Navigation hotfix subject：
  `fix: repair local review case navigation`
- Navigation hotfix remote commit independently verified：**YES**
- Formal review app workspace remained outside the repository：**YES**

### Formal review completion

- Formal review package：
  `G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1`
- Formal review workspace：
  `G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_review_workspace`
- Review cases：**130**
- Reviewed：**130**
- Pending：**0**
- Needs adjudication：**0**
- Reviewer：**Vincent**
- Export classification：
  `LOCAL_REVIEW_APP_COMPLETED_WORKBOOK_EXPORTED`

### Frozen artifacts

- Completed Workbook：
  `G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_review_workspace\exports\validation_error_human_review_completed.xlsx`
- Completed Workbook size：`31871231` bytes
- Completed Workbook SHA256：
  `C9DF0A38B115406791DF03BFDC714901A66A47BE95CE0E2047E573FCC8D6FB6C`
- Logical fingerprint：
  `F87882E8F6DBF20B6603FC5106BE5A78BD61E4A22A6500E9586E51498B4AAC35`
- Pre-export backup：
  `G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_review_workspace\backups\review_state_20260714T045900084110Z.sqlite3`
- Pre-export backup SHA256：
  `2BE5EC790D9A712127CAAF61DEFC676D9B334A40C15DB9C9508F81612978DA2C`
- Current review-state SQLite SHA256：
  `C75184C516B468433AA8F4D47DE4E6F451F09D7A8FE468BB3D653440AB676DDB`
- Current review event log SHA256：
  `6DB25DBF7AA37239A883A31AD4659145C7DFB2EDADAF0F199D48871319B3B89E`
- Source Workbook SHA256：
  `5DC9C1FDA69865D36C60EACB90A0AEA0FC9F4B263F30281723BB0E1172549DE5`
- Frozen package ZIP path：
  `G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_PACKAGE.zip`
- Frozen package ZIP SHA256：
  `6D6243FE8F3E12910C03A5EDCFF178CE20B180473EED43DED2B36301A877B42A`

### Scope finding requiring governance

人工複核期間確認，外部資料中含有相當數量的重大／疑似全損、可能無法繼續行駛
案例。第一版 FleetVision 的真實產品情境應以輕微至中度外觀損傷為核心。

後續分析必須建立下列 scope 分組，但本 Gate 不可修改任何資料或標註：

- `IN_SCOPE_LIGHT_MODERATE`
- `BOUNDARY_HEAVY_DAMAGE`
- `OUT_OF_SCOPE_CATASTROPHIC`

重大／疑似全損案例不得直接刪除；應保留為 out-of-scope／OOD 治理素材，且在
完成 scope analysis 前不得直接驅動 retraining 或 deployment threshold 決策。

### Mandatory safety boundary

- Completed Workbook 不可再次匯出、覆寫、開啟後儲存或人工修改。
- Source Workbook、frozen package、SQLite state、audit events 與 backups 維持唯讀。
- 不讀 test split。
- 不重新執行 model inference。
- 不修改 annotation／GT／canonical COCO／Registry／raw dataset／fixed splits。
- 不開始 retraining／fine-tuning。
- Threshold `0.20` 仍只是 balanced validation candidate，不是 deployment threshold。
- `RETRAINING_STATUS=NOT_YET_APPROVED`
- `DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED`

### Next authorized Gate

`PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS`

該 Gate 只允許：

1. 驗證 Completed Workbook 與 logical fingerprint。
2. 執行既有 completed-review validator。
3. 統計人工判斷、root cause、annotation quality、recommended action 與 priority。
4. 建立 annotation correction proposal 清單，但不可直接修改 annotation。
5. 分析重大／疑似全損案例並建立 scope 治理方案。
6. 產出是否需要資料補強、threshold analysis 或 retraining proposal 的正式建議。


<!-- PHASE_04_5L_PACKAGE_PATH_ERRATUM_20260714 -->

## 10. Phase 04.5L Handoff Package Path Erratum（2026-07-14）

The immutable completed-review snapshot records an incorrect nested path for the
frozen package ZIP. The snapshot remains unchanged for audit history; this erratum
is the controlling correction for artifact location only.

- Incorrect historical path：
  `G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1\phase04_5l_20260714_v1_PACKAGE.zip`
- Correct authoritative path：
  `G:\Project\FleetVision_Review_Packages\Phase04_5L\phase04_5l_20260714_v1_PACKAGE.zip`
- Artifact SHA256 remains：
  `6D6243FE8F3E12910C03A5EDCFF178CE20B180473EED43DED2B36301A877B42A`
- Immutable snapshot retained unchanged：
  `docs/00_project_management/handoffs/2026-07-14_phase04_5l_completed_review.md`
- Controlling erratum：
  `docs/00_project_management/handoffs/2026-07-14_phase04_5l_completed_review_path_erratum.md`
- Review results、logical fingerprint、scope findings、safety declarations and
  next authorized Gate are unchanged.

<!-- FLEETVISION-MANAGED:CURRENT-STATE:BEGIN -->
## Machine-readable state

~~~yaml
schema_version: 3
project: FleetVision
repository_root: 'G:\Project\FleetVision'
branch: main
governance_proposal_parent_checkpoint: "898e7a5d373d8d48887ff7bf73f42a85bc818a9f"
phase05s_effective_condition: "COMMIT_CONTAINING_THIS_BLOCK_PUSHED_AND_REMOTE_VERIFIED"
technical_phase: "05S-A1"
technical_phase_name: "Team Pairing Audit Design Review"
current_gate: "PHASE_05S_A1_DESIGN_REVIEW_BEFORE_IMPLEMENTATION_PLAN"
latest_completed_governance_gate: "PHASE_05R_05S_HANDOFF_RECONCILIATION"
previous_gate: "PHASE_05R_08_CPU_REPRODUCTION_AND_DATASET_V2_STATUS_RECONCILIATION"
previous_gate_disposition: "CHAT_CONFIRMED_PENDING_ARTIFACT_REHASH_WHERE_AVAILABLE"
phase05r_scope_contract: "docs/00_project_management/PHASE05R_SCOPE_CONTRACT.md"
phase05r_guide: "docs/01_phase_guides/phase_05r_model_recovery.md"
phase05r_log: "docs/00_project_management/phase_logs/PHASE_05R_LOG.md"
phase05s_a1_design: "docs/01_phase_guides/phase_05s_a1_team_pairing_audit_design.md"
recovery_notebook_drive_path: "/content/drive/MyDrive/AI_Class/00.Project/FleetVision/notebooks/FleetVision_Phase05_Model_Recovery.ipynb"
recovery_notebook_reconciled_sha256: "2086D3EA155748EF61E0751CAC796739CD9E5F4624744D2C0DCA726D67146CCF"
dataset_v1_zip_sha256: "B72812D97E08B312EBC239ADB43C7DE7DED29FB1B3098CD3BEA17C880813C58A"
baseline_candidate_01_sha256: "605FFAC6B1AA39A2E9F13BA09456943529B2788B7FCBEEACE43A3616D1C41C89"
baseline_classification: "BEST_AVAILABLE_POC_ONLY"
production_quality_gate: "FAILED"
phase05r_r4_07_resnet18_status: "CHAT_CONFIRMED_NOT_REPOSITORY_VERIFIED"
phase05r_r4_08_dataset_v2_status: "CHAT_CONFIRMED_NOT_REPOSITORY_VERIFIED"
dataset_v2_status: "CHAT_CONFIRMED_CPU_REPRODUCTION_PASSED_PENDING_REPOSITORY_ARTIFACT_VERIFICATION"
candidate_03_to_05_status: "SUPERSEDED_BY_DEMO_SPRINT_SCOPE"
recovery_training_started: false
frozen_test_access_authorized: false
frozen_test_used_for_tuning: false
test_split_mutation: false
raw_dataset_mutation: false
protected_external_assets_mutation: false
codex_status: "TASK_SPECIFICALLY_AUTHORIZED_FOR_THIS_HANDOFF_ONLY"
automatic_commit_push: false
worktree_policy: "CLEAN_OR_PROTECTED_UNTRACKED_ONLY"
protected_untracked_path: "outputs/metadata/external_assets/"
next_authorized_action: "REVIEW_REPOSITORY_TRACKED_PHASE_05S_A1_DESIGN_THEN_WRITE_IMPLEMENTATION_PLAN"
implementation_authorized: false
image_scan_authorized: false
training_authorized: false
frozen_test_listing_authorized: false
updated_at_local: "2026-07-19"
~~~

## Current checkpoint

- Technical Phase：**Phase 05S-A1 — Team Pairing Audit Design Review**
- Latest completed governance Gate：
  `PHASE_05R_05S_HANDOFF_RECONCILIATION`
- Current Gate：`PHASE_05S_A1_DESIGN_REVIEW_BEFORE_IMPLEMENTATION_PLAN`
- Baseline model：`BEST_AVAILABLE_POC_ONLY`
- Dataset v2：**CHAT_CONFIRMED／PENDING_ARTIFACT_REHASH_WHERE_AVAILABLE**
- Recovery training：**NOT STARTED**
- Frozen Test access：**NOT AUTHORIZED**
- Codex：`TASK_SPECIFICALLY_AUTHORIZED_FOR_THIS_HANDOFF_ONLY`
- Next authorized action：
  Review repository-tracked Phase 05S-A1 design, then write a separate
  implementation plan.

This state is effective only after the commit containing this block is pushed
and local HEAD, `origin/main` and GitHub remote `main` are equal.
<!-- FLEETVISION-MANAGED:CURRENT-STATE:END -->

<!-- FLEETVISION-MANAGED:PHASE_04_5L_F2_04_5M_DESIGN:BEGIN -->
## Phase 04.5L F2 completion and Phase 04.5M design handoff（2026-07-14）

This addendum is the controlling current state and supersedes earlier lines
that still identify Completed Workbook Export or F2 as the next Gate.

### Completed Gate

- Technical Phase: **Phase 04.5L — Validation Error Human Review**
- Gate outcome: **PASS**
- Classification:
  `PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS_COMPLETED`
- Review cases: **130**
- Scope reviewed: **130**
- Pending: **0**
- Needs adjudication: **0**
- Primary advisory recommendation:
  `DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING`
- Completed scope Workbook SHA256:
  `AC0EE5882E8E6C7A3E9300BF6AD1589EC18C169681AA6720F0C36132A42B3946`
- Annotation correction proposals: **2**
- Annotation defects suspected: **2**
- In-scope confirmed model error share: **0.935064935065**
- In-scope medium/high priority share: **0.935064935065**
- Non-scope share: **0.407692307692**
- Maximum total variation distance: **0.155144855145**

### Scope distribution

- `IN_SCOPE_LIGHT_MODERATE`: **77**
- `BOUNDARY_HEAVY_DAMAGE`: **28**
- `OUT_OF_SCOPE_CATASTROPHIC`: **25**

### Approved next design

- Next technical Phase: **Phase 04.5M — Data Correction Proposal Review**
- Approved approach: **A — dedicated two-case correction-review application**
- Human interface: local Traditional Chinese Streamlit
- Live state: SQLite
- Audit: append-only JSONL
- Backup: required
- Completed export: no-overwrite
- Direct Excel review: prohibited

### Current authorization

The next authorized work is a detailed Phase 04.5M implementation plan based on:

`docs/superpowers/specs/2026-07-14-phase04-5m-data-correction-proposal-review-design.md`

Implementation, annotation promotion, dataset mutation, retraining, and
deployment remain unauthorized.

```text
TEST_SPLIT_READ=NO
MODEL_INFERENCE_EXECUTED=NO
ANNOTATION_MODIFIED=NO
DATASET_MODIFIED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
NEXT_AUTHORIZED_ACTION=PHASE_04_5M_DETAILED_IMPLEMENTATION_PLAN
```
<!-- FLEETVISION-MANAGED:PHASE_04_5L_F2_04_5M_DESIGN:END -->

<!-- FLEETVISION-MANAGED:PHASE_04_5M_IMPLEMENTATION_PASS:BEGIN -->
## Phase 04.5M implementation completed（2026-07-15）

- Outcome: **PASS**
- Classification:
  `PHASE_04_5M_IMPLEMENTED_TESTED_AND_READY_FOR_PACKAGE_PREPARATION`
- Implementation: dedicated two-case Traditional Chinese Streamlit correction-review app
- Live state: SQLite
- Audit: append-only JSONL
- Backup: every successful save, retention 20
- Completed export: CSV／JSON／XLSX／proposed overlays／SHA256 evidence
- Formal two-case review package created: **NO**
- Human correction review started: **NO**

```text
TEST_SPLIT_READ=NO
MODEL_INFERENCE_EXECUTED=NO
ANNOTATION_MODIFIED=NO
CANONICAL_COCO_MODIFIED=NO
DATASET_MODIFIED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
NEXT_AUTHORIZED_ACTION=PHASE_04_5M_1_CORRECTION_REVIEW_PACKAGE_PREPARATION
```
<!-- FLEETVISION-MANAGED:PHASE_04_5M_IMPLEMENTATION_PASS:END -->


<!-- FLEETVISION-MANAGED:PHASE05R-ACTIVATION:BEGIN -->
## Phase 05R controlled recovery activation（2026-07-18）

Phase 05R is an additive recovery track. It does not overwrite the historical
Phase 05–10 roadmap.

Completed reconciliation and governance preparation:

- `PHASE_05R_00_STARTUP_RECONCILIATION`
- `PHASE_05R_00A_GOVERNANCE_ALIGNMENT_DECISION`
- `PHASE_05R_00B_REPOSITORY_GOVERNANCE_PROPOSAL_PREPARATION`
- `PHASE_05R_00C_LOCAL_GOVERNANCE_APPLICATION_AND_VERIFICATION`
- `PHASE_05R_00D_GOVERNANCE_COMMIT_PUSH_REMOTE_VERIFICATION`

The Phase 04.5M-1 correction-review package Gate is retained as incomplete and
deferred by this recovery decision.

Controlled identities:

```text
DATASET_V1_SHA256=B72812D97E08B312EBC239ADB43C7DE7DED29FB1B3098CD3BEA17C880813C58A
BASELINE_CANDIDATE_01_SHA256=605FFAC6B1AA39A2E9F13BA09456943529B2788B7FCBEEACE43A3616D1C41C89
RECOVERY_NOTEBOOK_SHA256=2086D3EA155748EF61E0751CAC796739CD9E5F4624744D2C0DCA726D67146CCF
BASELINE_CLASSIFICATION=BEST_AVAILABLE_POC_ONLY
PRODUCTION_QUALITY_GATE=FAILED
```

Current action:

`PHASE_05R_01_DATASET_LABEL_QUALITY_AUDIT`

Restrictions:

```text
TEST_SPLIT_READ=NO
FROZEN_TEST_ACCESS=NO
ANNOTATION_MODIFIED=NO
RAW_DATASET_MODIFIED=NO
DATASET_V2_CREATED=NO
RECOVERY_TRAINING_STARTED=NO
MODEL_REPLACED=NO
CODEX_STATUS=CONDITIONALLY_PAUSED
```
<!-- FLEETVISION-MANAGED:PHASE05R-ACTIVATION:END -->

<!-- FLEETVISION-MANAGED:PHASE05R-05S-RECONCILIATION:BEGIN -->
## Phase 05R/05S handoff reconciliation（2026-07-19）

### Completed Gate

- Gate：`PHASE_05R_05S_HANDOFF_RECONCILIATION`
- Outcome：`PASS`
- Classification：`PHASE_05R_05S_HANDOFF_RECONCILIATION_COMPLETED`
- Live repository parent：`898e7a5d373d8d48887ff7bf73f42a85bc818a9f`
- Phase 05R repository activation：`REPOSITORY_VERIFIED`
- Phase 05S-A1 design：`REPOSITORY_TRACKED_AFTER_THIS_GATE`

### Phase 05R facts reconciled

R4-07 ResNet18 facts from the external handoff package:

- input：512
- threshold：0.25
- Valid：29
- TP／FP／FN／TN：12／3／3／11
- F1：0.8
- AUROC：0.857142857143
- model SHA256：
  `A6289B25D8A1B9619DBE2AD4BC1D4D173163E9344CBE51D4E0A612FC8E4E99E1`
- predictions SHA256：
  `C9E1BC20FF79402D43B9686D680D2DE920A552FD0EB5EF0BAFA5CB53A19A769B`
- manifest SHA256：
  `0961A865BCA4316A73A6F6F1753B7B73234AD71A9A033E345A53622E765239B2`
- Trust classification：`CHAT_CONFIRMED_NOT_REPOSITORY_VERIFIED`

R4-08 facts from the external handoff package:

- Dataset v2 path：
  `grouped_dataset/internal_grouped_dataset_v2_dev_orientation_reviewed`
- 29 valid image／label hashes matched
- CPU reproduction passed
- threshold remains 0.25
- Hard Negative fine-tune not approved
- E01：`HOLD`
- E02／E03：`EXCLUDE_FROM_IMAGE_CLASSIFICATION`
- E04／E05／E06：`HARD_NEGATIVE`
- background shortcut and label-task mismatch confirmed
- Frozen Test not accessed
- Trust classification：`CHAT_CONFIRMED_NOT_REPOSITORY_VERIFIED`

These facts must not be upgraded to `REPOSITORY_VERIFIED` or
`ARTIFACT_VERIFIED` until a later Gate locates the actual artifacts and
recomputes or verifies the stated hashes.

### Phase 05S scope reconciled

- Track：seven-day demo sprint for the FleetVision second-stage workflow.
- Responsibility boundary：second stage only; no first-stage capture App and no
  large Dashboard.
- Required runtime strategy：local Windows Python interface with Colab fallback.
- Phase 05S-A1 source：`dataset/01_raw/04_team`
- Reported source image count：319
- Count trust classification：
  `CHAT_CONFIRMED_NOT_IMAGE_SCANNED_IN_HANDOFF_GATE`
- Approved A1 approach：semi-automated candidate pairing plus human confirmation.
- Human review default：Traditional Chinese local interface with SQLite live
  state, audit events and backups.
- Excel role：completed export／exchange／archive only.

### Current safety declarations

```text
NO_CODE_IMPLEMENTATION_IN_THIS_GATE=YES
NO_IMAGE_SCAN_IN_THIS_GATE=YES
NO_TRAINING_IN_THIS_GATE=YES
NO_FROZEN_TEST_ACCESS=YES
NO_PUBLIC_DATASET_EXPANSION=YES
NO_DASHBOARD=YES
NO_FIRST_STAGE_APP=YES
RAW_DATASET_MODIFIED=NO
PROTECTED_EXTERNAL_ASSETS_MODIFIED=NO
GENERATED_OUTPUT_COMMITTED=NO
IMPLEMENTATION_PLAN_AUTHORIZED=AFTER_REPOSITORY_TRACKED_DESIGN_REVIEW_ONLY
NEXT_AUTHORIZED_ACTION=REVIEW_REPOSITORY_TRACKED_PHASE_05S_A1_DESIGN_THEN_WRITE_IMPLEMENTATION_PLAN
```
<!-- FLEETVISION-MANAGED:PHASE05R-05S-RECONCILIATION:END -->

<!-- FLEETVISION-MANAGED:PHASE05S-A2-PLAN:BEGIN -->
## Phase 05S-A2 — Implementation Plan Approval and Documentation Checkpoint

- Date：2026-07-19
- Parent repository checkpoint：`6693f0d978b839713636288175cd8dca74172416`
- Outcome：**PASS**
- Classification：`PHASE_05S_A2_IMPLEMENTATION_PLAN_APPROVED_AND_DOCUMENTED`
- Design：approved and reconciled
- Implementation plan：approved
- Plan path：`docs/superpowers/plans/2026-07-19-phase05s-a1-team-pairing-audit-implementation-plan.md`
- Design conflicts resolved：3
- Implementation code written：false
- `dataset/01_raw/04_team` scanned：false
- Streamlit launched：false
- SQLite workspace created：false
- Training／inference：false
- Frozen Test access：false
- Dashboard／first-stage App work：false

The next action requires a separate explicit authorization:

`PHASE_05S_A3_IMPLEMENTATION_AUTHORIZATION_BEFORE_CODE`

A3 must begin with fresh read-only Git／governance reconciliation. Formal
`04_team` scanning remains deferred to the separately authorized A4
controlled-run Gate after A3 implementation and tests are complete.
<!-- FLEETVISION-MANAGED:PHASE05S-A2-PLAN:END -->
