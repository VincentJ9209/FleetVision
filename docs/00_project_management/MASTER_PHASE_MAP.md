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

**狀態：ACTIVE**

### 04A — Worklist／Validator／Excel Interface

**狀態：DONE**

### 04B — Multi-reviewer Collaboration Workflow

**狀態：DONE**

### 04C — Portable Image Link Compatibility

**狀態：ACTIVE**

- 舊相對 hyperlink 在 Allison Excel 環境會交由瀏覽器開啟
- Builder 已改為 Excel `HYPERLINK(...)` 公式
- Targeted／Regression／Full tests 已通過
- 尚需 TEMP package 實機驗證、Allison 電腦確認、commit／push、修補或重建正式 package

### 04D — Human Review Execution

**狀態：ACTIVE**

- Vincent 已開始人工審核，存在部分已完成結果
- Allison 初版 package 已交付，但需使用修正版或安全修補
- 已填寫資料不得遺失或重做

### 04E — Merge and Final Validation

**狀態：PLANNED**

Phase 04 Gate：500 筆分派完整、所有完成列通過 Validator、needs_followup 處理完成、skipped 原因合理、兩人結果合併、Reviewed Dataset 與分布報告完成。

## Phase 04.5 — External Dataset Intake and Audit

**狀態：PLANNED／不可遺漏**

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

執行 SHA256、perceptual hash、internal／external 跨來源比對與近似圖人工確認。

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
