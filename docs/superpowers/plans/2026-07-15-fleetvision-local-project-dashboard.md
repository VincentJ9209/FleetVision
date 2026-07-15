# FleetVision Local Project Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一套 repository-tracked、完全離線、唯讀的 FleetVision 專案治理 Dashboard，清楚分離 formal repository state 與 operational candidate state，並顯示 Phase/Gate、Git、證據、歷史、進度及安全硬閘。

**Architecture:** Dashboard 使用 vanilla HTML、CSS、ES module JavaScript 與兩份分離 JSON。Python validator 以 JSON Schema 與 cross-reference 規則在 commit 前 fail closed；瀏覽器以 runtime structural validation、10 秒 polling、last-valid snapshot fallback 與 safe text rendering 顯示資料。PowerShell 5.1 wrapper 僅啟動 loopback HTTP server，不執行 Git 或資料 mutation。

**Tech Stack:** HTML5、CSS3、ES2022 modules、Python 3.10+、jsonschema 4.x、pytest、Node.js built-in test runner（可選開發驗證）、PowerShell 5.1、Git。

## Global Constraints

- Repository root: `G:\Project\FleetVision`.
- Production branch: `main`.
- Approved base checkpoint: `374b2b99b997810da3e3c2beac0d7174df7c0e5f`.
- Dashboard repository path: `docs/00_project_management/project_dashboard/`.
- Dashboard branch: `feature/local-project-dashboard`.
- Dashboard worktree must be separate from `FleetVision_phase04_5n_implementation_374b2b9`.
- Browser is read-only and may not execute Git, N1, N2, Result ZIP apply, inference, training, or data mutation.
- Local server binds to `127.0.0.1` only.
- No CDN, remote API, remote font, telemetry, bundler, or runtime Node dependency.
- `project_status.json` and `project_history.json` remain separate from UI assets.
- Large ZIPs, extracted evidence, images, model files, databases, caches, and local backups remain outside Git.
- `outputs/metadata/external_assets/` must not be staged, committed, cleaned, moved, or rewritten.
- `N1_EXECUTED=NO` and `N2_EXECUTED=NO` throughout this implementation.
- `CANONICAL_COCO_MODIFIED=NO`, `DATASET_MODIFIED=NO`, `REGISTRY_MODIFIED=NO`, `FIXED_SPLITS_MODIFIED=NO`.
- `TRAINING_STARTED=NO`, `RETRAINING_STATUS=NOT_YET_APPROVED`, `DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED`.

---

## Planned File Structure

### Design and plan

- `docs/superpowers/specs/2026-07-15-fleetvision-local-project-dashboard-design.md`
- `docs/superpowers/plans/2026-07-15-fleetvision-local-project-dashboard.md`

### Dashboard

- `docs/00_project_management/project_dashboard/README.md`
- `docs/00_project_management/project_dashboard/index.html`
- `docs/00_project_management/project_dashboard/assets/dashboard.css`
- `docs/00_project_management/project_dashboard/assets/dashboard.js`
- `docs/00_project_management/project_dashboard/assets/icons.svg`
- `docs/00_project_management/project_dashboard/data/project_status.json`
- `docs/00_project_management/project_dashboard/data/project_history.json`
- `docs/00_project_management/project_dashboard/schemas/project_status.schema.json`
- `docs/00_project_management/project_dashboard/schemas/project_history.schema.json`

### Scripts and dependencies

- `scripts/validate_project_dashboard_data.py`
- `scripts/serve_project_dashboard.ps1`
- `docs/01_phase_guides/fleetvision_local_project_dashboard.md`
- Modify `pyproject.toml` to add `jsonschema>=4.23,<5`.
- Modify `requirements.txt` to add `jsonschema>=4.23,<5`.

### Tests

- `tests/test_project_dashboard_data.py`
- `tests/test_project_dashboard_static.py`
- `tests/test_project_dashboard_js.py`
- `tests/js/project_dashboard.test.mjs`

---

### Task 1: Lock schemas, validator interfaces, and dependencies

**Files:**
- Create: `docs/00_project_management/project_dashboard/schemas/project_status.schema.json`
- Create: `docs/00_project_management/project_dashboard/schemas/project_history.schema.json`
- Create: `scripts/validate_project_dashboard_data.py`
- Modify: `pyproject.toml`
- Modify: `requirements.txt`
- Test: `tests/test_project_dashboard_data.py`

**Interfaces:**
- `canonical_json_bytes(value: object) -> bytes`
- `compute_snapshot_id(document: dict[str, object]) -> str`
- `validate_dashboard_data(status_path: Path, history_path: Path, status_schema_path: Path, history_schema_path: Path) -> ValidationSummary`
- CLI: `python scripts/validate_project_dashboard_data.py --dashboard-root <path> --json`

- [ ] **Step 1: Write failing tests for valid documents, duplicate IDs, unknown references, required safety gates, and snapshot fingerprints.**

