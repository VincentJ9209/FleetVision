# Phase 04.5L Streamlit Scope Review Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace direct Excel scope review with a Traditional Chinese local Streamlit workflow backed by SQLite, completed-artifact export, and a fail-closed F2 contract, while making this the permanent FleetVision human-review standard.

**Architecture:** Keep F1 outputs immutable. A scope-specific verified package loader feeds a Traditional Chinese Streamlit app whose live state is SQLite plus JSONL audit events and scheduled backups. A no-overwrite exporter produces a completed scope Workbook, and F2 accepts only that completed artifact and evidence.

**Tech Stack:** Python 3.10+, Streamlit, SQLite, pandas, openpyxl, PyYAML, pytest, Windows PowerShell 5.1, Git.

## Global Constraints

- Current implementation base: `0775e003100b432da6e0db2d9b9f200112b1e88f`.
- Do not rerun F1.
- Do not execute F2 during implementation closure.
- Do not modify the existing completed validation-error Workbook.
- Do not read the test split, rerun inference, modify annotation/GT/dataset/Registry/fixed splits, or start training.
- `RETRAINING_STATUS=NOT_YET_APPROVED`.
- `DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED`.
- `outputs/metadata/external_assets/` remains protected untracked content.
- Human-facing UI and guides use Traditional Chinese; schema identifiers remain English.
- Excel is export/exchange/archive only, except an explicitly approved offline collaboration Gate.

---

## File responsibility map

### New production files

- `configs/data/severity_scope_review_app_config.yaml`: static app settings and analysis-root discovery.
- `src/fleetvision/review/severity_scope_review_mapping.py`: controlled values, Traditional Chinese labels, conditional validation, canonical mapping.
- `src/fleetvision/review/severity_scope_review_package.py`: F1 evidence, source, asset and checksum verification.
- `src/fleetvision/review/severity_scope_review_state.py`: SQLite state, audit events, filters, progress, backups and export history.
- `src/fleetvision/review/severity_scope_review_app.py`: runtime helpers and Traditional Chinese Streamlit UI.
- `src/fleetvision/review/severity_scope_review_export.py`: complete-state check and no-overwrite completed Workbook export.
- `scripts/phase04_5_run_severity_scope_review_app.py`: Streamlit subprocess launcher.
- `scripts/phase04_5_launch_severity_scope_review_app.ps1`: Windows operator launcher.
- `scripts/phase04_5_export_severity_scope_review_app_workbook.py`: controlled exporter CLI.
- `scripts/phase04_5_export_severity_scope_review_app_workbook.ps1`: Windows exporter launcher.

### Modified production files

- `src/fleetvision/data/validation_error_review_findings.py`: require completed scope export evidence and use completed Workbook in F2.
- `configs/data/phase04_5l_completed_review_findings_config.yaml`: add completed scope filename.
- `.gitignore`: ignore local scope SQLite, WAL/SHM, backups and completed outputs.

### Governance and guides

- `docs/00_project_management/HUMAN_REVIEW_INTERFACE_STANDARD.md`: permanent default operating model.
- `AGENTS.md`: mandatory human-review interface rule.
- `docs/00_project_management/WORKFLOW_GOVERNANCE.md`: replace legacy Excel-first human review section.
- `docs/00_project_management/DECISION_LOG.md`: add ADR-017 so the interface standard is a formal active decision.
- `docs/00_project_management/START_HERE.md`: add the standard to required reading.
- `docs/01_phase_guides/phase_04_5_completed_review_findings_analysis.md`: replace direct Excel instructions.
- `docs/01_phase_guides/phase_04_5_severity_scope_review_app.md`: operator guide.

### Tests

- `tests/scope_review_app_fixtures.py`
- `tests/test_severity_scope_review_mapping.py`
- `tests/test_severity_scope_review_package.py`
- `tests/test_severity_scope_review_state.py`
- `tests/test_severity_scope_review_app.py`
- `tests/test_severity_scope_review_export.py`
- `tests/test_validation_error_review_findings.py`: completed artifact/F2 regression tests.

---

### Task 1: Permanent governance standard

