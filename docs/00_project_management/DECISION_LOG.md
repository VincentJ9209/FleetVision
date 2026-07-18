# FleetVision Decision Log

> ADR = Architecture／Data／Workflow Decision Record。新決策不得刪除舊決策；若取代，使用 `Superseded by ADR-XXX`。

## ADR-001 — 使用新版 FleetVision 專案根目錄

- 日期：2026-07
- 狀態：Active
- 決策：正式根目錄為 `G:\Project\FleetVision`；舊 `irent-damage-detection` 不再使用

## ADR-002 — 第一版模型為 YOLOv8 Detect 單一類別 damage

- 日期：2026-07
- 狀態：Active
- 決策：YOLOv8 Detect、`damage`、Bounding Box
- 不包含：minor／claimable 作 YOLO 類別、自動理賠、Segmentation

## ADR-003 — Phase 03.5 Auto Prelabel 邊界

- 日期：2026-07
- 狀態：Active
- 決策：CLIP 僅 photo type、threshold 0.75；angle 僅明確規則；不自動推論 damage／severity；不任意重跑

## ADR-004 — Pilot 500 由 Vincent／Allison 各 250 筆

- 日期：2026-07
- 狀態：Active
- 決策：deterministic round-robin；以 `review_id` 合併

## ADR-005 — 人工完成狀態不能由自動建議產生

- 日期：2026-07
- 狀態：Active
- 決策：completed status 必須有人工 reviewer 與 reviewed_at

## ADR-006 — 外部 Kaggle／Roboflow 資料為正式資料補強策略

- 日期：2026-07-11
- 狀態：Active
- 決策：納入 Phase 04.5；先審計再進 train；不得混入 internal holdout
- 必要控制：Registry、License、class mapping、bbox QA、SHA256／perceptual hash、source tracking

## ADR-007 — 以 Internal Holdout 判斷外部資料是否有效

- 日期：2026-07-11
- 狀態：Active
- 決策：Internal-only、Internal+External、External pretrain + Internal fine-tune 都以固定 internal validation／test 評估

## ADR-008 — 一般車況採分層 Negative 與 Hard-negative 策略

- 日期：2026-07-11
- 狀態：Active
- 決策：一般 negatives 1,000～3,000；hard negatives 300～800；不將全部一般車況直接投入

## ADR-009 — Git 文件為專案單一真實來源

- 日期：2026-07-11
- 狀態：Active
- 決策：重大決策、狀態、風險與 Gate 必須寫入文件並提交 Git

## ADR-010 — Collaboration Workbook 圖片連結改用 HYPERLINK 公式

- 日期：2026-07-11
- 狀態：Active／Validated
- 決策：不再使用裸相對 `cell.hyperlink.target`；`open_image` 使用 Workbook 位置組合 `images\...` 的 portable Excel `HYPERLINK(...)` formula，並保留開啟時強制重算設定
- Dropdown 相容性：六組 Excel list Data Validation 使用 workbook-scoped named ranges，指向隱藏的 `選項清單`
- 安全邊界：Builder 不得覆蓋 active／completed canonical Workbook；正式人工成果必須保留
- 驗證：Targeted 6 passed；Merger regression 6 passed；Exporter regression 10 passed；Full 112 passed, 1 skipped；TEMP Vincent／Allison Package build PASS；Excel COM 驗收 PASS；Allison 實際人工流程完成

## ADR-011 — Formal Pilot 500 Merge Uses Verified Frozen Snapshot

- 日期：2026-07-12
- 狀態：Active／Validated
- 決策：正式 Merge 只使用已驗證 frozen snapshot，不直接使用可變動 canonical Workbook
- Source identity：source assignments 與 source worklist 必須保持 identity 一致
- 合併鍵：以 `review_id` 進行合併
- 正式驗收條件：必須通過 validator、500 unique review IDs、reviewed 500、pending 0、validation errors 0
- 正式 logical fingerprint：`1FF38FF9E9B04481A0C0BAD724E3D9B9ADFCA4E2C92441D8A2DC7DC3D30113FD`
- Frozen snapshot：`G:\Project\FleetVision_Backups\Phase04_Completed_Reviews\Frozen_500\20260711_235712`
- Formal merge provenance：`G:\Project\FleetVision_Backups\Phase04_Completed_Reviews\Formal_Merge_500\20260712_001744`
- 歷史保護：historical frozen snapshot 與 provenance 不得被後續修正覆寫
- 後續 Gate：Phase 04 下一步仍需 schema promotion 與 Reviewed Dataset build；不得直接以 `human_*` merged CSV 執行舊 Reviewed Dataset Builder

