# FleetVision Portfolio & Maintenance Reset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert FleetVision into a portfolio-ready, restartable project whose durable source of truth is GitHub, whose large artifacts are organized in Google Drive, and whose old ChatGPT threads are no longer required to resume work.

**Architecture:** Execute the approved reset in controlled gates: first establish a read-only inventory and concise GitHub workflow, then create the Drive skeleton and migrate artifacts category by category, then reconcile model/dataset/metric provenance, then finalize portfolio claims and run a cold-start acceptance test. Technical development remains paused throughout; this plan does not authorize Phase 05S-A3 implementation, training, Frozen Test access, canonical/raw dataset mutation, or first-pass permanent deletion.

**Tech Stack:** Git/GitHub, Markdown, PowerShell 5.1, Python 3.10+ for lightweight local verification, Google Drive, existing FleetVision pytest suite.

## Global Constraints

- Repository: `VincentJ9209/FleetVision`.
- Design baseline checkpoint: `ca4869ccbd418640269f4d8460a5cdf22959e810` (`docs: add portfolio maintenance reset design`).
- Execution baseline: the commit that adds this approved implementation plan at `docs/superpowers/plans/2026-08-10-fleetvision-portfolio-maintenance-reset-implementation-plan.md`; Task 1 must verify local `HEAD == origin/main == remote main` at that plan commit before any reset mutation.
- Codex authorization: explicitly reauthorized by the user on `2026-08-10` for this portfolio-maintenance reset only. This authorization does not grant Phase 05S-A3 implementation, model training, Frozen Test access, or protected-data mutation.
- Approved design: `docs/superpowers/specs/2026-08-10-fleetvision-portfolio-maintenance-reset-design.md`.
- Current technical phase: `Phase 05S-A2 — Implementation Plan Approved and Documented`.
- Technical development: `PAUSED`.
- Current activity: `PORTFOLIO_MAINTENANCE`.
- Next technical gate when development resumes: `PHASE_05S_A3_IMPLEMENTATION_AUTHORIZATION_BEFORE_CODE`.
- This maintenance reset must not authorize or implement Phase 05S-A3.
- `dataset/01_raw/` is immutable.
- Frozen Test search, listing, hashing, reading, tuning, or reuse is prohibited unless a later explicit gate authorizes it.
- `outputs/metadata/external_assets/` must never be staged, committed, deleted, cleaned, moved, or rewritten.
- Canonical COCO, canonical datasets, registry assets, completed human-review outputs, and frozen evidence are protected.
- GitHub is the durable project source of truth for code, configuration, tests, technical documentation, status, decisions, and artifact manifests.
- Google Drive is the artifact vault for large/generated/private assets.
- Chat history is temporary and must not contain unique information required to resume development.
- First-pass Google Drive permanent deletion count must remain exactly `0`.
- Drive migration strategy is `A1 — Classified Archive`.
- Every Drive batch follows `Audit → Classify → Move → Verify → Update Manifest → Next Batch`.
- Portfolio claims must be evidence-backed; folder names such as `final_selected` or `dataset_v3` are not provenance.
- Use explicit-path Git staging only. Never use `git add .` or `git add -A`.
- Before every commit: run `git diff --check`, inspect staged paths, and confirm protected assets are untouched.
- Before every push: confirm branch `main`, local HEAD relationship to `origin/main`, and intended commit subject.
- After every push: verify remote commit and final `git status --short`.

---

## Target File Structure

The plan converges repository documentation toward:

```text
FleetVision/
├── README.md
├── START_HERE.md
├── AGENTS.md
├── PROJECT_CONTEXT_BRIEF.md
├── src/
├── scripts/
├── configs/
├── tests/
├── sql/
├── demo/
├── notebooks/
└── docs/
    ├── 01_portfolio/
    │   ├── PROJECT_OVERVIEW.md
    │   ├── ARCHITECTURE.md
    │   ├── DATA_PIPELINE.md
    │   ├── MODEL_EVALUATION.md
    │   ├── RESULTS_AND_LIMITATIONS.md
    │   └── INTERVIEW_GUIDE.md
    ├── 02_workflow/
    │   ├── PROJECT_STATUS.md
    │   ├── HANDOFF_CURRENT.md
    │   ├── PROTECTED_ASSETS.md
    │   ├── WORKFLOW.md
    │   ├── ASSET_INVENTORY.md
    │   ├── DRIVE_MIGRATION_MANIFEST.md
    │   ├── MODEL_REGISTRY.md
    │   ├── DATASET_REGISTRY.md
    │   ├── RESULTS_REGISTRY.md
    │   └── COLD_START_ACCEPTANCE.md
    ├── 03_decisions/
    │   └── README.md
    └── 99_archive/
        └── legacy_project_management/
```

Existing implementation code under `src/`, `scripts/`, `configs/`, and `tests/` is not reorganized by this maintenance plan unless a broken documentation link requires a path-only correction.

---

### Task 1: Reconcile the Baseline and Establish the Inventory Gate

**Files:**
- Modify: `docs/superpowers/specs/2026-08-10-fleetvision-portfolio-maintenance-reset-design.md` (remove the extra blank line at EOF only)
- Create: `docs/02_workflow/ASSET_INVENTORY.md`
- Create: `docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md`

**Interfaces:**
- Consumes: approved reset design at commit `ca4869c`; the approved implementation-plan commit that directly follows it; current Git and Drive root state.
- Produces: the authoritative classification vocabulary and migration ledger used by every later Drive task.

- [ ] **Step 1: Verify the repository baseline before any edit**

Run from `G:\FleetVision\Project\FleetVision`:

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
```

Expected before edits:

```text
status: empty, or only the explicitly protected untracked external-assets path
branch: main
HEAD: same SHA as origin/main and GitHub remote main
HEAD^: ca4869ccbd418640269f4d8460a5cdf22959e810
HEAD subject: docs: add portfolio maintenance reset implementation plan
```

Verify the parent and subject with:

```powershell
git rev-parse HEAD^
git log -1 --pretty=%s
```

The exact execution-baseline SHA is therefore the newly created implementation-plan commit, not the design-spec commit. If `HEAD`, `origin/main`, and remote `main` do not agree, if the parent is not `ca4869ccbd418640269f4d8460a5cdf22959e810`, or if any unexpected path is modified, staged, deleted, renamed, or untracked, stop this task and reconcile before continuing.

- [ ] **Step 2: Normalize the approved spec EOF so `git diff --check` is clean**

Run:

```powershell
python -c "from pathlib import Path; p=Path(r'docs/superpowers/specs/2026-08-10-fleetvision-portfolio-maintenance-reset-design.md'); s=p.read_text(encoding='utf-8-sig').rstrip('\r\n')+'\n'; open(p,'w',encoding='utf-8',newline='\n').write(s)"
```

Then:

```powershell
git diff --check -- docs/superpowers/specs/2026-08-10-fleetvision-portfolio-maintenance-reset-design.md
```

Expected: no output.

- [ ] **Step 3: Create `ASSET_INVENTORY.md` with the fixed classification contract**

The file must contain these sections and values:

```markdown
# FleetVision Asset Inventory