**Files:**
- Create: `docs/00_project_management/HUMAN_REVIEW_INTERFACE_STANDARD.md`
- Modify: `AGENTS.md`
- Modify: `docs/00_project_management/WORKFLOW_GOVERNANCE.md`
- Modify: `docs/00_project_management/START_HERE.md`
- Modify: `docs/00_project_management/DECISION_LOG.md`

**Interfaces:**
- Produces the formal rule used by every future manual-review design and Start-of-Task Gate.

- [ ] **Step 1: Add the dedicated standard**

Write the exact fixed declarations:

```text
HUMAN_REVIEW_DEFAULT_INTERFACE=LOCAL_STREAMLIT_TRADITIONAL_CHINESE
LIVE_REVIEW_STATE=SQLITE
EXCEL_ROLE=EXPORT_EXCHANGE_ARCHIVE_ONLY
DIRECT_EXCEL_REVIEW_DEFAULT=PROHIBITED
```

Include the explicitly authorized no-Python collaborator exception and its backup/hash/assignment/merge/validator controls.

- [ ] **Step 2: Add mandatory references**

Add `HUMAN_REVIEW_INTERFACE_STANDARD.md` to `START_HERE.md` required reading and to `AGENTS.md` source-of-truth files.

- [ ] **Step 3: Replace legacy human-review bullets**

Replace the Excel-first section in `WORKFLOW_GOVERNANCE.md` with Streamlit/SQLite as default and Excel as controlled exception.

- [ ] **Step 4: Record ADR-017**

Append an Active decision stating that multi-case human review defaults to a Traditional Chinese Streamlit UI with SQLite live state, while Excel is limited to completed export, exchange, archive, or a separately approved no-Python collaboration package.

- [ ] **Step 5: Verify governance consistency**

Run:

```powershell
Select-String -Path AGENTS.md,docs\00_project_management\*.md -Pattern 'DIRECT_EXCEL_REVIEW_DEFAULT|LOCAL_STREAMLIT_TRADITIONAL_CHINESE'
```

Expected: declarations and references appear without contradictory Excel-default language.

- [ ] **Step 6: Commit**

```powershell
git add -- AGENTS.md docs/00_project_management/HUMAN_REVIEW_INTERFACE_STANDARD.md docs/00_project_management/WORKFLOW_GOVERNANCE.md docs/00_project_management/START_HERE.md docs/00_project_management/DECISION_LOG.md
git commit -m "docs: standardize streamlit human review workflow"
```

### Task 2: Scope mapping and package verification

**Files:**
- Create: `configs/data/severity_scope_review_app_config.yaml`
- Create: `src/fleetvision/review/severity_scope_review_mapping.py`
- Create: `src/fleetvision/review/severity_scope_review_package.py`
- Test: `tests/test_severity_scope_review_mapping.py`
- Test: `tests/test_severity_scope_review_package.py`
- Test helper: `tests/scope_review_app_fixtures.py`

**Interfaces:**
- Produces `ScopeReviewSelection`, `CanonicalScopeFields`, `ScopeReviewAppConfig`, `VerifiedScopePackage`, `load_verified_scope_package()`.

- [ ] **Step 1: Write mapping RED tests**

Test low confidence notes, catastrophic reason, insufficient evidence and timezone-aware timestamp requirements.

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_severity_scope_review_mapping.py -v
```

Expected: import failure before production modules exist.

- [ ] **Step 2: Implement mapping**

Implement controlled English values plus Traditional Chinese label maps and `derive_canonical_scope_fields()`.

- [ ] **Step 3: Write package RED tests**

Create a synthetic F1 workspace with 130 source rows, 260 verified assets, F1 Gate and checksum manifest. Add a tampered-template rejection test.

- [ ] **Step 4: Implement fail-closed loader**

Verify F1 classification, counts, hashes, full F1 manifest, source identity/order, initial pending fields, safe paths, asset count/size/hash and unique asset root.

- [ ] **Step 5: Run focused tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_severity_scope_review_mapping.py tests/test_severity_scope_review_package.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add -- configs/data/severity_scope_review_app_config.yaml src/fleetvision/review/severity_scope_review_mapping.py src/fleetvision/review/severity_scope_review_package.py tests/scope_review_app_fixtures.py tests/test_severity_scope_review_mapping.py tests/test_severity_scope_review_package.py
git commit -m "feat: verify severity scope review package"
```

