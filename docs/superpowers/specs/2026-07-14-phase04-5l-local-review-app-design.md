# FleetVision Phase 04.5L 本機中文人工審核介面設計規格

- 文件狀態：設計方向已確認，等待使用者審閱正式規格
- 日期：2026-07-14
- 專案：FleetVision／Project_FleetVision 車損辨識
- 適用階段：Phase 04.5L — Validation Error Human Review
- 操作者：Vincent
- 作業模式：單人、本機、離線優先
- 原始正式 review batch：`phase04_5l_20260714_v1`

## 1. 背景與問題

Phase 04.5L 已建立正式的 130-case validation-error review package，包含 130 張原始 validation 圖片、130 張 GT／prediction overlay、Excel Workbook、manifest、checksums 與 frozen transport ZIP。

現有 Workbook 適合機器驗證，但人工操作負擔過高：

1. 圖片縮圖過小，不利於觀察細小刮痕、反光與 bbox 邊界。
2. 每列同時呈現大量英文欄位與英文代碼。
3. 多數案例只需要少數判斷，卻必須理解全部 canonical 欄位。
4. annotation、模型錯誤、threshold trade-off 與 retraining 欄位同時出現。
5. 手動填寫 reviewer、時間與欄位組合容易產生 Validator 錯誤。

本設計新增只在本機執行的中文 Streamlit 審核介面，將人類操作與 canonical schema 分離：使用者只看中文、只回答必要問題；程式負責轉換、補齊與驗證英文 canonical 欄位。

## 2. 設計目標

第一版必須達成：

1. 一次只顯示一個案例。
2. 原圖與 Overlay 可大尺寸檢視。
3. 主要操作全部使用繁體中文。
4. 一般案例只需完成 2～4 個核心判斷。
5. 複雜欄位只在標註問題、無法判斷、高優先或「其他」時顯示。
6. 自動填入 `reviewer=Vincent`。
7. 自動產生含時區的 `reviewed_at_utc`。
8. 自動將中文選項映射為現有英文 canonical values。
9. 每次儲存後可關閉瀏覽器，之後從原進度繼續。
10. 完成後產生一份新的 completed Workbook，供既有 Exporter 與 Validator 使用。
11. 原始 review package、原始 Workbook 與 frozen transport ZIP 全程保持不變。
12. 不讀取 test split、不重新 inference、不修改 annotation／GT、不開始 training。

## 3. 非目標

第一版不包含：

- 多人同時審核。
- 登入、權限或角色管理。
- 雲端部署。
- PostgreSQL 或遠端資料庫。
- 線上協作與即時同步。
- 在介面中畫框或修改 bbox。
- 直接修改 canonical COCO、GT、Registry 或固定 split。
- 自動重新執行模型 inference。
- 自動核准 retraining 或 deployment。
- 行動裝置最佳化。
- 鍵盤快捷鍵作為 Gate 必要條件。

鍵盤快捷鍵可列為後續增強功能，但不得阻塞第一版交付。

## 4. 單人作業假設

本介面只支援 Vincent 單人作業：

- 固定 reviewer 為 `Vincent`。
- 同一時間只允許一個本機 Streamlit server。
- 建議只開啟一個瀏覽器分頁。
- 不處理多人衝突合併。
- 不需要帳號、密碼或網路服務。
- 所有圖片與審核資料留在本機。

如果未來需要多人審核，必須另立新設計，不在本階段擴充。

## 5. 資料與路徑邊界

### 5.1 凍結來源

來源 package：

```text
G:\Project\FleetVision_Review_Packages\Phase04_5L\
└── phase04_5l_20260714_v1\
    ├── assets\
    │   ├── original\
    │   └── overlay\
    ├── manifest\
    └── workbook\
        └── validation_error_human_review.xlsx
```

來源 Workbook SHA256：

```text
5DC9C1FDA69865D36C60EACB90A0AEA0FC9F4B263F30281723BB0E1172549DE5
```

凍結 package ZIP：

```text
phase04_5l_20260714_v1_PACKAGE.zip
```

凍結 ZIP SHA256：

```text
6D6243FE8F3E12910C03A5EDCFF178CE20B180473EED43DED2B36301A877B42A
```

介面啟動時必須驗證來源 Workbook、manifest、checksums 與必要 assets。驗證失敗時 fail closed，不可進入審核。

### 5.2 獨立 workspace

所有審核進度寫入獨立 sibling directory：