## ADR-012 — Promote Formal Human Review Schema Before Reviewed Dataset Build

- 日期：2026-07-12
- 狀態：Active／Validated
- 決策：Formal Merge CSV 保持 immutable；使用獨立 Schema Promotion Adapter 將 `human_*` 欄位映射至 canonical review 欄位
- Builder 邊界：既有 Reviewed Dataset Builder 不修改；Schema Promotion 與 Dataset Build 分開執行
- Canonical logical fingerprint：`26074E75E8BDB0436D10FC7BE81543254C186E3FB13F9D9C66F1230DC383DD7B`
- Canonical review CSV：`outputs/manual_review/collaboration/pilot500_review_labels_canonical.csv`
- Reviewed Dataset Build 使用已驗證 canonical review CSV；Gate：`REVIEWED_DATASET_BUILD_VERIFIED`
- 資料保護：`dataset/01_raw` 不得修改
- Annotation 邊界：annotation candidates 尚不是 YOLO labels
- 後續 Gate：Phase 04.5 必須先處理外部資料授權、mapping、品質與去重，方可與內部 annotation candidates 整合

## ADR-013 — Preserve Roboflow Raw Data and Repair Overflow Bboxes Non-destructively

- 日期：2026-07-12
- 狀態：Active／Validated
- Dataset ID：`rf_car_damage_seg_v1`
- 決策：`dataset/01_raw/99_external/roboflow/rf_car_damage_seg_v1` 保持 immutable；不得直接修寫 source annotation
- Raw audit：11,675 images；22,019 annotations；21,616 valid raw bbox；403 invalid overflow bbox；0 invalid segmentation；0 missing images
- Repair boundary：403 個 overflow bbox 僅於 `dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1` 執行 clipping
- Interim result：22,019 valid bbox；0 invalid bbox；repair status `clipped_overflow_verified`
- Registry promotion：`REAL_REGISTRY_PROMOTION_VERIFIED`；recovery `POST_EXECUTE_VERIFICATION_RECOVERED`
- Registry SHA256：`314b30242ed5ed4bce995bca9a2cae3c4cfa3b7aa89a7374e8dd531fe3193052`
- Registry commit：`17e2c915421a8f6bacacba87c01b3d09d55c62f6`
- Protected assets：`outputs/metadata/external_assets/` 保持 untracked、不得 stage／commit
- Acceptance boundary：`training_acceptance=NOT_YET_APPROVED`
- Pending controls：perceptual hash、internal cross-dedup、lineage acceptance review、final acceptance report
- 禁止事項：不得提前建立 YOLO labels、dataset split 或開始模型訓練

## ADR-014 — Canonicalize Roboflow Damage Category Aliases Before Downstream QA

- 日期：2026-07-12
- 狀態：Active／Validated
- Dataset ID：`rf_car_damage_seg_v1`
- 根因證據：三個 cleaned COCO split 均含 `damage-`（category id 0）與 `Car-Damage`（category id 1）；全部 22,019 annotations 僅引用 `Car-Damage`，`damage-` 為 0 annotations，且是 `Car-Damage` 的 source supercategory；無 mixed-category image、無第三種 category
- 決策：source aliases `Car-Damage` 與 `damage-` 均 canonicalize 為唯一類別 `{id: 0, name: damage, supercategory: damage}`
- 非破壞邊界：`cleaned_coco` 不修改；canonical output 寫入 `dataset/02_interim/99_external/roboflow/rf_car_damage_seg_v1/canonical_coco`
- Source cleaned COCO SHA256：train `B80D0601AEBEDDFF2E4AD98302A27F0DE4C6C91608F14B74398762654E8C86E6`；valid `28EC12ABDBC3A09D602D1B3F276DB3DE5F3571E2633EF4FC4401D92A761D1394`；test `E269A031DAF1A800264F333B961234F1AF6D182C8C6FA2A22B34DAE843BCDF4A`
- Canonical COCO SHA256：train `64FEA6E47624F2DB6AB77C7485017DC50924F737C6084C250FB2FB74E890077C`；valid `CDB6EFB9547DBE1BAF0C5A0FF2250EF242A9B552BC85FD74C897B68FD1A344D8`；test `A4BE2674BB0009C7245E0DE08410D18413F3F71E14EFE9376CD858028C98C2CE`
- Preservation Gate：11,675 images 與 22,019 annotations 前後一致；annotation IDs、image IDs、bbox、area、segmentation、iscrowd 與非 category metadata 保留；bbox geometry checksum 全部一致
- 下游邊界：canonical COCO 是 annotation QA 與未來 dataset materialization 的唯一允許 COCO input；不得再接受 `Car-Damage` 或 `damage-`
- Group-safe QA：1,677 families；leakage 0；9,670 model images；2,005 correlated eval variants excluded；invalid bbox 0；unresolved joins 0
- QA 結論：`ANNOTATION_QA_STRUCTURALLY_READY_FOR_TARGETED_VISUAL_REVIEW`
- Acceptance boundary：`training_acceptance=NOT_YET_APPROVED`，直到 400 項 targeted visual bbox review 完成且無 material label defect

