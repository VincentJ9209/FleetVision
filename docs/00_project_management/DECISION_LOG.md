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