```python
def test_valid_dashboard_documents_pass(dashboard_paths):
    summary = validate_dashboard_data(**dashboard_paths)
    assert summary.status == "PASS"


def test_duplicate_gate_id_blocks(dashboard_paths):
    status = load_status(dashboard_paths["status_path"])
    status["gates"].append(status["gates"][0])
    write_status_with_fingerprint(dashboard_paths["status_path"], status)
    with pytest.raises(DashboardValidationError, match="duplicate gate_id"):
        validate_dashboard_data(**dashboard_paths)
```

- [ ] **Step 2: Run the focused tests and confirm RED because the validator module and schemas do not exist.**

Run:

```text
pytest tests/test_project_dashboard_data.py -q
```

Expected: collection/import failure for `validate_project_dashboard_data.py`.

- [ ] **Step 3: Add `jsonschema>=4.23,<5` to both dependency files.**

- [ ] **Step 4: Implement Draft 2020-12 schemas with `additionalProperties: false`, enums, required fields, progress bounds, source references, safety gates, evidence and timeline contracts.**

- [ ] **Step 5: Implement the Python validator with deterministic fingerprint verification and cross-reference checks.**

The validator must reject:

```text
duplicate phase/gate/evidence/event IDs
unknown phase/gate/evidence references
missing source_refs
progress outside 0..100
missing safety gate keys
Result ZIP evidence without DO_NOT_COMMIT
history ordering regression
duplicate history event IDs
formal/candidate authority conflict
snapshot fingerprint mismatch
```

- [ ] **Step 6: Run the focused tests and confirm GREEN.**

```text
pytest tests/test_project_dashboard_data.py -q
```

Expected: all tests pass.

---

### Task 2: Create repository-backed current-state and history snapshots

**Files:**
- Create: `docs/00_project_management/project_dashboard/data/project_status.json`
- Create: `docs/00_project_management/project_dashboard/data/project_history.json`
- Modify tests: `tests/test_project_dashboard_data.py`

**Interfaces:**
- Status snapshot includes phases, gates, evidence, Git facts, candidate worktrees, current focus, warnings, and safety gates.
- History snapshot includes immutable ordered events and correction-event support.

- [ ] **Step 1: Add a test that loads the committed snapshots and checks the complete minimum Phase/Gate inventory.**

Required IDs include:

```text
PHASE_00, PHASE_01, PHASE_02, PHASE_03, PHASE_03_5, PHASE_04,
PHASE_04_5, PHASE_05, PHASE_06, PHASE_07, PHASE_08, PHASE_09,
PHASE_10, FUTURE_EXTENSIONS,
04.5M-0, 04.5M-1, 04.5M-2, 04.5N-1, 04.5N-2
```

- [ ] **Step 2: Run the inventory test and confirm RED because data files are absent.**

- [ ] **Step 3: Create the initial status snapshot.**

Represent:

```text
formal main HEAD=374b2b99...
production worktree invariant=PASS
04.5N candidate worktree=WORKTREE_VERIFIED
66/66 and 98/98 test counts=OPERATOR_REPORTED
implementation committed=false
push completed=false
N1/N2 not executed
```

- [ ] **Step 4: Create append-only history events from Phase 00 through the 04.5N design/plan checkpoint.**

- [ ] **Step 5: Compute and write deterministic `snapshot_id` values using the validator helper.**

- [ ] **Step 6: Run the data validator and focused tests.**

```text
python scripts/validate_project_dashboard_data.py --dashboard-root docs/00_project_management/project_dashboard --json
pytest tests/test_project_dashboard_data.py -q
```

Expected: PASS.

---

### Task 3: Build semantic HTML and accessible styling

**Files:**
- Create: `docs/00_project_management/project_dashboard/index.html`
- Create: `docs/00_project_management/project_dashboard/assets/dashboard.css`
- Create: `docs/00_project_management/project_dashboard/assets/icons.svg`
- Test: `tests/test_project_dashboard_static.py`

**Interfaces:**
- DOM IDs consumed by JavaScript:
  - `dashboard-root`, `status-message`, `search-input`, `filter-controls`
  - `overview-grid`, `phase-navigation`, `gate-list`
  - `current-focus`, `git-panel`, `safety-panel`
  - `evidence-table-body`, `history-timeline`, `warning-list`

- [ ] **Step 1: Write static tests for semantic landmarks, CSP, local-only assets, no embedded authoritative JSON, focus states, reduced motion, and loopback guidance.**

- [ ] **Step 2: Run static tests and confirm RED.**

- [ ] **Step 3: Create `index.html` with semantic header/nav/main/aside/sections, Traditional Chinese labels, accessible controls, and external local assets only.**

- [ ] **Step 4: Create responsive CSS optimized for a 27-inch desktop and usable at narrow widths.**

- [ ] **Step 5: Add an SVG symbol sprite with status, warning, evidence, Git, and timeline icons.**

- [ ] **Step 6: Run static tests and confirm GREEN.**

---

### Task 4: Implement runtime validation, rendering, search, filters, and refresh

**Files:**
- Create: `docs/00_project_management/project_dashboard/assets/dashboard.js`
- Create: `tests/js/project_dashboard.test.mjs`
- Create: `tests/test_project_dashboard_js.py`

