# FleetVision Drive Migration Manifest

## Rules
- First-pass permanent deletion: `false` for every row.
- Every move requires before/after verification.
- `PROTECTED` or `RECONCILE_REQUIRED` rows may not be moved until the relevant task approves them.

| ID | Current Path | Name | Type | Classification | Protected | Target Path | Evidence / Rationale | Delete Allowed | Verification |
|---|---|---|---|---|---|---|---|---|---|
| DRV-001 | `AI_Class/00.Project/FleetVision/` (parent ID `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl`) | `00.成果發表/` (ID `1JPupMGmZK7tp5wQtc5tBLXcdjesgaQYi`) | Folder | RECONCILE_REQUIRED | No | item-level split to approved Task 6 targets; source root itself remains in place | Live Drive grounding supersedes the generic `Drive root` label. Complete Task 6 inventory, moves, verification, and explicit NOT_MOVED rows are recorded below. | false | VERIFIED_WITH_NOT_MOVED — 31 metadata-only moves verified; 17 inventory rows retained |
| DRV-002 | Drive root | `internal_grouped_dataset_v1_20260717_212356/` | Folder | PROTECTED | Yes | `01_DATA/01_internal/` after dataset gate | Protected internal dataset; no move without dataset gate. | false | NOT_STARTED |
| DRV-003 | Drive root | `dataset_v3_relabel_working_20260720_091414/` | Folder | ARCHIVE | No | `99_ARCHIVE/02_old_datasets/` | Historical relabel working dataset retained as archive. | false | NOT_STARTED |
| DRV-004 | Drive root | relabel working ZIP | ZIP file | DUPLICATE_CANDIDATE | No | `99_ARCHIVE/06_duplicate_candidates/` | Identity must be verified before any duplicate decision. | false | NOT_STARTED |
| DRV-005 | Drive root | `grouped_dataset/` | Folder | RECONCILE_REQUIRED | Yes | archive/reconciliation first | Dataset provenance and identity require reconciliation. | false | NOT_STARTED |
| DRV-006 | Drive root | `models/` | Folder | RECONCILE_REQUIRED | Yes | reconcile before selecting current model | Model identities and current selection require reconciliation. | false | NOT_STARTED |
| DRV-007 | `FleetVision/99_ARCHIVE/01_deprecated_notebooks/` | `notebooks/` (ID `15U1-zwBIrVJ6VtLMbX-X_1VgV907IRxl`) | Folder | ARCHIVE | No | Keep archived; active evidence is limited to two tracked output-stripped notebooks | Six-notebook legacy/recovery container moved whole after notebook audit. | false | VERIFIED — T7-MOVE-001 |
| DRV-008 | old project root (ID `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl`) | `outputs/` (ID `1EkkV5JqRRK8vIZ6FzYgTTRG9_fIsYVzf`) | Folder | RECONCILE_REQUIRED | Yes | NOT_MOVED; later Task 8/9 item-level reconciliation | Mixed tree includes model/data and protected evaluation scope. | false | NOT_MOVED_TASK7_MIXED_SCOPE |
| DRV-009 | old project root (ID `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl`) | `04_5J/` (ID `1M-YAK1qvvKfaEQo7IuFd8jtNEarmQZgw`) | Folder | PROTECTED_RECONCILE_REQUIRED | Yes | Container NOT_MOVED; two direct notebooks archived item-by-item | `input/` and `runs/` remain in place; their contents were not listed or read. | false | ITEM_LEVEL_VERIFIED_CONTAINER_NOT_MOVED |
| DRV-010 | old project root (ID `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl`) | `04_5K/` (ID `1ScY9s0R08Jpwfccg_SnGjrJ_xmhRoR_Q`) | Folder | RECONCILE_REQUIRED | No | NOT_MOVED; later item-level reconciliation | Nested `runs/` was not proven wholly non-protected and Task 7-only. | false | NOT_MOVED_TASK7_BOUNDED_SAFETY |

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

## Task 6 — Portfolio and Project Asset Migration Pre-Move Gate

### Grounding and Selection Result

- Grounded source: `AI_Class/00.Project/FleetVision/00.成果發表/` (ID `1JPupMGmZK7tp5wQtc5tBLXcdjesgaQYi`).
- Source parent: old `FleetVision/` (ID `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl`).
- Recursive inventory: `87` descendants = `14` folders + `73` files.
- Inventory completeness: every discovered folder was listed; the deepest branches, `02.PPT/re/` and `Cloud Function - Colab/reference/`, contain no further folders.
- Active presentation deck: `0` — `NO_EVIDENCE_SAFE_ACTIVE_ASSET`. The latest `v4.1` deck contains unreconciled metrics, a `正式版模型` label, and an `已完成端到端流程` claim that conflict with current repository boundaries.
- Active overview asset: `0` — `NO_EVIDENCE_SAFE_ACTIVE_ASSET`. The overview document contains unreconciled quantitative and team-system claims.
- Active demo asset: `0` — `NO_EVIDENCE_SAFE_ACTIVE_ASSET`. Available video content could not be audited sufficiently to exclude unsupported claims; the strongest candidate remains `RECONCILE_REQUIRED/NOT_MOVED`.
- Interview screenshots: `0` selected. Phase 1 and Phase 3 images remain team/system project context rather than active individual portfolio claims.
- Stable public link: none. No sharing change is authorized; `INTERVIEW_GUIDE.md` is unchanged.
- Model weights and non-presentation duplicate candidates: `RECONCILE_REQUIRED/NOT_MOVED`; same name or size is not duplicate identity.
- All first-pass rows retain `Delete Allowed=false`; permanent deletion remains `0`.

### Complete Recursive Inventory and Classification

All links and identities below were observed from the grounded source tree. `VIA_PARENT` means the item's bytes and own parent metadata are not changed; it remains inside a folder that has one recorded metadata-only move.