## Inventory Status
- Design baseline Git commit: `ca4869ccbd418640269f4d8460a5cdf22959e810`
- Execution baseline Git commit: record the exact `git rev-parse HEAD` value verified in Task 1 Step 1
- Technical development: `PAUSED`
- Current activity: `PORTFOLIO_MAINTENANCE`
- Permanent deletion in first pass: `PROHIBITED`

## Classification Vocabulary
- `CURRENT` — active artifact used by the maintained project.
- `PORTFOLIO` — selected artifact used for interview/demo presentation.
- `ARCHIVE` — historical artifact retained outside the active workflow.
- `DUPLICATE_CANDIDATE` — suspected duplicate; retained until identity is verified.
- `PROTECTED` — must not be mutated or moved without an explicit safety gate.
- `RECONCILE_REQUIRED` — identity/provenance is insufficient to classify safely.

## Inventory Rules
1. Naming alone is not provenance.
2. First-pass deletion count is zero.
3. Protected and unique artifacts remain in place until verified.
4. Every moved Drive item must also appear in `DRIVE_MIGRATION_MANIFEST.md`.
5. GitHub paths record durable narrative/provenance; Drive stores large/private artifacts.

## Repository Baseline
| Asset | Current Path | Classification | Action |
|---|---|---|---|
| Approved reset design | `docs/superpowers/specs/2026-08-10-fleetvision-portfolio-maintenance-reset-design.md` | CURRENT | Keep |
| Current governance | `docs/00_project_management/` | RECONCILE_REQUIRED | Replace current-facing docs, then archive legacy directory |
| Root README | `README.md` | CURRENT | Rework for interview-first reading path |

## Drive Baseline
| Asset | Current Location | Classification | Protected | Initial Target |
|---|---|---|---|---|
| `00.成果發表/` | Drive root | PORTFOLIO | No | split to `00_PORTFOLIO/` and `04_PROJECT_ASSETS/` |
| `internal_grouped_dataset_v1_20260717_212356/` | Drive root | PROTECTED | Yes | `01_DATA/01_internal/` after dataset gate |
| `dataset_v3_relabel_working_20260720_091414/` | Drive root | ARCHIVE | No | `99_ARCHIVE/02_old_datasets/` |
| relabel working ZIP | Drive root | DUPLICATE_CANDIDATE | No | `99_ARCHIVE/06_duplicate_candidates/` |
| `grouped_dataset/` | Drive root | RECONCILE_REQUIRED | Yes | archive/reconciliation first |
| `models/` | Drive root | RECONCILE_REQUIRED | Yes | reconcile before selecting current model |
| `notebooks/` | Drive root | RECONCILE_REQUIRED | No | select representatives; archive remainder |
| `outputs/` | Drive root | RECONCILE_REQUIRED | No | retain evidence; archive remainder |
| `04_5J/` | Drive root | ARCHIVE | No | `99_ARCHIVE/04_old_experiments/` |
| `04_5K/` | Drive root | ARCHIVE | No | `99_ARCHIVE/04_old_experiments/` |
```

- [ ] **Step 4: Create `DRIVE_MIGRATION_MANIFEST.md` with a strict ledger schema**

Use this header and table definition:

```markdown
# FleetVision Drive Migration Manifest

## Rules
- First-pass permanent deletion: `false` for every row.
- Every move requires before/after verification.
- `PROTECTED` or `RECONCILE_REQUIRED` rows may not be moved until the relevant task approves them.

| ID | Current Path | Name | Type | Classification | Protected | Target Path | Evidence / Rationale | Delete Allowed | Verification |
|---|---|---|---|---|---|---|---|---|---|
```

Seed the manifest with the ten Drive baseline rows from `ASSET_INVENTORY.md`. Assign IDs `DRV-001` through `DRV-010` in the same order. Set every `Delete Allowed` value to `false` and every initial `Verification` value to `NOT_STARTED`.

- [ ] **Step 5: Run structural checks**

```powershell
Test-Path docs/02_workflow/ASSET_INVENTORY.md
Test-Path docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md
git diff --check
```

Expected:

```text
True
True
(no git diff --check output)
```

- [ ] **Step 6: Stage only the three authorized paths and inspect them**

```powershell
git add -- `
  "docs/superpowers/specs/2026-08-10-fleetvision-portfolio-maintenance-reset-design.md" `
  "docs/02_workflow/ASSET_INVENTORY.md" `
  "docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md"

git diff --cached --check
git diff --cached --name-only
```

Expected staged paths: exactly those three files.

- [ ] **Step 7: Commit and push the inventory gate**

```powershell
git commit -m "docs: establish portfolio reset inventory gate"
git push origin main
git status --short
git log -1 --oneline
```

Expected final worktree: clean, or protected-untracked-only.

---

### Task 2: Create the Minimal Development-Resumption Path

**Files:**
- Create: `START_HERE.md`
- Create: `docs/02_workflow/PROJECT_STATUS.md`
- Create: `docs/02_workflow/HANDOFF_CURRENT.md`
- Create: `docs/02_workflow/PROTECTED_ASSETS.md`
- Create: `docs/02_workflow/WORKFLOW.md`
- Modify: `AGENTS.md`
- Modify: `PROJECT_CONTEXT_BRIEF.md`

**Interfaces:**
- Consumes: current authoritative state from legacy `docs/00_project_management/` and the approved reset design.
- Produces: a four-document default startup path plus task-specific safety references.

- [ ] **Step 1: Read the current authoritative legacy files without editing them**

Inspect only:

```text
docs/00_project_management/START_HERE.md
docs/00_project_management/PROJECT_STATUS.md
docs/00_project_management/HANDOFF_CURRENT.md
docs/00_project_management/PROTECTED_ASSETS.md
docs/00_project_management/MASTER_PHASE_MAP.md
docs/00_project_management/DECISION_LOG.md
PROJECT_CONTEXT_BRIEF.md
AGENTS.md
```

Record any contradiction before writing. Live Git facts and cryptographic artifact identities outrank narrative history.

- [ ] **Step 2: Create root `START_HERE.md` as the only default entry point**

It must require this default read order only:

```text
1. START_HERE.md
2. PROJECT_CONTEXT_BRIEF.md
3. docs/02_workflow/PROJECT_STATUS.md
4. docs/02_workflow/HANDOFF_CURRENT.md
```

