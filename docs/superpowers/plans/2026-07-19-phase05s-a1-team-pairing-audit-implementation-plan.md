# FleetVision Phase 05S-A1 Team Pairing Audit Implementation Plan

> **Gate:** `PHASE_05S_A2_IMPLEMENTATION_PLAN`
> **Plan status:** Approved by Vincent on 2026-07-19
> **Repository checkpoint:** `6693f0d978b839713636288175cd8dca74172416`
> **Implementation authorization:** Not granted
> **Image scan authorization:** Not granted
> **Frozen Test access:** Prohibited

**Goal:** 建立一套本機、可復原、可稽核的 Team Pairing Audit 流程，把 `dataset/01_raw/04_team` 的未整理照片轉成 capture-batch 與 before／after 配對候選，經繁體中文 Streamlit＋SQLite 人工確認後，輸出可靠的 `NO_NEW_DAMAGE`／`EXISTING_DAMAGE_UNCHANGED` 展示案例。

**Architecture:** 採用「唯讀 inventory builder → candidate batch/contact sheet builder → Streamlit/SQLite review workspace → pair candidate engine → no-overwrite completed export」五層架構。沿用既有 Phase 04.5M 與 severity-scope review 工具的安全模式，但不重構或修改既有審核工具；A1 建立獨立、聚焦的模組，以避免七天專題時程內引入跨 Phase regression。

**Tech stack:** Python 3.10+、Pillow、NumPy、pandas、PyYAML、SQLite、Streamlit、openpyxl、pytest、Windows PowerShell 5.1。

## Global Constraints

- Repository root：`G:\Project\FleetVision`
- Production branch：`main`
- Source：`dataset/01_raw/04_team`
- Source 全程唯讀；不得移動、重新命名、刪除、覆蓋、重編碼或修改 EXIF。
- 不在 `dataset/01_raw` 下寫入任何檔案。
- 所有 generated outputs 位於 `outputs/phase05s/team_pairing_audit`，預設不 commit。
- Frozen Test 不搜尋、不列舉、不讀取、不雜湊、不調參。
- 本 Phase 不訓練、不 fine-tune、不執行 Damage Detector、不進行 before／after 車損模型比較。
- 本工具是 Internal Pair Review Utility，不是 Dashboard，不包含使用者登入、權限、通知、雲端部署或多人即時協作。
- Excel 只作 completed export／exchange／archive；live review state 固定為 SQLite。
- 使用者可見文字使用繁體中文；schema、欄位、controlled values 與程式識別字使用英文。
- 測試只使用 `tmp_path` 與合成圖片，不得讀取 `dataset/01_raw/04_team`。
- A3 implementation 完成前不得掃描 319 張正式圖片；正式掃描必須在獨立 A4 controlled-run Gate 授權。
- `outputs/metadata/external_assets/` 維持 `KNOWN_PREEXISTING_UNTRACKED_OUTPUT`；不得 stage、delete、move 或 modify。
- `phase00_init_project.py --validate` 的七項 legacy YOLO 缺失屬 `KNOWN_PREEXISTING_VALIDATOR_DRIFT`，不作為 A1 acceptance blocker，也不得建立假目錄修補。

---

## 1. Design Reconciliation Decisions

implementation 前先以 docs-only checkpoint 修正 tracked design 的三項文字衝突。

### 1.1 Review UI scope

將 design 的 out-of-scope：

`Dashboard and review UI`

修正為：

`Dashboard and final-product operational UI`

明確保留以下項目在 A1 scope：

- Traditional Chinese Streamlit Internal Pair Review Utility
- SQLite live state
- append-only JSONL audit events
- backup／resume
- completed CSV／JSON／XLSX export

### 1.2 Angle review surface

將「Excel review workbook must permit angle values」修正為：

- Streamlit 使用 controlled angle values；
- SQLite 保存 live review state；
- completed XLSX 只匯出已保存結果；
- 不允許直接以 Excel 作主要人工審核。

### 1.3 Validation boundary

移除「Phase 00 validator 必須 PASS」作為 A1 acceptance criterion，改為：

