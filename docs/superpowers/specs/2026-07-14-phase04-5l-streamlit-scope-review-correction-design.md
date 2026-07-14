# Phase 04.5L Streamlit Scope Review Correction Design

**Status:** APPROVED BY USER — 2026-07-14

## 1. 問題

Phase 04.5L F1 已成功建立 130 筆 severity-scope source、圖片 evidence、template Workbook 與 checksum evidence；但原 findings-analysis design 把後續人工審核描述為直接編輯 Excel。這與 FleetVision 已確認的人工審核模式衝突：本機繁體中文 Streamlit UI、SQLite live state、定期備份與 completed Workbook export。

這個交接缺口會造成：

- 操作者必須直接面對大量英文 schema 欄位；
- Excel 被誤當成 live state；
- 缺少 transaction、resume、audit event 與 deterministic backup；
- F2 無法區分 F1 template 與真正 completed artifact；
- 後續 Phase 可能再次重複相同錯誤。

## 2. 核准架構

採用獨立的 severity-scope review app，復用既有 Phase 04.5L review app 的操作模式，但不混用既有 validation-error domain schema。

```text
F1 immutable outputs
  ├─ severity_scope_review_source.csv
  ├─ scope_asset_manifest.csv
  ├─ severity_scope_review.xlsx (readonly template)
  └─ F1 evidence/checksums
        ↓ verified package loader
Traditional Chinese Streamlit scope-review app
        ↓ transactional save
scope_review_app/state/scope_review_state.sqlite3
scope_review_app/state/scope_review_events.jsonl
scope_review_app/backups/
        ↓ complete 130/130
controlled exporter
        ↓
scope_review_app/exports/severity_scope_review_completed.xlsx
scope_review_app/exports/scope_review_export_result.json
        ↓
F2 scope validator/findings
```

## 3. 設計選擇

### 3.1 採用：scope-specific app，復用既有模式

優點：

- validation-error app 不受 scope schema 影響；
- 可直接沿用本機 Streamlit、SQLite、事件紀錄、backup、filter、resume 模式；
- scope conditional rules 可獨立測試；
- F2 能明確要求 completed artifact。

### 3.2 不採用：直接擴充既有 validation-error app 成多模式

拒絕原因：兩個 domain 欄位、mapping、completion semantics 與 exporter 都不同；混合模式會增加 regression surface。

### 3.3 不採用：直接編輯 Excel

拒絕原因：違反既有人工審核作業模式。Excel 僅保留為 completed export、交換、封存或明確核准的無 Python 協作例外。

## 4. F1 邊界

F1 不重跑。現有 PASS workspace 保持有效。

App 只讀：

- `scope_review/severity_scope_review_source.csv`
- `scope_review/scope_asset_manifest.csv`
- `scope_review/severity_scope_review.xlsx`
- `evidence/f1_gate_result.json`
- `evidence/F1_SHA256SUMS.csv`
- `input_snapshot/extracted_package/` 下的 original／overlay evidence

Package loader 必須驗證：

- F1 PASS classification；
- 130 rows；
- source／template／asset manifest SHA256；
- F1 checksum manifest 全部 immutable outputs；
- 260 asset records，每案 original／overlay 各一；
- asset path 不可 absolute、`..` 或含 test segment；
- asset size／SHA256；
- source identity 唯一、順序固定、scope 初始狀態全部 pending。

## 5. UI

所有 user-facing copy 使用繁體中文。schema value 仍使用英文。

### 5.1 顯示

- original／overlay 左右比較；
- original only／overlay only；
- case index、review_case_id、image_id；
- 既有 validation-error 人工判斷摘要；
- reviewed／pending／needs adjudication progress。

### 5.2 篩選

- 全部案例
- 尚未完成
- 已完成
- 待裁決
- 低信心
- 災難性範圍外

### 5.3 編輯欄位

- scope group
- scope reason
- operability
- scope confidence
- reviewer notes

reviewer 與 reviewed timestamp 由系統自動填入。

### 5.4 動作

- 上一筆
- 儲存本筆
- 儲存並下一筆
- 標記待裁決