It must then define just-in-time references:

```text
Data/protected asset work → docs/02_workflow/PROTECTED_ASSETS.md
Repository workflow/Git gate → docs/02_workflow/WORKFLOW.md
Architecture decision work → docs/03_decisions/README.md
Historical phase investigation → docs/99_archive/legacy_project_management/
```

It must state:

```text
Technical phase: Phase 05S-A2
Technical development: PAUSED
Current activity: PORTFOLIO_MAINTENANCE
Next technical gate: PHASE_05S_A3_IMPLEMENTATION_AUTHORIZATION_BEFORE_CODE
A3 authorized: false
Chat history required: not yet retired
```

- [ ] **Step 3: Create concise `PROJECT_STATUS.md`**

The new status file must have exactly these top-level sections:

```markdown
# FleetVision Project Status
## Current State
## Implemented Capabilities
## Partial / Planned Capabilities
## Protected Boundaries
## Open Provenance Work
## Resume Point
```

`Current State` must preserve Phase 05S-A2, `PAUSED`, `PORTFOLIO_MAINTENANCE`, the last completed technical gate, and the A3 resume gate. Historical 04.5/05R execution transcripts must not be copied into this file.

- [ ] **Step 4: Create concise `HANDOFF_CURRENT.md`**

Required sections:

```markdown
# FleetVision Current Handoff
## Current Status
## Current Working Boundary
## Authoritative Assets
## Known Open Items
## Resume From Here
```

Required current facts:

```text
Technical phase = Phase 05S-A2
Technical development = PAUSED
Current activity = PORTFOLIO_MAINTENANCE
Last completed technical gate = PHASE_05S_A2_PLAN_DOCUMENT_APPLICATION_AND_CHECKPOINT
Next technical gate = PHASE_05S_A3_IMPLEMENTATION_AUTHORIZATION_BEFORE_CODE
A3 authorized = false
Frozen Test access authorized = false
Training/fine-tuning authorized = false
```

Known open items must include model provenance reconciliation, dataset provenance reconciliation, metric/claim reconciliation, and incomplete before/after comparison implementation.

- [ ] **Step 5: Create `PROTECTED_ASSETS.md` from the active safety contract**

At minimum retain these protected classes:

```text
outputs/metadata/external_assets/
dataset/01_raw/
completed/active human-review workbooks
reviewer manifests/manual-review ZIPs
frozen backups/SHA256 manifests
canonical CSV/COCO/dataset manifests
external source archives
internal holdout definitions
registry assets
model/training acceptance artifacts
```

Explicitly state that current maintenance work does not authorize Frozen Test access, raw/canonical mutation, training, or A3 implementation.

- [ ] **Step 6: Create `WORKFLOW.md` as the stable RAG-style task lifecycle**

It must define this exact lifecycle:

```text
Read core context
→ reconcile live Git state
→ define one task
→ read only task-specific references
→ Audit
→ Apply/Execute
→ Verify
→ update durable state if needed
→ explicit-path stage
→ commit/push only when authorized
→ remote verification
→ end session
```

Include explicit rules against broad `git add`, unrelated scope expansion, and treating chat as durable storage.

- [ ] **Step 7: Reduce `AGENTS.md` to durable rules only**

Keep:

```text
startup path
protected asset rules
immutable YOLOv8 single-class contract
no automated claim/liability interpretation
no raw/Frozen Test mutation/access without gate
production code location under src/fleetvision
notebooks are not primary business logic
large artifacts stay outside Git
verification + explicit-path Git rules
stop conditions
```

Remove repeated historical phase narratives, superseded task-specific Codex/Cursor details, and duplicated governance blocks that are now represented by `START_HERE.md` and `docs/02_workflow/*`.

Target size: approximately 50–100 lines, while preserving all safety-critical semantics.

- [ ] **Step 8: Simplify `PROJECT_CONTEXT_BRIEF.md`**

Keep stable project identity, scope, immutable architecture, major data strategy, current operational boundary, and system integration context. Remove stale checkpoint narration and duplicated task procedure now owned by `PROJECT_STATUS.md` and `WORKFLOW.md`.

- [ ] **Step 9: Verify startup references and stale-path removal**

Run:

```powershell
git grep -n "docs/00_project_management/START_HERE.md" -- README.md AGENTS.md PROJECT_CONTEXT_BRIEF.md START_HERE.md docs/02_workflow 2>$null
git grep -n "PHASE05R-CURRENT-HANDOFF" -- START_HERE.md docs/02_workflow 2>$null
git diff --check
```

Expected: no current-facing startup reference to the legacy `START_HERE`; no old Phase 05R current-handoff block in the new workflow files; no whitespace errors.

- [ ] **Step 10: Run the existing repository test suite because governance paths may be referenced by tests**

```powershell
python -m pytest -q -p no:cacheprovider
```

Record exact collected/passed/skipped/failed counts. Do not claim the prior `479 passed, 1 skipped` result; use this fresh run.

- [ ] **Step 11: Commit and push the development-resumption path**

Stage only:

```text
START_HERE.md
AGENTS.md
PROJECT_CONTEXT_BRIEF.md
docs/02_workflow/PROJECT_STATUS.md
docs/02_workflow/HANDOFF_CURRENT.md
docs/02_workflow/PROTECTED_ASSETS.md
docs/02_workflow/WORKFLOW.md
```

Commit:

```powershell
git commit -m "docs: simplify FleetVision resumption workflow"
git push origin main
```

---

### Task 3: Archive Legacy Governance Without Losing Auditability

**Files:**
- Move: `docs/00_project_management/` → `docs/99_archive/legacy_project_management/`
- Create: `docs/03_decisions/README.md`
- Modify: current-facing links in `README.md`, `START_HERE.md`, `AGENTS.md`, and `PROJECT_CONTEXT_BRIEF.md` only if required by the move.

**Interfaces:**
- Consumes: new workflow documents from Task 2.
- Produces: a clean current docs surface while retaining historical logs, handoffs, and full decision records in Git.

- [ ] **Step 1: Confirm no current-facing file still depends on legacy paths**

```powershell
git grep -n "docs/00_project_management/" -- README.md START_HERE.md AGENTS.md PROJECT_CONTEXT_BRIEF.md docs/02_workflow
```

Every hit must either be replaced with a new path or explicitly described as a historical archive reference.

- [ ] **Step 2: Move the legacy governance directory atomically with Git**

```powershell
New-Item -ItemType Directory -Force docs/99_archive | Out-Null
git mv "docs/00_project_management" "docs/99_archive/legacy_project_management"
```

Do not edit historical content during this move.

- [ ] **Step 3: Create `docs/03_decisions/README.md` as the active decision index**

