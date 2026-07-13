# Phase 04.5L 本機中文人工複核介面

## 目的

使用繁體中文、大尺寸原圖／Overlay 與少量條件式選項完成 130 個
validation-error cases。介面只在本機運作，不讀 test、不重新推論、不修改
annotation，也不開始 training。

本工具只協助人工複核與產出 completed Workbook。Threshold `0.20` 仍只是
`BALANCED_VALIDATION_THRESHOLD_CANDIDATE`，不是 deployment threshold。

## 啟動

開啟 Windows PowerShell 5.1：

```powershell
cd G:\Project\FleetVision

Set-ExecutionPolicy -Scope Process Bypass

.\scripts\phase04_5_launch_validation_error_review_app.ps1
```

瀏覽器未自動開啟時，使用 Streamlit 終端輸出的 Local URL，預設為：

```text
http://127.0.0.1:8501
```

同一時間只啟動一個本機審核 server，並只由 Vincent 單人操作。結束時回到
PowerShell 視窗按 `Ctrl+C`。

## 每張圖片的操作

1. 先看原圖與 Overlay；必要時切換成原圖或 Overlay 單圖模式。
2. 選擇主要判斷。
3. 確認系統縮限後的主要原因、標註品質、改善方向與重新訓練優先度。
4. 標註問題、高優先、無法判斷或選擇「其他」時，填寫具體說明。
5. 按「儲存本筆」或「儲存並下一筆」。
6. 可使用側邊欄跳轉，或依未完成、已完成、待裁決、高優先及標註問題篩選。

一般案例只會顯示四個主要欄位；需要額外證據的案例才會展開標註缺陷類型與
判斷說明。

## 狀態

- 未完成：尚未形成可匯出的最終人工判斷。
- 已完成：可納入 completed Workbook。
- 待裁決：目前仍有歧義，必須返回並改成已完成後才能匯出。
- 高優先：必須有具體說明。
- 標註問題：只提出 correction proposal，不會直接修改 GT 或 annotation。

## 中斷與恢復

關閉瀏覽器或停止 Streamlit 不會清除 SQLite 進度。重新啟動後會回到上次
檢視案例。每 10 次成功儲存建立 backup，最多保留 20 份。

正式 workspace：

```text
G:\Project\FleetVision_Review_Packages\Phase04_5L\
phase04_5l_20260714_v1_review_workspace
```

主要內容：

```text
state\review_state.sqlite3
state\review_events.jsonl
backups\review_state_*.sqlite3
exports\
app_logs\
```

原始正式 package 位於另一個唯讀目錄，workspace 不在 repository 內，也不會
被 Git commit。

## 匯出 completed Workbook

只有 130/130 已完成，且 pending 與 needs_adjudication 均為 0 時執行：

```powershell
cd G:\Project\FleetVision

.\.venv\Scripts\python.exe `
  scripts\phase04_5_export_validation_error_review_app_workbook.py
```

預期分類：

```text
LOCAL_REVIEW_APP_COMPLETED_WORKBOOK_EXPORTED
```

輸出位於：

```text
G:\Project\FleetVision_Review_Packages\Phase04_5L\
phase04_5l_20260714_v1_review_workspace\
exports\
validation_error_human_review_completed.xlsx
```

匯出器會在輸出前建立 SQLite backup，並禁止覆寫既有 completed Workbook。
若需要重新匯出，必須先對既有輸出進行正式封存與治理決策，不可直接刪除後重跑。

## 匯出後驗證

Completed Workbook 不是訓練核准，也不是 deployment acceptance。下一個正式
Gate 仍須使用既有 Phase 04.5L Exporter／Validator 驗證 Workbook 與 canonical
mapping，並由後續治理決定 correction proposal、retraining 或 threshold 分析。

匯出後記錄：

- Completed Workbook 完整路徑。
- SHA256。
- 130 個案例是否全部 `reviewed`。
- Validator classification 與 logical fingerprint。
- Source Workbook 與 frozen package ZIP hashes 是否仍與基準一致。

## 安全邊界

- 原始 batch、Workbook 與 frozen ZIP 不覆寫。
- 不修改 GT、canonical COCO、Registry、raw dataset 或 fixed split。
- 不讀 test split。
- 不重新 inference。
- 不開始 training／fine-tuning。
- 不執行 correction proposal。
- 不把 threshold `0.20` 視為部署門檻。
- completed Workbook 仍須通過既有 Phase 04.5L Exporter 與 Validator。
- `RETRAINING_STATUS` 與 `DEPLOYMENT_ACCEPTANCE` 均維持
  `NOT_YET_APPROVED`。
