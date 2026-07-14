# Phase 04.5L 繁體中文 Severity Scope Review App

## 目的

本工具使用本機 Streamlit、SQLite 與繁體中文介面完成 F1 產生的 130 筆 severity-scope 人工審核。F1 的 `severity_scope_review.xlsx` 是唯讀 template／稽核 artifact，不直接作為人工 live state。

## 正式資料流

```text
F1 PASS workspace
→ severity_scope_review_source.csv + scope_asset_manifest.csv
→ Streamlit scope review app
→ scope_review_app/state/scope_review_state.sqlite3
→ scope_review_app/state/scope_review_events.jsonl
→ scope_review_app/backups/
→ severity_scope_review_completed.xlsx
→ F2 validator/findings
```

## 啟動

在 Windows PowerShell 5.1：

```powershell
Set-Location -LiteralPath 'G:\Project\FleetVision'

.\scripts\phase04_5_launch_severity_scope_review_app.ps1
```

預設網址：

```text
http://127.0.0.1:8502
```

launcher 會自動尋找最新的有效 F1 PASS workspace。需要固定 workspace 時可傳入：

```powershell
.\scripts\phase04_5_launch_severity_scope_review_app.ps1 `
  -F1WorkspaceRoot '<F1_WORKSPACE_ROOT>'
```

## 介面功能

- 原圖／Overlay 左右比較或單圖檢視
- 全部、尚未完成、已完成、待裁決、低信心、災難性範圍外篩選
- 上一筆、下一筆、案例跳轉
- completed／pending／needs adjudication 進度
- 繁體中文選項 label，底層 controlled values 保持英文
- 儲存本筆、儲存並下一筆、標記待裁決
- 自動 reviewer `Vincent`
- 自動 Asia/Taipei timezone-aware timestamp
- 每 10 次成功儲存建立 SQLite backup，最多保留 20 份

## 完成條件

```text
reviewed = 130
pending = 0
needs_adjudication = 0
```

待裁決案例必須返回修正為已完成，才能匯出 completed scope Workbook。

## 匯出 Completed Scope Workbook

關閉或保留 Streamlit server 均可，另開 PowerShell 執行：

```powershell
Set-Location -LiteralPath 'G:\Project\FleetVision'

.\scripts\phase04_5_export_severity_scope_review_app_workbook.ps1
```

預期 classification：

```text
LOCAL_SCOPE_REVIEW_APP_COMPLETED_WORKBOOK_EXPORTED
```

正式輸出：

```text
<F1_WORKSPACE_ROOT>\scope_review_app\exports\
severity_scope_review_completed.xlsx
```

同目錄會產生：

```text
scope_review_export_result.json
```

匯出器會：

1. 驗證 130／130 reviewed；
2. 驗證 F1 source CSV、template Workbook、asset manifest SHA256；
3. 建立 pre-export SQLite backup；
4. transactionally 填入 completed Workbook；
5. 驗證 controlled values、conditional rules、identity、row order 與 source fields；
6. 驗證 embedded image count；
7. 禁止覆寫既有 completed output。

## F2 Gate

F2 只接受 `severity_scope_review_completed.xlsx` 與 `scope_review_export_result.json`。F1 原始 `severity_scope_review.xlsx` 必須保持與 F1 checksum manifest 一致；直接修改該檔會使 F2 fail closed。

## 安全邊界

```text
TEST_SPLIT_READ=NO
MODEL_INFERENCE_EXECUTED=NO
ANNOTATION_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```