<!-- PHASE_04_5J_04_5K_RECOVERY_20260713 -->

## ADR-015 — Test Set Is Single-Evaluation-Only; Phase 04.5K Tuning Uses Validation Only

- 日期：2026-07-13
- 狀態：Active／Validated by Phase 04.5J evidence
- 決策：Phase 04.5J 已使用 `best.pt` 對 test split 正式評估一次。後續 test split 不得用於 confidence threshold tuning、operating-point selection、error prioritization、資料改善排序或模型選擇。
- Phase 04.5K 唯一允許的 tuning／error-analysis split：`valid`
- Validation scale：168 images／325 ground-truth instances
- Matching：one-to-one greedy matching，IoU threshold 0.50；localization analysis floor 0.10
- Threshold outputs：high-recall、balanced、high-precision 三組 `VALIDATION_THRESHOLD_CANDIDATE`
- Deployment boundary：所有候選均不構成 deployment approval；`deployment_acceptance=NOT_YET_APPROVED`
- Training boundary：Phase 04.5K 不重新訓練、不 fine-tune、不修改 labels 或固定 split

## ADR-016 — Complete Validation-only Error Analysis Before Any Retraining

- 日期：2026-07-13
- 狀態：Active／Validated by Phase 04.5K evidence
- 決策：YOLOv8s baseline training 已於 Phase 04.5J 完成；Phase 04.5K 僅執行 validation-only threshold sweep、error taxonomy 與 human-review worklist，沒有重新訓練或 fine-tuning。
- Gate：`VALIDATION_ERROR_ANALYSIS_AND_THRESHOLD_CANDIDATES_COMPLETED`
- Evidence ZIP：`04_5K_20260713_114517_02a146be_ZIP_LOG.zip`
- ZIP SHA256：`4D54D2BD1DA9D4B4067B9B91001291E8A1FB3691D1F4CB4D4FFCDEED78872F89`
- Validation evidence：168 images／325 GT／20,566 raw predictions／379 detailed errors
- Candidate thresholds：high-recall `0.05`、balanced `0.20`、high-precision `0.80`
- Human-review evidence：130 cases／60 overlays／6 data-improvement priority categories
- Threshold boundary：`0.20` 是 balanced `VALIDATION_THRESHOLD_CANDIDATE`，不是 deployment threshold。
- Next control：完成人工複核與資料改善決策前，`retraining_status=NOT_YET_APPROVED`。
- Deployment boundary：`deployment_acceptance=NOT_YET_APPROVED`

<!-- FLEETVISION-MANAGED:DEC-GOV-2026-0713-01:BEGIN -->
## DEC-GOV-2026-0713-01 — Repository-backed cross-conversation state

**Decision:** Adopt Scheme C: Git repository Markdown is the formal cross-conversation source of truth, combined with a minimal new-chat bootstrap prompt.

**Rationale:** FleetVision has expanding datasets, long-running Phases, many Gates, one-time promotions, protected assets, and cryptographic evidence. Reconstructing state from chat summaries alone creates avoidable omission and staleness risk.

**Consequences:**

