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

## Task 5 — Drive Reset Skeleton Gate

- Gate result: `VERIFIED`
- Pre-create My Drive root direct-child count: `7`
- Post-create My Drive root direct-child count: `8`
- Root preservation: `7/7` original direct-child IDs remain under My Drive root parent `0ABtYiOl2DqpDUk9PVA`
- Destination folders: `32 CREATED`, `0 REUSED` (`1` FleetVision root, `6` top-level folders, `25` required subfolders)
- Empty-destination readback: `25/25` required leaf folders have zero direct children
- Existing asset actions: `0` move, `0` rename, `0` copy, `0` upload, `0` share, `0` trash, `0` delete
- First-pass permanent deletion count: `0`
- Existing migration rows `DRV-001` through `DRV-010` remain `NOT_STARTED`; Task 5 created empty destinations only.

### Pre-create My Drive Root Direct Children

| Name | Type | Observed ID | Observed Link |
|---|---|---|---|
| `Vincent_AI_Portfolio/` | Folder | `1AfS4e7wYYLjn_3DEgZqcve2F-USFNFC-` | [Open](https://drive.google.com/drive/folders/1AfS4e7wYYLjn_3DEgZqcve2F-USFNFC-) |
| `橘家有事｜YouTube 專案/` | Folder | `1tkaHCtXINoxyGV2H-ri0-zDqigUcwOPd` | [Open](https://drive.google.com/drive/folders/1tkaHCtXINoxyGV2H-ri0-zDqigUcwOPd) |
| `Career/` | Folder | `12zt3Uqmh3eZ1Ok8-MVu3uomqfscgQK6a` | [Open](https://drive.google.com/drive/folders/12zt3Uqmh3eZ1Ok8-MVu3uomqfscgQK6a) |
| `AI_Class/` | Folder | `1pnYHGkUKQxy9lVxOgeGELsAj8HaVv3Uh` | [Open](https://drive.google.com/drive/folders/1pnYHGkUKQxy9lVxOgeGELsAj8HaVv3Uh) |
| `透過 Chrome 儲存/` | Folder | `1Ph8sW3L0IaChAeEKGhv39TRpsEcxePi4` | [Open](https://drive.google.com/drive/folders/1Ph8sW3L0IaChAeEKGhv39TRpsEcxePi4) |
| `投資交易/` | Folder | `1wIHDzr38fKYgaKmkZmqxvrSrLK6k-Qw8` | [Open](https://drive.google.com/drive/folders/1wIHDzr38fKYgaKmkZmqxvrSrLK6k-Qw8) |
| `Google AI Studio/` | Folder | `1QtGyVrpR0LQ1RGAUiTJBu6MvUq9UrEWI` | [Open](https://drive.google.com/drive/folders/1QtGyVrpR0LQ1RGAUiTJBu6MvUq9UrEWI) |

### Drive Destination IDs

| Destination Path | State | Drive ID | Link | Readback |
|---|---|---|---|---|
| `FleetVision/` | CREATED | `1wiabQ8ELbyd7UOvZlXkyrQLQbwfb0Wif` | [Open](https://drive.google.com/drive/folders/1wiabQ8ELbyd7UOvZlXkyrQLQbwfb0Wif) | VERIFIED: 6 direct children |
| `FleetVision/00_PORTFOLIO/` | CREATED | `1FV0ZpCmn7xlesHuDzhFAeM2dvbBgTjzW` | [Open](https://drive.google.com/drive/folders/1FV0ZpCmn7xlesHuDzhFAeM2dvbBgTjzW) | VERIFIED: 4 direct children |
| `FleetVision/00_PORTFOLIO/01_Project_Overview/` | CREATED | `1cKNE0NQKu2dj6VeIbraEx4nmHPnEfhUe` | [Open](https://drive.google.com/drive/folders/1cKNE0NQKu2dj6VeIbraEx4nmHPnEfhUe) | VERIFIED: empty |
| `FleetVision/00_PORTFOLIO/02_Presentation/` | CREATED | `12EXU7wRyLJ9gY22urzbaAnydIZTMI5B7` | [Open](https://drive.google.com/drive/folders/12EXU7wRyLJ9gY22urzbaAnydIZTMI5B7) | VERIFIED: empty |
| `FleetVision/00_PORTFOLIO/03_Demo/` | CREATED | `1s_L5ux-OW6aI4fBPrdheAbk7tVbyQCO5` | [Open](https://drive.google.com/drive/folders/1s_L5ux-OW6aI4fBPrdheAbk7tVbyQCO5) | VERIFIED: empty |
| `FleetVision/00_PORTFOLIO/04_Interview_Assets/` | CREATED | `1e-GR83QhGgf9FwrRg61krO2P6qZjcMOu` | [Open](https://drive.google.com/drive/folders/1e-GR83QhGgf9FwrRg61krO2P6qZjcMOu) | VERIFIED: empty |
| `FleetVision/01_DATA/` | CREATED | `1dVA2CajesUX9m4bOckSFtXxiUnzY538K` | [Open](https://drive.google.com/drive/folders/1dVA2CajesUX9m4bOckSFtXxiUnzY538K) | VERIFIED: 4 direct children |
| `FleetVision/01_DATA/01_internal/` | CREATED | `1bMzY5H48l7svSj_YU0hD-8qbSTLOaMMB` | [Open](https://drive.google.com/drive/folders/1bMzY5H48l7svSj_YU0hD-8qbSTLOaMMB) | VERIFIED: empty |
| `FleetVision/01_DATA/02_external/` | CREATED | `16nUXFkoZq173e2z_7TWHa6pMPkwFj8qt` | [Open](https://drive.google.com/drive/folders/16nUXFkoZq173e2z_7TWHa6pMPkwFj8qt) | VERIFIED: empty |
| `FleetVision/01_DATA/03_reviewed/` | CREATED | `1lxAmz3ck--b9JsogQqAPbSziRVgCO-yH` | [Open](https://drive.google.com/drive/folders/1lxAmz3ck--b9JsogQqAPbSziRVgCO-yH) | VERIFIED: empty |
| `FleetVision/01_DATA/04_annotations/` | CREATED | `1R5m1PxdGsnl3iI2MQ7efblC7Hu_wO4N2` | [Open](https://drive.google.com/drive/folders/1R5m1PxdGsnl3iI2MQ7efblC7Hu_wO4N2) | VERIFIED: empty |
| `FleetVision/02_MODELS/` | CREATED | `1Qdu1a9Bz8yJMCTHmsw7u2BR8d0Bvi-Pk` | [Open](https://drive.google.com/drive/folders/1Qdu1a9Bz8yJMCTHmsw7u2BR8d0Bvi-Pk) | VERIFIED: 3 direct children |
| `FleetVision/02_MODELS/01_current/` | CREATED | `18aS9iKTDBUlV3ivsWlzw15nU4SKSK7LV` | [Open](https://drive.google.com/drive/folders/18aS9iKTDBUlV3ivsWlzw15nU4SKSK7LV) | VERIFIED: empty |
| `FleetVision/02_MODELS/02_evaluation/` | CREATED | `1fHMj15sLeD8AGyrUBmB9bk2LcA2wi-77` | [Open](https://drive.google.com/drive/folders/1fHMj15sLeD8AGyrUBmB9bk2LcA2wi-77) | VERIFIED: empty |
| `FleetVision/02_MODELS/03_model_evidence/` | CREATED | `1VMss9gCmwHXiudj97ItldBbnnUTVefvD` | [Open](https://drive.google.com/drive/folders/1VMss9gCmwHXiudj97ItldBbnnUTVefvD) | VERIFIED: empty |
| `FleetVision/03_EXPERIMENTS/` | CREATED | `1gq9ILZ9zpcRrYSqJQBuCyN8sqP_1m4C1` | [Open](https://drive.google.com/drive/folders/1gq9ILZ9zpcRrYSqJQBuCyN8sqP_1m4C1) | VERIFIED: 4 direct children |
| `FleetVision/03_EXPERIMENTS/01_notebooks/` | CREATED | `1Lngwx-YQLlKaLWSs6KxA_nYgd8roGctI` | [Open](https://drive.google.com/drive/folders/1Lngwx-YQLlKaLWSs6KxA_nYgd8roGctI) | VERIFIED: empty |
| `FleetVision/03_EXPERIMENTS/02_training/` | CREATED | `1SIARHVvSzec2xUqgELkPqGpteJBcHV4w` | [Open](https://drive.google.com/drive/folders/1SIARHVvSzec2xUqgELkPqGpteJBcHV4w) | VERIFIED: empty |
| `FleetVision/03_EXPERIMENTS/03_inference/` | CREATED | `1GfDc6azLwvWkZEqxk9InGK9fSltIyMBe` | [Open](https://drive.google.com/drive/folders/1GfDc6azLwvWkZEqxk9InGK9fSltIyMBe) | VERIFIED: empty |
| `FleetVision/03_EXPERIMENTS/04_evaluation/` | CREATED | `1r24tmCQGDl1Dl_CnmxTsmOHMC-CP_Gvp` | [Open](https://drive.google.com/drive/folders/1r24tmCQGDl1Dl_CnmxTsmOHMC-CP_Gvp) | VERIFIED: empty |
| `FleetVision/04_PROJECT_ASSETS/` | CREATED | `1i0NAzvD82Ih8nIp70clk6EtY9SUJl0Sd` | [Open](https://drive.google.com/drive/folders/1i0NAzvD82Ih8nIp70clk6EtY9SUJl0Sd) | VERIFIED: 3 direct children |
| `FleetVision/04_PROJECT_ASSETS/01_phase1_capture/` | CREATED | `1qTeD-y9uEpuSOquJCzKA_BvrPUG94Jag` | [Open](https://drive.google.com/drive/folders/1qTeD-y9uEpuSOquJCzKA_BvrPUG94Jag) | VERIFIED: empty |
| `FleetVision/04_PROJECT_ASSETS/02_phase2_detection/` | CREATED | `1udVhs2TKxgzOeDuGAtvnZPiGEaAzEPS0` | [Open](https://drive.google.com/drive/folders/1udVhs2TKxgzOeDuGAtvnZPiGEaAzEPS0) | VERIFIED: empty |
| `FleetVision/04_PROJECT_ASSETS/03_phase3_dashboard/` | CREATED | `1a5SrioOwdTitxQ2qYilrhHcqRd2jbODx` | [Open](https://drive.google.com/drive/folders/1a5SrioOwdTitxQ2qYilrhHcqRd2jbODx) | VERIFIED: empty |
| `FleetVision/99_ARCHIVE/` | CREATED | `1UtHROZBdOjzAbEcexQigzapzRvU0Tqjs` | [Open](https://drive.google.com/drive/folders/1UtHROZBdOjzAbEcexQigzapzRvU0Tqjs) | VERIFIED: 7 direct children |
| `FleetVision/99_ARCHIVE/01_deprecated_notebooks/` | CREATED | `1d_wPAIJQrdCjuXaQMQl7dBuZqXQTDbeI` | [Open](https://drive.google.com/drive/folders/1d_wPAIJQrdCjuXaQMQl7dBuZqXQTDbeI) | VERIFIED: empty |
| `FleetVision/99_ARCHIVE/02_old_datasets/` | CREATED | `1H1QGj-n6wZrVzQcEBcC0ziaVOztg8D89` | [Open](https://drive.google.com/drive/folders/1H1QGj-n6wZrVzQcEBcC0ziaVOztg8D89) | VERIFIED: empty |
| `FleetVision/99_ARCHIVE/03_old_models/` | CREATED | `15DV3cOZdUzPs6dIY4ViWFZXxlCIQN6P6` | [Open](https://drive.google.com/drive/folders/15DV3cOZdUzPs6dIY4ViWFZXxlCIQN6P6) | VERIFIED: empty |
| `FleetVision/99_ARCHIVE/04_old_experiments/` | CREATED | `1Hn3sDT1RqZNyzjaYu2YA5tN0W6I8twfb` | [Open](https://drive.google.com/drive/folders/1Hn3sDT1RqZNyzjaYu2YA5tN0W6I8twfb) | VERIFIED: empty |
| `FleetVision/99_ARCHIVE/05_old_presentations/` | CREATED | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` | [Open](https://drive.google.com/drive/folders/146utuTSsHtomWALO-PkXLeWliwO4ThG0) | VERIFIED: empty |
| `FleetVision/99_ARCHIVE/06_duplicate_candidates/` | CREATED | `1GKTVtkwZX9UdznlZ2E9y0oNf0EYL2oqK` | [Open](https://drive.google.com/drive/folders/1GKTVtkwZX9UdznlZ2E9y0oNf0EYL2oqK) | VERIFIED: empty |
| `FleetVision/99_ARCHIVE/99_uncategorized_legacy/` | CREATED | `1qfeTTOEjOlz-0sdx66mTaiRzCi8jdwoR` | [Open](https://drive.google.com/drive/folders/1qfeTTOEjOlz-0sdx66mTaiRzCi8jdwoR) | VERIFIED: empty |

### Independent Readback

| Listed Parent | Expected Direct Children | Observed Direct Children | Result |
|---|---:|---:|---|
| My Drive root | 8 (7 original + `FleetVision/`) | 8 | VERIFIED |
| `FleetVision/` | 6 | 6 | VERIFIED |
| `FleetVision/00_PORTFOLIO/` | 4 | 4 | VERIFIED |
| `FleetVision/01_DATA/` | 4 | 4 | VERIFIED |
| `FleetVision/02_MODELS/` | 3 | 3 | VERIFIED |
| `FleetVision/03_EXPERIMENTS/` | 4 | 4 | VERIFIED |
| `FleetVision/04_PROJECT_ASSETS/` | 3 | 3 | VERIFIED |
| `FleetVision/99_ARCHIVE/` | 7 | 7 | VERIFIED |
