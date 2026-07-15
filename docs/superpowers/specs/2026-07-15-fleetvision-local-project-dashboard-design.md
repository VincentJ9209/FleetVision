# FleetVision Local Project Dashboard Design Specification

- **Date:** 2026-07-15
- **Status:** `APPROVED_FOR_IMPLEMENTATION`
- **Project:** FleetVision / Project_FleetVision
- **Subproject:** FleetVision Local Project Dashboard
- **Selected direction:** A — repository-tracked static dashboard
- **Proposed repository spec path:** `docs/superpowers/specs/2026-07-15-fleetvision-local-project-dashboard-design.md`
- **Proposed dashboard path:** `docs/00_project_management/project_dashboard/`
- **Implementation authorization:** `GRANTED_BY_VINCENT_2026-07-15`
- **Dashboard worktree creation authorization:** `GRANTED_AFTER_LOCAL_PREFLIGHT_V3_PASS`
- **Phase 04.5N implementation commit authorization:** `NOT_GRANTED_BY_THIS_SPEC`
- **N1 execution authorization:** `NOT_GRANTED`
- **N2 execution authorization:** `NOT_GRANTED`
- **Retraining status:** `NOT_YET_APPROVED`
- **Deployment acceptance:** `NOT_YET_APPROVED`

---

## 1. Purpose

FleetVision Local Project Dashboard is a **read-only local project-governance and evidence dashboard**. It presents the repository checkpoint, Phase/Gate map, current work focus, authorized and prohibited actions, safety hard gates, test evidence, Result ZIP metadata, and historical timeline.

It is not the Phase 10 product inference dashboard. It must not:

- run model inference;
- read unauthorized test-split artifacts;
- execute Phase 04.5N-1 or Phase 04.5N-2;
- modify canonical annotations or canonical COCO;
- modify datasets, Registry records, or fixed splits;
- start training, retraining, or fine-tuning;
- authorize a Gate from the browser.

The dashboard must answer these questions without requiring the operator to reconstruct state from chat history:

1. What Phase and Gate are formally recorded in the repository?
2. What candidate work exists outside production `main`?
3. What is completed, in progress, pending review, ready, pending execution, blocked, planned, future, or not approved?
4. What is the next authorized action?
5. What actions are prohibited?
6. What Git checkpoint, tests, classification, artifact path, and SHA256 support each state?
7. Are formal repository state and candidate worktree state synchronized?
8. Are safety hard gates clear?

---

## 2. Repository evidence and verification boundary

### 2.1 Independently verified remote facts

```text
Repository: VincentJ9209/FleetVision
Default branch: main
Remote main HEAD: 374b2b99b997810da3e3c2beac0d7174df7c0e5f
Commit subject: docs: add phase04.5N design and implementation plan
```

The remote commit contains the approved Phase 04.5N design and detailed implementation plan. It does not contain the operator-reported Task 1–3 candidate implementation.

### 2.2 Repository sources reviewed

The design uses the required startup order and relevant decision sources:

```text
docs/00_project_management/START_HERE.md
AGENTS.md
PROJECT_CONTEXT_BRIEF.md
docs/00_project_management/WORKFLOW_GOVERNANCE.md
docs/00_project_management/HUMAN_REVIEW_INTERFACE_STANDARD.md
docs/00_project_management/PROTECTED_ASSETS.md
docs/00_project_management/PROJECT_STATUS.md
docs/00_project_management/HANDOFF_CURRENT.md
docs/00_project_management/MASTER_PHASE_MAP.md
docs/00_project_management/phase_logs/PHASE_04_5_LOG.md
docs/00_project_management/DECISION_LOG.md
docs/superpowers/specs/2026-07-15-phase04-5n-controlled-annotation-correction-promotion-design.md
docs/superpowers/plans/2026-07-15-phase04-5n-controlled-annotation-correction-promotion.md
```

### 2.3 Local facts not independently verified in this environment

The following Windows paths are not directly accessible from the current execution environment:

```text
G:\Project\FleetVision
C:\Users\Vincent\AppData\Local\Temp\FleetVision_phase04_5n_implementation_374b2b9
```

Therefore these facts remain `OPERATOR_REPORTED` until the supplied PowerShell 5.1 local preflight is run:

```text
Branch=main
Local HEAD=374b2b99b997810da3e3c2beac0d7174df7c0e5f
origin/main=374b2b99b997810da3e3c2beac0d7174df7c0e5f
Production worktree contains only outputs/metadata/external_assets/...
Task 1 independent review=PASS
Task 2 independent review=PASS
Task 3=PASS
Task 3 focused tests=66/66 passed
Task 1–3 regression=98/98 passed
IMPLEMENTATION_COMMITTED=NO
PUSH_COMPLETED=NO
N1_EXECUTED=NO
N2_EXECUTED=NO
CANONICAL_COCO_MODIFIED=NO
DATASET_MODIFIED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
```

### 2.4 Local preflight Gate

Before any repository write or Dashboard worktree creation, a local preflight must verify:

- repository root and current branch;
- local HEAD, `origin/main`, and remote `main` HEAD;
- production worktree invariant;
- registered worktrees;
- exact Phase 04.5N implementation worktree path, branch, HEAD, and status;
- absence of an unexpected existing Dashboard worktree;
- presence and SHA256 of required governance documents;
- no direct conflict with the expected design base checkpoint.

A remote-only check is insufficient for commit, push, or worktree creation.

---

## 3. Repository-state findings that shape the design

### 3.1 Formal state and candidate state are different concepts

The repository-backed `main` contains Phase 04.5N design and implementation plan. The operator reports an implementation candidate in an isolated worktree with Task 1–3 tests passing, but it is uncommitted and unpushed.

The dashboard must display both states and must never silently upgrade candidate evidence into formal repository state.

### 3.2 Governance documents contain historical and controlling sections

Some project-management files retain older summaries above newer addenda. The dashboard data preparation process must use source precedence and controlling markers, not simply the first Phase/status text found in a file.

Examples of possible disagreement:

- top-of-file status versus later controlling addendum;
- `PROJECT_STATUS.md` versus an older Phase log;
- formal repository state versus an uncommitted implementation worktree;
- narrative status versus actual Git SHA or artifact SHA256.

The dashboard must preserve and display conflicts instead of guessing.

### 3.3 Phase 04.5N authorization boundary is immutable

```text
04.5N-1 — Staged Correction Build and Validation
04.5N-2 — Separately Authorized Atomic Promotion
```

An N1 PASS does not authorize N2. Candidate implementation completion does not mean N1 was executed. N2 requires a separate explicit authorization and fresh pre-promotion verification.

### 3.4 Protected assets and worktree invariant

Permitted production worktree states:

```text
clean
or only:
?? outputs/metadata/external_assets/
```

Any other staged, modified, deleted, renamed, or untracked path blocks Dashboard worktree creation, Apply, Commit, and Push.

---

## 4. Scope

### 4.1 In scope for the Dashboard subproject

1. Complete Phase and Gate mapping from repository-backed governance records.
2. Current formal state and separate operational candidate state.
3. Overall and per-Phase governance progress bars.
4. Current work focus, next authorized action, blocking conditions, and prohibited actions.
5. Git checkpoint and worktree alignment.
6. Safety hard-gate display.
7. Gate test counts, outcome, classification, commit checkpoint, Result ZIP path, and SHA256 evidence.
8. Historical timeline.
9. Search and status filters.
10. Offline operation with local files only.
11. Automatic refresh through a loopback local HTTP server.
12. UI/data separation using `project_status.json` and `project_history.json`.
13. JSON Schema contracts and validation.
14. Future controlled status updates from Result ZIP evidence.
15. Git tracking of source, schema, small normalized JSON governance data, tests, and documentation.
16. Exclusion of large Result ZIPs and generated evidence from Git.
17. Dedicated Dashboard worktree isolated from Phase 04.5N implementation work.

### 4.2 Out of scope for the first implementation

1. Browser editing or write-back.
2. Automatic Git commands from the browser.
3. Client-side mutation of governance Markdown.
4. Automatic parsing of arbitrary prose into authoritative state.
5. Result ZIP Apply without a separate authorization Gate.
6. N1 or N2 execution.
7. Canonical annotation promotion.
8. Dataset, Registry, or fixed-split mutation.
9. Test-split access.
10. Inference, training, retraining, fine-tuning, or deployment acceptance.
11. Cloud hosting.
12. Authentication or multi-user collaboration.
13. Replacing `PROJECT_STATUS.md`, `HANDOFF_CURRENT.md`, `MASTER_PHASE_MAP.md`, Phase logs, or Decision Log as formal sources.
14. Committing Result ZIPs, extracted evidence, images, models, databases, caches, or review packages.
15. Codex or Cursor Agent usage.

---

## 5. Approaches considered

### 5.1 Selected: Vanilla static dashboard