- A1 targeted tests PASS；
- existing review regression tests PASS；
- full pytest suite於 implementation closure 執行；
- `git diff --check` PASS；
- exact changed-path allowlist PASS；
- protected assets 未變更；
- Phase 00 legacy drift 只記錄，不建立 legacy dataset 目錄。

---

## 2. Selected Implementation Approach

### 2.1 Chosen approach

採用 **A1-specific modules following proven review patterns**：

- 參考 Phase 04.5M／severity-scope 的 SQLite、audit、backup、Streamlit、export 模式；
- 不修改既有 `annotation_correction_review_*` 或 `severity_scope_review_*` 模組；
- 不在本期抽象化大型 generic review framework；
- 僅在 A1 模組內重用既有小型 helper 或安全慣例。

### 2.2 Rejected alternatives

**直接延伸 Phase 04.5M app：不採用。**
其資料契約固定為兩筆 annotation correction cases，強行擴充會混入 bbox、GT、prediction 等不相關語意。

**先重構共用 review framework：不採用。**
雖可減少重複，但會同時影響多個已驗證工作流，增加 regression 與時程風險。

**Excel live review：禁止。**
不符合 HUMAN_REVIEW_INTERFACE_STANDARD 與使用者核准。

---

## 3. Planned File Boundary

### 3.1 Docs-only A2 checkpoint

**Create**

- `docs/superpowers/plans/2026-07-19-phase05s-a1-team-pairing-audit-implementation-plan.md`

**Modify**

- `docs/01_phase_guides/phase_05s_a1_team_pairing_audit_design.md`
- `docs/00_project_management/PROJECT_STATUS.md`
- `docs/00_project_management/HANDOFF_CURRENT.md`
- `docs/00_project_management/NEW_CHAT_BOOTSTRAP.md`
- `docs/00_project_management/phase_logs/PHASE_05S_LOG.md`（new，preferred）

`MASTER_PHASE_MAP.md` 僅在 Gate 結構需要改變時修改；本計畫預設沿用既有 05S-A1／A2／A3／A4 結構，因此不修改。
`DECISION_LOG.md` 不新增 ADR，因本計畫只落實已存在 DEC-05S-001～006 與 ADR-017／018。

### 3.2 A3 implementation files

**Create**

- `configs/data/team_pairing_audit_config.yaml`
- `src/fleetvision/data/team_pairing_audit.py`
- `src/fleetvision/review/team_pairing_review_mapping.py`
- `src/fleetvision/review/team_pairing_review_state.py`
- `src/fleetvision/review/team_pairing_review_app.py`
- `src/fleetvision/review/team_pairing_review_export.py`
- `scripts/phase05s_build_team_pairing_audit.py`
- `scripts/phase05s_run_team_pairing_review_app.py`
- `scripts/phase05s_export_team_pairing_review.py`
- `scripts/phase05s_build_team_pairing_audit.ps1`
- `scripts/phase05s_launch_team_pairing_review_app.ps1`
- `scripts/phase05s_export_team_pairing_review.ps1`
- `tests/team_pairing_audit_fixtures.py`
- `tests/test_team_pairing_audit.py`
- `tests/test_team_pairing_review_mapping.py`
- `tests/test_team_pairing_review_state.py`
- `tests/test_team_pairing_review_app.py`
- `tests/test_team_pairing_review_export.py`
- `docs/01_phase_guides/phase_05s_a1_team_pairing_audit.md`

**Modify**

- `.gitignore`
- `docs/00_project_management/PROJECT_STATUS.md`
- `docs/00_project_management/HANDOFF_CURRENT.md`
- `docs/00_project_management/phase_logs/PHASE_05S_LOG.md`
- `docs/00_project_management/NEW_CHAT_BOOTSTRAP.md`

### 3.3 Files explicitly not modified

- `dataset/01_raw/**`
- Frozen Test definitions or paths
- existing Phase 04.5M／severity-scope review modules
- model configs、weights、notebooks
- Dashboard files
- first-stage App files
- Registry、canonical COCO、annotations、fixed splits
- `scripts/phase00_init_project.py`

---

## 4. Output Workspace Contract

每次正式 builder 執行建立 no-overwrite workspace：