### Task 3: SQLite state and app runtime

**Files:**
- Create: `src/fleetvision/review/severity_scope_review_state.py`
- Create: `src/fleetvision/review/severity_scope_review_app.py`
- Test: `tests/test_severity_scope_review_state.py`
- Test: `tests/test_severity_scope_review_app.py`

**Interfaces:**
- Produces `ScopeReviewStateStore`, `ScopeReviewRuntime`, `save_scope_review_selection()`, navigation and filter helpers.

- [ ] **Step 1: Write state RED tests**

Cover initialize, save, reopen/resume, progress, filters, event log and backup.

- [ ] **Step 2: Implement SQLite store**

Use WAL, FULL synchronous, foreign keys, busy timeout, `BEGIN IMMEDIATE`, pinned workspace metadata, case identity and revisioned audit events.

- [ ] **Step 3: Write app-helper RED tests**

Cover bounded navigation, queued selector updates, deterministic backup schedule and automatic backup after the configured save count.

- [ ] **Step 4: Implement app runtime and lazy Streamlit UI**

Keep `streamlit` import inside `render_app()` so pure tests do not require a running UI server. Use Traditional Chinese labels and automatic reviewer/timestamp.

- [ ] **Step 5: Run tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_severity_scope_review_state.py tests/test_severity_scope_review_app.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add -- src/fleetvision/review/severity_scope_review_state.py src/fleetvision/review/severity_scope_review_app.py tests/test_severity_scope_review_state.py tests/test_severity_scope_review_app.py
git commit -m "feat: add streamlit severity scope review state"
```

### Task 4: Completed scope exporter

**Files:**
- Create: `src/fleetvision/review/severity_scope_review_export.py`
- Create: `scripts/phase04_5_export_severity_scope_review_app_workbook.py`
- Create: `scripts/phase04_5_export_severity_scope_review_app_workbook.ps1`
- Test: `tests/test_severity_scope_review_export.py`

**Interfaces:**
- Produces `export_completed_scope_workbook()` and classification `LOCAL_SCOPE_REVIEW_APP_COMPLETED_WORKBOOK_EXPORTED`.

- [ ] **Step 1: Write RED tests**

Test incomplete-state blocking, completed export, source immutability and no-overwrite.

- [ ] **Step 2: Implement transactional exporter**

Copy the F1 template to staging, fill only `SCOPE_COLUMNS`, run existing scope validator, verify image count and atomically rename.

- [ ] **Step 3: Add export evidence**

Write `scope_review_export_result.json` containing completed hash, counts, source hashes, pre-export backup and safety declarations.

- [ ] **Step 4: Run tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_severity_scope_review_export.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add -- src/fleetvision/review/severity_scope_review_export.py scripts/phase04_5_export_severity_scope_review_app_workbook.py scripts/phase04_5_export_severity_scope_review_app_workbook.ps1 tests/test_severity_scope_review_export.py
git commit -m "feat: export completed severity scope review"
```

### Task 5: Launchers and Traditional Chinese operator guide

**Files:**
- Create: `scripts/phase04_5_run_severity_scope_review_app.py`
- Create: `scripts/phase04_5_launch_severity_scope_review_app.ps1`
- Create: `docs/01_phase_guides/phase_04_5_severity_scope_review_app.md`
- Modify: `docs/01_phase_guides/phase_04_5_completed_review_findings_analysis.md`

**Interfaces:**
- Produces the operator commands for launch, resume and completed export.

- [ ] **Step 1: Add Python launcher**

Build the Streamlit command with `--server.port=8502`, `--server.address=127.0.0.1`, usage stats disabled and optional fixed F1 workspace.

- [ ] **Step 2: Add PowerShell launchers**

Use PowerShell 5.1, strict mode, explicit project Python and no `exit 1`.

- [ ] **Step 3: Replace Excel instructions**

State that `severity_scope_review.xlsx` is read-only and the app/exporter are mandatory.

- [ ] **Step 4: Parser and help verification**

