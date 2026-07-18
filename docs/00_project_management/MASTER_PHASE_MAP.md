# FleetVision Master Phase Map

> 本文件是 FleetVision 的正式執行路線。任何後續工作都必須對應到明確 Phase、前置條件與驗收 Gate。

## Phase 狀態代碼

- `DONE`：已完成並建立 Git checkpoint
- `ACTIVE`：目前進行中
- `READY`：前置條件完成，可開始
- `BLOCKED`：有阻塞
- `PLANNED`：已規劃但尚未開始
- `FUTURE`：長期延伸

## Phase 00 — Project Governance and Architecture

**狀態：DONE／持續維護**

目標：建立正式專案結構、固定不可變模型架構、建立 Git／測試／文件／checkpoint 規範。

Gate：核心架構清楚、新舊專案路徑無混用、重大決策可追蹤。

## Phase 01 — Metadata Catalog

**狀態：DONE**

目標：掃描原始資料、建立 metadata、驗證 schema、不修改 `dataset/01_raw/`。

Gate：約 27,660 列、支援 `.jfif`、schema 與測試通過。

## Phase 02 — Review Queue

**狀態：DONE**

目標：建立可追蹤的人工審核佇列，保留原始 identity。

## Phase 03 — Human Review Schema and Validation

**狀態：DONE**

目標：定義人工欄位、建立 Validator、區分自動建議與人工完成。

## Phase 03.5 — Auto Prelabel Pilot

**狀態：DONE／FROZEN**

固定規則：photo type threshold 0.75；不使用 `_1/_2/_3/_4` 推論 angle；不推論 damage／severity；不重跑 inference。

## Phase 04 — Pilot Human Review and Reviewed Dataset

**狀態：COMPLETED**

### 04A — Worklist／Validator／Excel Interface

**狀態：DONE**

### 04B — Multi-reviewer Collaboration Workflow

**狀態：DONE**

### 04C — Portable Image Link Compatibility

**狀態：DONE**

- 舊相對 hyperlink 在 Allison Excel 環境會交由瀏覽器開啟
- Builder 已改為 Excel `HYPERLINK(...)` 公式
- Targeted／Regression／Full tests 已通過
- TEMP package 實機驗證、Allison 電腦確認、Excel COM 驗收已完成

### 04D — Human Review Execution

**狀態：DONE**

- Vincent：250／250 reviewed
- Allison：250／250 reviewed
- 合計：500／500 reviewed；pending：0；validation errors：0
- 兩份完成版 canonical Workbook 已凍結；正式人工成果未被 Builder 覆蓋

### 04E — Merge and Final Validation

**狀態：DONE**

已完成：

- 500 筆 reviewer assignment
- 500／500 human review；pending：0；validation errors：0
- verified frozen snapshot（`NEW_FREEZE_VERIFIED`）
- formal merge preflight（`FORMAL_MERGE_PREFLIGHT_PASS`）
- formal merge（`FORMAL_MERGE_VERIFIED`）
- merge post-write verification
- formal merge logical fingerprint：`1FF38FF9E9B04481A0C0BAD724E3D9B9ADFCA4E2C92441D8A2DC7DC3D30113FD`
- schema promotion（`SCHEMA_PROMOTION_VERIFIED`）
- canonical review logical fingerprint：`26074E75E8BDB0436D10FC7BE81543254C186E3FB13F9D9C66F1230DC383DD7B`
- reviewed dataset build（`REVIEWED_DATASET_BUILD_VERIFIED`）
- annotation candidates list（82 筆）
- distribution／data quality report
- final verification

Phase 04 Gate：500 筆分派完整、所有完成列通過 Validator、兩人結果合併、canonical review promotion、Reviewed Dataset 與分布報告完成。

## Phase 04.5 — External Dataset Intake and Audit

**狀態：IN PROGRESS**

目前已驗證 checkpoint：