```text
outputs/phase05s/team_pairing_audit/
└── workspaces/
    └── team_pairing_audit_<YYYYMMDD_HHMMSS>_<run8>/
        ├── source/
        │   ├── source_snapshot_before.json
        │   ├── source_snapshot_after.json
        │   └── source_snapshot_verification.json
        ├── candidates/
        │   ├── team_image_inventory.csv
        │   ├── team_capture_batch_candidates.csv
        │   ├── team_capture_batch_members.csv
        │   ├── team_before_after_pair_candidates.csv
        │   └── candidate_manifest.json
        ├── contact_sheets/
        │   └── <batch_id>.jpg
        ├── review/
        │   ├── team_pair_review.sqlite
        │   ├── team_pair_review.sqlite-wal
        │   ├── team_pair_review.sqlite-shm
        │   ├── team_pair_review_events.jsonl
        │   └── backups/
        ├── exports/
        │   └── completed_<YYYYMMDD_HHMMSS>/
        │       ├── team_image_inventory.csv
        │       ├── team_capture_batch_candidates.csv
        │       ├── team_image_reviews_completed.csv
        │       ├── team_before_after_pair_candidates.csv
        │       ├── team_pair_review_completed.xlsx
        │       ├── team_pairing_summary.json
        │       └── SHA256SUMS.csv
        └── logs/
```

規則：

- workspace 路徑必須位於 project root 內的指定 output root。
- output path 若解析至 `dataset/01_raw` 或 Frozen Test 相關範圍，立即 fail closed。
- 同名 workspace／completed export 不覆蓋。
- partial export 發生錯誤時必須清除 staging directory，不留下半成品。
- generated artifacts 全部 untracked。

---

## 5. Data Contracts

### 5.1 Deterministic IDs

- `image_id`：`team_` 加上 normalized relative path 的 SHA256 前 20 hex；不得使用 row number。
- `batch_id`：`batch_` 加上排序後 image IDs、selected times 與 batch-gap config fingerprint 的 SHA256 前 20 hex。
- `pair_candidate_id`：`pair_` 加上 before batch ID、after batch ID 與 pairing config fingerprint 的 SHA256 前 20 hex。
- 所有 ordering 固定使用 normalized relative path、selected capture time、filename 作 deterministic tie-break。

### 5.2 Inventory contract

`team_image_inventory.csv` 依 approved design 保留全部 required columns，並增加：

- `inventory_sequence`
- `capture_time_parse_warning`
- `source_snapshot_sha256`
- `representative_for_exact_group`
- `eligible_for_batch_candidate`

Unreadable 圖片仍保留一列，但：

- `is_readable = false`
- 不參與 perceptual hash、batch、contact sheet 或 pair candidate
- error 寫入 `read_error`
- 不使全批次停止，除非 unreadable rate 超過 config threshold

### 5.3 Perceptual hash

- 使用 Pillow＋NumPy 實作 deterministic 64-bit pHash，不新增 dependency。
- 預設 Hamming distance threshold：`6`。
- exact duplicate 先以 SHA256 分組。
- near duplicate 只標示 candidate group，不自動刪除、不自動排除 confirmed pair。
- 319 張規模允許 deterministic O(n²) 比對。
- group 建立規則必須避免不透明 transitive chain；以 stable representative 為中心建立 advisory group。

### 5.4 Timestamp selection

優先序固定：

1. EXIF `DateTimeOriginal`
2. EXIF `DateTimeDigitized`
3. 其他有效 EXIF datetime
4. filesystem creation time
5. filesystem modified time
6. missing／invalid → manual review

每張圖保存原始值、parse 結果、selected source、selected capture time、confidence 與 warning。
不得將 filesystem timestamp 宣稱為實際拍攝時間，只能標記為 fallback。

### 5.5 Capture batch candidates

- 依 selected capture time 排序。
- adjacent gap `> 10 minutes` 開新 candidate batch。
- 不跨 calendar date 自動合併。
- missing／low-confidence time 隔離成 review-required candidates。
- exact duplicate group 預設僅使用 representative 建 candidate，但所有 duplicate member 保留於 membership table。
- `team_capture_batch_members.csv` 保存 batch-to-image 關係，避免把 image list 塞入單一 CSV cell。

