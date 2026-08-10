# FleetVision 人工審核介面標準

## 1. 適用範圍

本規範適用於 FleetVision 所有需要人工逐筆判讀、分類、裁決、品質確認、錯誤分析或資料改善建議的工作，包括但不限於：

- 圖片品質與角度複核
- 車損可見性與嚴重度複核
- validation-error root-cause review
- severity／scope boundary review
- annotation candidate／correction proposal review
- perceptual duplicate／near-duplicate review
- 外部資料 intake quality review

任何新 Phase 或 sub-Gate 只要包含多筆人工審核，均必須在設計階段套用本規範；不得等 Vincent 再次提醒。

## 2. 預設作業模式

FleetVision 人工審核的預設模式固定為：

```text
唯讀來源與圖片證據
→ 本機繁體中文 Streamlit 介面
→ SQLite live review state
→ append-only JSONL audit events
→ 定期 SQLite backups
→ 完成條件驗證
→ no-overwrite completed Workbook／CSV export
→ downstream validator／Gate
```

### 強制要求

1. 使用本機 Streamlit 介面，所有使用者可見文字以繁體中文呈現；穩定的 schema value、欄位名稱及程式識別字維持英文。
2. 顯示足以做判斷的原圖、Overlay 或其他證據，並支援案例跳轉、篩選、進度統計與中斷恢復。
3. live review state 必須寫入 SQLite；不得把 Excel 當作主要進度狀態或唯一人工輸入來源。
4. 每次成功儲存必須形成可稽核事件；事件鏡像使用 append-only JSONL 或同等不可靜默改寫的紀錄。
5. 必須按固定間隔建立 SQLite backup，並設定 retention。
6. reviewer 與 timezone-aware reviewed timestamp 由系統自動寫入，不要求操作者手動輸入。
7. active／source／completed artifacts 必須分離；所有正式匯出預設 no-overwrite。
8. 匯出前必須驗證 reviewed、pending、needs_adjudication 等 completion counts。
9. 匯出後必須重新驗證 schema、identity、row order、immutable source fields、SHA256 及必要的圖片／附件完整性。
10. 人工審核不得讀取未授權 test split、重新 inference、修改 annotation／GT／dataset／Registry／fixed splits，或開始 training。

## 3. Excel 的角色

Excel 只允許作為：

- completed export artifact
- 跨人員交換格式
- 無 Python 環境協作者的受控離線 package
- 稽核、封存或主管檢視格式

Excel 不得作為 FleetVision 單人本機人工審核的預設 live state，也不得要求操作者直接修改含大量 schema／identity 欄位的正式 Workbook。

### 受控 Excel 例外

只有在協作者無法執行本機 Streamlit／Python，且該 Gate 明確核准時，才可建立 Excel collaboration package。例外流程仍必須包含：

1. source hash 與 pre-change backup；
2. 明確鎖定可修改欄位；
3. reviewer assignment manifest；
4. identity-key merge；
5. no-overwrite merger；
6. merge 後 validator 與 SHA256；
7. 保留各 reviewer 原始檔。

此例外不得被推廣成後續人工審核的預設模式。

## 4. 設計與實作 Gate

所有新人工審核功能的 design spec／implementation plan 必須明列：

- 是否可復用既有 Streamlit review framework；
- source package 與 immutable evidence；
- UI 欄位、繁中 label 與 controlled values；
- SQLite schema 與 workspace identity；
- save transaction、event log、backup interval／retention；
- progress／filter／resume 行為；
- completed export contract；
- validator 與 downstream Gate；
- failure-no-overwrite 與 recovery；
- test split、inference、annotation、training 安全聲明。

若計畫只提出「直接編輯 Excel」而沒有說明受控例外理由，Start-of-Task Gate 必須阻擋該計畫。

## 5. 最低測試要求

至少涵蓋：

- controlled value 與條件式語意驗證；
- SQLite initialize／save／resume；
- workspace identity mismatch fail-closed；
- audit event continuity；
- backup interval 與 retention；
- navigation／filter／progress；
- incomplete review export blocked；
- completed export no-overwrite；
- source field／row order／identity immutability；
- source／asset／completed artifact hash validation；
- failure cleanup 不留下 partial output；
- existing review workflow regression tests；
- full repository tests at implementation closure。

## 6. 完成證據

人工審核 Gate 不得只以「畫面上看起來完成」宣告 PASS。必須記錄：

- source package path、case count 與 SHA256；
- SQLite path、progress counts 與 backup path；
- completed export path、size 與 SHA256；
- validator classification；
- logical fingerprint 或等效 identity evidence；
- test／inference／annotation／training safety declarations；
- local HEAD、`origin/main`、remote HEAD 與 worktree classification。

## 7. FleetVision 固定原則

```text
HUMAN_REVIEW_DEFAULT_INTERFACE=LOCAL_STREAMLIT_TRADITIONAL_CHINESE
LIVE_REVIEW_STATE=SQLITE
EXCEL_ROLE=EXPORT_EXCHANGE_ARCHIVE_ONLY
DIRECT_EXCEL_REVIEW_DEFAULT=PROHIBITED
REVIEW_RESUME_AND_BACKUP=REQUIRED
REVIEW_AUDIT_TRAIL=REQUIRED
FAILURE_NO_OVERWRITE=REQUIRED
```