| # | Current Path / Name | Observed ID / Link | Type | Direct Parent ID | Visibility | Classification | Planned Execution |
|---:|---|---|---|---|---|---|---|
| 1 | `00.彙總發表/` | [`1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j`](https://drive.google.com/open?id=1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j) | Folder | `1JPupMGmZK7tp5wQtc5tBLXcdjesgaQYi` | not shared | RECONCILE_REQUIRED | NOT_MOVED; contains unresolved demo/model/notebook context |
| 2 | `01.web app/` | [`1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g`](https://drive.google.com/open?id=1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g) | Folder | `1JPupMGmZK7tp5wQtc5tBLXcdjesgaQYi` | not shared | RECONCILE_REQUIRED | NOT_MOVED; retains explicit non-presentation duplicate candidate |
| 3 | `02.Auto Labeling/` | [`1L8pV9VGLtRs89eknQbo12E8DlNDXOR1e`](https://drive.google.com/open?id=1L8pV9VGLtRs89eknQbo12E8DlNDXOR1e) | Folder | `1JPupMGmZK7tp5wQtc5tBLXcdjesgaQYi` | not shared | RECONCILE_REQUIRED | NOT_MOVED; retains model and duplicate-candidate artifacts |
| 4 | `03.系統部署&架構規劃/` | [`1HlzCo0bIBI7XakkweV-l2G8g0_a-SG3d`](https://drive.google.com/open?id=1HlzCo0bIBI7XakkweV-l2G8g0_a-SG3d) | Folder | `1JPupMGmZK7tp5wQtc5tBLXcdjesgaQYi` | not shared | PROJECT_ASSET | MOVE-001 VERIFIED |
| 5 | `00.彙總發表/3282_完整流程APP_DASHBOARDmp4` | [`1llx0Fzn4_bw3Zs6XTfijbOTPhKh3Dj_9`](https://drive.google.com/open?id=1llx0Fzn4_bw3Zs6XTfijbOTPhKh3Dj_9) | MP4 | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | shared; access not verified | ARCHIVE | MOVE-026 VERIFIED |
| 6 | `00.彙總發表/簡報架構` | [`1YYFLPjc7SM3KLW3SR8zkqa_ox8P4YyHFmFOeeI7eWdU`](https://drive.google.com/open?id=1YYFLPjc7SM3KLW3SR8zkqa_ox8P4YyHFmFOeeI7eWdU) | Google Doc | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | not shared | ARCHIVE | MOVE-027 VERIFIED |
| 7 | `00.彙總發表/3282_Billy-webapp-20260723-175216.mp4` | [`1ab1tKdN3bB1LmlM8uvmXI38Bvr2AooUO`](https://drive.google.com/open?id=1ab1tKdN3bB1LmlM8uvmXI38Bvr2AooUO) | MP4 | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | not shared | ARCHIVE | MOVE-028 VERIFIED |
| 8 | `00.彙總發表/05.Assets/` | [`1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1`](https://drive.google.com/open?id=1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1) | Folder | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | not shared | ARCHIVE | MOVE-018 VERIFIED after six child moves |
| 9 | `00.彙總發表/04.Demo/` | [`1QCIP8ye1WpZfIofFMQi5_tRi1rR37PGh`](https://drive.google.com/open?id=1QCIP8ye1WpZfIofFMQi5_tRi1rR37PGh) | Empty folder | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | not shared | ARCHIVE | MOVE-029 VERIFIED |
| 10 | `00.彙總發表/03.Speaker_Notes_QA/` | [`1gUQppQKYG3xv7w7Sxx5cum5j1B-N-Xkw`](https://drive.google.com/open?id=1gUQppQKYG3xv7w7Sxx5cum5j1B-N-Xkw) | Empty folder | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | not shared | ARCHIVE | MOVE-030 VERIFIED |
| 11 | `00.彙總發表/02.PPT/` | [`1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t`](https://drive.google.com/open?id=1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t) | Folder | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | not shared | RECONCILE_REQUIRED | NOT_MOVED; retains unaudited primary demo candidate |
| 12 | `00.彙總發表/01.Presentation_Master/` | [`1Hf9xsQyfs8z6VtwZ6cXftO4s1IgTIeHR`](https://drive.google.com/open?id=1Hf9xsQyfs8z6VtwZ6cXftO4s1IgTIeHR) | Folder | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | not shared | ARCHIVE | MOVE-031 VERIFIED |
| 13 | `00.彙總發表/Cloud Function - Colab/` | [`1XrK-FGC8hEccUX56ZywNnnCQ1mYe22WP`](https://drive.google.com/open?id=1XrK-FGC8hEccUX56ZywNnnCQ1mYe22WP) | Folder | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | not shared | RECONCILE_REQUIRED | NOT_MOVED; mixed model/notebook/credential scope |
| 14 | `00.彙總發表/05.Assets/06_最終車損模型訓練曲線.png` | [`1D-8ynDccx_DBDs1rW_nakoItXpWFL6KU`](https://drive.google.com/open?id=1D-8ynDccx_DBDs1rW_nakoItXpWFL6KU) | PNG | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | not shared | PROJECT_ASSET | MOVE-012 VERIFIED |
| 15 | `00.彙總發表/05.Assets/05_DBSCAN_分群結果.png` | [`153No-5Eos3nem7DOMHb7LCbAU2pPdlb3`](https://drive.google.com/open?id=153No-5Eos3nem7DOMHb7LCbAU2pPdlb3) | PNG | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | not shared | PROJECT_ASSET | MOVE-013 VERIFIED |
| 16 | `00.彙總發表/05.Assets/04_Feature_Correlation_Matrix.png` | [`1IEwrRciinWpmqtsv0nC0KFUbqLkthMey`](https://drive.google.com/open?id=1IEwrRciinWpmqtsv0nC0KFUbqLkthMey) | PNG | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | not shared | PROJECT_ASSET | MOVE-014 VERIFIED |
| 17 | `00.彙總發表/05.Assets/03_四角度實拍照片.png` | [`1-pSvHqt1Zxqc4WXx5kO3-zc7GQCtez7M`](https://drive.google.com/open?id=1-pSvHqt1Zxqc4WXx5kO3-zc7GQCtez7M) | PNG | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | not shared | PROJECT_ASSET | MOVE-015 VERIFIED |
| 18 | `00.彙總發表/05.Assets/02_WebApp_Demo流程畫面.png` | [`1l3QnkYqmp-qEYOCoYcoe-NuH5e-HPYNU`](https://drive.google.com/open?id=1l3QnkYqmp-qEYOCoYcoe-NuH5e-HPYNU) | PNG | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | not shared | PROJECT_ASSET | MOVE-016 VERIFIED |
| 19 | `00.彙總發表/05.Assets/01_系統部署架構圖.png` | [`1rABt3prY0n7vw1YwF0nNejtYqBhSpZPv`](https://drive.google.com/open?id=1rABt3prY0n7vw1YwF0nNejtYqBhSpZPv) | PNG | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | not shared | PROJECT_ASSET | MOVE-017 VERIFIED |
| 20 | `00.彙總發表/02.PPT/車況之眼_智慧巡檢系統_成果發表_v4.1` | [`1pjECAs6lH5kD6R5B9Slcgh05uPLzMsy5cO4k54sekQI`](https://drive.google.com/open?id=1pjECAs6lH5kD6R5B9Slcgh05uPLzMsy5cO4k54sekQI) | Google Slides | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | not shared | ARCHIVE | MOVE-019 VERIFIED; audited unsafe for active claims |
| 21 | `00.彙總發表/02.PPT/車況之眼_智慧巡檢系統.mp4` | [`150U7TxI00K3qoGO65OX98_T_u4c_5bgN`](https://drive.google.com/open?id=150U7TxI00K3qoGO65OX98_T_u4c_5bgN) | MP4 | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | not shared | ARCHIVE | MOVE-020 VERIFIED |
| 22 | `00.彙總發表/02.PPT/車況之眼_智慧巡檢系統_NMI.mp4` | [`1ojUBiwrx4jPD8m8zZbFoCO8jHgCkcDVm`](https://drive.google.com/open?id=1ojUBiwrx4jPD8m8zZbFoCO8jHgCkcDVm) | MP4 | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | not shared | ARCHIVE | MOVE-021 VERIFIED |
| 23 | `00.彙總發表/02.PPT/車況之眼_智慧巡檢系統_DemoVideo.mp4` | [`1BwvAcdC1SYo_cX7MDwdI6glUlDsP3ixq`](https://drive.google.com/open?id=1BwvAcdC1SYo_cX7MDwdI6glUlDsP3ixq) | MP4 | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | not shared | RECONCILE_REQUIRED | NOT_MOVED; content cannot be audited sufficiently |
| 24 | `00.彙總發表/02.PPT/講稿彙整` | [`1dZQTbe05wSoApvyQi71tRJ1I2In9yaQLxi7FgSUoOw4`](https://drive.google.com/open?id=1dZQTbe05wSoApvyQi71tRJ1I2In9yaQLxi7FgSUoOw4) | Google Doc | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | not shared | ARCHIVE | MOVE-022 VERIFIED |
| 25 | `00.彙總發表/02.PPT/簡報時間` | [`12vU3RWolYq4YHHdh3-PIYibSeHcZRTGrNyIGfC-Wy-8`](https://drive.google.com/open?id=12vU3RWolYq4YHHdh3-PIYibSeHcZRTGrNyIGfC-Wy-8) | Google Sheet | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | not shared | ARCHIVE | MOVE-023 VERIFIED |
| 26 | `00.彙總發表/02.PPT/FleetVision：從混亂到清晰的數據旅程.docx` | [`1It4GcH7ehbgGRLQR8rPIIgfjq1T8Nl-p`](https://drive.google.com/open?id=1It4GcH7ehbgGRLQR8rPIIgfjq1T8Nl-p) | DOCX | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | not shared | ARCHIVE | MOVE-024 VERIFIED; audited unsafe for active claims |
| 27 | `00.彙總發表/02.PPT/re/` | [`12anZhv5rGmp8laizHPyQjhptupVfxPb1`](https://drive.google.com/open?id=12anZhv5rGmp8laizHPyQjhptupVfxPb1) | Folder | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | not shared | ARCHIVE | MOVE-025 VERIFIED |
| 28 | `.../re/車況之眼_智慧巡檢系統_成果發表_v4` | [`1aZd-Y-7_SCeZAqHmLze2XlreM_ZJBrKy_TPn6GztMgs`](https://drive.google.com/open?id=1aZd-Y-7_SCeZAqHmLze2XlreM_ZJBrKy_TPn6GztMgs) | Google Slides | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 29 | `.../re/車況之眼_智慧巡檢系統_成果發表_v3.講稿版` | [`1RoDU2DsmXdqbY89t_v2RTYHgPeEgbH2lsLq8AL_SlIs`](https://drive.google.com/open?id=1RoDU2DsmXdqbY89t_v2RTYHgPeEgbH2lsLq8AL_SlIs) | Google Slides | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 30 | `.../re/車況之眼_智慧巡檢系統_成果發表_v2` | [`1v1uaoS8HmFa_kMWvEZW51LP4aFxaVvgZgDzBS3m5EmE`](https://drive.google.com/open?id=1v1uaoS8HmFa_kMWvEZW51LP4aFxaVvgZgDzBS3m5EmE) | Google Slides | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 31 | `.../re/車況之眼_智慧巡檢系統_成果發表_v1.pptx` | [`1ISOfkj4K9lGtZuCxcaTWsOgyrED1OhWQ`](https://drive.google.com/open?id=1ISOfkj4K9lGtZuCxcaTWsOgyrED1OhWQ) | PPTX | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 32 | `.../re/車況之眼_智慧巡檢系統_成果發表.pptx` | [`19rFyBUlC0OfUvZTzd2z9KoksD9SukiBD`](https://drive.google.com/open?id=19rFyBUlC0OfUvZTzd2z9KoksD9SukiBD) | PPTX | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 33 | `.../re/VehicleConditionEye_v1.8_Notebook_TED_Integrated.pptx` | [`1qbDuv8gbjqTLS7WqkhjC409BuSBpxWDH`](https://drive.google.com/open?id=1qbDuv8gbjqTLS7WqkhjC409BuSBpxWDH) | PPTX | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 34 | `.../re/車況之眼_智慧巡檢系統_成果發表_v1.3_穩定版.pptx` | [`1Lp3RgZg9tLQfT38O2q6sVp0agxFH75Mi`](https://drive.google.com/open?id=1Lp3RgZg9tLQfT38O2q6sVp0agxFH75Mi) | PPTX | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 35 | `.../re/車況之眼_智慧巡檢系統_成果發表_v1.2.pptx` | [`1jdlpCQuB0WYcb5Mu4GLRqoRqvGiD4csU`](https://drive.google.com/open?id=1jdlpCQuB0WYcb5Mu4GLRqoRqvGiD4csU) | PPTX | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 36 | `.../re/FleetVision_車況之眼_成果發表_最終定稿_v1.0.pptx` | [`1pwuV4NRxCiuIhyF5ApFwZXsddhuVCAzf`](https://drive.google.com/open?id=1pwuV4NRxCiuIhyF5ApFwZXsddhuVCAzf) | PPTX | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 37 | `.../re/車況之眼_智慧巡檢系統_TED_Edition_v2.1.pptx` | [`1w9uFGk_stJVpzW-fmPIgwnbey_kQ0ixW`](https://drive.google.com/open?id=1w9uFGk_stJVpzW-fmPIgwnbey_kQ0ixW) | PPTX | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 38 | `.../re/車況之眼_智慧巡檢系統_Conference_Edition_v3.1.pptx` | [`1sGeCQcEUkyKtjmNs3GXiWXr8qIo9eYuz`](https://drive.google.com/open?id=1sGeCQcEUkyKtjmNs3GXiWXr8qIo9eYuz) | PPTX | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 39 | `.../re/車況之眼_智慧巡檢系統_成果發表_新版_MASTER流程簡報_v1.pptx` | [`1Wo2SM6r8mbacQgOARRccYzmmfVcOG2_b`](https://drive.google.com/open?id=1Wo2SM6r8mbacQgOARRccYzmmfVcOG2_b) | PPTX | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 40 | `.../re/車況之眼_智慧巡檢系統_成果發表_Final_Candidate_v5_Editable.pptx` | [`1U9wvZWmtcTYOdVuF_ulNG8QgM0urQrmj`](https://drive.google.com/open?id=1U9wvZWmtcTYOdVuF_ulNG8QgM0urQrmj) | PPTX | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 41 | `.../re/車況之眼_智慧巡檢系統_成果發表_Final_Candidate_v4.pptx` | [`1Xi5_mfuitcgaha0oK86sy7if0imZdBXO`](https://drive.google.com/open?id=1Xi5_mfuitcgaha0oK86sy7if0imZdBXO) | PPTX | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 42 | `.../re/車況之眼_智慧巡檢系統_成果發表_Final_Candidate_v1.pptx` | [`1x0_03Ap6Ky4E7cd3xOxzMPxm4x6roewy`](https://drive.google.com/open?id=1x0_03Ap6Ky4E7cd3xOxzMPxm4x6roewy) | PPTX | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | not shared | ARCHIVE | VIA_PARENT MOVE-025 |
| 43 | `.../01.Presentation_Master/未命名文件` | [`1tRUt8I4rg7VlWegalCKqUovAGazRZvEE19WYPPCZRog`](https://drive.google.com/open?id=1tRUt8I4rg7VlWegalCKqUovAGazRZvEE19WYPPCZRog) | Google Doc | `1Hf9xsQyfs8z6VtwZ6cXftO4s1IgTIeHR` | not shared | ARCHIVE | VIA_PARENT MOVE-031 |
| 44 | `.../01.Presentation_Master/車況之眼_智慧巡檢系統_Presentation_Master_v1.0.docx` | [`1FpQhj22eU2LtJXIaZnOtct45g0YiOha9`](https://drive.google.com/open?id=1FpQhj22eU2LtJXIaZnOtct45g0YiOha9) | DOCX | `1Hf9xsQyfs8z6VtwZ6cXftO4s1IgTIeHR` | not shared | ARCHIVE | VIA_PARENT MOVE-031 |
| 45 | `.../Cloud Function - Colab/reference/` | [`1ledzNwpk3FUBnFeY8myLyZ_279cshCZe`](https://drive.google.com/open?id=1ledzNwpk3FUBnFeY8myLyZ_279cshCZe) | Folder | `1XrK-FGC8hEccUX56ZywNnnCQ1mYe22WP` | not shared | RECONCILE_REQUIRED | NOT_MOVED |
| 46 | `.../Cloud Function - Colab/YOLO_car_damage_detection_V5.pt` | [`1qrMR1absDvDKWEbhGE6pV5Q3K7_f3HzB`](https://drive.google.com/open?id=1qrMR1absDvDKWEbhGE6pV5Q3K7_f3HzB) | Model artifact | `1XrK-FGC8hEccUX56ZywNnnCQ1mYe22WP` | not shared | RECONCILE_REQUIRED | NOT_MOVED; later model reconciliation |
| 47 | `.../Cloud Function - Colab/車損辨識引擎 Colab 串接_v1.ipynb` | [`1MGGB2gcSySxSIMDGZC8dsTgSoZC4sJwb`](https://drive.google.com/open?id=1MGGB2gcSySxSIMDGZC8dsTgSoZC4sJwb) | Notebook | `1XrK-FGC8hEccUX56ZywNnnCQ1mYe22WP` | not shared | RECONCILE_REQUIRED | NOT_MOVED; later notebook reconciliation |
| 48 | `.../Cloud Function - Colab/service-account.json` | [`1aEbqkS1yAI_EeBDovI7p6Y2Qr5KwjqkV`](https://drive.google.com/open?id=1aEbqkS1yAI_EeBDovI7p6Y2Qr5KwjqkV) | Credential JSON | `1XrK-FGC8hEccUX56ZywNnnCQ1mYe22WP` | not shared | RECONCILE_REQUIRED | NOT_MOVED; sensitive credential context |
| 49 | `.../reference/現況跟實作.md` | [`1v64QpVLp_WJUY0172AWv95obkviaVewX`](https://drive.google.com/open?id=1v64QpVLp_WJUY0172AWv95obkviaVewX) | Markdown | `1ledzNwpk3FUBnFeY8myLyZ_279cshCZe` | not shared | RECONCILE_REQUIRED | NOT_MOVED with mixed reference folder |
| 50 | `.../reference/CarDentScratch.pt` | [`137GYrPXSf38V1qmkm3BWYwSMvXVYd93V`](https://drive.google.com/open?id=137GYrPXSf38V1qmkm3BWYwSMvXVYd93V) | Model artifact | `1ledzNwpk3FUBnFeY8myLyZ_279cshCZe` | not shared | RECONCILE_REQUIRED | NOT_MOVED; later model reconciliation |
| 51 | `.../reference/engine_colab_template.md` | [`1d7uDDbBcyCvtFdD30TKfnfLVYGUcr_8d`](https://drive.google.com/open?id=1d7uDDbBcyCvtFdD30TKfnfLVYGUcr_8d) | Markdown | `1ledzNwpk3FUBnFeY8myLyZ_279cshCZe` | not shared | RECONCILE_REQUIRED | NOT_MOVED with mixed reference folder |
| 52 | `.../reference/output.txt` | [`103fNox1txnHJjA-vyHxl2nhf34YrdKWu`](https://drive.google.com/open?id=103fNox1txnHJjA-vyHxl2nhf34YrdKWu) | Text | `1ledzNwpk3FUBnFeY8myLyZ_279cshCZe` | not shared | RECONCILE_REQUIRED | NOT_MOVED with mixed reference folder |
| 53 | `01.web app/智能檢車 Web App 前端開發作業程序 的副本` | [`12xQClfvFwjLTwKGnho_K7KQcxIXbfvfgeWGPHqw8ah8`](https://drive.google.com/open?id=12xQClfvFwjLTwKGnho_K7KQcxIXbfvfgeWGPHqw8ah8) | Google Doc | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | not shared | DUPLICATE_CANDIDATE | NOT_MOVED; explicit copy, identity not verified |
| 54 | `01.web app/智能檢車 Web App 前端開發作業程序.docx` | [`1gO-9_JSaF8aJgDBWfE4aVaUlzP-g8u8Q`](https://drive.google.com/open?id=1gO-9_JSaF8aJgDBWfE4aVaUlzP-g8u8Q) | DOCX | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | not shared | PROJECT_ASSET | MOVE-002 VERIFIED |
| 55 | `01.web app/車牌車輪辨識2` | [`1h4wG62BB9CyZy6Pt13o4KRvHq7rf_O2U`](https://drive.google.com/open?id=1h4wG62BB9CyZy6Pt13o4KRvHq7rf_O2U) | PNG | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | not shared | PROJECT_ASSET | MOVE-003 VERIFIED |
| 56 | `01.web app/車牌車輪辨識1` | [`1brnUiaEj6EaZTNEZ3SYgqE00SoLwdXUj`](https://drive.google.com/open?id=1brnUiaEj6EaZTNEZ3SYgqE00SoLwdXUj) | PNG | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | not shared | PROJECT_ASSET | MOVE-004 VERIFIED |
| 57 | `01.web app/FullVideo.mp4` | [`1Ia6H0xXjU3RWolUTBleHdYBSpgJ_ZQqP`](https://drive.google.com/open?id=1Ia6H0xXjU3RWolUTBleHdYBSpgJ_ZQqP) | MP4 | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | not shared | PROJECT_ASSET | MOVE-005 VERIFIED; team Phase 1 context only |
| 58 | `01.web app/03_故意輸錯車牌測試辨識` | [`1Hd8zPlfoUhYapa5Qt0VFrPiZb_egWeRX`](https://drive.google.com/open?id=1Hd8zPlfoUhYapa5Qt0VFrPiZb_egWeRX) | MP4 | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | not shared | PROJECT_ASSET | MOVE-006 VERIFIED; team Phase 1 test context |
| 59 | `01.web app/Car Damage Project 3a5ed27c22388036b84ff1c72b1359f7.md` | [`1kSS01E-YG_cAqgzPXPjcSU1-VRxl7Wca`](https://drive.google.com/open?id=1kSS01E-YG_cAqgzPXPjcSU1-VRxl7Wca) | Markdown | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | not shared | PROJECT_ASSET | MOVE-007 VERIFIED |
| 60 | `01.web app/智能檢車 Web App 前端開發作業程序.pdf` | [`1qk9CPWd4ixyvgHJ2m52OKqokQVheuk1V`](https://drive.google.com/open?id=1qk9CPWd4ixyvgHJ2m52OKqokQVheuk1V) | PDF | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | not shared | PROJECT_ASSET | MOVE-008 VERIFIED |
| 61 | `02.Auto Labeling/auto_label_V2.4_Feature_Engineering-Copy2 (3).html` | [`1xHW9yBrThhmAZ5l4c7VdLZbpcOd9mPfE`](https://drive.google.com/open?id=1xHW9yBrThhmAZ5l4c7VdLZbpcOd9mPfE) | HTML | `1L8pV9VGLtRs89eknQbo12E8DlNDXOR1e` | not shared | DUPLICATE_CANDIDATE | NOT_MOVED; explicit copy, identity not verified |
| 62 | `02.Auto Labeling/影像車損辨識開發流程.docx` | [`1VsYrrA3Qq9vn-upEh0HlTSWV0W2NVgbg`](https://drive.google.com/open?id=1VsYrrA3Qq9vn-upEh0HlTSWV0W2NVgbg) | DOCX | `1L8pV9VGLtRs89eknQbo12E8DlNDXOR1e` | not shared | PROJECT_ASSET | MOVE-009 VERIFIED |
| 63 | `02.Auto Labeling/auto_label_V2.4_Feature_Engineering-Copy2_nocell.html` | [`1W1t2ku41e7mfbGxJOiAcozjBQJVgd9yM`](https://drive.google.com/open?id=1W1t2ku41e7mfbGxJOiAcozjBQJVgd9yM) | HTML | `1L8pV9VGLtRs89eknQbo12E8DlNDXOR1e` | not shared | PROJECT_ASSET | MOVE-010 VERIFIED |
| 64 | `02.Auto Labeling/YOLO_car_damage_detection_V5.pt` | [`1UrR_rtfSOAKPjOgIpSd8dIDp7BJsiErF`](https://drive.google.com/open?id=1UrR_rtfSOAKPjOgIpSd8dIDp7BJsiErF) | Model artifact | `1L8pV9VGLtRs89eknQbo12E8DlNDXOR1e` | not shared | RECONCILE_REQUIRED | NOT_MOVED; later model reconciliation |
| 65 | `02.Auto Labeling/auto_label_V2.4_Feature_Engineering.html` | [`1EOayq6dzy7Wrr43l6WOhXWhAGJL77sap`](https://drive.google.com/open?id=1EOayq6dzy7Wrr43l6WOhXWhAGJL77sap) | HTML | `1L8pV9VGLtRs89eknQbo12E8DlNDXOR1e` | not shared | PROJECT_ASSET | MOVE-011 VERIFIED |
| 66 | `03.系統部署&架構規劃/ChatGPT Image 2026年7月24日 下午12_22_23.png` | [`1WnUmPA4D27zWcRFTfFJBufJk-dWHGHfm`](https://drive.google.com/open?id=1WnUmPA4D27zWcRFTfFJBufJk-dWHGHfm) | PNG | `1HlzCo0bIBI7XakkweV-l2G8g0_a-SG3d` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 67 | `03.系統部署&架構規劃/車況之眼_智慧巡檢系統_實際應用功能流程圖_Editable.pptx` | [`1JFbCFiL29KA5VCRqT6bRGnSaIl9h6qQx`](https://drive.google.com/open?id=1JFbCFiL29KA5VCRqT6bRGnSaIl9h6qQx) | PPTX | `1HlzCo0bIBI7XakkweV-l2G8g0_a-SG3d` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 68 | `03.系統部署&架構規劃/Dashboard/` | [`1E48Mmv5HL9DfLhaGrGgc2GxIqrfHFME9`](https://drive.google.com/open?id=1E48Mmv5HL9DfLhaGrGgc2GxIqrfHFME9) | Folder | `1HlzCo0bIBI7XakkweV-l2G8g0_a-SG3d` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 69 | `03.系統部署&架構規劃/系統開發規格文件/` | [`1eY7PXuxAbkHWLDKE6DOScj6IHeS8qGlO`](https://drive.google.com/open?id=1eY7PXuxAbkHWLDKE6DOScj6IHeS8qGlO) | Folder | `1HlzCo0bIBI7XakkweV-l2G8g0_a-SG3d` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 70 | `03.系統部署&架構規劃/imp_前端 Firebase 整合與建立訂單及拍照上傳實作計畫.md` | [`1C-RklqV63_h4l7Hv8SQLG9Y9_kZcZMkt`](https://drive.google.com/open?id=1C-RklqV63_h4l7Hv8SQLG9Y9_kZcZMkt) | Markdown | `1HlzCo0bIBI7XakkweV-l2G8g0_a-SG3d` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 71 | `03.系統部署&架構規劃/deployment_architecture_v2.png` | [`1MwA_y1FJTm0x9Vxqw2sZxu3IB5rld3Aq`](https://drive.google.com/open?id=1MwA_y1FJTm0x9Vxqw2sZxu3IB5rld3Aq) | PNG | `1HlzCo0bIBI7XakkweV-l2G8g0_a-SG3d` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 72 | `.../Dashboard/Screenshot_20260722-174816.png` | [`1pOwm7RZ1Nmib5pclxwAX21a7lu3z5RU-`](https://drive.google.com/open?id=1pOwm7RZ1Nmib5pclxwAX21a7lu3z5RU-) | PNG | `1E48Mmv5HL9DfLhaGrGgc2GxIqrfHFME9` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 73 | `.../Dashboard/Screenshot_20260722-174823.png` | [`1HKzgu67uOx0S1yeYTsufYHZZK721J1-s`](https://drive.google.com/open?id=1HKzgu67uOx0S1yeYTsufYHZZK721J1-s) | PNG | `1E48Mmv5HL9DfLhaGrGgc2GxIqrfHFME9` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 74 | `.../Dashboard/Screenshot_20260722-174913.png` | [`1IwjEFqlT9Hjx1zqkvtb4yAH5PGv_H1NY`](https://drive.google.com/open?id=1IwjEFqlT9Hjx1zqkvtb4yAH5PGv_H1NY) | PNG | `1E48Mmv5HL9DfLhaGrGgc2GxIqrfHFME9` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 75 | `.../Dashboard/Screenshot_20260722-174923.png` | [`1GCh1vPX-B86tEfZxsimkEaCkLMKXEXMe`](https://drive.google.com/open?id=1GCh1vPX-B86tEfZxsimkEaCkLMKXEXMe) | PNG | `1E48Mmv5HL9DfLhaGrGgc2GxIqrfHFME9` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 76 | `.../Dashboard/Screenshot_20260722-174932.png` | [`1IM419uTLVmzVywzdaNIWmYFslJcbvW7T`](https://drive.google.com/open?id=1IM419uTLVmzVywzdaNIWmYFslJcbvW7T) | PNG | `1E48Mmv5HL9DfLhaGrGgc2GxIqrfHFME9` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 77 | `.../Dashboard/Screenshot_20260722-174942.png` | [`1K22IvLpJdtVV1BY3PdGdC1gFxbi35g7i`](https://drive.google.com/open?id=1K22IvLpJdtVV1BY3PdGdC1gFxbi35g7i) | PNG | `1E48Mmv5HL9DfLhaGrGgc2GxIqrfHFME9` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 78 | `.../Dashboard/dashboard-rentals-list_20260722.png` | [`1S6HzapZbhc4SFQpqJbog40PR9vQU5UP8`](https://drive.google.com/open?id=1S6HzapZbhc4SFQpqJbog40PR9vQU5UP8) | PNG | `1E48Mmv5HL9DfLhaGrGgc2GxIqrfHFME9` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 79 | `.../Dashboard/dashboard-review-detail_20260722.png` | [`1YGir_chDpW1brM5SN2q6Tn8Ub2ZZPhZP`](https://drive.google.com/open?id=1YGir_chDpW1brM5SN2q6Tn8Ub2ZZPhZP) | PNG | `1E48Mmv5HL9DfLhaGrGgc2GxIqrfHFME9` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 80 | `.../系統開發規格文件/00_命名建議.docx` | [`19gbvSRdutQmCBMKT5kiDGIwULnTbc8s4`](https://drive.google.com/open?id=19gbvSRdutQmCBMKT5kiDGIwULnTbc8s4) | DOCX | `1eY7PXuxAbkHWLDKE6DOScj6IHeS8qGlO` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 81 | `.../系統開發規格文件/01_SAS_系統架構書.docx` | [`1hakg5wN4fLaCj-5qCpFYyL06K6CgwzpP`](https://drive.google.com/open?id=1hakg5wN4fLaCj-5qCpFYyL06K6CgwzpP) | DOCX | `1eY7PXuxAbkHWLDKE6DOScj6IHeS8qGlO` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 82 | `.../系統開發規格文件/02_SDD_系統規格書.docx` | [`1oLLvY0vis3CDOc0_hDolEKEeQn97fcYE`](https://drive.google.com/open?id=1oLLvY0vis3CDOc0_hDolEKEeQn97fcYE) | DOCX | `1eY7PXuxAbkHWLDKE6DOScj6IHeS8qGlO` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 83 | `.../系統開發規格文件/03_IAM與Firebase權限操作手冊.docx` | [`1Xe55cyFEzsdgbURC2FVfl-2M2kEJMMlC`](https://drive.google.com/open?id=1Xe55cyFEzsdgbURC2FVfl-2M2kEJMMlC) | DOCX | `1eY7PXuxAbkHWLDKE6DOScj6IHeS8qGlO` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 84 | `.../系統開發規格文件/04_前端模組規格書與串接資料包.docx` | [`1AMesU3AMtXFIPedxwvoMU1OggwV-xX0m`](https://drive.google.com/open?id=1AMesU3AMtXFIPedxwvoMU1OggwV-xX0m) | DOCX | `1eY7PXuxAbkHWLDKE6DOScj6IHeS8qGlO` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 85 | `.../系統開發規格文件/05_後端模組規格書.docx` | [`19wHYTuyyBT7Xln4516YLbIJourAf_AMh`](https://drive.google.com/open?id=19wHYTuyyBT7Xln4516YLbIJourAf_AMh) | DOCX | `1eY7PXuxAbkHWLDKE6DOScj6IHeS8qGlO` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 86 | `.../系統開發規格文件/06_專案時程規劃.docx` | [`1h1XG69_uOPlFam-ZTqo-4a0doeIvzxEK`](https://drive.google.com/open?id=1h1XG69_uOPlFam-ZTqo-4a0doeIvzxEK) | DOCX | `1eY7PXuxAbkHWLDKE6DOScj6IHeS8qGlO` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |
| 87 | `.../系統開發規格文件/07_開發任務規格書 for AGENT.docx` | [`1T2VZ-eQRDquUCfWvJf7iginxrJ47jtJK`](https://drive.google.com/open?id=1T2VZ-eQRDquUCfWvJf7iginxrJ47jtJK) | DOCX | `1eY7PXuxAbkHWLDKE6DOScj6IHeS8qGlO` | not shared | PROJECT_ASSET | VIA_PARENT MOVE-001 |

### Pre-Recorded Execution Table

Only the following `31` item IDs may receive Task 6 `update_file` calls. Every call must omit `name`, `file_uri`, and `mime_type`, add only the listed target parent, and remove only the listed source parent.

| Move | Item ID | Exact Source Parent ID | Exact Target Folder ID / Path | Classification | Rationale | Delete Allowed | Status |
|---|---|---|---|---|---|---|---|
| MOVE-001 | `1HlzCo0bIBI7XakkweV-l2G8g0_a-SG3d` | `1JPupMGmZK7tp5wQtc5tBLXcdjesgaQYi` | `1a5SrioOwdTitxQ2qYilrhHcqRd2jbODx` / `FleetVision/04_PROJECT_ASSETS/03_phase3_dashboard/` | PROJECT_ASSET | Phase 3 deployment/dashboard material is team/system engineering context. | false | VERIFIED — source absent; target present; parents=[`1a5SrioOwdTitxQ2qYilrhHcqRd2jbODx`] |
| MOVE-002 | `1gO-9_JSaF8aJgDBWfE4aVaUlzP-g8u8Q` | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | `1qTeD-y9uEpuSOquJCzKA_BvrPUG94Jag` / `.../01_phase1_capture/` | PROJECT_ASSET | Phase 1 Web App procedure, team context. | false | VERIFIED |
| MOVE-003 | `1h4wG62BB9CyZy6Pt13o4KRvHq7rf_O2U` | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | `1qTeD-y9uEpuSOquJCzKA_BvrPUG94Jag` / `.../01_phase1_capture/` | PROJECT_ASSET | Phase 1 capture-model screenshot, team context. | false | VERIFIED |
| MOVE-004 | `1brnUiaEj6EaZTNEZ3SYgqE00SoLwdXUj` | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | `1qTeD-y9uEpuSOquJCzKA_BvrPUG94Jag` / `.../01_phase1_capture/` | PROJECT_ASSET | Phase 1 capture-model screenshot, team context. | false | VERIFIED |
| MOVE-005 | `1Ia6H0xXjU3RWolUTBleHdYBSpgJ_ZQqP` | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | `1qTeD-y9uEpuSOquJCzKA_BvrPUG94Jag` / `.../01_phase1_capture/` | PROJECT_ASSET | Phase 1 Web App workflow video, private team context only. | false | VERIFIED |
| MOVE-006 | `1Hd8zPlfoUhYapa5Qt0VFrPiZb_egWeRX` | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | `1qTeD-y9uEpuSOquJCzKA_BvrPUG94Jag` / `.../01_phase1_capture/` | PROJECT_ASSET | Phase 1 wrong-license-plate test video, private team context. | false | VERIFIED |
| MOVE-007 | `1kSS01E-YG_cAqgzPXPjcSU1-VRxl7Wca` | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | `1qTeD-y9uEpuSOquJCzKA_BvrPUG94Jag` / `.../01_phase1_capture/` | PROJECT_ASSET | Phase 1 Web App project note, team context. | false | VERIFIED |
| MOVE-008 | `1qk9CPWd4ixyvgHJ2m52OKqokQVheuk1V` | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | `1qTeD-y9uEpuSOquJCzKA_BvrPUG94Jag` / `.../01_phase1_capture/` | PROJECT_ASSET | Phase 1 Web App procedure PDF, team context. | false | VERIFIED |
| MOVE-009 | `1VsYrrA3Qq9vn-upEh0HlTSWV0W2NVgbg` | `1L8pV9VGLtRs89eknQbo12E8DlNDXOR1e` | `1udVhs2TKxgzOeDuGAtvnZPiGEaAzEPS0` / `.../02_phase2_detection/` | PROJECT_ASSET | Phase 2 damage-analysis development process. | false | VERIFIED |
| MOVE-010 | `1W1t2ku41e7mfbGxJOiAcozjBQJVgd9yM` | `1L8pV9VGLtRs89eknQbo12E8DlNDXOR1e` | `1udVhs2TKxgzOeDuGAtvnZPiGEaAzEPS0` / `.../02_phase2_detection/` | PROJECT_ASSET | Phase 2 feature-engineering evidence export. | false | VERIFIED |
| MOVE-011 | `1EOayq6dzy7Wrr43l6WOhXWhAGJL77sap` | `1L8pV9VGLtRs89eknQbo12E8DlNDXOR1e` | `1udVhs2TKxgzOeDuGAtvnZPiGEaAzEPS0` / `.../02_phase2_detection/` | PROJECT_ASSET | Phase 2 feature-engineering evidence export. | false | VERIFIED |
| MOVE-012 | `1D-8ynDccx_DBDs1rW_nakoItXpWFL6KU` | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | `1udVhs2TKxgzOeDuGAtvnZPiGEaAzEPS0` / `.../02_phase2_detection/` | PROJECT_ASSET | Historical Phase 2 training-curve image; not an active metric claim. | false | VERIFIED |
| MOVE-013 | `153No-5Eos3nem7DOMHb7LCbAU2pPdlb3` | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | `1udVhs2TKxgzOeDuGAtvnZPiGEaAzEPS0` / `.../02_phase2_detection/` | PROJECT_ASSET | Historical Phase 2 DBSCAN evidence. | false | VERIFIED |
| MOVE-014 | `1IEwrRciinWpmqtsv0nC0KFUbqLkthMey` | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | `1udVhs2TKxgzOeDuGAtvnZPiGEaAzEPS0` / `.../02_phase2_detection/` | PROJECT_ASSET | Historical Phase 2 correlation evidence. | false | VERIFIED |
| MOVE-015 | `1-pSvHqt1Zxqc4WXx5kO3-zc7GQCtez7M` | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | `1qTeD-y9uEpuSOquJCzKA_BvrPUG94Jag` / `.../01_phase1_capture/` | PROJECT_ASSET | Phase 1 four-angle capture example, team context. | false | VERIFIED |
| MOVE-016 | `1l3QnkYqmp-qEYOCoYcoe-NuH5e-HPYNU` | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | `1qTeD-y9uEpuSOquJCzKA_BvrPUG94Jag` / `.../01_phase1_capture/` | PROJECT_ASSET | Phase 1 Web App demo screenshot, team context. | false | VERIFIED |
| MOVE-017 | `1rABt3prY0n7vw1YwF0nNejtYqBhSpZPv` | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | `1a5SrioOwdTitxQ2qYilrhHcqRd2jbODx` / `.../03_phase3_dashboard/` | PROJECT_ASSET | System deployment diagram, team/system context. | false | VERIFIED |
| MOVE-018 | `1o9mh9AMZwE6c1cuTnYMRShfzqJi-trB1` | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `FleetVision/99_ARCHIVE/05_old_presentations/` | ARCHIVE | Legacy presentation asset container after its classified children move. | false | VERIFIED |
| MOVE-019 | `1pjECAs6lH5kD6R5B9Slcgh05uPLzMsy5cO4k54sekQI` | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Latest team deck is unsafe for active claims; preserve reversibly as history. | false | VERIFIED |
| MOVE-020 | `150U7TxI00K3qoGO65OX98_T_u4c_5bgN` | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Presentation media variant; not selected active demo. | false | VERIFIED |
| MOVE-021 | `1ojUBiwrx4jPD8m8zZbFoCO8jHgCkcDVm` | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Presentation media variant; not selected active demo. | false | VERIFIED |
| MOVE-022 | `1dZQTbe05wSoApvyQi71tRJ1I2In9yaQLxi7FgSUoOw4` | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Historical speaker notes. | false | VERIFIED |
| MOVE-023 | `12vU3RWolYq4YHHdh3-PIYibSeHcZRTGrNyIGfC-Wy-8` | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Historical presentation timing sheet. | false | VERIFIED |
| MOVE-024 | `1It4GcH7ehbgGRLQR8rPIIgfjq1T8Nl-p` | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Overview contains unreconciled claims; archive instead of active promotion. | false | VERIFIED |
| MOVE-025 | `12anZhv5rGmp8laizHPyQjhptupVfxPb1` | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Folder contains 15 superseded presentation variants. | false | VERIFIED |
| MOVE-026 | `1llx0Fzn4_bw3Zs6XTfijbOTPhKh3Dj_9` | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Earlier full-flow presentation media; sharing state remains unchanged. | false | VERIFIED |
| MOVE-027 | `1YYFLPjc7SM3KLW3SR8zkqa_ox8P4YyHFmFOeeI7eWdU` | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Historical presentation-structure note. | false | VERIFIED |
| MOVE-028 | `1ab1tKdN3bB1LmlM8uvmXI38Bvr2AooUO` | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Earlier Web App presentation media variant. | false | VERIFIED |
| MOVE-029 | `1QCIP8ye1WpZfIofFMQi5_tRi1rR37PGh` | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Empty legacy presentation demo container; no deletion. | false | VERIFIED |
| MOVE-030 | `1gUQppQKYG3xv7w7Sxx5cum5j1B-N-Xkw` | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Empty legacy speaker-note container; no deletion. | false | VERIFIED |
| MOVE-031 | `1Hf9xsQyfs8z6VtwZ6cXftO4s1IgTIeHR` | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` / `.../05_old_presentations/` | ARCHIVE | Historical presentation-master folder and its two documents. | false | VERIFIED |

Pre-execution action counters:

```text
move = 0
rename = 0
copy = 0
upload = 0
share = 0
trash = 0
delete = 0
permanent deletion = 0
```

### Post-Batch Independent Readback

- Execution result: `31 VERIFIED`, `0 PENDING`, `0 FAILED`.
- Each moved ID was absent from its exact old parent, present in its exact target parent, and returned `parent_ids=[expected target ID]` immediately after its `update_file` call.
- An independent post-batch listing was then performed for the grounded source, every retained source branch, and all four used targets.

| Independently Listed Parent | ID | Direct Children | Result |
|---|---|---:|---|
| Grounded source `00.成果發表/` | `1JPupMGmZK7tp5wQtc5tBLXcdjesgaQYi` | 3 | VERIFIED: only explicit NOT_MOVED containers remain |
| `00.彙總發表/` | `1sZLGHUyDJwTExzCisKkTnOKytj9TYb3j` | 2 | VERIFIED: `02.PPT/` and `Cloud Function - Colab/` only |
| `01.web app/` | `1FA9AggxqKVEu23x_V93DQTXm5zx5OH1g` | 1 | VERIFIED: explicit copy candidate only |
| `02.Auto Labeling/` | `1L8pV9VGLtRs89eknQbo12E8DlNDXOR1e` | 2 | VERIFIED: explicit copy candidate and model artifact only |
| `00.彙總發表/02.PPT/` | `1Nf0mGVvJW86iWgJovF5X_fyq5pVQR_7t` | 1 | VERIFIED: unaudited primary demo candidate only |
| `00.彙總發表/Cloud Function - Colab/` | `1XrK-FGC8hEccUX56ZywNnnCQ1mYe22WP` | 4 | VERIFIED: mixed reference/model/notebook/credential items retained |
| `FleetVision/04_PROJECT_ASSETS/01_phase1_capture/` | `1qTeD-y9uEpuSOquJCzKA_BvrPUG94Jag` | 9 | VERIFIED |
| `FleetVision/04_PROJECT_ASSETS/02_phase2_detection/` | `1udVhs2TKxgzOeDuGAtvnZPiGEaAzEPS0` | 6 | VERIFIED |
| `FleetVision/04_PROJECT_ASSETS/03_phase3_dashboard/` | `1a5SrioOwdTitxQ2qYilrhHcqRd2jbODx` | 2 | VERIFIED |
| `FleetVision/99_ARCHIVE/05_old_presentations/` | `146utuTSsHtomWALO-PkXLeWliwO4ThG0` | 14 | VERIFIED |

### Retained NOT_MOVED Items

- `17` inventory rows remain explicitly `NOT_MOVED`.
- The retained set consists of unresolved containers plus: one unaudited private demo, three model artifacts, one notebook, one credential JSON, mixed reference material, and two explicit non-presentation duplicate candidates.
- These items were not promoted, archived, renamed, copied, shared, trashed, or deleted. Later notebook/model/duplicate reconciliation tasks must use the recorded IDs rather than infer identity from names.

### Final Action Counters

```text
metadata-only move = 31
rename = 0
copy = 0
upload = 0
share = 0
trash = 0
delete = 0
permanent deletion = 0
active deck selected = 0
active overview selected = 0
active demo selected = 0
interview link added = 0
```

Sharing states were not modified. The archived `3282_完整流程APP_DASHBOARDmp4` item continues to report `shared=true` with provider visibility `access_not_verified`; no public-access claim is made.

## Task 7 — Notebook and Experiment Evidence Migration Pre-Move Gate

### Grounding and Safety Result

- Grounded source root: `AI_Class/00.Project/FleetVision/` (ID `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl`).
- Grounded source root direct children: `16`; Task 7 scope covers `9` direct items (`3` notebooks, `2` ZIPs, and `4` folders). The other `7` remain governed by prior or later tasks.
- Notebook identities: `11` (`6` under the old `notebooks/` folder, `3` at the old project root, and `2` under `04_5J/`).
- Bounded static JSON review: `6` notebooks; no cell execution, training, inference, or external data access occurred.
- Size-bounded metadata-only exclusions: `5` notebooks (`2,031,431`–`13,041,224` bytes) whose recovery/demo/output-rich identity did not justify content retrieval.
- Secret-literal matches across the six bounded static reviews: `0`; credential-file/private-key reference matches: `0`.
- Static review did not print cell source, output text, credentials, private paths, or metrics. Frozen-boundary references were counted only to prevent unsafe active selection.
- Active Drive-hosted notebooks selected: `0`. Every Drive candidate either contains embedded outputs, is a recovery/demo variant, references protected evaluation boundaries, is not byte-identical to the tracked output-stripped equivalent, or cannot satisfy all active-selection criteria safely.
- Active tracked notebooks selected: `2` output-stripped repository notebooks. They remain historical evidence and are not authorization to run training or inference.
- Mixed `outputs/`, `04_5J/`, and `04_5K/` containers remain `NOT_MOVED/RECONCILE_REQUIRED` at the old project root. Only the two direct notebook files under `04_5J/` may move individually; nested model/data artifacts remain intact for Tasks 8–9. Protected-risk `input/` and `day1_test_evaluation/` contents were not listed, fetched, hashed, or read.
- Before execution: metadata-only move `0`; rename/copy/upload/share/trash/delete `0`; permanent deletion `0`.

### Complete Notebook Identity Inventory

`Embedded Outputs` is a structural count only. `NOT_READ_SIZE_BOUND` means only Drive metadata was read.

| # | Current Path / Name | Drive ID | Size | Modified UTC | Apparent Stage | Embedded Outputs | Tracked Git Equivalent | Classification / Planned Action |
|---:|---|---|---:|---|---|---:|---|---|
| 1 | `notebooks/FleetVision_Colab_Rapid_Detection_Training_v4.ipynb` | `14drOkZLzyI9SjfLvEgLOA0aoFtmt58LK` | 45,497 | `2026-07-20T07:39:52.742Z` | rapid-detection training/recovery | 0; static; Frozen-boundary refs 10 | None | ARCHIVE; via old `notebooks/` container T7-MOVE-001 |
| 2 | `notebooks/FleetVision_Phase05R_B1_Model_Data_Audit` | `1-mmBDEUu0vO6MVCArOh_89s6yr_eGF8v` | 212,961 | `2026-07-19T18:26:13.166Z` | Phase 05R recovery audit | 8; static | None | ARCHIVE; recovery evidence via T7-MOVE-001 |
| 3 | `notebooks/FleetVision_Phase05_Model_Recovery.ipynb` | `1y9fSZtFq5xxNR-VTfPJG5YDx2QxI6MT9` | 13,041,224 | `2026-07-18T17:05:15.082Z` | model recovery | NOT_READ_SIZE_BOUND | None | ARCHIVE; output-rich recovery via T7-MOVE-001 |
| 4 | `notebooks/FleetVision_Day3_CLI_API_Demo.ipynb` | `1FpttQMvYhbIG_jGTw2kixSuzDv_2Lzqf` | 2,032,431 | `2026-07-17T18:23:22.905Z` | CLI/API demo | NOT_READ_SIZE_BOUND | None | ARCHIVE; output-rich historical demo via T7-MOVE-001 |
| 5 | `notebooks/FleetVision_Day2_Inference.ipynb` | `15-5zQO9fGnU8S95QEOH3r8NUTWVg6EHx` | 2,407,412 | `2026-07-17T17:35:56.473Z` | historical inference | NOT_READ_SIZE_BOUND | None | ARCHIVE; Phase 03.5 inference remains frozen; via T7-MOVE-001 |
| 6 | `notebooks/FleetVision_Day1_Training_20260717.ipynb` | `1mYEmP6r7mZn5ow_XsRx23lZTjOEuAZ_x` | 163,280 | `2026-07-17T15:49:14.283Z` | historical training/evaluation | 12; static; Frozen-boundary refs 4 | None | ARCHIVE; historical training via T7-MOVE-001 |
| 7 | root `FleetVision_Colab_Rapid_Detection_Training_v4.ipynb` | `1_X26Vs4mG1aY5wH9eRcNsMtlOM92qMrX` | 6,576,224 | `2026-07-21T05:21:01.242Z` | rapid-detection training/recovery | NOT_READ_SIZE_BOUND | Same title as row 1, but size differs by 6,530,727 bytes; identity unresolved | DUPLICATE_CANDIDATE; T7-MOVE-002 |
| 8 | root `FleetVision_Phase05R_Cell_R4_08R5.ipynb` | `1YirQgcn1_GVcgmuh7mhRcYBQ-p7XByqA` | 2,057,119 | `2026-07-18T18:05:20.150Z` | Phase 05R recovery cell | NOT_READ_SIZE_BOUND | None | ARCHIVE; deprecated recovery notebook; T7-MOVE-003 |
| 9 | root `phase03_5_auto_review_prelabeller_clean.ipynb` | `1QUoYrveX4mgWZVzb7JCUzuK3BdXb-NCe` | 226,852 | `2026-07-17T15:27:45.260Z` | Phase 03.5 prelabel inference | 36; static | `notebooks/phase03_5_auto_review_prelabeller.ipynb` is output-stripped and 14,115 bytes; identity differs | ARCHIVE; frozen historical inference evidence; T7-MOVE-004 |
| 10 | `04_5J/FleetVision_04_5K_Validation_Error_Analysis_8_4_93.ipynb` | `1JguKck5KpXISZEluoR-cPKbMn-2yODAZ` | 81,083 | `2026-07-13T11:25:22.668Z` | validation error analysis | 3; static; Frozen-boundary refs 1 | Same-named tracked notebook is output-stripped and 76,446 bytes; identity differs | ARCHIVE historical evidence; direct-file T7-MOVE-010 |
| 11 | `04_5J/FleetVision_04_5J_Controlled_Baseline_Training_8_4_93.ipynb` | `1N708t2WSISqot9D86F4tMUUJmuJD7b_5` | 63,935 | `2026-07-13T08:29:22.668Z` | controlled baseline training | 9; static; Frozen-boundary refs 3 | None | ARCHIVE historical training evidence; direct-file T7-MOVE-011 |

### Active Tracked Notebook Selection

| Tracked Notebook | Role | Selection Evidence | Current Status |
|---|---|---|---|
| `notebooks/FleetVision_04_5K_Validation_Error_Analysis_8_4_93.ipynb` | model evaluation | Output-stripped (`0` outputs, `0` executed cells), no secret literal or credential reference, repository tests validate its contract | HISTORICAL_EVIDENCE; not safe/authorized to run under Phase 05S-A2 |
| `notebooks/phase03_5_auto_review_prelabeller.ipynb` | inference/prelabel evidence | Output-stripped (`0` outputs, `0` executed cells), no secret literal or credential reference, tracked with repository configuration/tests | HISTORICAL_EVIDENCE_FROZEN; Phase 03.5 may not be rerun |

### Complete Experiment Container Inventory

The table inventories every direct branch that will move with its complete parent container. `VIA_PARENT` preserves nested identity without opening model, dataset, Frozen Test, or private payload contents.

| Current Path / Name | Observed ID | Type | Direct Parent | Classification | Planned Execution |
|---|---|---|---|---|---|
| `outputs/candidate02_tile2x2_audit/` | `1SrqyHyNSZagnkqpsMFu8gibsXdImEFOt` | Folder | `outputs/` | ARCHIVE_RECONCILIATION | NOT_MOVED; mixed parent retained for Tasks 8–9 |
| `outputs/candidate02b_overlap25_audit/` | `1_gVE_JQc0i872ZJhXu-I2oO3t5LLu-Jt` | Folder | `outputs/` | ARCHIVE_RECONCILIATION | NOT_MOVED; mixed parent retained for Tasks 8–9 |
| `outputs/candidate02b_overlap25_training/` | `1-TGf2dUcBGlNWym2llEirIKtaxEUyqNw` | Folder | `outputs/` | HISTORICAL_EXPERIMENT | NOT_MOVED; mixed parent retained for Tasks 8–9 |
| `outputs/candidate03a_patch_detection/` | `1zwHgZbHi8n8IX3KTA8-cu1BdolAn3FqI` | Folder | `outputs/` | HISTORICAL_EXPERIMENT | NOT_MOVED; mixed parent retained for Tasks 8–9 |
| `outputs/rapid_detection_recovery_colab/` | `13E6gYGUuxpbtmsg38Ipzgs61r31YAKYz` | Folder | `outputs/` | RECOVERY_ARCHIVE | NOT_MOVED; mixed parent retained for Tasks 8–9 |
| `outputs/models/` | `1jaFzH6c141zg7QVuMavMEaOUgt6q_q_L` | Folder | `outputs/` | RECONCILE_REQUIRED | NOT_MOVED; model identities deferred to Task 8 |
| `outputs/phase05r/` | `1YQx_ZpQvzL1IOzRXancDwAVioQiTr5tT` | Folder | `outputs/` | RECOVERY_ARCHIVE | NOT_MOVED; mixed parent retained for Tasks 8–9 |
| `outputs/day3_demo/` | `1MHoPtVBd3oPrrDeeliZnrR3TwjGE0ALL` | Folder | `outputs/` | HISTORICAL_EXPERIMENT | NOT_MOVED; mixed parent retained for Tasks 8–9 |
| `outputs/day2_inference/` | `1W0UF-MA3tZeQ-MiHH-I875jbzyOUybgu` | Folder | `outputs/` | HISTORICAL_EXPERIMENT | NOT_MOVED; no inference run |
| `outputs/day1_test_evaluation/` | `1FkqqIsz-wGs2iol0EG2mI7rtIByrYh--` | Folder | `outputs/` | PROTECTED_HISTORICAL_EVIDENCE | NOT_MOVED; contents not listed or read |
| `outputs/day1_label_audit/` | `1dm1rrwoWiNgP0B5sdIMM3XpEnlSvwyx-` | Folder | `outputs/` | HISTORICAL_EXPERIMENT | NOT_MOVED; mixed parent retained for Tasks 8–9 |
| `outputs/phase03_5/` | `1zLEvCzh1hVn9rnY5m_nKhuuDVIDOrhP0` | Folder | `outputs/` | FROZEN_HISTORICAL_EVIDENCE | NOT_MOVED; contents not listed or read |
| `04_5J/FleetVision_04_5K_Validation_Error_Analysis_8_4_93.ipynb` | `1JguKck5KpXISZEluoR-cPKbMn-2yODAZ` | Notebook | `04_5J/` | HISTORICAL_EVIDENCE | Direct-file T7-MOVE-010 |
| `04_5J/FleetVision_04_5J_Controlled_Baseline_Training_8_4_93.ipynb` | `1N708t2WSISqot9D86F4tMUUJmuJD7b_5` | Notebook | `04_5J/` | HISTORICAL_EVIDENCE | Direct-file T7-MOVE-011 |
| `04_5J/runs/` | `19RwpAfbPcCw9fv_wXlK6uqA3jmc2mxfD` | Folder | `04_5J/` | RECONCILE_REQUIRED | NOT_MOVED; weights/results not inspected |
| `04_5J/input/` | `1zDOE-EEpvap7DmhpeBVAXgY8gCPs6nhw` | Folder | `04_5J/` | PROTECTED_RECONCILE_REQUIRED | NOT_MOVED; contents not listed or read |
| `04_5K/runs/` | `1MV9C9xhKPMxFyVaZwC68o3fCj0-G1t8Y` | Folder | `04_5K/` | RECONCILE_REQUIRED | NOT_MOVED; results not inspected |
| root `FleetVision_Candidate02_Tile2x2_NoAug.zip` | `15T7sWEDVh2ipOJqxkUWofhl-y4D0r4cf` | ZIP, 26,456,356 bytes | old project root | ARCHIVE_RECONCILIATION | T7-MOVE-008; bytes not opened |
| root `FleetVision_colab_pilot_500_v2.zip` | `1iVH_7c2WPdmbQyMpbD6kBmC-R1H7Bm2R` | ZIP, 209,477,353 bytes | old project root | ARCHIVE_RECONCILIATION | T7-MOVE-009; bytes not opened |

### Pre-Recorded Task 7 Execution Table

Only rows marked `PENDING_EXECUTION` or `VERIFIED` may receive or have received Task 7 `update_file` calls. Rows marked `CANCELLED_NOT_MOVED` are explicitly prohibited. Every permitted call must omit `name`, `file_uri`, and `mime_type`; add only the listed target parent; and remove only the verified old parent.

| Move | Item ID | Exact Old Parent ID | Exact Target Parent ID / Path | Classification | Rationale | Delete Allowed | Status |
|---|---|---|---|---|---|---|---|
| T7-MOVE-001 | `15U1-zwBIrVJ6VtLMbX-X_1VgV907IRxl` | `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl` | `1d_wPAIJQrdCjuXaQMQl7dBuZqXQTDbeI` / `FleetVision/99_ARCHIVE/01_deprecated_notebooks/` | ARCHIVE | Complete six-notebook legacy/recovery container; no candidate satisfies all active criteria. | false | VERIFIED — safety correction arrived after this first safe move; source absent, target present, parents=[`1d_wPAIJQrdCjuXaQMQl7dBuZqXQTDbeI`] |
| T7-MOVE-002 | `1_X26Vs4mG1aY5wH9eRcNsMtlOM92qMrX` | `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl` | `1GKTVtkwZX9UdznlZ2E9y0oNf0EYL2oqK` / `FleetVision/99_ARCHIVE/06_duplicate_candidates/` | DUPLICATE_CANDIDATE | Same title as a 45,497-byte notebook but 6,576,224 bytes; identity unresolved and no deletion allowed. | false | VERIFIED — source absent; target present; parents=[`1GKTVtkwZX9UdznlZ2E9y0oNf0EYL2oqK`] |
| T7-MOVE-003 | `1YirQgcn1_GVcgmuh7mhRcYBQ-p7XByqA` | `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl` | `1d_wPAIJQrdCjuXaQMQl7dBuZqXQTDbeI` / `FleetVision/99_ARCHIVE/01_deprecated_notebooks/` | ARCHIVE | Output-rich Phase 05R recovery notebook; historical recovery evidence only. | false | VERIFIED — source absent; target present; parents=[`1d_wPAIJQrdCjuXaQMQl7dBuZqXQTDbeI`] |
| T7-MOVE-004 | `1QUoYrveX4mgWZVzb7JCUzuK3BdXb-NCe` | `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl` | `1d_wPAIJQrdCjuXaQMQl7dBuZqXQTDbeI` / `FleetVision/99_ARCHIVE/01_deprecated_notebooks/` | ARCHIVE | Output-rich Phase 03.5 notebook; inference is frozen and tracked output-stripped evidence already exists. | false | VERIFIED — source absent; target present; parents=[`1d_wPAIJQrdCjuXaQMQl7dBuZqXQTDbeI`] |
| T7-MOVE-005 | `1EkkV5JqRRK8vIZ6FzYgTTRG9_fIsYVzf` | `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl` | NOT_MOVED — remains under old project root | RECONCILE_REQUIRED | Mixed output tree contains later Task 8/9 model/data and protected evaluation scope. | false | CANCELLED_NOT_MOVED |
| T7-MOVE-006 | `1M-YAK1qvvKfaEQo7IuFd8jtNEarmQZgw` | `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl` | NOT_MOVED — remains under old project root | PROTECTED_RECONCILE_REQUIRED | Container includes protected-risk `input/` and unlisted `runs/`; only direct notebooks may move. | false | CANCELLED_NOT_MOVED |
| T7-MOVE-007 | `1ScY9s0R08Jpwfccg_SnGjrJ_xmhRoR_Q` | `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl` | NOT_MOVED — remains under old project root | RECONCILE_REQUIRED | Nested `runs/` was not proven wholly non-protected and Task 7-only. | false | CANCELLED_NOT_MOVED |
| T7-MOVE-008 | `15T7sWEDVh2ipOJqxkUWofhl-y4D0r4cf` | `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl` | `1Hn3sDT1RqZNyzjaYu2YA5tN0W6I8twfb` / `FleetVision/99_ARCHIVE/04_old_experiments/` | ARCHIVE_RECONCILIATION | Candidate02 experiment package preserved whole; bytes and nested data not inspected. | false | VERIFIED — source absent; target present; parents=[`1Hn3sDT1RqZNyzjaYu2YA5tN0W6I8twfb`] |
| T7-MOVE-009 | `1iVH_7c2WPdmbQyMpbD6kBmC-R1H7Bm2R` | `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl` | `1Hn3sDT1RqZNyzjaYu2YA5tN0W6I8twfb` / `FleetVision/99_ARCHIVE/04_old_experiments/` | ARCHIVE_RECONCILIATION | Historical pilot package preserved whole; private payload bytes not inspected. | false | VERIFIED — source absent; target present; parents=[`1Hn3sDT1RqZNyzjaYu2YA5tN0W6I8twfb`] |
| T7-MOVE-010 | `1JguKck5KpXISZEluoR-cPKbMn-2yODAZ` | `1M-YAK1qvvKfaEQo7IuFd8jtNEarmQZgw` | `1Hn3sDT1RqZNyzjaYu2YA5tN0W6I8twfb` / `FleetVision/99_ARCHIVE/04_old_experiments/` | ARCHIVE | Direct historical validation-analysis notebook; container input/runs remain untouched. | false | VERIFIED — source absent; target present; parents=[`1Hn3sDT1RqZNyzjaYu2YA5tN0W6I8twfb`] |
| T7-MOVE-011 | `1N708t2WSISqot9D86F4tMUUJmuJD7b_5` | `1M-YAK1qvvKfaEQo7IuFd8jtNEarmQZgw` | `1Hn3sDT1RqZNyzjaYu2YA5tN0W6I8twfb` / `FleetVision/99_ARCHIVE/04_old_experiments/` | ARCHIVE | Direct historical baseline-training notebook; container input/runs remain untouched. | false | VERIFIED — source absent; target present; parents=[`1Hn3sDT1RqZNyzjaYu2YA5tN0W6I8twfb`] |

### Task 7 Post-Batch Independent Readback

- Permitted metadata-only moves: `8 VERIFIED`, `0 PENDING`, `0 FAILED`.
- Cancelled mixed-container moves: `3 CANCELLED_NOT_MOVED` (`outputs/`, `04_5J/`, `04_5K/`).
- Safety correction timing: T7-MOVE-001 completed before the corrected bounded-container rule arrived; it was a permitted notebook-only container move and verified exact. The write sequence was then terminated before T7-MOVE-002. No mixed/protected container moved.
- Every verified item is absent from its exact old parent, present in its exact target parent, and reports exactly one expected target parent.

| Independently Listed Parent | ID | Direct Children | Result |
|---|---|---:|---|
| Old project root | `1li3KfpTp53YIy4_PtOJcvqMpunUQW5Zl` | 10 | VERIFIED: all six moved direct items absent; `outputs/`, `04_5J/`, and `04_5K/` remain |
| `04_5J/` | `1M-YAK1qvvKfaEQo7IuFd8jtNEarmQZgw` | 2 | VERIFIED: `runs/` and `input/` remain; two direct notebooks absent |
| `04_5K/` | `1ScY9s0R08Jpwfccg_SnGjrJ_xmhRoR_Q` | 1 | VERIFIED: `runs/` remains; container not moved |
| `outputs/` | `1EkkV5JqRRK8vIZ6FzYgTTRG9_fIsYVzf` | 12 | VERIFIED: all direct mixed branches remain; container not moved |
| `FleetVision/03_EXPERIMENTS/01_notebooks/` | `1Lngwx-YQLlKaLWSs6KxA_nYgd8roGctI` | 0 | VERIFIED: no Drive notebook was promoted active |
| `FleetVision/99_ARCHIVE/01_deprecated_notebooks/` | `1d_wPAIJQrdCjuXaQMQl7dBuZqXQTDbeI` | 3 | VERIFIED: legacy six-notebook container plus two root historical notebooks |
| `FleetVision/99_ARCHIVE/06_duplicate_candidates/` | `1GKTVtkwZX9UdznlZ2E9y0oNf0EYL2oqK` | 1 | VERIFIED: unresolved rapid-training notebook only |
| `FleetVision/99_ARCHIVE/04_old_experiments/` | `1Hn3sDT1RqZNyzjaYu2YA5tN0W6I8twfb` | 4 | VERIFIED: two direct historical notebooks plus Candidate02 and pilot ZIPs |

### Task 7 Final Action Counters

```text
metadata-only move = 8
rename = 0
copy = 0
upload = 0
share = 0
bytes replacement = 0
trash = 0
delete = 0
permanent deletion = 0
active Drive notebook selected = 0
active tracked notebook selected = 2
cancelled mixed-container move = 3
```

No notebook was executed; no training, fine-tuning, or inference ran; Frozen Test contents/results were not listed, fetched, hashed, or read.