**Interfaces:**
- Exports:
  - `validateStatusDocument(document) -> string[]`
  - `validateHistoryDocument(document, statusDocument) -> string[]`
  - `computeHardGateSummary(safetyGates) -> {level, label}`
  - `filterGateRecords(gates, phasesById, query, statusFilter) -> Gate[]`
  - `formatTaipeiTimestamp(value) -> string`
- Browser bootstrap runs only when `document` exists.

- [ ] **Step 1: Write Node tests for structural validation, hard-gate trust behavior, query matching, status filtering, and history reference rejection.**

- [ ] **Step 2: Run `node --test tests/js/project_dashboard.test.mjs` and confirm RED.**

- [ ] **Step 3: Implement pure exported functions without DOM dependencies.**

- [ ] **Step 4: Implement safe rendering using `textContent`, `createElement`, and local SVG references only.**

- [ ] **Step 5: Implement 10-second cache-disabled polling, fingerprint comparison, last-valid snapshot retention, exponential backoff capped at 60 seconds, and UI-state preservation.**

- [ ] **Step 6: Run Node and pytest wrapper tests.**

```text
node --test tests/js/project_dashboard.test.mjs
pytest tests/test_project_dashboard_js.py -q
```

Expected: PASS; pytest may SKIP only when Node is unavailable.

---

### Task 5: Add loopback server wrapper and operator documentation

**Files:**
- Create: `scripts/serve_project_dashboard.ps1`
- Create: `docs/00_project_management/project_dashboard/README.md`
- Create: `docs/01_phase_guides/fleetvision_local_project_dashboard.md`
- Modify: `tests/test_project_dashboard_static.py`

**Interfaces:**
- PowerShell parameters:
  - `[int]$Port = 8765`
  - `[string]$ProjectRoot`
  - `[switch]$NoBrowser`
- Executes:
  - `python -m http.server <port> --bind 127.0.0.1 --directory <dashboard-root>`

- [ ] **Step 1: Add failing tests for strict mode, loopback binding, required file checks, no repository mutation commands, and `file://` warning documentation.**

- [ ] **Step 2: Implement the PowerShell 5.1 wrapper with one consolidated preflight/result block and foreground server execution.**

- [ ] **Step 3: Write Dashboard README and phase guide covering validation, start/stop, JSON update process, trust model, safety boundaries, and troubleshooting.**

- [ ] **Step 4: Run static tests and Python compile checks.**

```text
pytest tests/test_project_dashboard_static.py -q
python -m py_compile scripts/validate_project_dashboard_data.py
```

Expected: PASS.

---

### Task 6: Browser smoke verification and closure checks

**Files:**
- No production-file changes expected unless smoke verification identifies a defect.

**Interfaces:**
- Serve with Python loopback HTTP.
- Verify with headless Chromium when available.

- [ ] **Step 1: Run all focused Dashboard tests.**

```text
pytest tests/test_project_dashboard_data.py tests/test_project_dashboard_static.py tests/test_project_dashboard_js.py -q
node --test tests/js/project_dashboard.test.mjs
```

- [ ] **Step 2: Start a temporary loopback server and verify HTTP 200 for HTML, CSS, JS, status JSON, and history JSON.**

- [ ] **Step 3: Run headless Chromium and verify the rendered DOM contains Phase cards, current focus, safety hard gate, evidence rows, and timeline events.**

- [ ] **Step 4: Validate JSON and run compile/static safety scans.**

```text
python scripts/validate_project_dashboard_data.py --dashboard-root docs/00_project_management/project_dashboard --json
python -m py_compile scripts/validate_project_dashboard_data.py
```

- [ ] **Step 5: Run relevant repository regression tests and full suite in the real isolated FleetVision worktree.**

```text
pytest -q
```

- [ ] **Step 6: Verify exact changed paths, `git diff --check`, no large ZIPs, and protected assets untouched.**

- [ ] **Step 7: Commit exact allowlisted files on `feature/local-project-dashboard`, push the branch, and verify remote branch HEAD only when local tests pass.**

---

## Completion Classification

Implementation closure may use:

```text
OUTCOME=PASS
CLASSIFICATION=FLEETVISION_LOCAL_PROJECT_DASHBOARD_IMPLEMENTED_TESTED_AND_BRANCH_PUBLISHED
DASHBOARD_LOADS_FROM_LOCALHOST=YES
LOOPBACK_ONLY=YES
INTERNET_DEPENDENCY=NO
FORMAL_AND_CANDIDATE_STATE_SEPARATE=YES
JSON_SCHEMA_VALIDATION=PASS
RUNTIME_STRUCTURAL_VALIDATION=PASS
N1_EXECUTED=NO
N2_EXECUTED=NO
CANONICAL_COCO_MODIFIED=NO
DATASET_MODIFIED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```

If branch publication cannot be completed, use the narrower truthful classification:

```text
FLEETVISION_LOCAL_PROJECT_DASHBOARD_RELEASE_CANDIDATE_VERIFIED_NOT_APPLIED
```
