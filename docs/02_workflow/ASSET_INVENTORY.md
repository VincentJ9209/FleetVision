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
| `internal_grouped_dataset_v1_20260717_212356/` | `FleetVision/01_DATA/01_internal/` | PROTECTED / HISTORICAL_BASELINE | Yes | Keep; Task 9 parent move VERIFIED, same Drive item ID |
| `dataset_v3_relabel_working_20260720_091414/` | `FleetVision/99_ARCHIVE/02_old_datasets/` | ARCHIVE / WORKING_COPY | No | Keep archived; explicitly NOT_CANONICAL |
| relabel working ZIP | `FleetVision/99_ARCHIVE/06_duplicate_candidates/` | DUPLICATE_CANDIDATE | No | Keep; no deletion/equivalence claim |
| `FleetVision_YOLO_Labels_Package.zip` | old project root | ARCHIVE_RECONCILIATION | Yes | NOT_MOVED; export provenance unresolved |
| `grouped_dataset/` | old project root | ARCHIVE_RECONCILIATION | Yes | NOT_MOVED; lineage/holdout unresolved |
| `models/` | Drive root | RECONCILE_REQUIRED | Yes | reconcile before selecting current model |
| `notebooks/` | Drive root | RECONCILE_REQUIRED | No | select representatives; archive remainder |
| `outputs/` | Drive root | RECONCILE_REQUIRED | No | retain evidence; archive remainder |
| `04_5J/` | Drive root | ARCHIVE | No | `99_ARCHIVE/04_old_experiments/` |
| `04_5K/` | Drive root | ARCHIVE | No | `99_ARCHIVE/04_old_experiments/` |

## Drive Reset Skeleton

- Skeleton gate: `VERIFIED`
- FleetVision destination root: `1wiabQ8ELbyd7UOvZlXkyrQLQbwfb0Wif` ([Open](https://drive.google.com/drive/folders/1wiabQ8ELbyd7UOvZlXkyrQLQbwfb0Wif))
- Folder result: `32 CREATED`, `0 REUSED`
- Structure result: `6/6` top-level folders and `25/25` required subfolders verified
- Empty-destination result: all `25` leaf folders have zero direct children
- Root preservation: all `7` pre-existing My Drive root direct children retain their original IDs and My Drive root parent
- Existing asset migration: `NOT_STARTED`; Task 5 did not move, rename, copy, upload, share, trash, or delete an existing asset
- First-pass permanent deletion count: `0`
- Complete destination IDs, links, creation state, and readback evidence: `docs/02_workflow/DRIVE_MIGRATION_MANIFEST.md`

| Top-level Destination | State | Drive ID | Link | Required Subfolders |
|---|---|---|---|---:|
| `00_PORTFOLIO/` | CREATED | `1FV0ZpCmn7xlesHuDzhFAeM2dvbBgTjzW` | [Open](https://drive.google.com/drive/folders/1FV0ZpCmn7xlesHuDzhFAeM2dvbBgTjzW) | 4/4 VERIFIED |
| `01_DATA/` | CREATED | `1dVA2CajesUX9m4bOckSFtXxiUnzY538K` | [Open](https://drive.google.com/drive/folders/1dVA2CajesUX9m4bOckSFtXxiUnzY538K) | 4/4 VERIFIED |
| `02_MODELS/` | CREATED | `1Qdu1a9Bz8yJMCTHmsw7u2BR8d0Bvi-Pk` | [Open](https://drive.google.com/drive/folders/1Qdu1a9Bz8yJMCTHmsw7u2BR8d0Bvi-Pk) | 3/3 VERIFIED |
| `03_EXPERIMENTS/` | CREATED | `1gq9ILZ9zpcRrYSqJQBuCyN8sqP_1m4C1` | [Open](https://drive.google.com/drive/folders/1gq9ILZ9zpcRrYSqJQBuCyN8sqP_1m4C1) | 4/4 VERIFIED |
| `04_PROJECT_ASSETS/` | CREATED | `1i0NAzvD82Ih8nIp70clk6EtY9SUJl0Sd` | [Open](https://drive.google.com/drive/folders/1i0NAzvD82Ih8nIp70clk6EtY9SUJl0Sd) | 3/3 VERIFIED |
| `99_ARCHIVE/` | CREATED | `1UtHROZBdOjzAbEcexQigzapzRvU0Tqjs` | [Open](https://drive.google.com/drive/folders/1UtHROZBdOjzAbEcexQigzapzRvU0Tqjs) | 7/7 VERIFIED |

## Task 9 — Dataset Provenance Gate

- Gate result: `VERIFIED_WITH_EXPLICIT_UNRESOLVED_ITEMS`.
- Dataset registry: `docs/02_workflow/DATASET_REGISTRY.md`.
- Metadata-only Drive moves: `3 VERIFIED`.
- Explicit unresolved items retained in old project root: `2` (`grouped_dataset/`, `FleetVision_YOLO_Labels_Package.zip`).
- Working relabel copy remains `WORKING_COPY / NOT_CANONICAL` and was archived; it was not promoted to Dataset v3.
- Protected internal baseline moved last with the same Drive item ID into `FleetVision/01_DATA/01_internal/`; content was not mutated.
- Frozen Test contents were not accessed; first-pass permanent deletion remains `0`.
