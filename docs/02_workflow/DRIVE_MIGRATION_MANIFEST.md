# FleetVision Drive Migration Manifest

## Rules
- First-pass permanent deletion: `false` for every row.
- Every move requires before/after verification.
- `PROTECTED` or `RECONCILE_REQUIRED` rows may not be moved until the relevant task approves them.

| ID | Current Path | Name | Type | Classification | Protected | Target Path | Evidence / Rationale | Delete Allowed | Verification |
|---|---|---|---|---|---|---|---|---|---|
| DRV-001 | Drive root | `00.成果發表/` | Folder | PORTFOLIO | No | split to `00_PORTFOLIO/` and `04_PROJECT_ASSETS/` | Portfolio presentation material; split requires later item-level inventory. | false | NOT_STARTED |
| DRV-002 | Drive root | `internal_grouped_dataset_v1_20260717_212356/` | Folder | PROTECTED | Yes | `01_DATA/01_internal/` after dataset gate | Protected internal dataset; no move without dataset gate. | false | NOT_STARTED |
| DRV-003 | Drive root | `dataset_v3_relabel_working_20260720_091414/` | Folder | ARCHIVE | No | `99_ARCHIVE/02_old_datasets/` | Historical relabel working dataset retained as archive. | false | NOT_STARTED |
| DRV-004 | Drive root | relabel working ZIP | ZIP file | DUPLICATE_CANDIDATE | No | `99_ARCHIVE/06_duplicate_candidates/` | Identity must be verified before any duplicate decision. | false | NOT_STARTED |
| DRV-005 | Drive root | `grouped_dataset/` | Folder | RECONCILE_REQUIRED | Yes | archive/reconciliation first | Dataset provenance and identity require reconciliation. | false | NOT_STARTED |
| DRV-006 | Drive root | `models/` | Folder | RECONCILE_REQUIRED | Yes | reconcile before selecting current model | Model identities and current selection require reconciliation. | false | NOT_STARTED |
| DRV-007 | Drive root | `notebooks/` | Folder | RECONCILE_REQUIRED | No | select representatives; archive remainder | Representative notebooks require review before archiving. | false | NOT_STARTED |
| DRV-008 | Drive root | `outputs/` | Folder | RECONCILE_REQUIRED | No | retain evidence; archive remainder | Evidence retention requires reconciliation before archival. | false | NOT_STARTED |
| DRV-009 | Drive root | `04_5J/` | Folder | ARCHIVE | No | `99_ARCHIVE/04_old_experiments/` | Historical experiment retained as archive. | false | NOT_STARTED |
| DRV-010 | Drive root | `04_5K/` | Folder | ARCHIVE | No | `99_ARCHIVE/04_old_experiments/` | Historical experiment retained as archive. | false | NOT_STARTED |