Include only active decisions that materially constrain current work, each with a one-line rationale and a link to the archived full decision log. At minimum index:

```text
YOLOv8 Detect with single class damage
external dataset governance before training use
internal holdout separation
group-safe/data-leakage controls
GitHub as durable source of truth
validation-only threshold/error analysis after test evaluation
human-review interface default (Streamlit + SQLite; Excel export/archive role)
product claim boundary (no liability/claim adjudication)
```

Link the full history to:

```text
../99_archive/legacy_project_management/DECISION_LOG.md
```

- [ ] **Step 4: Verify current startup paths and archive presence**

```powershell
Test-Path docs/99_archive/legacy_project_management/DECISION_LOG.md
Test-Path docs/99_archive/legacy_project_management/HANDOFF_CURRENT.md
Test-Path docs/03_decisions/README.md
git grep -n "docs/00_project_management/" -- README.md START_HERE.md AGENTS.md PROJECT_CONTEXT_BRIEF.md docs/02_workflow docs/03_decisions 2>$null
git diff --check
```

Expected: all three `Test-Path` results are `True`; no stale current-facing legacy path remains except an intentional archive link; no whitespace errors.

- [ ] **Step 5: Run tests and commit the archive checkpoint**

```powershell
python -m pytest -q -p no:cacheprovider
git add -- README.md START_HERE.md AGENTS.md PROJECT_CONTEXT_BRIEF.md docs/02_workflow docs/03_decisions docs/99_archive/legacy_project_management
git diff --cached --check
git diff --cached --name-status
git commit -m "docs: archive legacy FleetVision governance"
git push origin main
```

Do not use broad staging outside the listed paths.

---

### Task 4: Build the Interview-First Portfolio Reading Path

**Files:**
- Create: `docs/01_portfolio/PROJECT_OVERVIEW.md`
- Create: `docs/01_portfolio/ARCHITECTURE.md`
- Create: `docs/01_portfolio/DATA_PIPELINE.md`
- Create: `docs/01_portfolio/MODEL_EVALUATION.md`
- Create: `docs/01_portfolio/RESULTS_AND_LIMITATIONS.md`
- Create: `docs/01_portfolio/INTERVIEW_GUIDE.md`
- Modify: `README.md`
- Move to archive after content is harvested: `docs/00_project_overview/`, `docs/04_reports/`, `docs/05_presentation/` → `docs/99_archive/legacy_portfolio_docs/`

**Interfaces:**
- Consumes: repository-backed README evidence, stable context, code paths, current workflow status.
- Produces: the 5–10 minute hiring-manager reading path. Model-specific claims remain constrained by later reconciliation tasks.

- [ ] **Step 1: Harvest usable content before moving legacy docs**

Read:

```text
README.md
docs/00_project_overview/project_background.md
docs/00_project_overview/system_architecture.md
docs/00_project_overview/tool_workflow.md
docs/04_reports/final_report_draft.md
docs/04_reports/project_structure_audit.md
docs/05_presentation/demo_script.md
```

Do not copy stale claims without repository or artifact evidence.

- [ ] **Step 2: Create `PROJECT_OVERVIEW.md`**

Required sections:

```markdown
# Project Overview
## Problem
## FleetVision Scope
## My Primary Contribution
## Three-Stage Team Context
## What Is Implemented Today
## What Is Not Implemented
```

The ownership section must explicitly identify FleetVision Phase 2/data-and-model workflow as the primary individual contribution. Phase 1 capture and Phase 3 dashboard/review are system/team context unless evidence proves individual implementation.

- [ ] **Step 3: Create `ARCHITECTURE.md`**

Include a Mermaid diagram with this logical boundary:

```text
Phase 1 Capture
→ image + metadata contract
→ Phase 2 FleetVision validation/data/model/evaluation
→ pairing/before-after comparison boundary
→ Phase 3 human review/dashboard context
```

Every node must be tagged conceptually as `IMPLEMENTED`, `PARTIAL`, or `PLANNED` in accompanying text.

- [ ] **Step 4: Create `DATA_PIPELINE.md`**

Describe, with repository links where available:

```text
metadata inventory
review queue
human review
reviewed dataset
external intake + license/registry
bbox repair/canonicalization
deduplication
group-safe split/QA
```

Include a data-safety section explaining raw immutability, internal/external separation, and frozen evaluation boundaries.

- [ ] **Step 5: Create `MODEL_EVALUATION.md`**

Describe methodology only until Task 9 fills the reconciled results table:

```text
YOLOv8 Detect, one class damage
IoU-based matching
validation-only threshold analysis
FP/FN taxonomy
human-review feedback loop
test-use boundary
```

Do not present a folder named `final_selected` as final model evidence.

- [ ] **Step 6: Create `RESULTS_AND_LIMITATIONS.md`**

At this checkpoint, include only claims already repository-backed and label historical model metrics as historical evidence rather than final performance. Required limitation statements:

```text
no production deployment
no automated insurance/claim/liability conclusion
before/after damage comparison not complete
private datasets/model weights not distributed in Git
model/dataset/results provenance reconciliation still in progress until Task 9
```

- [ ] **Step 7: Create `INTERVIEW_GUIDE.md`**

Structure:

```markdown
# Interview Guide
## 30-Second Summary
## 2-Minute Technical Walkthrough
## Five Evidence Cases
## Questions I Expect
## Claims I Must Not Overstate
## Demo / Presentation Assets
```

The five evidence cases are: data governance, external dataset intake, human-in-the-loop review, model evaluation/error analysis, and before/after architecture boundary.

- [ ] **Step 8: Rework root `README.md` into the portfolio landing page**

Use this section order:

```text
Hero / one-sentence purpose
Problem
What I Built
Architecture
Key Engineering Challenges
Evidence-Backed Results
Demo / Portfolio Assets
Tech Stack
Repository Tour
Reproduce / Test
Limitations
Current Status
```

Do not add unreconciled model metrics. Link deeper details to `docs/01_portfolio/*` and workflow state to `START_HERE.md`.

- [ ] **Step 9: Archive superseded portfolio-era docs after links are migrated**

```powershell
New-Item -ItemType Directory -Force docs/99_archive/legacy_portfolio_docs | Out-Null
git mv docs/00_project_overview docs/99_archive/legacy_portfolio_docs/00_project_overview
git mv docs/04_reports docs/99_archive/legacy_portfolio_docs/04_reports
git mv docs/05_presentation docs/99_archive/legacy_portfolio_docs/05_presentation
```

- [ ] **Step 10: Verify links, repository references, and tests**

```powershell
git diff --check
python -m pytest -q -p no:cacheprovider
```