- Dataset ID：`rf_car_damage_seg_v1`
- Registry／License／download version capture 已完成
- Raw structural QA：11,675 images；22,019 annotations；21,616 valid bbox；403 invalid overflow bbox
- Non-destructive interim clipping：403 repaired；22,019 valid interim bbox；0 invalid interim bbox
- Registry promotion／post-execute recovery／commit-push checkpoint 已驗證
- Registry commit：`17e2c915421a8f6bacacba87c01b3d09d55c62f6`
- Production deduplication：39,335 images；0 hash errors；0 exact groups；33,844 external perceptual candidates
- Group-safe plan：1,677 source families；family leakage 0；9,670 model-included images；2,005 correlated evaluation variants excluded
- Canonical COCO：`Car-Damage`／`damage-` -> `damage`；class count 1；22,019 annotations；bbox geometry preserved
- Annotation／split balance QA：invalid bbox 0；unresolved joins 0；unannotated included 0；ready for 400-item targeted visual review
- `training_acceptance=NOT_YET_APPROVED`
- 尚待完成：targeted visual label QA、lineage acceptance review、final acceptance report
- 禁止提前建立 YOLO labels、dataset split 或開始模型訓練

### 04.5A Candidate Search

搜尋 Kaggle、Roboflow Universe 與必要的公開／學術來源。

### 04.5B Registry and License Audit

所有候選先進入 `dataset/00_catalog/external_dataset_registry.csv`，不得先下載後補登錄。

### 04.5C Download and Version Capture

記錄 dataset version、download date、source URL、publisher、license evidence 與原始格式。

### 04.5D Technical Audit

檢查 task type、bbox、class、圖片品質、domain similarity、severe damage 偏差與輕微刮痕覆蓋程度。

### 04.5E Class Normalization

所有可接受類別映射至 `damage`，保留原始 class 於 metadata。

### 04.5F Deduplication

執行 SHA256、perceptual hash、internal／external 跨來源比對、group-safe split planning、COCO category canonicalization 與 annotation／split balance QA。Canonical COCO 是下游 annotation QA 與未來 dataset materialization 的唯一允許 COCO input；targeted visual QA 完成前不得核准 training acceptance。

### 04.5G Acceptance Report

輸出 accepted、rejected、needs_review、rejection reason、usable image count、usable bbox count。

Phase 04.5 Gate：每個資料集有 License 狀態、未確認 License 不進正式 train、類別映射／bbox QA／去重／Registry／接受報告完成。

## Phase 05 — Bounding Box Annotation and QA

**狀態：PLANNED**

目標：對內部有效車損圖片與外部需修正資料建立一致的 `damage` bbox。

Gate：class 僅 `damage`、圖片與 label 配對完整、bbox schema 正確、抽樣 QA 通過。

## Phase 06 — Versioned YOLO Dataset Build

**狀態：PLANNED**

預計版本：

- `v001_internal_only`
- `v002_internal_plus_external`
- `v003_external_pretrain_internal_finetune`

Gate：group split 無洩漏、internal test frozen、labels valid、manifest 可重現。

## Phase 07 — Internal-only Baseline Training

**狀態：PLANNED**

評估：Precision、Recall、mAP50、mAP50-95、False Positive、False Negative、small damage recall、角度／光線／車色分層表現。

## Phase 08 — External Data Experiments

**狀態：PLANNED**

- Experiment B：Internal + External
- Experiment C：External pretraining + Internal fine-tuning

比較原則：相同 seed、model family、internal validation／test 與核心訓練設定。

## Phase 09 — Error Analysis and Data Iteration

**狀態：PLANNED**

分析反光、水痕、陰影、接縫誤判，細小刮痕／遠距離漏判，車色／角度／光線偏差與 external domain shift。

## Phase 10 — Inference, Dashboard and Portfolio

**狀態：PLANNED**

建立批次推論、Streamlit Demo、Dashboard、Model Card、專案報告與作品集。