```text
HTML + CSS + JavaScript + JSON
No framework
No bundler
No CDN
No remote font
No telemetry
No Node runtime requirement
```

**Advantages**

- Matches the approved HTML/CSS/JavaScript direction.
- Fully offline when served from localhost.
- Small dependency and review surface.
- Easy Git diff and long-term maintenance.
- UI and data remain cleanly separated.
- No generated build directory is required.

**Trade-off**

- UI components and runtime structural validation must be implemented directly.
- Charts should remain simple and governance-focused.

### 5.2 Rejected for initial version: generated static site

A Python script could generate the final HTML from repository documents. This is rejected for the initial version because it would blur source-data and presentation boundaries and create generated HTML as another state artifact.

### 5.3 Rejected for this subproject: Streamlit dashboard

Streamlit remains the default for multi-case human-review workflows. This Dashboard is a read-only governance view with an approved static HTML/CSS/JavaScript direction, so Streamlit is unnecessary here.

---

## 6. Repository location and worktree isolation

### 6.1 Tracked Dashboard location

```text
docs/00_project_management/project_dashboard/
```

### 6.2 Design spec location

```text
docs/superpowers/specs/2026-07-15-fleetvision-local-project-dashboard-design.md
```

### 6.3 Dedicated worktree requirement

Dashboard design finalization, implementation, tests, and review must use a dedicated worktree created from the exact approved production checkpoint.

It must not use or modify:

```text
C:\Users\Vincent\AppData\Local\Temp\FleetVision_phase04_5n_implementation_374b2b9
```

Recommended pattern:

```text
Worktree: C:\Users\Vincent\AppData\Local\Temp\FleetVision_project_dashboard_<base-short-sha>
Branch: feature/local-project-dashboard
```

The exact base SHA must be resolved from live Git after local preflight. Worktree creation must fail closed when:

- production `main` is not synchronized;
- remote `main` moved from the reviewed base;
- production status violates the protected invariant;
- the Dashboard worktree path already exists unexpectedly;
- the branch points to unrelated work;
- the path overlaps the Phase 04.5N worktree;
- required source-of-truth documents are missing.

No Dashboard implementation begins in the production checkout.

---

## 7. Proposed file structure

```text
docs/00_project_management/project_dashboard/
├─ README.md
├─ index.html
├─ assets/
│  ├─ dashboard.css
│  ├─ dashboard.js
│  └─ icons.svg
├─ data/
│  ├─ project_status.json
│  └─ project_history.json
└─ schemas/
   ├─ project_status.schema.json
   └─ project_history.schema.json
```

Supporting files, subject to a separately approved implementation plan:

```text
scripts/
├─ serve_project_dashboard.ps1
├─ validate_project_dashboard_data.py
└─ update_project_dashboard_from_result_zip.py   # future controlled capability

tests/
├─ test_project_dashboard_data.py
├─ test_project_dashboard_static.py
└─ test_project_dashboard_result_zip_update.py   # future controlled capability
```

The first implementation may omit the Result ZIP updater while preserving its interfaces and data contracts. The initial version must include data validation and must not rely only on browser rendering for correctness.

---

## 8. Source-of-truth and trust model

### 8.1 Source precedence

The Dashboard preserves FleetVision precedence:

1. Live Git facts.
2. SHA256 calculated from actual artifacts.
3. `PROJECT_STATUS.md` controlling section.
4. `HANDOFF_CURRENT.md` controlling section.
5. Current Phase log.
6. `MASTER_PHASE_MAP.md`.
7. Decision Log and approved design/plan records relevant to the state.
8. Historical chat or operator narrative.

### 8.2 Trust levels

```text
REPOSITORY_VERIFIED
ARTIFACT_VERIFIED
WORKTREE_VERIFIED
OPERATOR_REPORTED
STALE_OR_CONFLICTING
UNVERIFIED
```

Definitions:

- `REPOSITORY_VERIFIED`: read from the named repository file at a recorded Git ref or from Git metadata.
- `ARTIFACT_VERIFIED`: independently calculated path, size, and SHA256 match the recorded evidence.
- `WORKTREE_VERIFIED`: local preflight directly inspected the named worktree.
- `OPERATOR_REPORTED`: supplied by the operator but not independently inspected in the current environment.
- `STALE_OR_CONFLICTING`: contradicted by a higher-precedence source or controlling addendum.
- `UNVERIFIED`: present but not validated.

### 8.3 Authority boundary

The Dashboard is a derived visualization. It does not become the formal authority merely because its JSON is tracked.

