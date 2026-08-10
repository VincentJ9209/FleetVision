# FleetVision Portfolio & Maintenance Reset — Design Spec
- Date: 2026-08-10
- Repository: `VincentJ9209/FleetVision`
- Target repository path: `docs/superpowers/specs/2026-08-10-fleetvision-portfolio-maintenance-reset-design.md`
- Current technical state: `Phase 05S-A2 — Implementation Plan Approved and Documented`
- Technical development: `PAUSED`
- Current activity: `PORTFOLIO_MAINTENANCE`
- Selected migration strategy: `A1 — Classified Archive`

## 1. Purpose

This maintenance reset converts FleetVision from a conversation-heavy, phase-history-heavy working project into a portfolio-ready and restartable repository with clear storage boundaries.

The target state has three explicit responsibilities:

1. **GitHub** is the project source of truth for code, configuration, automated tests, technical documentation, current status, decisions, and workflow.
2. **Google Drive** stores large or generated artifacts such as datasets, model weights, experiment outputs, videos, presentations, review packages, and classified historical archives.
3. **ChatGPT / other AI work sessions** are temporary execution contexts and must not contain unique project knowledge required to resume development.

The reset must preserve existing technical boundaries. It does not authorize Phase 05S-A3 implementation, training, fine-tuning, Frozen Test access, canonical dataset mutation, or deployment claims.

## 2. Success Criteria

The reset is complete only when all of the following are true:

- GitHub provides a concise portfolio reading path and a separate development-resumption path.
- `HANDOFF_CURRENT.md` contains current state only.
- `PROJECT_STATUS.md` and the phase map no longer function as historical chat transcripts.
- Google Drive root is reduced to six intentional top-level areas.
- Drive archive uses the approved A1 classified archive structure.
- No file is permanently deleted during the first migration pass.
- Dataset, model, and metric provenance are reconciled into explicit registries.
- Portfolio claims are backed by repository or artifact evidence.
- A cold-start session can reconstruct the current state from GitHub plus Drive without old chat history.
- Old FleetVision conversations can be deleted without losing unique project information.

## 3. Source-of-Truth Architecture

### 3.1 GitHub

GitHub is authoritative for:

- production code under `src/fleetvision/`;
- scripts, configuration, tests, SQL, and tracked notebook templates;
- architecture and data/workflow decisions;
- current technical phase and activity;
- project handoff and resumption instructions;
- portfolio documentation;
- artifact manifests and provenance references.

Large binary/generated assets remain outside Git.

### 3.2 Google Drive

Drive is an artifact vault, not the primary narrative record. Its target root is:

```text
FleetVision/
├── 00_PORTFOLIO/
├── 01_DATA/
├── 02_MODELS/
├── 03_EXPERIMENTS/
├── 04_PROJECT_ASSETS/
└── 99_ARCHIVE/
```

The approved A1 archive is:

```text
99_ARCHIVE/
├── 01_deprecated_notebooks/
├── 02_old_datasets/
├── 03_old_models/
├── 04_old_experiments/
├── 05_old_presentations/
├── 06_duplicate_candidates/
└── 99_uncategorized_legacy/
```

### 3.3 Chat Sessions

Chat sessions are disposable. A session may analyze, plan, or execute a scoped task, but any durable state change must be reflected in GitHub documentation and/or Drive artifact manifests before the session ends.

## 4. GitHub Information Architecture

The repository must expose two independent reading paths.

### 4.1 Portfolio path

```text
README.md
→ docs/01_portfolio/PROJECT_OVERVIEW.md
→ docs/01_portfolio/ARCHITECTURE.md
→ docs/01_portfolio/DATA_PIPELINE.md
→ docs/01_portfolio/MODEL_EVALUATION.md
→ docs/01_portfolio/RESULTS_AND_LIMITATIONS.md
→ docs/01_portfolio/INTERVIEW_GUIDE.md
```

Purpose: allow a hiring manager to understand the problem, scope, contribution, engineering decisions, evidence, results, and limitations within approximately 5–10 minutes.

### 4.2 Development-resumption path

```text
START_HERE.md
→ PROJECT_CONTEXT_BRIEF.md
→ docs/02_workflow/PROJECT_STATUS.md
→ docs/02_workflow/HANDOFF_CURRENT.md
→ task-specific decision / safety document only when needed
```

Purpose: allow a new AI session or developer to recover the current state without reading old chats or large historical logs.

### 4.3 Target documentation structure

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
    ├── 02_workflow/
    ├── 03_decisions/
    └── 99_archive/