### 5.6 Batch review controlled values

`manual_batch_status`：

- `pending`
- `confirmed`
- `split_required`
- `merge_required`
- `exclude`
- `uncertain`

`manual_stage`：

- `before`
- `after`
- `unknown`

`manual_vehicle_id`：

- 使用者建立的內部代碼，例如 `TEAMCAR-001`
- 不要求 OCR
- 不將車牌作 hard dependency
- UI 可從既有 vehicle IDs 選取或建立新 ID
- trim、uppercase、controlled pattern validation

A1 不實作複雜 interactive split／merge editor。
`split_required` 與 `merge_required` 是終端 audit disposition，該 batch 不進入 pair generation。若 A4 run 顯示大量 batch 無法使用，再開獨立 correction Gate。

### 5.7 Image angle review

只要求 `confirmed` batch 中、可能參與 pair generation 的 readable representative images完成 angle label。

Controlled values：

- `front_left`
- `front_right`
- `rear_left`
- `rear_right`
- `front`
- `rear`
- `left_side`
- `right_side`
- `closeup`
- `interior`
- `other`
- `unknown`

Human angle label 為 confirmed pair 的唯一權威來源。

### 5.8 Pair candidate rules

pair engine 只使用：

- `manual_batch_status = confirmed`
- 相同 `manual_vehicle_id`
- 一個 `before`、一個 `after`
- after start time 晚於 before end time
- 預設同 calendar date
- elapsed time ≤ 12 hours
- 至少一個有效 angle overlap
- 優先排序 four-angle overlap 較高者

不自動確認 pair。

### 5.9 Pair review controlled values

`manual_pair_status`：

- `pending`
- `confirmed`
- `rejected`
- `uncertain`

`manual_existing_damage_visible`：

- `yes`
- `no`
- `uncertain`

`manual_new_damage_status`：

- `none`
- `suspected`
- `uncertain`

`manual_demo_role`：

- `none`
- `primary`
- `backup`

Derived case classification：

- confirmed + existing=`no` + new=`none` → `NO_NEW_DAMAGE`
- confirmed + existing=`yes` + new=`none` → `EXISTING_DAMAGE_UNCHANGED`
- confirmed + new=`suspected` → `NEW_DAMAGE_CANDIDATE`
- 其他不確定組合 → `MANUAL_REVIEW_REQUIRED`

A1 不宣稱模型已完成 damage comparison；以上為 team-known outcome 的人工確認案例分類。

---

## 6. SQLite Review-State Contract

### 6.1 Tables

- `workspace_metadata`
- `source_images`
- `candidate_batches`
- `batch_members`
- `batch_reviews`
- `image_reviews`
- `pair_candidates`
- `pair_reviews`
- `app_state`
- `audit_events`
- `export_history`

### 6.2 Workspace identity

SQLite initialize 必須鎖定：

- schema version
- project root
- source root
- candidate manifest SHA256
- inventory SHA256
- batch candidates SHA256
- batch members SHA256
- config SHA256
- reviewer
- timezone
- expected image／batch counts

既有 database identity 與目前 workspace 不一致時 fail closed，不可靜默重建或覆蓋。

### 6.3 Transaction behavior

每次 batch／image／pair save：

1. `BEGIN IMMEDIATE`
2. 驗證 controlled values 與 immutable identity
3. revision +1
4. 更新 review row
5. 插入 audit event
6. commit
7. 同步 append-only JSONL
8. 依 backup interval建立 SQLite backup
9. 驗證 event ID continuity

預設：

- backup every 10 successful saves
- retention 20
- completed export 前強制建立一次 final backup

### 6.4 Resume and filters

UI 支援 batch review／pair review mode、pending／confirmed／uncertain／excluded filter、vehicle filter、stage filter、current case persistence、previous／next navigation、progress counts 與 last viewed item resume。

---

## 7. Streamlit UI Contract

### 7.1 Top-level screens

1. **批次審核**
   - contact sheet
   - batch metadata
   - member thumbnails
   - vehicle ID
   - before／after
   - batch status
   - notes