```text
G:\Project\FleetVision_Review_Packages\Phase04_5L\
└── phase04_5l_20260714_v1_review_workspace\
    ├── state\
    │   ├── review_state.sqlite3
    │   └── review_events.jsonl
    ├── backups\
    ├── exports\
    └── app_logs\
```

不得把進度寫回來源 batch，也不得修改來源 Workbook。

### 5.3 Repository 邊界

應用程式原始碼可提交至 FleetVision repository；執行產物、workspace、SQLite、logs、backups 與 completed Workbook 不得 commit。

## 6. 技術架構

第一版採用：

- UI：Streamlit。
- 語言：Python。
- 本機狀態：SQLite（Python 標準函式庫 `sqlite3`）。
- 稽核事件：append-only JSON Lines。
- 圖片：直接讀取正式 package 中的 original／overlay。
- 匯出：以來源 Workbook 的副本建立 completed Workbook。
- 最終驗證：沿用既有 Phase 04.5L Exporter 與 Validator。

### 6.1 建議程式邊界

預計新增：

```text
configs/data/validation_error_review_app_config.yaml
src/fleetvision/review/validation_error_review_app.py
src/fleetvision/review/validation_error_review_mapping.py
src/fleetvision/review/validation_error_review_state.py
scripts/phase04_5_run_validation_error_review_app.py
scripts/phase04_5_export_validation_error_review_app_workbook.py
tests/test_validation_error_review_app.py
docs/01_phase_guides/phase_04_5_validation_error_review_app.md
```

各模組責任：

- `validation_error_review_mapping.py`
  - 中文 UI 選項。
  - 中文選項到 canonical values 的確定性映射。
  - 條件式欄位與欄位組合規則。
- `validation_error_review_state.py`
  - SQLite schema。
  - transactional save。
  - 進度恢復。
  - event log。
  - backup。
- `validation_error_review_app.py`
  - Streamlit 畫面。
  - 單案例導航。
  - 輸入驗證。
  - 進度統計。
- `phase04_5_export_validation_error_review_app_workbook.py`
  - 讀取完成狀態。
  - 複製原始 Workbook。
  - 只寫入 human-review 欄位。
  - 產生 no-overwrite completed Workbook。
  - 呼叫既有 semantic validation。

## 7. UI 設計

### 7.1 頁面配置

Streamlit 使用 wide layout。

頁首顯示：

```text
FleetVision 04.5L 中文人工複核
案例 18 / 130
已完成 17｜待裁決 2｜未審核 111
```

主畫面：

1. 圖片顯示模式：
   - 左右比較。
   - 只看原圖。
   - 只看 Overlay。
2. 原圖與 Overlay 大尺寸顯示。
3. 當前案例摘要：
   - 圖片名稱。
   - 系統初步錯誤分類。
   - GT 數量。
   - threshold 0.20 以上的 prediction 數量。
   - max confidence。
   - best IoU。
4. 中文快速判斷區。
5. 儲存與導航按鈕。

### 7.2 大圖策略

不使用額外 image-zoom 套件作為第一版必要依賴。

提供：

- 左右比較模式。
- 單圖全寬模式。
- 瀏覽器本身縮放。
- 點擊「放大檢視」後在頁面下方以全寬重新顯示。

第一版成功標準是細小損傷可在單圖全寬模式下辨識，不要求滑鼠滾輪局部縮放。

### 7.3 核心判斷

第一層固定顯示「主要結果」：

- 模型漏檢
- 模型誤報
- 模型框不準
- 重複預測
- 標註有問題
- 門檻取捨
- 圖片無效
- 無法判斷

第二層依主要結果顯示相關欄位：

- 主要原因。
- 標註品質。
- 改善方向。
- 優先程度。
- 必要時的標註缺陷類型。
- 必要時的備註。

一般案例不顯示英文 canonical code。

### 7.4 條件式欄位

以下情況展開詳細欄位：

- 選擇「標註有問題」。
- 標註品質為「明確有問題」。
- 選擇「無法判斷」。
- 優先程度為「高」。
- 任一選項為「其他」。

其餘情況使用簡化模式。

## 8. 中文到 canonical 的映射

### 8.1 主要結果