Every displayed Phase, Gate, status, classification, checkpoint, test result, evidence ZIP, and safety declaration must include `source_refs`.

Example:

```json
{
  "source_refs": [
    {
      "type": "repository_file",
      "path": "docs/00_project_management/PROJECT_STATUS.md",
      "ref": "374b2b99b997810da3e3c2beac0d7174df7c0e5f",
      "section": "PHASE_04_5M_IMPLEMENTATION_PASS"
    }
  ]
}
```

### 8.4 Formal and candidate state separation

The Dashboard must show:

```text
Formal repository state
Operational candidate state
Alignment classification
Conflict or missing-evidence warnings
```

Initial representation:

```text
Formal main:
- Remote HEAD 374b2b99...
- 04.5N design and implementation plan repository-backed
- 04.5N candidate implementation not committed to main

Operational candidate:
- Separate 04.5N implementation worktree
- Task 1 independent review PASS
- Task 2 independent review PASS
- Task 3 PASS
- 66/66 focused tests reported
- 98/98 Task 1–3 regression reported
- commit pending
- push pending
- N1 not executed
- N2 not executed or authorized
```

Candidate state must never overwrite formal state.

---

## 9. Status, outcome, and alignment taxonomy

### 9.1 Status values

```text
COMPLETED
IN_PROGRESS
PENDING_REVIEW
READY
PENDING_EXECUTION
BLOCKED
NOT_APPROVED
PLANNED
FUTURE
FROZEN
DEPRECATED
```

### 9.2 Outcome values

```text
PASS
FAIL
BLOCKED
NOT_RUN
NOT_APPLICABLE
UNKNOWN
```

### 9.3 Alignment values

```text
SYNCED
LOCAL_AHEAD
REMOTE_AHEAD
DIVERGED
CANDIDATE_UNCOMMITTED
CANDIDATE_COMMITTED_NOT_PUSHED
FORMAL_CANDIDATE_CONFLICT
UNKNOWN
```

The UI must use text and an icon in addition to color.

---

## 10. Data architecture

## 10.1 `project_status.json`

Purpose: current snapshot only.

```json
{
  "schema_version": "1.0",
  "snapshot_id": "sha256:<fingerprint>",
  "generated_at_utc": "2026-07-15T00:00:00Z",
  "display_timezone": "Asia/Taipei",
  "project": {},
  "repository": {},
  "state_alignment": {},
  "current_focus": {},
  "safety_gates": [],
  "phases": [],
  "gates": [],
  "evidence": [],
  "warnings": []
}
```

### Repository fields

```text
repository_name
repository_root
branch
local_head
origin_main
remote_head
checkpoint_subject
production_worktree_status
allowed_untracked_paths
candidate_worktrees
verification_level
verified_at_utc
```

Unknown local facts are represented as `null` and accompanied by a warning. Chat values must not be relabeled as verified.

### Current-focus fields

```text
technical_phase
technical_gate
formal_status
candidate_status
current_work_summary
next_authorized_action
prohibited_actions
blocking_conditions
```

### Phase fields

```text
phase_id
title
status
progress
weight
gate_ids
summary
source_refs
```

### Gate fields

```text
gate_id
phase_id
title
status
outcome
classification
progress
trust_level
test_summary
evidence_ids
git_checkpoint
authorized_actions
prohibited_actions
source_refs
```

### Evidence fields

```text
evidence_id
type
filename
path
sha256
size_bytes
classification
created_at_utc
verification_status
commit_policy
source_refs
```

Large Result ZIP evidence must use:

```text
commit_policy=DO_NOT_COMMIT
```

## 10.2 `project_history.json`

Purpose: append-only timeline.

```json
{
  "schema_version": "1.0",
  "snapshot_id": "sha256:<fingerprint>",
  "generated_at_utc": "2026-07-15T00:00:00Z",
  "events": []
}
```

Each event includes:

```text
event_id
occurred_at_utc
recorded_at_utc
phase_id
gate_id
event_type
status
outcome
classification
summary
git_checkpoint
test_summary
evidence_ids
safety_snapshot
trust_level
source_refs
```

Committed history events are immutable. A correction is a new correction event referencing the prior event; it is not an in-place rewrite.

## 10.3 Validation layers

Because the Dashboard uses vanilla JavaScript with no external schema library, validation is layered:

