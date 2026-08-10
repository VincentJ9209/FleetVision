# FleetVision Asset Inventory

## Inventory Status
- Design baseline Git commit: `ca4869ccbd418640269f4d8460a5cdf22959e810`
- Execution baseline Git commit: `e32abbba173cd43abe9e1f2de371c1382e73c004`
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
| Current governance | `docs/99_archive/legacy_project_management/` | ARCHIVED | Historical governance retained for auditability; current workflow is under `docs/02_workflow/` |
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