Manually open every Markdown link changed in `README.md` and the six portfolio files. Any link to `docs/00_project_management`, `docs/00_project_overview`, `docs/04_reports`, or `docs/05_presentation` must be intentional archive history only.

- [ ] **Step 11: Commit the portfolio reading path**

Commit:

```powershell
git commit -m "docs: build interview-first FleetVision portfolio"
git push origin main
```

---

### Task 5: Create the Google Drive A1 Skeleton Without Moving Existing Assets

**Files:**
- Modify: `docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md`
- Modify: `docs/02_workflow/ASSET_INVENTORY.md`

**Drive folders to create:**

```text
FleetVision/
├── 00_PORTFOLIO/
│   ├── 01_Project_Overview/
│   ├── 02_Presentation/
│   ├── 03_Demo/
│   └── 04_Interview_Assets/
├── 01_DATA/
│   ├── 01_internal/
│   ├── 02_external/
│   ├── 03_reviewed/
│   └── 04_annotations/
├── 02_MODELS/
│   ├── 01_current/
│   ├── 02_evaluation/
│   └── 03_model_evidence/
├── 03_EXPERIMENTS/
│   ├── 01_notebooks/
│   ├── 02_training/
│   ├── 03_inference/
│   └── 04_evaluation/
├── 04_PROJECT_ASSETS/
│   ├── 01_phase1_capture/
│   ├── 02_phase2_detection/
│   └── 03_phase3_dashboard/
└── 99_ARCHIVE/
    ├── 01_deprecated_notebooks/
    ├── 02_old_datasets/
    ├── 03_old_models/
    ├── 04_old_experiments/
    ├── 05_old_presentations/
    ├── 06_duplicate_candidates/
    └── 99_uncategorized_legacy/
```

**Interfaces:**
- Consumes: manifest from Task 1 and current Drive root.
- Produces: empty destination structure only; existing artifacts remain unmoved.

- [ ] **Step 1: Audit the Drive root and record the exact pre-create listing**

Record every direct child name, type, and Drive identifier/link in the manifest. No move or delete is permitted in this step.

- [ ] **Step 2: Create every approved folder exactly once**

Use the Drive connector/API. If a folder already exists with the exact intended purpose, reuse it and record the existing ID instead of creating a duplicate.

- [ ] **Step 3: Verify the new skeleton independently**

List the Drive root and each new top-level folder. Pass condition:

```text
all six top-level areas exist
all required subfolders exist
no original root artifact was moved
permanent deletion count = 0
```

- [ ] **Step 4: Update the manifest with folder IDs/links and gate result**

Add a `Drive Destination IDs` section to `DRIVE_MIGRATION_MANIFEST.md`. Mark the skeleton gate `VERIFIED` only after the independent listing confirms it.

- [ ] **Step 5: Commit only the manifest/inventory update**

```powershell
git add -- docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md docs/02_workflow/ASSET_INVENTORY.md
git diff --cached --check
git commit -m "docs: record verified Drive reset skeleton"
git push origin main
```

---

### Task 6: Migrate Portfolio and Project Assets (Drive Batches D1–D2)

**Files:**
- Modify: `docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md`
- Modify: `docs/01_portfolio/INTERVIEW_GUIDE.md` only when a selected Drive asset becomes a stable portfolio link.

**Drive scope:**
- Source: `00.成果發表/`
- Targets: `00_PORTFOLIO/*`, `04_PROJECT_ASSETS/*`, and archive folders for superseded presentation variants.

**Interfaces:**
- Consumes: verified Drive skeleton.
- Produces: a small intentional public/interview-facing asset set plus classified engineering context assets.

- [ ] **Step 1: Inventory all direct and relevant nested children under `00.成果發表/`**

Classify each as one of:

```text
PORTFOLIO
PROJECT_ASSET
ARCHIVE
DUPLICATE_CANDIDATE
```

Preserve team ownership/context in the rationale.

- [ ] **Step 2: Select portfolio presentation artifacts**

Prefer one authoritative presentation deck, one primary demo video, one concise project-overview asset, and only the screenshots needed for interview explanation. Keep alternate/rehearsal/duplicate media in archive, not the active portfolio surface.

- [ ] **Step 3: Move Phase 1/2/3 engineering assets to `04_PROJECT_ASSETS`**

Map capture/web-app materials to `01_phase1_capture`, FleetVision damage-analysis evidence to `02_phase2_detection`, and dashboard/review context to `03_phase3_dashboard`.

- [ ] **Step 4: Move superseded presentation variants to `99_ARCHIVE/05_old_presentations`**

No deletion. Record every source/target pair in the manifest before executing the move.

- [ ] **Step 5: Verify every moved item by Drive ID or stable file identity**

Pass condition per row:

```text
source no longer appears in old parent
same Drive item ID appears in target parent, or connector explicitly confirms a move without copy
classification unchanged
Delete Allowed = false
Verification = VERIFIED
```

- [ ] **Step 6: Update interview links only for stable selected assets**

Do not publish private raw data or internal review artifacts. If a Drive asset is not intentionally shareable, document its existence without creating a public link.

- [ ] **Step 7: Commit the verified manifest checkpoint**

```powershell
git add -- docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md docs/01_portfolio/INTERVIEW_GUIDE.md
git diff --cached --check
git commit -m "docs: record portfolio asset migration"
git push origin main
```

---

### Task 7: Migrate Representative Notebooks and Experiment Evidence (Drive Batches D3–D4)

**Files:**
- Modify: `docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md`
- Create or modify: `notebooks/README.md`

**Drive scope:**
- `notebooks/`
- root-level `.ipynb` files
- `outputs/`
- `04_5J/`
- `04_5K/`
- experiment ZIP packages such as Candidate02 and pilot/recovery archives

**Interfaces:**
- Consumes: portfolio/data architecture and existing experiment history.
- Produces: a small representative notebook set and clearly archived recovery/debug/duplicate artifacts.

- [ ] **Step 1: Audit notebook identities before choosing representatives**

For each notebook record name, size, modified time, apparent stage, whether outputs are embedded, and whether an equivalent tracked notebook exists in GitHub.

Representative selection criteria, all required:

```text
maps to a meaningful pipeline stage
has distinct evidence value
not a byte/content duplicate of a better version
contains no secret/private payload inappropriate for portfolio use
is understandable/reproducible enough to preserve as active evidence
```

- [ ] **Step 2: Select at most 3–5 active notebooks**

Use functional roles rather than old recovery numbering:

```text
data / audit
training
model evaluation
inference / demo (only if useful)
```

Do not rename or move until identity and role are recorded in the manifest.

- [ ] **Step 3: Move selected Drive notebooks to `03_EXPERIMENTS/01_notebooks/`**