1. **Repository/CI validation:** Python validator performs full JSON Schema, referential-integrity, enum, uniqueness, progress, and source-reference checks before commit.
2. **Runtime validation:** JavaScript performs strict structural and critical-field validation before rendering.
3. **Fail-closed rendering:** invalid snapshots are rejected in full; the last valid snapshot remains visible with an error banner.

The browser does not silently ignore unknown critical fields or repair invalid data.

---

## 11. Phase and Gate mapping

The initial inventory must include all repository-backed Phases and every historically named Gate that is needed to explain project state. At minimum:

```text
Phase 00
Phase 01
Phase 02
Phase 03
Phase 03.5
Phase 04
  04A
  04B
  04C
  04D
  04E
Phase 04.5
  04.5A
  04.5B
  04.5C
  04.5D
  04.5E
  04.5F and its recorded sub-Gates
  04.5G
  04.5J
  04.5K
  04.5L and recorded sub-Gates
  04.5M-0
  04.5M-1
  04.5M-2
  04.5N-1
  04.5N-2
Phase 05
Phase 06
Phase 07
Phase 08
Phase 09
Phase 10
Future extensions
```

Requirements:

- preserve exact historical Gate IDs, names, outcomes, classifications, test counts, and evidence;
- do not flatten all sub-Gates into a single Phase status;
- mark deprecated or superseded state explicitly;
- keep 04.5N-1 and 04.5N-2 as independent authorization boundaries;
- represent missing or stale Phase-log coverage as a warning rather than inventing events.

---

## 12. Progress model

Progress bars represent governance milestone completion, not time or schedule forecasts.

### 12.1 Gate progress

Each Gate stores an explicit reviewed percentage. Browser code does not infer progress from prose or test counts.

### 12.2 Phase progress

```text
phase_progress =
  sum(completed_or_explicit_gate_weight) /
  sum(total_gate_weight) * 100
```

Rules:

- `COMPLETED` contributes full Gate weight.
- `IN_PROGRESS` contributes only an explicitly stored reviewed percentage.
- `PENDING_REVIEW`, `READY`, `PENDING_EXECUTION`, `BLOCKED`, `NOT_APPROVED`, `PLANNED`, and `FUTURE` contribute zero unless the JSON contains an explicitly reviewed partial value.
- N1 and N2 are weighted separately.

### 12.3 Overall progress

```text
overall_progress =
  sum(phase_weight * phase_progress) /
  sum(phase_weight)
```

The UI label must state:

```text
治理里程碑完成度，不代表工期完成度
```

### 12.4 Candidate implementation progress

A separate progress component prevents implementation completion from being mistaken for production execution:

```text
04.5N implementation Tasks 1–3: 3/3 passed
Implementation commit: pending
Push: pending
N1 production execution: not run
N2 canonical promotion: not authorized
```

---

## 13. User interface design

### 13.1 Primary desktop target

The main layout is optimized for a 27-inch desktop monitor while remaining responsive.

### 13.2 Header

- project title;
- data timestamp and trust state;
- formal/candidate alignment indicator;
- auto-refresh status;
- search box;
- manual refresh button.

### 13.3 Overview row

1. Overall governance progress.
2. Current formal technical Phase.
3. Current Gate and candidate Gate.
4. Formal repository checkpoint.
5. Safety hard-gate summary.

### 13.4 Main three-column region

- **Left:** Phase navigator and status filters.
- **Center:** Phase/Gate cards and progress.
- **Right:** current focus, next authorized action, prohibited actions, Git facts, worktree state, and evidence.

### 13.5 Lower sections

- evidence table;
- historical timeline;
- source/conflict warnings;
- data methodology and provenance.

### 13.6 Search targets

```text
Phase ID
Gate ID
title
classification
commit SHA
Result ZIP filename
evidence SHA256
summary
```

### 13.7 Filters

```text
All
Completed
In progress
Pending review
Ready
Pending execution
Blocked
Not approved
Planned
Future
```

Search and filters operate only in memory and never modify JSON.

### 13.8 Accessibility

- semantic landmarks;
- full keyboard operation;
- visible focus state;
- WCAG-compatible contrast;
- icon plus text for status;
- `aria-live` for refresh/error messages;
- respect `prefers-reduced-motion`;
- system fonts only;
- no hover-only functionality;
- Traditional Chinese UI labels;
- stable English machine values shown as secondary code text where useful.

---

## 14. Offline and local-server behavior

### 14.1 Offline definition

```text
No internet
No CDN
No remote API
No external font
No telemetry
All assets local
```

The supported mode is localhost HTTP, not direct `file://`, because browser security restrictions commonly block local JSON `fetch()`.