```

Historical phase logs, superseded handoffs, and deprecated specifications may be retained under `docs/99_archive/` only when they still have independent audit or learning value. Purely duplicated narrative may be removed from current files because Git history already preserves prior versions.

## 5. Current-Document Simplification Rules

### 5.1 `HANDOFF_CURRENT.md`

Must contain current state only:

- technical phase;
- current activity;
- last completed gate;
- next authorized gate when development resumes;
- current safety boundaries;
- current authoritative assets;
- known open items;
- exact resume instructions.

Historical 04.5L, 04.5M, 05R, and prior 05S handoff blocks must not remain in the current handoff after migration.

### 5.2 `PROJECT_STATUS.md`

Must summarize:

- current technical status;
- completed major capabilities;
- partial/planned capabilities;
- current risks and unresolved provenance issues;
- resume point.

It must not serve as an append-only execution transcript.

### 5.3 Phase map

Must become a high-level roadmap. Fine-grained gates belong in archived phase logs or Git history, not the primary roadmap.

### 5.4 `AGENTS.md`

Must retain only rules that materially prevent unsafe or inconsistent work:

- startup reading order;
- protected asset boundaries;
- raw/Frozen Test restrictions;
- large artifact policy;
- engineering/test discipline;
- Git verification and commit rules.

Repeated governance blocks and obsolete AI-specific operational detail should be removed or archived.

### 5.5 `START_HERE.md`

Every session reads only the minimum core context by default. Additional documents are loaded just-in-time according to task type.

## 6. Portfolio Presentation Design

The root README must be interview-first, not governance-first. It should lead with:

1. the business/operational problem;
2. the user’s actual contribution and project scope;
3. architecture;
4. key engineering challenges;
5. evidence-backed results;
6. demo assets;
7. stack;
8. repository tour;
9. reproducibility/testing;
10. limitations and current status.

The repository must distinguish the broader three-stage team architecture from the user’s primary Phase 2 contribution. Phase 1 capture and Phase 3 review/dashboard may be shown as system context or integration surfaces, but must not be presented as individually implemented work unless supported by evidence.

Recommended technical evidence case studies:

- Data governance and human review pipeline.
- External dataset intake, license/registry, bbox QA, canonicalization, and deduplication.
- Human-in-the-loop Streamlit/SQLite review workflow.
- YOLOv8 validation/error-analysis methodology.
- Before/after comparison architecture, explicitly labeled implemented/partial/planned as appropriate.

## 7. Drive Migration Classification

Every major Drive item receives exactly one primary classification during the first pass:

- `CURRENT`
- `PORTFOLIO`
- `ARCHIVE`
- `DUPLICATE_CANDIDATE`
- `PROTECTED`
- `RECONCILE_REQUIRED`

The first migration pass permits moves and reclassification only after audit. It permits no permanent deletion.

### 7.1 Initial known mapping

- `00.成果發表/` → split between `00_PORTFOLIO/` and `04_PROJECT_ASSETS/`.
- `internal_grouped_dataset_v1_20260717_212356/` → `01_DATA/01_internal/`, protected historical baseline.
- `dataset_v3_relabel_working_20260720_091414/` → `99_ARCHIVE/02_old_datasets/`, because its own README identifies it as a working copy rather than canonical Dataset v3.
- Same relabel ZIP → `99_ARCHIVE/06_duplicate_candidates/` pending content verification.
- `grouped_dataset/` → archive/reconciliation first because of legacy/flattened structure.
- `models/` → split only after model provenance reconciliation.
- `notebooks/` → retain a small set of representative notebooks; archive recovery/debug/deprecated variants.
- `outputs/` → retain selected evidence; archive full historical experiment output trees.
- `04_5J/` and `04_5K/` → historical experiment evidence/archive.
- root-level duplicate notebooks and ZIPs → duplicate-candidate review before any deletion.

## 8. Migration Manifest

Before moving high-value assets, create a Drive migration manifest with at least:

- current path;
- file/folder name;
- artifact type;
- classification;
- target path;
- decision rationale/evidence;
- protected flag;
- deletion allowed flag;
- verification result;
- checksum or identity data when available.

During the first pass, `deletion_allowed=false` for every item.

## 9. Provenance Reconciliation

### 9.1 Model registry

Create a registry that maps each model candidate to:

- training dataset/version;
- experiment/notebook;
- weight location;
- SHA256 where available;
- validation metrics;
- test metrics and test-use boundary;
- experiment date;
- quality/deployment status;
- allowed portfolio claim.

A folder named `final_selected` must not be assumed to be the current reference model. If no model satisfies the desired quality/provenance bar, the valid outcome is to declare that there is no production/final model and identify a verified historical baseline instead.

### 9.2 Results registry

Every displayed metric must be tied to:

- model;
- dataset/version;
- split;
- threshold/operating point when relevant;
- date;
- evidence artifact;
- allowed interpretation.

Resume and portfolio claims may use only evidence-backed values from this registry.

### 9.3 Dataset registry

Create a registry that differentiates:

- raw source data;
- reviewed/canonical data;
- frozen/holdout data;
- working copies;
- training exports;
- historical baselines;
- external datasets and license/lineage status.

Working copies must never be implicitly promoted by file naming alone.

## 10. Migration Execution Order

Implementation must follow this order:

1. **Phase A — Freeze and inventory**: read-only inventory; no move/delete.
2. **Phase B — GitHub source-of-truth cleanup**: create concise portfolio/workflow paths and current docs.
3. **Phase C — Drive skeleton creation**: create approved top-level and archive folders; old data remains intact.
4. **Phase D — Category-by-category Drive migration**: Portfolio → Project Assets → Notebooks → Experiments → Models → Datasets → remaining legacy.
5. **Phase E — Model, metric, and dataset reconciliation**.
6. **Phase F — Portfolio claims and presentation finalized from reconciled evidence**.
7. **Phase G — Cold-start test**.
8. **Phase H — Chat-history retirement**.
9. **Phase I — Portfolio-ready paused-state checkpoint**.

Datasets move late because lineage, holdout boundaries, and duplication risk are higher.

## 11. Per-Batch Migration Gate

Every Drive batch must use:

```text
Audit → Classify → Move → Verify → Update Manifest → Next Batch
```

A failed verification stops that batch. Protected assets and unique artifacts remain in place until identity and target placement are confirmed.

## 12. Cold-Start Acceptance Test

A new session with no historical FleetVision conversation context receives only the GitHub repository and Drive artifact root.

It must correctly determine:

- project problem and scope;
- the user’s primary contribution;
- current technical phase/activity;
- completed vs partial vs planned capabilities;
- next technical gate;
- protected/raw/Frozen Test boundaries;
- current model status without mistaking a historical POC for production;
- dataset status without mistaking a relabel working copy for canonical data;
- architecture and before/after workflow boundaries;
- where large artifacts live and how to resume work.

Pass condition:

```text
CHAT_HISTORY_REQUIRED = FALSE
```

Old FleetVision chat threads must not be retired before this gate passes.

## 13. Deletion Policy

Permanent Drive deletion is explicitly outside the first migration pass.

After the reset is complete, a separate optional archive-cleanup task may permanently remove only independently verified items such as:

- byte-identical duplicate ZIPs;
- empty folders;
- confirmed duplicate notebooks;
- duplicate model weights;
- fully superseded generated exports with preserved provenance.

Permanent deletion requires an explicit user-approved deletion list.

## 14. Final Definition of Done

The maintenance reset is complete when:

- README is interview-oriented and evidence-backed;
- portfolio and workflow docs are separated;
- current handoff contains current state only;
- status/phase documents are concise and non-duplicative;
- Drive root contains only the six approved top-level areas;
- A1 archive classification is complete;
- model, results, and dataset registries exist;
- representative notebooks and experiment evidence are selected;
- portfolio/demo/presentation assets are consolidated;
- no first-pass permanent deletion occurred;
- cold-start test passes;
- chat history is no longer required;
- technical development remains paused;
- the next technical resume point remains Phase 05S-A3 unless a later explicitly approved decision changes it.

## 15. Non-Goals

This reset does not include:

- new feature development;
- Phase 05S-A3 implementation;
- new model training/fine-tuning;
- Frozen Test access;
- canonical/raw dataset mutation;
- production deployment;
- automatic insurance/claim adjudication;
- segmentation expansion;
- permanent archive deletion in the first pass.

## 16. Self-Review Result

- Placeholder scan: PASS — no unresolved `TBD`/`TODO` requirements.
- Consistency check: PASS — GitHub is source of truth; Drive is artifact storage; chat is temporary throughout the design.
- Scope check: PASS — this document covers one maintenance-reset program and explicitly separates later deletion and technical development.
- Ambiguity check: PASS — first-pass deletion is prohibited; model/dataset naming is not accepted as provenance; cold-start pass is required before chat retirement.