展示定位：單張車輛外觀車損偵測＋借還車前後比對規則雛形，不宣稱正式自動理賠系統。

## Future Extension — Angle／Quality Gate Model

**狀態：FUTURE**

角度與品質 gate 可作為未來獨立模型或規則層，但不得在第一版 `damage` Detect 尚未完成前擴張範圍。

<!-- PHASE_04_5J_04_5K_RECOVERY_20260713 -->

## Phase 04.5J — Controlled Colab Baseline Training

**狀態：DONE**

Gate：`CONTROLLED_COLAB_BASELINE_TRAINING_COMPLETED`。

- YOLOv8s Detect；single class `damage`
- 33 epochs；best epoch 13；early stopping
- Validation best：P 0.4868／R 0.3508／mAP50 0.3516／mAP50-95 0.1620
- Test 已正式評估一次，後續不得用於 threshold tuning
- Deployment acceptance：`NOT_YET_APPROVED`

## Phase 04.5K — Baseline Error Analysis

**狀態：DONE**

目標：只使用 validation split 完成逐影像 TP／FP／FN matching、confidence threshold sweep、三種 validation operating-point candidates、error taxonomy、人工複核工作清單與資料改善優先排序。

Gate：

- `best.pt` SHA256 與 04.5J 一致：`90A880513A42EF2DB1373902D98FF09D1756AB7A8A4EEA6A7AA231D4020B77BF`
- validation 168 images／325 GT instances
- raw predictions：20,566
- validation threshold candidates：high-recall `0.05`、balanced `0.20`、high-precision `0.80`
- review cases：130；representative overlays：60；data-improvement priority categories：6
- test split 未被讀取或用於 tuning
- 未開始任何 training／fine-tuning；annotation 未修改
- 產出可追蹤 manifest、checksums、error records 與 improvement priorities
- Classification：`VALIDATION_ERROR_ANALYSIS_AND_THRESHOLD_CANDIDATES_COMPLETED`
- Final ZIP：`04_5K_20260713_114517_02a146be_ZIP_LOG.zip`
- ZIP SHA256：`4D54D2BD1DA9D4B4067B9B91001291E8A1FB3691D1F4CB4D4FFCDEED78872F89`
- Deployment acceptance：`NOT_YET_APPROVED`
- 下一工作 Gate：完成人工複核 130 個 validation error cases，形成資料改善與是否重新訓練的正式決策

<!-- FLEETVISION-MANAGED:PHASE_04_5L:BEGIN -->
## Phase 04.5L — Validation Error Human Review

**狀態：ACTIVE**

目標：只使用 Phase 04.5K validation error artifacts，對 130 個 error cases 進行人工複核，確認模型錯誤、annotation／data-quality 問題、資料改善動作與重新訓練優先順序。

目前 checkpoint：

- 04.5L-2 implementation：PASS
- 04.5L-2C verification／governance sync／commit-push：PASS after remote verification
- Classification：VALIDATION_ERROR_HUMAN_REVIEW_IMPLEMENTATION_VERIFIED
- Config／workflow／prepare／export／validate／summarize／tests／guide：已建立
- Implementation files：8
- Formal review Workbook：尚未建立
- Canonical review CSV：尚未建立
- Test split read：false
- Annotation modified：false
- Training／fine-tuning：未執行
- Retraining status：NOT_YET_APPROVED
- Deployment acceptance：NOT_YET_APPROVED

下一 Gate：04.5L-3 Review Package Preparation Audit。Audit 必須先確認 authoritative 04.5K evidence、130-case identity、validation-only boundary、asset completeness、output no-overwrite 與 protected-assets boundary，才能授權建立正式人工複核套件。
<!-- FLEETVISION-MANAGED:PHASE_04_5L:END -->

<!-- FLEETVISION-MANAGED:CURRENT-CHECKPOINT:BEGIN -->
## Current repository checkpoint