| 中文主要結果 | canonical mapping |
|---|---|
| 模型漏檢 | `error_disposition=confirmed_model_error` |
| 模型誤報 | `confirmed_model_error` + `primary_root_cause=background_false_positive` |
| 模型框不準 | `confirmed_model_error` + `localization_error` |
| 重複預測 | `confirmed_model_error` + `duplicate_prediction` |
| 標註有問題 | `annotation_issue` + `annotation_quality=defect_suspected` |
| 門檻取捨 | `expected_threshold_tradeoff` + `threshold_analysis_only` |
| 圖片無效 | `invalid_review_case` + `invalid_or_low_quality_image` |
| 無法判斷 | `ambiguous_case` + `ambiguous_visual_evidence` |

### 8.2 標註品質

| 中文 | canonical |
|---|---|
| 正確 | `correct` |
| 有疑問 | `questionable` |
| 明確有問題 | `defect_suspected` |
| 無法評估 | `not_applicable` |

當標註不是 `defect_suspected`：

```text
annotation_defect_type=none
correction_proposal_required=no
```

當標註為 `defect_suspected`：

```text
correction_proposal_required=yes
recommended_action=create_annotation_correction_proposal
annotation_defect_type 必須為具體值
review_notes 必填
```

### 8.3 自動欄位

系統自動設定：

```text
reviewer=Vincent
reviewed_at_utc=<Asia/Taipei offset-aware ISO 8601>
secondary_root_cause=none
```

只有使用者展開進階設定時，才可選擇其他 secondary root cause。

### 8.4 建議動作預設值

系統依結果與原因提供預設值，但使用者可在合法範圍內調整：

| 條件 | 預設建議 |
|---|---|
| 小損傷或弱視覺訊號漏檢 | `add_positive_sample` |
| 背景或反光誤報 | `add_hard_negative` |
| localization／duplicate | `adjust_model_strategy` |
| 光線、模糊、裁切 | `investigate_image_quality` |
| preprocessing 疑慮 | `investigate_preprocessing` |
| threshold trade-off | `threshold_analysis_only` |
| invalid image | `exclude_invalid_image_proposal` |
| annotation defect | `create_annotation_correction_proposal` |

## 9. 狀態與持久化

### 9.1 SQLite schema

至少包含：

- `workspace_metadata`
  - source package identity。
  - source Workbook SHA256。
  - schema version。
  - reviewer。
  - created／updated timestamps。
- `review_cases`
  - immutable source identity。
  - UI selections。
  - derived canonical human fields。
  - status。
  - revision。
  - saved timestamp。
- `app_state`
  - last viewed case。
  - filter。
  - sort。
- `export_history`
  - completed Workbook path。
  - SHA256。
  - export timestamp。

### 9.2 儲存規則

每次「儲存」或「儲存並下一筆」：

1. 驗證目前 UI 組合。
2. 產生 canonical human fields。
3. 在單一 SQLite transaction 中更新案例。
4. 寫入 append-only event log。
5. 更新進度統計。
6. 成功後才切換案例。

失敗時保留目前畫面，不切換下一筆。

### 9.3 Backup

- 每完成 10 次成功儲存，建立一份 SQLite backup。
- 每次產生 completed Workbook 前建立 backup。
- 保留最近 20 份自動 backup。
- 不覆寫既有 backup。

## 10. 審核狀態

支援：

- 未審核：`pending`
- 已完成：`reviewed`
- 待裁決：`needs_adjudication`

規則：

- 一般完成案例儲存為 `reviewed`。
- 「無法判斷」預設儲存為 `needs_adjudication`。
- `needs_adjudication` 可稍後返回修改。
- completed Workbook 只有在：
  - 130/130 為 `reviewed`
  - 0 pending
  - 0 needs_adjudication
  - semantic validation 無錯誤
  時才可產生。

## 11. 導航與篩選

必要功能：

- 上一筆。
- 儲存。
- 儲存並下一筆。
- 跳至指定案例編號。
- 篩選：
  - 全部。
  - 未審核。
  - 已完成。
  - 待裁決。
  - 高優先。
  - 標註問題。
- 可返回已完成案例修改。
- App 啟動時回到最後檢視案例。

第一版不要求鍵盤快捷鍵。

## 12. 匯出完成版 Workbook

匯出流程：

1. 驗證來源 Workbook SHA256 未變。
2. 驗證 130 個 source identity 與 source fingerprint。
3. 驗證所有案例均為 `reviewed`。
4. 執行 canonical semantic validation。
5. 複製來源 Workbook至 workspace `exports/`。
6. 只寫入現有 human-review 欄位。
7. 不修改 source columns、圖片、sheet order、named ranges 或 data validation。
8. 重新讀取 completed Workbook 並驗證。
9. 計算 SHA256。
10. 寫入 export history。
11. no-overwrite；既有完成檔存在時直接 BLOCKED。