Move deprecated/recovery/debug notebook variants to `99_ARCHIVE/01_deprecated_notebooks/`. Root-level duplicate notebook candidates go first to `99_ARCHIVE/06_duplicate_candidates/` if identity is not fully verified.

- [ ] **Step 4: Classify `outputs/`, `04_5J/`, and `04_5K/`**

Keep small evidence summaries needed for provenance under `03_EXPERIMENTS/02_training`, `03_inference`, or `04_evaluation`. Preserve complete historical experiment trees under `99_ARCHIVE/04_old_experiments/`.

- [ ] **Step 5: Update `notebooks/README.md`**

For each active tracked or Drive-hosted notebook, state:

```text
purpose
status (current evidence / historical evidence)
dataset dependency
whether GPU is needed
whether the notebook is safe to run now under Phase 05S-A2
where large outputs live
```

Historical training notebooks must not be described as authorization to retrain.

- [ ] **Step 6: Verify every Drive move and commit the manifest**

No permanent deletion. After Drive verification:

```powershell
git add -- docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md notebooks/README.md
git diff --cached --check
git commit -m "docs: classify FleetVision notebook and experiment evidence"
git push origin main
```

---

### Task 8: Reconcile and Migrate Models (Drive Batch D5)

**Files:**
- Create: `docs/02_workflow/MODEL_REGISTRY.md`
- Create: `docs/02_workflow/RESULTS_REGISTRY.md`
- Modify: `docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md`

**Drive scope:**
- `models/`
- model artifacts inside `outputs/models/` and recovery experiment folders

**Interfaces:**
- Consumes: repository Phase 04.5J/04.5K evidence, Drive model folders, weight identities, training/evaluation records.
- Produces: an explicit mapping from weight artifact to experiment and allowed claim; only then may a reference model be selected.

- [ ] **Step 1: Inventory every candidate weight and model-selection record**

At minimum inspect:

```text
models/final_selected/
models/model_selection/
models/candidate_01/
models/candidate_02/
outputs/models/
rapid_detection_recovery_colab artifacts
```

Record Drive ID/path, file size, date, filename, known SHA256 evidence, training notebook/experiment linkage, and quality status.

- [ ] **Step 2: Create `MODEL_REGISTRY.md` with this schema**

```markdown
# FleetVision Model Registry

| Model ID | Artifact | SHA256 / Identity | Training Dataset | Experiment | Validation Evidence | Test Evidence | Quality Status | Allowed Portfolio Claim |
|---|---|---|---|---|---|---|---|---|
```

Use explicit status labels such as:

```text
VERIFIED_HISTORICAL_BASELINE
BEST_AVAILABLE_POC_ONLY
EXPERIMENTAL
UNRESOLVED_IDENTITY
```

Do not use `FINAL` or `PRODUCTION` unless artifact evidence and acceptance gates support it.

- [ ] **Step 3: Seed the known historical controlled baseline from repository evidence**

Record the Phase 04.5J YOLOv8s baseline as historical evidence with its repository-recorded weight SHA and validation/test metrics. State that the test result was a one-time historical evaluation and is not available for tuning.

- [ ] **Step 4: Record the `final_selected` POC artifact separately**

If the Drive selection record identifies `BEST_AVAILABLE_POC_ONLY` and `quality_gate_pass=false`, preserve that classification. It must not replace the verified 04.5J baseline merely because the folder name says `final_selected`.

- [ ] **Step 5: Create `RESULTS_REGISTRY.md` with provenance-complete metric rows**

Schema:

```markdown
# FleetVision Results Registry

| Result ID | Model ID | Dataset / Version | Split | Threshold / Operating Point | Metric | Value | Evidence | Allowed Interpretation |
|---|---|---|---|---|---|---|---|---|
```

Every metric shown in README/presentation after Task 10 must correspond to a row here.

- [ ] **Step 6: Move model artifacts only after registry identity is assigned**

Use:

```text
02_MODELS/01_current/        → only selected current reference artifact, if one is justified
02_MODELS/02_evaluation/     → evaluation/model-selection evidence
02_MODELS/03_model_evidence/ → historical/experimental model artifacts
99_ARCHIVE/03_old_models/    → superseded model trees that remain valuable only as history
```

A valid outcome is that `01_current/` contains only a README/status marker and no weight because no model meets the current-reference standard.

- [ ] **Step 7: Verify Drive identities and commit registries**

```powershell
git add -- docs/02_workflow/MODEL_REGISTRY.md docs/02_workflow/RESULTS_REGISTRY.md docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md
git diff --cached --check
git commit -m "docs: reconcile FleetVision model provenance"
git push origin main
```

---

### Task 9: Reconcile and Migrate Datasets (Drive Batch D6)

**Files:**
- Create: `docs/02_workflow/DATASET_REGISTRY.md`
- Modify: `docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md`
- Modify: `docs/02_workflow/ASSET_INVENTORY.md`

**Drive scope:**
- `internal_grouped_dataset_v1_20260717_212356/`
- `dataset_v3_relabel_working_20260720_091414/`
- same-name relabel ZIP
- `grouped_dataset/`
- YOLO labels package and dataset-related ZIP exports

**Interfaces:**
- Consumes: protected-asset contract and prior lineage evidence.
- Produces: explicit canonical/working/historical/export distinctions so future work cannot accidentally train from the wrong folder.

- [ ] **Step 1: Create `DATASET_REGISTRY.md` before moving anything**

Schema:

```markdown
# FleetVision Dataset Registry

| Dataset ID | Artifact / Location | Role | Canonical Status | Split / Holdout Boundary | Lineage Evidence | Protection | Allowed Use |
|---|---|---|---|---|---|---|---|
```

Use role/status vocabulary:

```text
RAW_SOURCE
REVIEWED_CANONICAL
HISTORICAL_BASELINE
WORKING_COPY
TRAINING_EXPORT
EXTERNAL_SOURCE
ARCHIVE_RECONCILIATION
FROZEN_HOLDOUT_DEFINITION
```

- [ ] **Step 2: Register `internal_grouped_dataset_v1_20260717_212356` as protected historical baseline**

Record its `train/`, `valid/`, `test/`, and `lineage/` structure without reading Frozen Test contents. Allowed action is location/identity documentation and controlled move only; no content mutation.

- [ ] **Step 3: Register the relabel working copy as `WORKING_COPY`**

Its own README states it is not formal Dataset v3 and must not overwrite the original baseline. Preserve that statement in the registry and move the folder to:

```text
99_ARCHIVE/02_old_datasets/
```

- [ ] **Step 4: Place the matching relabel ZIP in duplicate-candidate archive**

Move to:

```text
99_ARCHIVE/06_duplicate_candidates/
```