2. **角度標記**
   - selected batch images
   - one image at a time
   - controlled angle
   - duplicate／readability evidence
   - save and next

3. **前後配對**
   - before and after contact sheets side by side
   - elapsed time
   - overlap angles
   - existing damage visible
   - new damage status
   - pair decision
   - demo role
   - notes

4. **完成狀態**
   - total／terminal／pending counts
   - unresolved split／merge／uncertain counts
   - confirmed pairs
   - primary／backup demo cases
   - export readiness

### 7.2 UI safety

- 只 bind `127.0.0.1`
- 不提供 upload、delete、rename、move、EXIF edit
- 不顯示 Frozen Test 路徑
- 不呼叫外部 API
- 不執行 OCR
- 不執行模型 inference
- image preview 使用 source read-only path
- source path 必須位於 approved `04_team` root
- missing source image 時顯示 blocking evidence，不自動修復

---

## 8. Completed Export Contract

### 8.1 Export readiness

completed export 需同時符合：

- 所有 candidate batches 不再是 `pending`
- 所有 confirmed batches 有 vehicle ID 與 stage
- 所有用於 pair overlap 的 required images 有 angle label
- 所有 generated pair candidates 不再是 `pending`
- confirmed pairs ≥ 3
- primary demo pair = 1
- primary pair derived classification 為 `NO_NEW_DAMAGE` 或 `EXISTING_DAMAGE_UNCHANGED`
- blocking unresolved count = 0
- SQLite integrity check = `ok`
- audit event continuity PASS
- final backup created
- source snapshot before／after byte SHA256 完全一致

`split_required`、`merge_required`、`exclude`、`uncertain` 可保留於 completed audit，但不進入 confirmed pairs。

### 8.2 XLSX sheets

`team_pair_review_completed.xlsx`：

- `執行摘要`
- `圖片清單`
- `候選批次`
- `批次成員`
- `圖片角度`
- `配對候選`
- `確認案例`
- `稽核資訊`

XLSX 只作 completed export，無 live input requirement，不含公式依賴，且不得覆蓋既有 completed export。

### 8.3 Summary JSON

至少記錄：

- run ID／timestamps
- repository commit
- config path／SHA256
- source／output roots
- source count and snapshot verification
- readable／unreadable
- timestamp source distribution
- exact／near duplicate counts
- candidate／terminal batch counts
- angle review counts
- pair candidate／confirmed counts
- derived classification distribution
- primary／backup demo IDs
- warnings
- Frozen Test declaration
- training／inference declarations
- artifact paths／sizes／SHA256

---

## 9. Task-by-Task Implementation Sequence

### Task 1 — A2 docs-only design reconciliation and plan checkpoint

**Files**

- Create implementation plan file
- Modify tracked design and governance state files only

**Acceptance**

- 三項 design conflicts 已明確修正
- plan 自我檢查無 placeholder、scope expansion 或矛盾
- no code／config／test files
- no image scan
- `git diff --check` PASS
- exact-path commit／push／remote verification
- final worktree only protected residual

**Suggested commit**

`docs(phase05s): plan A1 team pairing audit implementation`

### Task 2 — Configuration and domain mapping contract

**Implementation requirements**

- parse and validate all config values
- safe relative path checks
- source/output separation checks
- controlled values
- derived pair classification
- vehicle ID normalization
- immutable review fields
- fail-closed errors

**Tests**

- invalid path/config blocked
- controlled values accepted/rejected
- derived classifications exact
- reviewer/timestamp generated by system
- no raw/Frozen Test path accepted

**Suggested commit**

`feat(phase05s): add team pairing audit contracts`

### Task 3 — Read-only inventory, timestamp and duplicate audit

**Implementation requirements**

- supported-extension discovery
- deterministic IDs
- image readability/dimensions
- EXIF timestamp priority
- filesystem fallback
- SHA256／pHash
- exact／near duplicate audit
- before／after source snapshots
- atomic CSV／JSON writes
- no source mutation

**Tests**

- deterministic ordering and IDs
- EXIF priority
- missing/malformed EXIF
- unreadable image handling
- exact/near duplicates
- source bytes unchanged
- output-under-raw blocked
- zero-image source blocked