預計輸出：

```text
phase04_5l_20260714_v1_review_workspace\
└── exports\
    └── validation_error_human_review_completed.xlsx
```

completed Workbook 產生後，仍須使用既有 Phase 04.5L Exporter 與 Validator，才能產生正式 canonical CSV。

## 13. 錯誤處理

### 13.1 啟動阻擋

以下情況不得啟動審核：

- source Workbook SHA256 不符。
- manifest 或 checksum 不符。
- 缺少 original／overlay。
- case count 不是 130。
- source identity 重複。
- workspace 綁定到不同 source package。
- repository／package path 包含 test split。

### 13.2 儲存阻擋

以下組合不得儲存為 reviewed：

- 必填欄位缺少。
- annotation defect 未選具體 defect type。
- annotation defect 沒有 notes。
- high priority 沒有 notes。
- 「其他」沒有 notes。
- canonical controlled value 不合法。

### 13.3 恢復

若 SQLite 無法開啟：

- 不自動建立空白狀態覆蓋原檔。
- 顯示 BLOCKED。
- 列出最近 backup。
- 由受控 recovery Gate 選擇 backup。

## 14. 安全與治理邊界

應用程式必須固定輸出：

```text
TEST_SPLIT_READ: NO
MODEL_INFERENCE_EXECUTED: NO
ANNOTATION_MODIFIED: NO
TRAINING_STARTED: NO
RETRAINING_STATUS: NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE: NOT_YET_APPROVED
```

禁止：

- 修改 source batch。
- 修改 frozen package ZIP。
- 修改 GT 或 canonical COCO。
- 重新推論。
- 讀取 test split。
- 自動開始 retraining。
- 自動認定 deployment threshold。
- 將 workspace／review result commit 到 Git。

## 15. 測試策略

### 15.1 Mapping tests

逐一驗證中文選項到 canonical values：

- 模型漏檢。
- 模型誤報。
- localization。
- duplicate。
- annotation defect。
- threshold trade-off。
- invalid image。
- ambiguous case。

### 15.2 Semantic rule tests

驗證：

- defect_suspected 強制 proposal=yes。
- defect_suspected 強制 correction action。
- defect type 不可為 none。
- high priority 強制 notes。
- reviewed 強制必要欄位。
- needs_adjudication 不可輸出 completed Workbook。

### 15.3 State tests

驗證：

- transaction save。
- reload 後進度不遺失。
- duplicate case 不產生第二筆。
- revision 正確增加。
- backup 建立。
- source package identity 不符時 BLOCKED。

### 15.4 Export tests

驗證：

- 只修改 human columns。
- source columns logical identity 不變。
- sheet order 不變。
- embedded images 保留。
- no-overwrite。
- completed Workbook 可被既有 reader 讀取。
- 既有 Validator 在完整合法資料上 PASS。
- 未完成資料 export BLOCKED。

### 15.5 Gate tests

- Focused tests。
- Full repository test suite。
- CLI `--help`。
- Streamlit module import smoke。
- source package read-only verification。
- final Git status verification。

## 16. 驗收條件

第一版完成必須同時符合：

1. 可在 Windows PowerShell 5.1 啟動。
2. 瀏覽器顯示繁體中文 UI。
3. 正確載入 130 cases。
4. 原圖／Overlay 可切換左右與單圖全寬。
5. 一般案例只需少量中文選項。
6. 條件式欄位依規則顯示。
7. 每次儲存均持久化。
8. 關閉並重新啟動後恢復進度。
9. reviewer 與時間自動填入。
10. canonical mapping 通過測試。
11. completed Workbook 僅在 130/130 reviewed 時產生。
12. completed Workbook 可通過既有 Phase 04.5L Validator。
13. 原始 batch、Workbook 與 ZIP SHA256 保持不變。
14. 沒有 test read、inference、annotation mutation 或 training。
15. workspace 不進入 Git。

## 17. 實作順序

設計規格核准後，實作計畫應依序處理：

1. Mapping 與 semantic rule engine。
2. SQLite state store 與 backup。
3. completed Workbook exporter。
4. Streamlit UI。
5. end-to-end package integration。
6. Windows PowerShell launcher。
7. focused／full tests。
8. controlled commit／push。
9. local review app preparation Gate。
10. Vincent 開始正式 130-case 審核。

不得先做 UI 再補 mapping／state／export；資料契約與安全邊界必須先完成。