### 14.2 PowerShell 5.1 server wrapper

The implementation plan may add a wrapper around:

```text
python -m http.server <port> --bind 127.0.0.1 --directory docs/00_project_management/project_dashboard
```

The wrapper must:

- verify repository root and dashboard files;
- bind only to loopback;
- select or validate a port;
- open the browser;
- print one consolidated result block;
- not modify repository files;
- stop with a clear error when Python or required assets are unavailable.

### 14.3 Auto-refresh

Default polling interval:

```text
10 seconds
```

Behavior:

1. fetch status with cache disabled;
2. compare `snapshot_id` and `generated_at_utc`;
3. fetch history with cache disabled and compare its fingerprint;
4. render only after both files pass runtime validation and cross-reference checks;
5. preserve search, filters, expanded cards, and scroll context;
6. show last successful refresh and current error;
7. use exponential backoff after repeated failures, capped at 60 seconds;
8. retain the last valid snapshot on failure.

No WebSocket, daemon, external API, or background repository writer is required.

---

## 15. Safety hard-gate display

At minimum:

```text
TEST_SPLIT_READ
MODEL_INFERENCE_EXECUTED
CANONICAL_ANNOTATION_MODIFIED
CANONICAL_COCO_MODIFIED
DATASET_MODIFIED
REGISTRY_MODIFIED
FIXED_SPLITS_MODIFIED
TRAINING_STARTED
RETRAINING_STATUS
DEPLOYMENT_ACCEPTANCE
```

Each item includes:

```text
value
expected_safe_value
status
trust_level
source_refs
verified_at_utc
```

Current candidate expectation:

```text
TEST_SPLIT_READ=NO
MODEL_INFERENCE_EXECUTED=NO
CANONICAL_ANNOTATION_MODIFIED=NO
CANONICAL_COCO_MODIFIED=NO
DATASET_MODIFIED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```

Unsafe, unknown, stale, or conflicting values force:

```text
HARD GATE NOT CLEAR
```

A green hard-gate state requires verified evidence, not only a safe-looking string.

---

## 16. Git and worktree panel

Display:

```text
Repository
Branch
Local HEAD
origin/main
Remote HEAD
Commit subject
Production worktree classification
Allowed protected untracked paths
Candidate worktree path
Candidate branch
Candidate HEAD
Candidate status
Implementation committed
Push completed
Dashboard worktree path and branch
```

The browser never executes Git. Values come from controlled JSON snapshots.

Any production path outside the protected invariant renders as `BLOCKED`.

---

## 17. Evidence and test display

Each Gate may show:

```text
Focused tests
Regression tests
Full repository tests
Skipped tests
Failed tests
Outcome
Classification
Git checkpoint
Result ZIP filename
Result ZIP SHA256
Evidence trust level
Evidence source references
```

Current 04.5N candidate representation:

```text
focused_tests_passed=66
focused_tests_total=66
regression_tests_passed=98
regression_tests_total=98
trust_level=OPERATOR_REPORTED until local preflight or structured evidence verifies it
implementation_committed=false
push_completed=false
n1_executed=false
n2_executed=false
```

Large ZIPs remain outside Git. Only normalized metadata may be tracked after review.

---

## 18. Current-state update workflow

### 18.1 Initial and manual controlled updates

The first implementation uses reviewed JSON edits or a deterministic repository-side generator, followed by:

```text
Edit/Generate → Validate → Review diff → Commit exact paths → Push → Remote verify
```

The browser does not create state.

### 18.2 Future Result ZIP controlled updater

This is a future capability and is not required for initial UI completion unless separately approved.

Workflow:

```text
Audit → Proposal → Review → Apply → Verify
```

#### Audit

The updater receives one explicit Result ZIP path and:

- verifies existence, size, and SHA256;
- extracts only to an isolated temporary directory;
- rejects path traversal, absolute paths, device paths, and symlinks;
- locates structured result JSON and checksum manifests;
- never trusts filename alone;
- does not parse human-formatted pytest summaries;
- verifies classification and Gate transition against allowlists;
- verifies safety declarations;
- records source ZIP metadata.

#### Proposal

It produces outside final data paths:

```text
project_status.proposed.json
project_history_event.proposed.json
dashboard_update_audit.json
```

It does not overwrite current Dashboard data.

#### Apply

Apply requires separate explicit authorization and must:

- verify current JSON hashes have not drifted;
- validate proposed data against schemas and transition rules;
- append exactly one immutable history event;
- atomically replace the current status snapshot;
- create a small backup;
- rerun validators;
- record before/after SHA256;
- roll back on verification failure.