- Every new conversation starts from `START_HERE.md`.
- Gate completion includes project-state document synchronization.
- Large datasets and outputs remain outside Markdown; documents store paths, counts, lineage, timestamps, classifications, and SHA256 values.
- Direct GitHub writes are prohibited when local and remote state have not been reconciled.
- Local HEAD, `origin/main`, and remote HEAD must agree before controlled repository writes.
<!-- FLEETVISION-MANAGED:DEC-GOV-2026-0713-01:END -->

## ADR-017 — Human-review workflows default to Traditional Chinese Streamlit and SQLite

- 日期：2026-07-14
- 狀態：Active
- 決策：FleetVision 所有多筆人工審核預設使用本機繁體中文 Streamlit 介面；active progress 使用 SQLite transaction 保存，並具備 resume、audit events 與定期 backup。
- Excel 邊界：Excel 僅作 completed export、交換、封存或明確 Gate 核准的無 Python 協作 package；直接編輯 Excel 不得作為單人本機人工審核的預設 live state。
- 自動欄位：reviewer 與 timezone-aware reviewed timestamp 由系統寫入。
- 完成邊界：正式 completed Workbook／CSV 必須由 no-overwrite exporter 產生，並通過 identity、row order、immutable source fields、schema、SHA256 與 downstream validator。
- 復用要求：新人工審核工具在 design 階段必須先檢查並安全復用既有 Streamlit／SQLite review framework。
- 受控例外：協作者無法執行 Python／Streamlit 時，需由獨立 Gate 核准 Excel collaboration package，且保留 source hash、backup、欄位鎖定、assignment、identity-key merge、原始 reviewer 檔、no-overwrite merger 與 post-merge validator。
- 正式規範：`docs/00_project_management/HUMAN_REVIEW_INTERFACE_STANDARD.md`。
- 安全邊界：本決策不授權讀取 test、重新 inference、修改 annotation／GT／dataset／Registry／fixed splits、training、retraining 或 deployment。

## ADR-018 — User-visible artifacts require target-environment rehearsal

- 日期：2026-07-14
- 狀態：Active
- 決策：提供給 Vincent 的 installer、correction ZIP 與操作腳本必須是通過 target-environment rehearsal 的 release candidate，不得把正式 FleetVision workspace 當作第一個 integration-test environment。
- Windows 契約：rehearsal 必須涵蓋 PowerShell 5.1、Git `core.autocrlf`、CRLF、UTF-8 BOM、EOF、openpyxl／Windows file-handle semantics。
- 驗證順序：先執行 exact-path allowlist、`git diff --check`、parser／compile 與其他低成本檢查；通過後才執行 focused、regression 與必要的 full suite。
- 安裝器契約：必須具備 no-overwrite、transaction rollback、idempotency、protected-asset preservation 與 consolidated PASS／BLOCKED result。
- 交付邊界：內部 debug versions 不對使用者逐版交付；同一 Gate 原則上只交付一個正式 release candidate。


<!-- FLEETVISION-MANAGED:DEC-05R-001-006:BEGIN -->
## DEC-05R-001 — Reclassify the three-day selected model as a recovery baseline

- 日期：2026-07-18
- 狀態：Active
- 決策：historical `final_selected` model is named `baseline_candidate_01`
  for recovery governance.
- SHA256：`605FFAC6B1AA39A2E9F13BA09456943529B2788B7FCBEEACE43A3616D1C41C89`
- Classification：`BEST_AVAILABLE_POC_ONLY`
- Consequence：technical Demo completion does not equal production model acceptance.

## DEC-05R-002 — Add Phase 05R without overwriting Phase 05–10

- 日期：2026-07-18
- 狀態：Active
- 決策：adopt `Phase 05R — Model Recovery & Dataset Quality Audit` as an
  additive controlled recovery track.
- Consequence：historical Phase 05–10 definitions and completed evidence remain intact.
- Phase 04.5M-1：deferred, not completed or deleted.

## DEC-05R-003 — Permit one controlled Dataset v2

- 日期：2026-07-18
- 狀態：Active
- 決策：permit one versioned `fleetvision_damage_v2` only after audit,
  reviewed-correction and lineage Gates pass.
- Restrictions：raw sources and Frozen Test remain immutable; every correction
  requires evidence and deterministic manifests.

## DEC-05R-004 — Validation Gate precedes Frozen Test and CLI／API replacement

- 日期：2026-07-18
- 狀態：Active
- 決策：Candidate selection and threshold determination use validation only.
- Candidate limit：C03–C05, maximum three in the first round.
- Consequence：no Frozen Test and no model replacement before validation acceptance.

