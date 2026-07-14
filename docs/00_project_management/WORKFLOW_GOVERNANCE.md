# FleetVision Workflow Governance

## 1. 核心原則

FleetVision 不依賴聊天記憶推進。

正式真相來源：Git Repository、Project Context、Project Status、Master Phase Map、Decision Log、Data Registry、測試與輸出稽核。

任何只存在對話、未寫入文件與 Git 的重大決策，視為尚未正式生效。

## 2. 每個任務的標準循環

1. Context Check
2. Goal Check
3. Dependency Check
4. Safe Implementation
5. Test
6. Output Audit
7. Documentation Update
8. Git Checkpoint
9. Next-phase Gate

### Context Check 必查

- Project root
- branch
- worktree
- current Phase／subphase
- latest checkpoint
- immutable architecture
- protected formal outputs

### Safe Implementation 原則

- 原始資料唯讀
- 正式輸出預設不覆寫
- 先 TEMP smoke test，再正式產出
- 多人結果以 identity key 合併
- 所有人工結果先備份

### Test 至少依任務執行

- Targeted tests
- Regression tests
- Full tests
- `git diff --check`
- data count／schema／file existence audit
- formula／link audit
- failure no-overwrite audit

### Documentation Update

判斷是否更新：Project Status、Master Phase Map、Decision Log、Phase guide、external registry、model card／experiment record。

## 3. Codex 任務模式

每個 Codex prompt 必須包含：

```text
Context Lock
- Project:
- Project root:
- Current Phase:
- Current status:
- Immutable architecture:
- Data imbalance strategy:
- External data status:
- In scope:
- Out of scope:
- Files allowed:
- Formal outputs protected:
- Acceptance criteria:
- Required tests:
- Required document updates:
- Commit/push permission:
```

模式：小型明確修改直接送出；多檔且驗收明確用 Goal；架構不明用 Plan。資料切分、合併、去重、實驗設計使用 High。

## 4. Colab／Notebook 規範

每個儲存格開頭標註：儲存格編號、操作類型、插入或覆蓋位置、主要目的、執行前提、重點、驗收標準。

每次只進行一個清楚步驟，不假設使用者知道執行順序。

## 5. 資料治理規範

- `dataset/01_raw/` 唯讀
- 衍生資料可追蹤 source、builder、config、generation date、schema version
- 外部資料先進 Registry 再下載
- 優先 group split
- internal test frozen
- external data 不進 internal test
- 重複與近似圖不得跨 split
- 每次 split 需有 manifest

## 6. 人工審核規範

正式標準見 `docs/00_project_management/HUMAN_REVIEW_INTERFACE_STANDARD.md`。

### 預設模式

- 本機人工審核預設使用繁體中文 Streamlit 介面。
- active progress 使用 SQLite transaction 保存，並支援中斷恢復。
- 每次成功儲存形成 audit event；按設定間隔建立 SQLite backup 並保留 retention。
- reviewer 與 timezone-aware reviewed timestamp 由系統自動寫入。
- 只修改人工欄位；不得修改 review identity、image identity、original path、source bucket、assignment、suggestions 或 canonical order。
- completed Workbook／CSV 使用 no-overwrite exporter 產生，再經 validator 與 SHA256 稽核。
- Excel 僅作 completed export、交換、封存或明確核准的無 Python 協作 package，不作為預設 live review state。

### 受控 Excel 協作例外

協作者無法執行 Python／Streamlit 時，必須由獨立 Gate 核准 Excel collaboration package，並具備：source hash、pre-change backup、可修改欄位鎖定、reviewer assignment、identity-key merge、原始 reviewer 檔保留、no-overwrite merger、post-merge validator 與 SHA256。

```text
HUMAN_REVIEW_DEFAULT_INTERFACE=LOCAL_STREAMLIT_TRADITIONAL_CHINESE
LIVE_REVIEW_STATE=SQLITE
EXCEL_ROLE=EXPORT_EXCHANGE_ARCHIVE_ONLY
DIRECT_EXCEL_REVIEW_DEFAULT=PROHIBITED
```