**Suggested commit**

`feat(phase05s): add read-only team image inventory audit`

### Task 4 — Capture batches and contact sheets

**Implementation requirements**

- 10-minute configurable boundary
- calendar-date isolation
- missing-time isolation
- exact duplicate representative handling
- candidate batch/member CSVs
- deterministic 4-column contact sheets
- atomic no-overwrite output

**Tests**

- exactly 10 minutes remains same batch
- over 10 minutes creates new batch
- date boundary splits
- low-confidence/missing time isolated
- duplicate traceability preserved
- contact sheet labels/order/dimensions
- source images unchanged

**Suggested commit**

`feat(phase05s): add capture batch and contact sheet candidates`

### Task 5 — SQLite review workspace

**Implementation requirements**

- schema/tables listed above
- initialize from verified candidate artifacts
- workspace identity fail-closed
- save/revision/audit transaction
- JSONL continuity
- backup interval/retention
- progress/filter/resume
- SQLite integrity checks

**Tests**

- initialize/save/reopen/resume
- identity mismatch blocked
- revision monotonic
- event continuity
- simulated save rollback
- backup every 10 saves
- retention 20
- no partial/corrupt state accepted

**Suggested commit**

`feat(phase05s): add pairing review SQLite state`

### Task 6 — Batch and image-angle Streamlit review

**Implementation requirements**

- Traditional Chinese UI
- candidate batch navigation/filter
- contact-sheet and thumbnail evidence
- vehicle/stage/status save
- angle review for confirmed candidate images
- terminal status counts
- local-only binding
- no direct Excel editing

**Tests**

- navigation/filter helpers
- pending selection handling
- progress counts
- batch save validation
- angle requirements
- split/merge dispositions excluded from pair eligibility
- runtime session identity

**Suggested commit**

`feat(phase05s): add batch and angle review utility`

### Task 7 — Pair candidate engine and pair review UI

**Implementation requirements**

- generate pairs only from confirmed batches
- same vehicle/before-after/time limit
- angle overlap scoring
- deterministic ranking and IDs
- pair side-by-side evidence
- manual decision and demo role
- derived classification
- only one primary demo pair

**Tests**

- same vehicle required
- correct stage ordering
- elapsed time limit
- date rule
- angle overlap
- non-confirmed batch excluded
- one primary role invariant
- derived output exact
- pair save/resume

**Suggested commit**

`feat(phase05s): add before-after pair review`

### Task 8 — Completed exporter and evidence manifest

**Implementation requirements**

- completion validation
- no-overwrite staging directory
- CSV／JSON／XLSX
- deterministic row order
- immutable source fields
- final source snapshot verification
- SHA256SUMS
- export history
- failure cleanup

**Tests**

- incomplete export blocked
- fewer than 3 confirmed pairs blocked
- missing/duplicate primary demo blocked
- source snapshot mismatch blocked
- no-overwrite
- failure leaves no partial export
- output schema/order/hash
- Excel sheet names and counts

**Suggested commit**

`feat(phase05s): add completed pairing audit exports`

### Task 9 — PowerShell 5.1 operational wrappers and guide

**Implementation requirements**

- `#requires -Version 5.1`
- `Set-StrictMode -Version Latest`
- `$ErrorActionPreference = "Stop"`
- repository/config/workspace preconditions
- `.venv\Scripts\python.exe` verification
- consolidated PASS／BLOCKED result
- no broad Git actions
- no auto-commit/push
- generated outputs ignored

**Suggested commit**

`chore(phase05s): add pairing audit operational workflow`

### Task 10 — A3 implementation closure

**Fresh verification**

```powershell
python -m pytest tests/test_team_pairing_audit.py -q
python -m pytest tests/test_team_pairing_review_mapping.py -q
python -m pytest tests/test_team_pairing_review_state.py -q
python -m pytest tests/test_team_pairing_review_app.py -q
python -m pytest tests/test_team_pairing_review_export.py -q

python -m pytest `
  tests/test_annotation_correction_review_state.py `
  tests/test_annotation_correction_review_app.py `
  tests/test_severity_scope_review_state.py `
  -q

python -m compileall -q src/fleetvision scripts
python -m pytest -q
git diff --check
git status --short
```