| Item | Current value |
|---|---|
| Current technical phase | 05S-A1 — Team Pairing Audit Design Review |
| Current Gate | `PHASE_05S_A1_DESIGN_REVIEW_BEFORE_IMPLEMENTATION_PLAN` |
| Previous Gate | `PHASE_05R_05S_HANDOFF_RECONCILIATION` |
| Previous Gate disposition | Completed handoff synchronization |
| Recovery training | Not started |
| Frozen Test access | Not authorized |
| Codex | Task-specific authorization for this handoff only |

This checkpoint is effective only after the commit containing it is pushed and
remote verified.
<!-- FLEETVISION-MANAGED:CURRENT-CHECKPOINT:END -->

<!-- FLEETVISION-MANAGED:PHASE_04_5L_F2_AND_04_5M:BEGIN -->
## Phase 04.5L F2 — Completed Review Findings Analysis

**Status: DONE**

- Classification:
  `PHASE_04_5L_COMPLETED_REVIEW_VALIDATION_AND_FINDINGS_ANALYSIS_COMPLETED`
- Review cases: 130
- Scope reviewed: 130
- Pending/adjudication: 0/0
- Primary advisory recommendation:
  `DATA_CORRECTION_REQUIRED_BEFORE_RETRAINING`
- Correction proposals: 2
- Non-scope share: 0.407692307692
- Maximum total variation distance: 0.155144855145
- No test read, inference, annotation mutation, or training.

## Phase 04.5M — Data Correction Proposal Review

**Status: DESIGN APPROVED／IMPLEMENTATION NOT STARTED**

Selected approach: dedicated two-case correction-review application.

Gate sequence:

1. `04.5M-0` — F2 state synchronization and approved design.
2. `04.5M-1` — verified two-case review package preparation.
3. `04.5M-2` — Traditional Chinese Streamlit/SQLite review and completed export.
4. `04.5N` — future controlled annotation-correction promotion, separately authorized.

Phase 04.5M produces reviewed proposals only. It does not modify canonical
annotations or approve retraining.
<!-- FLEETVISION-MANAGED:PHASE_04_5L_F2_AND_04_5M:END -->

<!-- FLEETVISION-MANAGED:PHASE_04_5M_IMPLEMENTED:BEGIN -->
## Phase 04.5M — Data Correction Proposal Review Implementation

**Status: IMPLEMENTED／TESTED／PACKAGE NOT YET CREATED**

Implemented components:

1. correction decision and bbox geometry domain contract;
2. exact two-case validation-only package builder;
3. SQLite live state, JSONL audit, every-save backup;
4. Traditional Chinese Streamlit interface;
5. completed CSV／JSON／XLSX／proposed-overlay export;
6. PowerShell 5.1 operational wrappers;
7. focused, regression, and full-suite verification.

Implementation classification:

`PHASE_04_5M_IMPLEMENTED_TESTED_AND_READY_FOR_PACKAGE_PREPARATION`

Next Gate:

`PHASE_04_5M_1_CORRECTION_REVIEW_PACKAGE_PREPARATION`

Phase 04.5N annotation promotion remains unstarted and separately governed.
<!-- FLEETVISION-MANAGED:PHASE_04_5M_IMPLEMENTED:END -->


<!-- FLEETVISION-MANAGED:PHASE05R-MAP:BEGIN -->
## Phase 05R — Model Recovery & Dataset Quality Audit

**Status：ACTIVE AFTER GOVERNANCE COMMIT REMOTE VERIFICATION**

Phase 05R is additive. Existing historical Phase 05–10 definitions remain
unchanged.

Dependencies：

```text
Phase 00–04 governance and reviewed data
              │
Phase 04.5 validation-error and correction evidence
              │
Three-day baseline PoC and honest test failure
              ▼
Phase 05R controlled recovery track
```

### Governance entry