<!-- FLEETVISION-MANAGED:ONE-SHOT-DELIVERY-GOVERNANCE:BEGIN -->
## 7. 一次性交付與安裝器驗收

對使用者提供的 ZIP、installer、PowerShell 腳本與 correction package，必須先在與
目標 commit 一致的隔離 repository 完成 rehearsal，才能標示為可下載版本。

固定要求：

1. 模擬 Windows Git checkout，涵蓋 CRLF、UTF-8 BOM、EOF 與 PowerShell 5.1。
2. 先執行 path allowlist、`git diff --check`、parser／compile 等低成本檢查。
3. 低成本檢查全部通過後，才執行 focused、regression 與必要的 full suite。
4. 驗證 no-overwrite、transaction rollback、idempotency 與 protected assets。
5. 使用者正式 workspace 不得作為第一個 integration-test environment。
6. 內部 debug build 不交付；使用者只接收通過 rehearsal 的 release candidate。

```text
USER_VISIBLE_ARTIFACT=RELEASE_CANDIDATE_ONLY
TARGET_ENVIRONMENT_REHEARSAL=REQUIRED
CHEAP_CHECKS_BEFORE_FULL_SUITE=REQUIRED
PRODUCTION_WORKSPACE_AS_FIRST_TEST=PROHIBITED
```
<!-- FLEETVISION-MANAGED:ONE-SHOT-DELIVERY-GOVERNANCE:END -->

## 8. 實驗治理規範

每次訓練記錄：experiment_id、git commit、dataset version、manifest、model、weights、seed、imgsz、batch、epochs、patience、augmentations、environment、metrics、artifact paths、notes。

External data 是否有效，只能以 internal validation／test 表現判斷。

## 9. 必須新增 ADR 的變更

- YOLO class 改變
- Detect 改為 Segmentation
- 重新執行 Phase 03.5
- 調整 internal test
- 更換標註定義
- 改變外部資料接受規則
- 改變 group split key
- 改變專案根目錄
- 將理賠判定納入模型輸出
- 擴張到正式生產部署

## 10. 完成聲明

只有在具備 tests output、audit output、expected counts、Git status、local／remote sync 與 updated documentation 時才可宣告完成。

原則：Evidence before assertion。

<!-- FLEETVISION-MANAGED:SCHEME-C:BEGIN -->
## Repository-backed operating model (Scheme C)

### Source of truth

The Git repository is the formal source of truth for:

- operating rules
- current Phase and Gate
- protected assets
- decisions
- current handoff
- phase-level execution history
- artifact paths, counts, and SHA256 values

Chat summaries are convenience copies and must be reconciled against the repository.

### Gate lifecycle

1. **Audit** — read-only or metadata-only inspection; no worktree mutation.
2. **Apply/Execute** — only the explicitly authorized change.
3. **Verify** — check outputs, invariants, protected assets, and Git diff.
4. **Commit** — stage an exact allowlist only.
5. **Push** — push only after verification.
6. **Remote verification** — require local HEAD = `origin/main` = GitHub remote HEAD.
7. **State synchronization** — update `PROJECT_STATUS.md`, `HANDOFF_CURRENT.md`, and the current phase log within the same logical Gate.

### Script standards

- Windows PowerShell 5.1 compatible.
- `Set-StrictMode -Version Latest`.
- `Stop = "Stop"`.
- Fail closed when a precondition is unknown.
- Emit one consolidated result block.
- Avoid recursive hashing of large datasets unless a Gate explicitly requires it.
- Record counts, paths, lineage, timestamps, and SHA256 for governed artifacts.

### Git standards

- Production branch: `main`.
- No force push.
- No broad `git add .` or `git add -A`.
- Stage exact allowlisted paths.
- Never stage the protected external-assets directory.
- Technical changes and documentation state must not contradict each other.
<!-- FLEETVISION-MANAGED:SCHEME-C:END -->

