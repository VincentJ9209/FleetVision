# FleetVision Project Context Brief

> 本文件是 FleetVision 專案的核心上下文鎖定文件。任何 ChatGPT、Codex、Cursor 或人工協作者在執行專案工作前，必須先閱讀本文件。

## 1. 專案識別

- 專案名稱：FleetVision
- 中文名稱：車損辨識
- 正式本機根目錄：`G:\Project\FleetVision`
- 舊專案架構：`irent-damage-detection` 已停用，不得再引用或混用
- 主要語言：繁體中文
- 版本控制：Git，主分支 `main`

## 2. 專案目標

建立一套可追蹤、可重現、可展示的車輛外觀車損辨識流程，涵蓋：

1. 圖片資料盤點與品質篩選
2. 人工審核與資料治理
3. 車損 Bounding Box 標註
4. YOLOv8 Detect 訓練與評估
5. 外部 Kaggle／Roboflow 資料審計與補強
6. Internal-only 與 Internal+External 實驗比較
7. 錯誤分析、資料補強與模型迭代
8. 推論 Demo、Dashboard、報告與作品集

## 3. 不可變核心架構

除非 Decision Log 新增正式 ADR 並明確取代，否則以下規則不得變更：

- 第一版模型：YOLOv8 Detect
- 第一版 YOLO 類別：單一類別 `damage`
- 標註型態：Bounding Box
- `minor_damage` 與 `claimable_damage`：保留於 metadata、來源分類與後續規則，不作為第一版 YOLO 類別
- 第一版模型不負責：自動判定理賠責任、自動估價、法律或保險結論
- CLIP：只用於 `photo_type` 建議，threshold 固定為 `0.75`
- Angle：只可使用明確檔名規則或人工判定，不得用 `_1/_2/_3/_4` 推測
- `damage` 與 `severity` 必須由人工確認
- Phase 03.5 已完成並封存，不得重新執行 CLIP／Colab inference，除非有正式 ADR 與完整重跑計畫

## 4. 目前資料概況

內部原始資料約為：

- 一般車況：27,367 張
- claimable damage：53 張
- minor damage：240 張
- Master metadata：約 27,660 列

主要風險：

- 正負樣本極度不平衡
- 車損正樣本數量不足
- 輕微刮痕、凹陷、裂痕與不同拍攝條件分布可能不足
- 一般正常照片過多，不能全部直接投入訓練
- 外部資料尚未搜尋、授權審查與下載

## 5. 固定資料策略

### Phase 04.5 — External Dataset Intake and Audit

此階段為正式外部資料接收與審計階段，負責 Kaggle 與 Roboflow 候選資料集搜尋、License 審查、下載版本記錄、類別映射、Bounding Box 品質抽查、跨來源去重與接受／拒絕報告。

此階段為正式專案路線的必要部分，後續不得遺漏，且未通過授權、品質與去重審計的外部資料，不得進入正式訓練集。

### 5.1 Internal Data

內部資料負責定義真實目標場景：租車／車輛外觀檢查、手機拍攝、真實光線、反光、污漬與背景、輕微車損與實際使用情境。

### 5.2 Negative Samples

一般車況照片不全部投入。初始策略：

- 分層抽樣 1,000～3,000 張一般 exterior negative samples
- 按角度、車色、距離、光線與來源分布抽樣

### 5.3 Hard Negatives

初始目標 300～800 張，優先包含：反光、水痕、陰影、髒污、車門接縫、保險桿輪廓、車燈反射、貼紙、正常造型凹凸、夜間噪點。

### 5.4 External Data

Kaggle／Roboflow 外部車損資料為正式既定待辦，不得遺漏。

外部資料必須依序完成：

1. 搜尋與候選登錄
2. License 審查
3. 下載與版本記錄
4. 原始類別盤點
5. 類別映射至 `damage`
6. Bounding Box 品質抽查
7. SHA256 與 perceptual hash 去重
8. 與 internal data 跨來源去重
9. 接受／拒絕紀錄
10. 只納入通過審計的外部資料

外部資料不得直接混入 internal holdout test set。

## 6. 固定實驗策略

### Experiment A — Internal-only Baseline

- Train：FleetVision internal train
- Validation：FleetVision internal validation
- Test：FleetVision frozen internal holdout

### Experiment B — Internal + External

- Train：FleetVision internal train + accepted external train
- Validation：FleetVision internal validation
- Test：FleetVision frozen internal holdout

### Experiment C — External Pretraining + Internal Fine-tuning

- Pretrain：accepted external data
- Fine-tune：FleetVision internal train
- Validation／Test：FleetVision internal

所有模型最終都以 internal holdout 表現判定是否對真實場景有效。

## 7. 資料洩漏防護

- 優先使用 `vehicle_id`、`rental_id` 或同來源群組進行 group split
- 同一車輛、同一租借紀錄、同一連拍或近似圖片不得跨 train／validation／test
- 外部資料與內部資料需跨來源去重
- Frozen internal test set 建立後不得因模型表現不佳而任意更換

## 8. 目前人工審核規則

Phase 04 目前由 Vincent 與 Allison 各 250 筆。

- 只可修改 `human_*` 欄位
- `low_quality` 必須搭配 `human_is_exterior_review = 0`
- 無法判定車損不等於確認無車損
- 模糊／遮擋／無法可靠判斷使用 `needs_followup`
- `skipped` 只用於檔案損壞、遺失、重複、流程性排除
- 一般無關照片通常標為 `irrelevant + reviewed`
- Angle 僅使用 Excel 實際下拉選單
- 不依檔名 `_1/_2/_3/_4` 判斷角度

## 9. 工具與執行分工

- Cursor／PowerShell：本機操作、檔案檢查、Git、執行 scripts
- Codex：多檔程式實作、測試與重構
- Colab：GPU 訓練
- Excel：人工審核
- Google Drive：同步與備份
- GitHub：程式碼、設定、測試、文件版本控制

原則：

- 程式碼、設定、測試與文件可進 Git
- 原始圖片、人工審核工作簿、ZIP、正式輸出 CSV 預設不進 Git
- `dataset/01_raw/` 不得被程式修改
- 未到正式階段不得提前建立 YOLO labels 或開始訓練

## 10. 每次任務前必查

1. 現在是哪個 Phase
2. 前一 Phase 是否通過驗收
3. 是否涉及原始資料
4. 是否破壞不可變架構
5. 是否影響人工結果
6. 是否涉及外部資料與 License
7. 是否可能造成資料洩漏
8. 是否需更新 Project Status／Decision Log／Master Phase Map
9. 是否需 commit／push checkpoint

## 11. 每次任務後必查

1. 測試結果
2. 輸出數量與內容
3. Git boundary
4. 正式輸出是否被意外覆蓋
5. 文件是否更新
6. Decision Log 是否新增或取代
7. Project Status 是否反映最新狀態
8. 是否建立可回復 checkpoint