| Gate | Status |
|---|---|
| 05R-00 Startup Reconciliation | Complete |
| 05R-00A Governance Alignment Decision | Complete |
| 05R-00B Governance Proposal Preparation | Complete |
| 05R-00C Local Governance Application and Verification | Complete before commit |
| 05R-00D Commit／Push／Remote Verification | Activation requirement |

### Recovery execution

| Gate | Purpose |
|---|---|
| 05R-01 | Dataset and label quality audit |
| 05R-02 | Baseline validation FP／FN error analysis |
| 05R-03 | Hard-negative and annotation-correction review |
| 05R-04 | Versioned Dataset v2 |
| 05R-05 | Candidate 03–05 training |
| 05R-06 | Validation quality Gate |
| 05R-07 | Single-model Frozen Test |
| 05R-08 | CLI／API model replacement if accepted |

### Hard boundaries

- Raw data and protected external assets remain immutable.
- Frozen Test is unavailable through 05R-06.
- First round is limited to one Dataset v2 and three candidates.
- Phase 04.5M-1 remains incomplete and deferred.
- Phase 04.5N remains separately governed and is not implied by Phase 05R.
<!-- FLEETVISION-MANAGED:PHASE05R-MAP:END -->

<!-- FLEETVISION-MANAGED:PHASE05S-MAP:BEGIN -->
## Phase 05S — Seven-day Demo Sprint and Second-stage Before/After Workflow

**Status：ACTIVE AFTER HANDOFF RECONCILIATION COMMIT REMOTE VERIFICATION**

Phase 05S is a demo-sprint track for the FleetVision second-stage workflow. It
does not authorize the first-stage capture App, a large Dashboard,
Segmentation, uncontrolled data collection, public dataset expansion, Frozen
Test tuning or insurance／responsibility decisions.

### Product boundary

Phase 05S is limited to the second stage:

```text
640x640 before／after photos + metadata
input contract validation
vehicle region／background suppression
A-level obvious damage detection
B-level visible minor-damage candidates
closeup-required output
same-view／same-vehicle-region before-after comparison
structured outputs for human review
```

Allowed decision outputs:

```text
NO_NEW_DAMAGE
NEW_DAMAGE_CANDIDATE
MANUAL_REVIEW_REQUIRED
```

### Gate sequence

| Gate | Purpose | Mutation／training boundary | Status |
|---|---|---|---|
| 05S-00 | Handoff reconciliation and source-of-truth sync | governance Markdown only | Complete after this commit |
| 05S-A1 | Team-captured before／after pairing audit design review | no image scan; no implementation | Active |
| 05S-A2 | Implementation plan for A1 | docs plan only | Pending design review |
| 05S-A3 | Local Windows audit workflow implementation | code/config/tests only; generated outputs untracked | Not authorized |
| 05S-A4 | Controlled run on `04_team` | read-only source; outputs outside raw | Not authorized |
| 05S-B | Demo comparison workflow | only after confirmed pairs | Not authorized |

### Phase 05S-A1 design

- Design document：
  `docs/01_phase_guides/phase_05s_a1_team_pairing_audit_design.md`
- Source：`dataset/01_raw/04_team`
- Reported source count：319 images
- Count trust：`CHAT_CONFIRMED_NOT_IMAGE_SCANNED_IN_HANDOFF_GATE`
- Approach：semi-automated candidate pairing plus human confirmation
- Interface：local Traditional Chinese Python／Streamlit
- Live state：SQLite
- Excel role：completed export／exchange／archive only

### Hard boundaries

- `dataset/01_raw/` remains immutable.
- Frozen Test is locked and must not be searched, listed, hashed or read.
- This handoff Gate performs no image scan, no code implementation and no
  training.
- Implementation plan is the next document after Vincent reviews the tracked
  design.
- Generated CSV, JSON, XLSX, contact sheets, review packages and model outputs
  are not committed unless a later Gate explicitly designates them tracked
  governance artifacts.
<!-- FLEETVISION-MANAGED:PHASE05S-MAP:END -->