Do not delete it even if folder contents appear equivalent; deletion requires a later independent identity check and explicit user-approved list.

- [ ] **Step 5: Register `grouped_dataset/` as `ARCHIVE_RECONCILIATION` unless clean lineage proves otherwise**

Because the folder contains legacy/flattened path artifacts and mixed-generation content, keep it out of active data paths. Move to:

```text
99_ARCHIVE/02_old_datasets/grouped_dataset_legacy/
```

only after the manifest records its unique contents/risks.

- [ ] **Step 6: Move the protected internal baseline last**

After registry and target verification, move the top-level folder to:

```text
01_DATA/01_internal/internal_grouped_dataset_v1_20260717_212356/
```

Verify by Drive item identity and structure names only. Do not inspect or hash Frozen Test images unless a later explicit gate authorizes it.

- [ ] **Step 7: Classify label/export ZIPs**

If they are reproducible exports, archive them; if they contain unique annotation evidence, register them under `01_DATA/04_annotations/` or `03_EXPERIMENTS` according to actual provenance. Naming alone is insufficient.

- [ ] **Step 8: Verify no protected data was modified and commit**

Pass conditions:

```text
first-pass deletion count = 0
raw content mutation = 0
Frozen Test content access = 0
working copy not promoted to canonical
all moved dataset rows = VERIFIED
```

Commit:

```powershell
git add -- docs/02_workflow/DATASET_REGISTRY.md docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md docs/02_workflow/ASSET_INVENTORY.md
git diff --cached --check
git commit -m "docs: reconcile FleetVision dataset provenance"
git push origin main
```

---

### Task 10: Finalize Evidence-Backed Portfolio Claims

**Files:**
- Modify: `README.md`
- Modify: `docs/01_portfolio/MODEL_EVALUATION.md`
- Modify: `docs/01_portfolio/RESULTS_AND_LIMITATIONS.md`
- Modify: `docs/01_portfolio/INTERVIEW_GUIDE.md`
- Modify: `docs/01_portfolio/PROJECT_OVERVIEW.md` if ownership wording needs evidence correction

**Interfaces:**
- Consumes: `MODEL_REGISTRY.md`, `DATASET_REGISTRY.md`, `RESULTS_REGISTRY.md`, verified Drive portfolio assets.
- Produces: final interview-facing claims where each important number or capability maps to evidence.

- [ ] **Step 1: Build a claim checklist from the current README and portfolio docs**

For each quantitative or status claim, record its supporting registry row or repository path. Remove any claim that cannot be supported.

- [ ] **Step 2: Update model results from `RESULTS_REGISTRY.md` only**

If a metric is historical, say `historical controlled baseline`. If a metric uses validation operating-point analysis, distinguish it from model-training metrics and from deployment thresholds. Do not merge metrics from different experiments into one apparent final score.

- [ ] **Step 3: Confirm ownership language**

Phase 2/data governance/model evaluation may be described as the primary FleetVision contribution when supported by repository evidence. Phase 1 capture and Phase 3 dashboard/review remain team/system context unless evidence proves individual ownership.

- [ ] **Step 4: Confirm claim boundaries**

The portfolio must explicitly avoid claiming:

```text
production SaaS readiness
automated insurance adjudication
reliable true-new-damage detection from paired rentals before sufficient paired validation exists
completed before/after workflow
production-ready final model if no such model is accepted
```

- [ ] **Step 5: Verify all links and run the full test suite**

```powershell
git diff --check
python -m pytest -q -p no:cacheprovider
```

Record exact fresh counts.

- [ ] **Step 6: Commit the reconciled portfolio claims**

```powershell
git add -- README.md docs/01_portfolio/PROJECT_OVERVIEW.md docs/01_portfolio/MODEL_EVALUATION.md docs/01_portfolio/RESULTS_AND_LIMITATIONS.md docs/01_portfolio/INTERVIEW_GUIDE.md
git diff --cached --check
git commit -m "docs: reconcile FleetVision portfolio claims"
git push origin main
```

---

### Task 11: Run the Chat-Independent Cold-Start Acceptance Test

**Files:**
- Create: `docs/02_workflow/COLD_START_ACCEPTANCE.md`
- Modify only after PASS: `docs/02_workflow/HANDOFF_CURRENT.md`
- Modify only after PASS: `docs/02_workflow/PROJECT_STATUS.md`
- Modify only after PASS: `START_HERE.md`

**Interfaces:**
- Consumes: final GitHub reading paths plus reorganized Drive artifact root.
- Produces: objective evidence that old ChatGPT conversations are no longer required.

- [ ] **Step 1: Create the acceptance document before testing**

Required checklist:

```markdown
# FleetVision Cold-Start Acceptance

## Inputs Allowed
- GitHub repository
- Google Drive FleetVision root
- No historical FleetVision chat context

## Required Answers
- project problem and scope
- primary individual contribution
- current technical phase/activity
- completed vs partial vs planned capabilities
- next technical gate
- protected/raw/Frozen Test boundaries
- current model status without treating POC as production
- dataset status without treating relabel working copy as canonical
- architecture/before-after boundaries
- artifact storage/resume workflow

## Result
CHAT_HISTORY_REQUIRED = TRUE
```

Initial value must remain `TRUE` until the independent test passes.

- [ ] **Step 2: Start a new clean ChatGPT context**

Give it only the GitHub repository and Drive root. Use this prompt verbatim:

```text
Read the FleetVision repository and its linked Drive artifact structure. Without using any previous FleetVision chat history, explain: (1) the project problem and scope, (2) what is implemented/partial/planned, (3) my primary contribution versus team-system context, (4) the current technical phase and next authorized gate, (5) protected/raw/Frozen Test boundaries, (6) the current model and dataset provenance status, (7) where large artifacts live, and (8) exactly how development should resume.
```

- [ ] **Step 3: Grade every required answer as PASS or FAIL**

Any material error fails the cold-start gate. In particular, fail if the new session:

```text
calls a POC/folder-named model production/final
calls the relabel working copy canonical Dataset v3
claims A3 is authorized
uses Frozen Test for tuning
claims before/after damage comparison is implemented
attributes team Phase 1/3 work to the individual without evidence
requires an old chat to recover a missing critical fact
```

- [ ] **Step 4: If any item fails, repair GitHub/Drive source-of-truth and rerun from a new clean context**

Do not weaken the acceptance rubric to make the test pass.

- [ ] **Step 5: On full PASS, change the result to**

```text
CHAT_HISTORY_REQUIRED = FALSE
```

Update `HANDOFF_CURRENT.md`, `PROJECT_STATUS.md`, and `START_HERE.md` to state that historical chat is not required for project resumption.

- [ ] **Step 6: Commit the cold-start gate**