### 18.3 Artifact policy

```text
Result ZIP=DO_NOT_COMMIT
Extracted evidence=DO_NOT_COMMIT
Generated overlays/images=DO_NOT_COMMIT
Normalized small JSON metadata=MAY_COMMIT_AFTER_REVIEW
Small update audit summary=MAY_COMMIT_WHEN_DESIGNATED
```

---

## 19. Error handling

### 19.1 Data load failure

- retain last valid snapshot;
- show filename, timestamp, and error;
- do not render partial new data.

### 19.2 Schema or structural failure

- reject the new snapshot;
- show technical details;
- never silently coerce invalid enums, progress, or references.

### 19.3 Reference failure

Examples:

- Gate references an unknown Phase;
- evidence ID is missing;
- duplicate event or Gate ID;
- invalid status enum;
- progress outside 0–100;
- history event references an unknown Gate;
- formal and candidate state claim the same authority with conflicting facts.

Any critical reference failure blocks the new snapshot.

### 19.4 Trust conflict

When a state claims commit, push, execution, or promotion without supporting evidence:

```text
STATE EVIDENCE CONFLICT
```

---

## 20. Security and integrity

- read-only UI;
- data-derived strings rendered with safe text assignment, not unsafe HTML;
- no `eval` or dynamic code execution;
- no remote JavaScript;
- no user-provided HTML injection;
- strict JSON validation before rendering;
- loopback-only server;
- no telemetry;
- no secrets;
- no browser write-back;
- no automatic Git operation;
- no automatic Result ZIP Apply;
- no recursive hashing of large datasets;
- no exposure of sensitive local paths beyond explicitly approved governance fields;
- Content Security Policy compatible with local static assets;
- generated links are local evidence references only and are not executed automatically.

---

## 21. Test strategy

### 21.1 Data-contract tests

- JSON Schema acceptance and rejection;
- unique Phase, Gate, event, and evidence IDs;
- valid Phase/Gate/evidence references;
- status, outcome, alignment, and trust enums;
- progress bounds and formulas;
- mandatory source references;
- mandatory safety flags;
- Result ZIP commit policy;
- append-only history ordering and duplicate-event rejection;
- formal/candidate conflict detection;
- stale-source warning behavior;
- N1/N2 authorization separation.

### 21.2 Static-asset tests

- required files exist;
- no CDN, remote script, external font, or telemetry endpoint;
- `index.html` contains required semantic landmarks;
- JSON is not embedded as the authoritative source;
- no `eval`;
- safe text rendering;
- CSS contains focus and reduced-motion behavior;
- direct `file://` guidance is present;
- localhost server command binds to `127.0.0.1`.

### 21.3 Browser smoke checks

- Chrome and Edge on Windows;
- 27-inch desktop layout;
- narrow viewport;
- localhost load;
- auto-refresh;
- search;
- filters;
- timeline expansion;
- invalid or missing JSON;
- server stop/restart;
- state conflict warning;
- hard-gate warning;
- preservation of UI state across refresh.

### 21.4 Worktree and repository checks

- local preflight PASS;
- dedicated Dashboard worktree;
- no overlap with 04.5N worktree;
- exact changed-path allowlist;
- protected external-assets unchanged;
- `git diff --check`;
- production worktree invariant before commit/push;
- local HEAD = `origin/main` = remote HEAD after authorized closure.

### 21.5 Future updater tests

- valid Result ZIP proposal;
- wrong classification;
- missing checksum;
- path traversal and symlink rejection;
- duplicate history event;
- invalid Gate transition;
- current JSON drift;
- atomic Apply and rollback;
- large ZIP remains untracked.

---

## 22. Implementation acceptance criteria

Implementation may be declared complete only when structured evidence confirms:

```text
DASHBOARD_LOADS_FROM_LOCALHOST=YES
LOOPBACK_ONLY=YES
INTERNET_DEPENDENCY=NO
PROJECT_STATUS_JSON_SEPARATE=YES
PROJECT_HISTORY_JSON_SEPARATE=YES
JSON_SCHEMA_VALIDATION=PASS
RUNTIME_STRUCTURAL_VALIDATION=PASS
COMPLETE_PHASE_GATE_MAPPING=YES
OVERALL_PROGRESS_VISIBLE=YES
PER_PHASE_PROGRESS_VISIBLE=YES
CURRENT_FOCUS_VISIBLE=YES
NEXT_AUTHORIZED_ACTION_VISIBLE=YES
PROHIBITED_ACTIONS_VISIBLE=YES
FORMAL_AND_CANDIDATE_STATE_SEPARATE=YES
TRUST_LEVEL_VISIBLE=YES
GIT_CHECKPOINT_VISIBLE=YES
WORKTREE_STATE_VISIBLE=YES
SAFETY_HARD_GATES_VISIBLE=YES
TEST_COUNTS_VISIBLE=YES
CLASSIFICATION_VISIBLE=YES
RESULT_ZIP_EVIDENCE_VISIBLE=YES
SEARCH_WORKS=YES
STATUS_FILTERS_WORK=YES
TIMELINE_WORKS=YES
AUTO_REFRESH_WORKS=YES
LARGE_RESULT_ZIPS_COMMITTED=NO
PROTECTED_EXTERNAL_ASSETS_TOUCHED=NO
N1_EXECUTED=NO
N2_EXECUTED=NO
CANONICAL_ANNOTATION_MODIFIED=NO
CANONICAL_COCO_MODIFIED=NO
DATASET_MODIFIED=NO
REGISTRY_MODIFIED=NO
FIXED_SPLITS_MODIFIED=NO
TRAINING_STARTED=NO
RETRAINING_STATUS=NOT_YET_APPROVED
DEPLOYMENT_ACCEPTANCE=NOT_YET_APPROVED
```

Required closure evidence:

- focused Dashboard tests;
- relevant governance regression tests;
- full repository tests when required by the approved implementation plan;
- Python compile checks;
- PowerShell 5.1 parser check;
- browser smoke evidence;
- `git diff --check`;
- exact path allowlist;
- production and candidate worktree verification;
- independent review;
- explicit commit/push authorization;
- remote HEAD verification.

---

## 23. Design decisions

1. The Dashboard is a repository-tracked static site.
2. Vanilla HTML/CSS/JavaScript is selected.
3. No external runtime or build dependency is required.
4. Localhost HTTP is the supported offline mode.
5. The server binds to `127.0.0.1` only.
6. UI is read-only.
7. Current status and history are separate JSON files.
8. JSON Schema plus runtime validation is required.
9. Formal and candidate states are separate.
10. Trust level and source references are visible.
11. Progress is deterministic and not inferred from prose.
12. History is append-only.
13. Result ZIPs and extracted evidence remain outside Git.
14. Future Result ZIP updates use Audit → Proposal → Review → Apply → Verify.
15. The Dashboard cannot authorize or execute a Gate.
16. Dashboard work uses a dedicated worktree.
17. The 04.5N implementation worktree remains isolated.
18. N1 and N2 remain unexecuted and unauthorized.
19. Canonical data, Registry, fixed splits, and training remain protected.
20. Codex and Cursor Agent remain prohibited.
21. Implementation is authorized by Vincent after `PREFLIGHT_PASS=True` on 2026-07-15.

---

## 24. Spec self-review

### Placeholder scan

- No `TBD`, `TODO`, or unresolved implementation authorization remains.
- Local facts are explicitly marked unverified rather than guessed.

### Internal consistency

- Static UI, JSON separation, localhost refresh, source precedence, and read-only boundary agree.
- N1/N2 authorization separation is preserved across data, UI, and acceptance criteria.

### Scope check

- Initial Dashboard UI/data validation is one coherent implementation plan.
- Result ZIP updater is explicitly future/optional and may be split into a later plan.

### Ambiguity check

- Formal versus candidate state is explicit.
- Progress is governance progress, not schedule progress.
- Local preflight is mandatory before writes or worktree creation.
- The browser does not parse prose into authority or perform Git/data mutations.

---

## 25. Approval record

Vincent approved this design and authorized direct execution on 2026-07-15 after the local PowerShell 5.1 preflight reported:

```text
PREFLIGHT_PASS=True
LOCAL_HEAD=374b2b99b997810da3e3c2beac0d7174df7c0e5f
ORIGIN_MAIN=374b2b99b997810da3e3c2beac0d7174df7c0e5f
REMOTE_HEAD=374b2b99b997810da3e3c2beac0d7174df7c0e5f
PRODUCTION_WORKTREE_INVARIANT=PASS
DASHBOARD_WORKTREE_PATH_CLEAR=YES
```

Authorization is limited to the Dashboard subproject and does not authorize Phase 04.5N N1/N2 execution, canonical data mutation, Registry or fixed-split mutation, training, retraining, or deployment acceptance.