## 6. Scope semantics

Controlled values 以 findings config 為權威來源。App mapping 與 F2 validator 必須一致。

強制規則：

- low confidence 需要 notes；
- `other` 需要 notes；
- `insufficient_visual_evidence` 需要 low confidence 與 notes；
- `OUT_OF_SCOPE_CATASTROPHIC` 需要 approved catastrophic reason；
- catastrophic + likely drivable 需要 notes；
- `IN_SCOPE_LIGHT_MODERATE` 不得使用 catastrophic collision／vehicle integrity compromised；
- needs adjudication 需要 notes；
- reviewed timestamp 必須 timezone-aware。

## 7. SQLite state

Workspace：`<F1_ROOT>/scope_review_app/`。

內容：

- `state/scope_review_state.sqlite3`
- `state/scope_review_events.jsonl`
- `backups/scope_review_state_<UTC>.sqlite3`
- `exports/`
- `app_logs/`

Workspace identity 固定：

- F1 workspace root；
- source CSV SHA256；
- template Workbook SHA256；
- asset manifest SHA256；
- case count；
- reviewer；
- timezone。

既有 state identity 不符時 fail closed，不得自動重建或覆寫。

每次 save 為單一 SQLite transaction，revision 遞增並建立 audit event。每 10 次成功 save 建立 backup，保留 20 份。

## 8. Completed exporter

只有：

```text
reviewed=130
pending=0
needs_adjudication=0
```

才可匯出。

Exporter：

1. 重新驗證 F1 source／template／asset manifest；
2. 建立 pre-export backup；
3. 複製 F1 template 到 staging；
4. 依 review_case_id 寫入 8 個 scope fields；
5. 使用既有 `read_scope_workbook`／`validate_scope_dataframe` 驗證；
6. 驗證 source fields、row order、identity 與 embedded image count；
7. atomic rename；
8. 寫出 `scope_review_export_result.json`；
9. 禁止 overwrite。

Classification：

```text
LOCAL_SCOPE_REVIEW_APP_COMPLETED_WORKBOOK_EXPORTED
```

## 9. F2 correction

F2 必須：

- 驗證 F1 checksum manifest 的全部 F1 outputs；不得再把 template Workbook 視為可變動檔案；
- 要求 completed scope Workbook；
- 要求 export result JSON；
- 驗證 completed hash、130／130 counts、source hashes、安全聲明與 classification；
- 使用 completed Workbook 執行 scope CSV export 與 findings；
- 未完成、直接修改 F1 template、缺少 export evidence 或 hash mismatch 均 fail closed。

## 10. 永久治理規範

新增 `HUMAN_REVIEW_INTERFACE_STANDARD.md` 並由 `START_HERE.md`、`AGENTS.md`、`WORKFLOW_GOVERNANCE.md` 引用；同時新增 ADR-017，使此規則成為正式 Active workflow decision。

固定規則：

```text
HUMAN_REVIEW_DEFAULT_INTERFACE=LOCAL_STREAMLIT_TRADITIONAL_CHINESE
LIVE_REVIEW_STATE=SQLITE
EXCEL_ROLE=EXPORT_EXCHANGE_ARCHIVE_ONLY
DIRECT_EXCEL_REVIEW_DEFAULT=PROHIBITED
```

無 Python 協作者只能在明確 Gate 核准後使用受控 Excel collaboration package；不得把例外當作預設。

## 11. 安全邊界

- 不重跑 F1；
- 不執行 F2；
- 不讀 test split；
- 不重新 inference；
- 不修改 annotation／GT／dataset／Registry／fixed splits；
- 不 training／fine-tuning；
- 不修改既有 completed validation-error Workbook；
- 不 stage／commit protected external assets。

## 12. 驗收

- focused scope app tests PASS；
- existing validation-error review app tests PASS；
- findings tests PASS；
- full repository tests PASS；
- PowerShell 5.1 parser scan PASS；
- `git diff --check` PASS；
- exact allowlist only；
- local／origin／remote sync after push；
- F1 workspace remains valid and original template SHA unchanged。