```powershell
git add -- START_HERE.md docs/02_workflow/COLD_START_ACCEPTANCE.md docs/02_workflow/HANDOFF_CURRENT.md docs/02_workflow/PROJECT_STATUS.md
git diff --cached --check
git commit -m "docs: verify chat-independent FleetVision handoff"
git push origin main
```

Old ChatGPT threads may be manually retired only after this remote checkpoint is verified.

---

### Task 12: Final Reset Verification and Portfolio-Ready Paused Checkpoint

**Files:**
- Modify: `docs/02_workflow/PROJECT_STATUS.md`
- Modify: `docs/02_workflow/HANDOFF_CURRENT.md`
- Modify: `docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md`
- Modify: `README.md` only if final verification exposes a stale link/status.

**Interfaces:**
- Consumes: all prior tasks.
- Produces: final maintenance-reset completion checkpoint; technical development remains paused.

- [ ] **Step 1: Verify GitHub documentation structure**

```powershell
$required = @(
  'README.md',
  'START_HERE.md',
  'AGENTS.md',
  'PROJECT_CONTEXT_BRIEF.md',
  'docs/01_portfolio/PROJECT_OVERVIEW.md',
  'docs/01_portfolio/ARCHITECTURE.md',
  'docs/01_portfolio/DATA_PIPELINE.md',
  'docs/01_portfolio/MODEL_EVALUATION.md',
  'docs/01_portfolio/RESULTS_AND_LIMITATIONS.md',
  'docs/01_portfolio/INTERVIEW_GUIDE.md',
  'docs/02_workflow/PROJECT_STATUS.md',
  'docs/02_workflow/HANDOFF_CURRENT.md',
  'docs/02_workflow/PROTECTED_ASSETS.md',
  'docs/02_workflow/WORKFLOW.md',
  'docs/02_workflow/ASSET_INVENTORY.md',
  'docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md',
  'docs/02_workflow/MODEL_REGISTRY.md',
  'docs/02_workflow/DATASET_REGISTRY.md',
  'docs/02_workflow/RESULTS_REGISTRY.md',
  'docs/02_workflow/COLD_START_ACCEPTANCE.md',
  'docs/03_decisions/README.md'
)
$required | ForEach-Object { "{0}`t{1}" -f (Test-Path $_), $_ }
```

Expected: every row begins `True`.

- [ ] **Step 2: Verify Drive root acceptance**

Drive root must contain the six approved top-level areas as the active structure:

```text
00_PORTFOLIO
01_DATA
02_MODELS
03_EXPERIMENTS
04_PROJECT_ASSETS
99_ARCHIVE
```

Legacy items may exist only if the manifest explicitly records an unresolved blocker. The target completion state is no unclassified legacy item at root.

- [ ] **Step 3: Verify the no-delete invariant**

Inspect `DRIVE_MIGRATION_MANIFEST.md`. Every first-pass row must retain:

```text
Delete Allowed = false
```

and the maintenance reset must report permanent deletion count `0`.

- [ ] **Step 4: Verify provenance registries**

Pass conditions:

```text
no active model is selected solely by folder name
no dataset working copy is labeled canonical by name alone
every portfolio metric maps to RESULTS_REGISTRY
test-use boundaries are explicit
Drive locations are recorded for large artifacts
```

- [ ] **Step 5: Verify current technical state did not advance**

`PROJECT_STATUS.md` and `HANDOFF_CURRENT.md` must still state:

```text
Technical phase = Phase 05S-A2
Technical development = PAUSED
Next technical gate = PHASE_05S_A3_IMPLEMENTATION_AUTHORIZATION_BEFORE_CODE
A3 authorized = false
```

Portfolio maintenance must not create a fake technical phase completion.

- [ ] **Step 6: Run fresh repository verification**

```powershell
python -m pytest -q -p no:cacheprovider
git diff --check
git status --short
```

Required: `0 failed`; `git diff --check` no output; worktree clean or protected-untracked-only.

- [ ] **Step 7: Update final reset status**

Add to `PROJECT_STATUS.md`:

```text
Portfolio reset = COMPLETE
Drive active structure = CLEAN
A1 archive classification = COMPLETE
Model provenance = RECONCILED
Dataset provenance = RECONCILED
Metric provenance = RECONCILED
Chat dependency = NONE
Technical development = PAUSED
Resume gate = PHASE_05S_A3_IMPLEMENTATION_AUTHORIZATION_BEFORE_CODE
```

Only use `COMPLETE`/`RECONCILED` if the preceding checks actually passed.

- [ ] **Step 8: Commit and push the final paused checkpoint**

```powershell
git add -- README.md docs/02_workflow/PROJECT_STATUS.md docs/02_workflow/HANDOFF_CURRENT.md docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md
git diff --cached --check
git diff --cached --name-only
git commit -m "docs: complete FleetVision portfolio maintenance reset"
git push origin main
git status --short
git log -1 --oneline
```

Remote verification must confirm the final commit before reporting reset completion.

---

## Explicitly Deferred Work

The following are not part of this implementation plan and require separate authorization/specification:

```text
Phase 05S-A3 implementation
new before/after pairing implementation
new model training or fine-tuning
Frozen Test access or re-evaluation
canonical/raw dataset mutation
production deployment
segmentation expansion
permanent Drive archive deletion
```

A later optional archive-cleanup task may delete only an explicit user-approved list of independently verified duplicates/empty/superseded artifacts.

---

## Plan Self-Review

### Spec Coverage

- Source-of-truth separation: Tasks 1–4.
- GitHub portfolio and development reading paths: Tasks 2–4.
- A1 Drive skeleton and classified archive: Tasks 5–9.
- First-pass no-delete policy: Global constraints + Tasks 5–9 + Task 12.
- Model provenance: Task 8.
- Dataset provenance: Task 9.
- Metric provenance: Tasks 8 and 10.
- Interview-first claims and ownership boundaries: Tasks 4 and 10.
- Cold-start test: Task 11.
- Chat retirement gate: Task 11.
- Final paused state and resume point: Task 12.

No approved design requirement is intentionally omitted.

### Placeholder Scan

PASS — the plan contains no unresolved placeholder markers or unspecified validation steps. Deferred work is explicitly outside this plan rather than a placeholder.

### Interface / Naming Consistency

PASS — all current workflow files use `docs/02_workflow/`; portfolio files use `docs/01_portfolio/`; the active decision index uses `docs/03_decisions/`; legacy governance is moved to `docs/99_archive/legacy_project_management/`.

### Scope Check

PASS — although the reset touches GitHub documentation and Drive artifacts, the tasks are intentionally sequential parts of one approved maintenance program. Each task ends at an independently reviewable Git/Drive checkpoint, and no technical feature development is mixed into the reset.