```powershell
[scriptblock]::Create((Get-Content scripts/phase04_5_launch_severity_scope_review_app.ps1 -Raw)) | Out-Null
.\.venv\Scripts\python.exe scripts/phase04_5_run_severity_scope_review_app.py --help
.\.venv\Scripts\python.exe scripts/phase04_5_export_severity_scope_review_app_workbook.py --help
```

Expected: parser PASS and both help commands exit 0.

- [ ] **Step 5: Commit**

```powershell
git add -- scripts/phase04_5_run_severity_scope_review_app.py scripts/phase04_5_launch_severity_scope_review_app.ps1 docs/01_phase_guides/phase_04_5_severity_scope_review_app.md docs/01_phase_guides/phase_04_5_completed_review_findings_analysis.md
git commit -m "docs: route scope review through local streamlit app"
```

### Task 6: F2 completed-artifact Gate

**Files:**
- Modify: `configs/data/phase04_5l_completed_review_findings_config.yaml`
- Modify: `src/fleetvision/data/validation_error_review_findings.py`
- Modify: `tests/test_validation_error_review_findings.py`

**Interfaces:**
- Produces `verify_completed_scope_review_export()` and changes F2 input from F1 template to completed scope Workbook.

- [ ] **Step 1: Write RED regression tests**

Test that F2 rejects missing export evidence, template modifications and completed hash mismatch; verify valid evidence returns the completed Workbook path.

- [ ] **Step 2: Make all F1 outputs immutable**

Remove the checksum exception that previously allowed `severity_scope_review.xlsx` to change.

- [ ] **Step 3: Add completed-artifact verifier**

Require classification, PASS outcome, 130/130 counts, source hashes, safety declarations and completed Workbook SHA256.

- [ ] **Step 4: Route F2 to completed Workbook**

Call `export_scope_classification()` with `paths.scope_completed_workbook`, not the F1 template.

- [ ] **Step 5: Run regression tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validation_error_review_findings.py tests/test_severity_scope_review_export.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add -- configs/data/phase04_5l_completed_review_findings_config.yaml src/fleetvision/data/validation_error_review_findings.py tests/test_validation_error_review_findings.py
git commit -m "fix: require completed scope review artifact for F2"
```

### Task 7: Ignore local artifacts and implementation closure

**Files:**
- Modify: `.gitignore`
- Create: `docs/superpowers/specs/2026-07-14-phase04-5l-streamlit-scope-review-correction-design.md`
- Create: `docs/superpowers/plans/2026-07-14-phase04-5l-streamlit-scope-review-correction.md`

- [ ] **Step 1: Ignore local state and exports**

Add patterns for scope SQLite/WAL/SHM, JSONL events, backups, completed Workbook and export result.

- [ ] **Step 2: Run focused suite**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_severity_scope_review_mapping.py tests/test_severity_scope_review_package.py tests/test_severity_scope_review_state.py tests/test_severity_scope_review_app.py tests/test_severity_scope_review_export.py tests/test_validation_error_review_findings.py tests/test_validation_error_review_app.py -v
```

Expected: zero failures.

- [ ] **Step 3: Run full repository suite**

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected: zero failures; existing documented skips only.

- [ ] **Step 4: Compile and diff checks**

```powershell
.\.venv\Scripts\python.exe -m py_compile src/fleetvision/review/severity_scope_review_mapping.py src/fleetvision/review/severity_scope_review_package.py src/fleetvision/review/severity_scope_review_state.py src/fleetvision/review/severity_scope_review_app.py src/fleetvision/review/severity_scope_review_export.py
git diff --check
git status --short
```

Expected: only exact allowlist plus protected external assets.

- [ ] **Step 5: Controlled commit and push**

Stage exact paths only. Do not stage `outputs/metadata/external_assets/`. Reconcile local HEAD, `origin/main` and remote HEAD before and after non-force push.

- [ ] **Step 6: Hard stop**

Do not launch the review app and do not execute F2 as part of implementation closure. The next Gate is operator launch and 130-case review.

## Plan self-review

- Spec coverage: governance, package verification, Traditional Chinese UI, SQLite state, backup, completed exporter and F2 correction are each mapped to a task.
- Placeholder scan: no unresolved placeholder instructions.
- Type consistency: production interfaces use the exact class and function names listed in the file map.
- Safety scope: no F1 rerun, F2 execution, test access, inference, annotation mutation or training.