PowerShell 5.1 parser check必須涵蓋三個新 wrappers。

**A3 acceptance**

- synthetic tests only
- real `04_team` scan = NO
- Frozen Test access = NO
- training/inference = NO
- existing review regressions PASS
- full pytest PASS
- exact changed-path allowlist
- generated outputs absent or ignored
- governance docs synchronized
- separate explicit authorization required before commit/push

**Suggested final A3 commit**

`feat(phase05s): implement team pairing audit workflow`

---

## 10. A4 Controlled Run Plan — Separately Authorized

A4 不屬於 A3 implementation execution。A3 commit／push／remote verification後，另做 startup reconciliation，才可授權正式掃描。

### A4-01 Read-only inventory run

- verify local／origin／remote sync
- verify worktree clean or protected-untracked-only
- calculate pre-run source snapshot
- run builder against `dataset/01_raw/04_team`
- expected reported count 約 319，但實際 count 以 live scan 為準
- calculate post-run source snapshot
- require byte-preserved PASS
- inspect inventory/batch/contact-sheet summary
- no human review yet
- no commit generated outputs

### A4-02 Human batch／angle／pair review

- launch local Streamlit
- confirm all candidate batches into terminal status
- assign vehicle/stage for confirmed batches
- angle-label eligible images
- generate/refresh pair candidates
- review all pair candidates
- select one primary and at least two backup/confirmed pairs
- stop Streamlit cleanly
- preserve SQLite/JSONL/backups

### A4-03 Completed export and evidence

- final source snapshot compare
- export completed CSV／JSON／XLSX/SHA256
- validate at least 3 confirmed pairs
- prefer 3–5 reliable pairs
- exactly one primary demo
- primary classification `NO_NEW_DAMAGE` or `EXISTING_DAMAGE_UNCHANGED`
- generated outputs remain untracked
- update governance docs with counts/hashes/classification
- exact-path docs/code commit only
- push and remote verification

---

## 11. Explicit Non-Goals

- plate OCR
- vehicle re-identification model
- angle classifier
- automatic pair confirmation
- automatic damage comparison
- Damage Detector retraining
- segmentation
- Dashboard
- first-stage capture App
- cloud deployment
- authentication/permissions
- multi-user concurrency
- operating analytics
- insurance/claim/liability decisions
- Frozen Test access

---

## 12. Risk Controls

| Risk | Control |
|---|---|
| Raw image mutation | pre/post SHA256 snapshot, output-root enforcement, read-only operations |
| Incorrect EXIF assumptions | timestamp source/confidence recorded; filesystem fallback not treated as authoritative |
| Near-duplicate false grouping | conservative pHash threshold; advisory only; no automatic deletion |
| Wrong batch boundaries | candidate-only rule; human terminal disposition |
| Pair leakage across vehicles | confirmed vehicle ID required |
| Excel becoming live state | SQLite-only saves; XLSX generated only by completed exporter |
| Existing review app regression | no refactor; focused regression tests |
| Partial outputs | staging directory + atomic promotion + cleanup |
| Stale workspace | workspace identity and artifact SHA256 fail-closed |
| Protected residual accidentally staged | exact-path stage allowlists |
| Phase 00 drift misdiagnosed | documented pre-existing classification; no fake legacy dirs |
| Scope expansion | A1-specific allowlist and explicit non-goals |

---

## 13. Plan Approval Gate

Approval of this plan authorizes only：

`PHASE_05S_A2_PLAN_DOCUMENT_APPLICATION_AND_CHECKPOINT`

This means：

- apply the docs-only design corrections；
- add the implementation plan file；
- synchronize required governance Markdown；
- run docs/Git verification；
- exact-path commit／push only after separate explicit authorization。

Plan approval does **not** authorize：

- A3 implementation code；
- scanning `dataset/01_raw/04_team`；
- launching Streamlit；
- creating SQLite/output workspaces；
- model training or inference；
- Frozen Test access；
- Dashboard or first-stage App work。
