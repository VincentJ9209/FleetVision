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
- 狀態：Pending Validation
- 決策：不再使用裸相對 `cell.hyperlink.target`；使用 Workbook 位置組合 `images\...` 的 Excel `HYPERLINK(...)`；開啟時強制重算
- 證據：Targeted 5 passed；Regression 6 passed；Full 111 passed, 1 skipped
- 尚需：Allison 實機驗證、commit／push、正式 package 修補／重建