## DEC-05R-005 — Freeze the recovery Test contract

- 日期：2026-07-18
- 狀態：Active
- 決策：evaluate one validation-approved model once on Frozen Test.
- Prohibited：use Test results for tuning, threshold changes, candidate
  reselection or data-priority decisions.
- Test modification：never authorized by Phase 05R.

## DEC-05R-006 — Separate local governance application from canonical publication

- 日期：2026-07-18
- 狀態：Active
- 決策：`00C` applies and verifies exact governance files locally without
  staging, commit or push. `00D` requires separate explicit authorization and
  completes exact-path commit, push and remote verification.
- Rationale：GitHub is the long-term source of truth and automatic commit／push
  is prohibited.
- Codex：`CONDITIONALLY_PAUSED`; each task requires task-specific authorization.
<!-- FLEETVISION-MANAGED:DEC-05R-001-006:END -->

<!-- FLEETVISION-MANAGED:DEC-05S-001-006:BEGIN -->
## DEC-05S-001 — Limit the demo sprint to FleetVision second-stage responsibility

- 日期：2026-07-19
- 狀態：Active
- 決策：Phase 05S is limited to the second-stage before／after damage-review
  workflow. FleetVision does not implement the first-stage capture App or a
  large Dashboard in this sprint.
- Inputs：640x640 before／after photos plus metadata.
- Outputs：`NO_NEW_DAMAGE`、`NEW_DAMAGE_CANDIDATE`、`MANUAL_REVIEW_REQUIRED`.
- Prohibited：responsibility assignment, insurance settlement, Segmentation,
  uncontrolled data collection and public dataset expansion.

## DEC-05S-002 — Use a multi-stage human-review architecture

- 日期：2026-07-19
- 狀態：Active
- 決策：Phase 05S uses a staged workflow: input contract validation,
  vehicle-region／background suppression, obvious-damage detection,
  minor-damage candidate surfacing, closeup-required output, same-view
  before／after comparison and structured human-review outputs.
- Human review default：local Traditional Chinese Python／Streamlit interface
  with SQLite live state, append-only audit events and backups.
- Excel boundary：completed export／exchange／archive only.

## DEC-05S-003 — Prioritize A-level and B-level demo outcomes; defer C-level scope

- 日期：2026-07-19
- 狀態：Active
- 決策：The seven-day demo sprint prioritizes A-level obvious damage detection
  and B-level visible minor-damage candidates. C-level future expansion is
  deferred until a later Gate.
- Consequence：Phase 05S must not expand into broad model research,
  Segmentation, Dashboard implementation or first-stage capture tooling.

## DEC-05S-004 — Retain full-image classification as baseline evidence only

- 日期：2026-07-19
- 狀態：Active
- 決策：Full-image classification and ResNet18 recovery evidence may be used as
  baseline or diagnostic evidence, but not as final production acceptance for
  before／after damage decisions.
- R4-07 and R4-08 trust classification：
  `CHAT_CONFIRMED_NOT_REPOSITORY_VERIFIED` until the actual artifacts are
  located and independently verified.

## DEC-05S-005 — Adopt Phase 05S-A1 team pairing audit strategy

- 日期：2026-07-19
- 狀態：Active
- 決策：Adopt semi-automated candidate pairing plus human confirmation for the
  team-captured `dataset/01_raw/04_team` source.
- Reported source count：319 images.
- Count trust classification：
  `CHAT_CONFIRMED_NOT_IMAGE_SCANNED_IN_HANDOFF_GATE`.
- Confirmation boundary：vehicle identity, capture batch, view angle,
  before／after stage, rental pairing, existing damage and no-new-damage status
  remain human-confirmed.

## DEC-05S-006 — Use local Windows Python interface with Colab fallback

- 日期：2026-07-19
- 狀態：Active
- 決策：Phase 05S implementation planning must target a local Windows Python
  workflow first, with Colab as mandatory backup for environment or compute
  risk.
- Local interface：Traditional Chinese Streamlit／SQLite unless a later Gate
  approves a controlled exception.
- Colab fallback：backup only; it does not authorize Frozen Test access,
  training, dataset mutation or bypassing local governance.
<!-- FLEETVISION-MANAGED:DEC-05S-001-006:END -->
