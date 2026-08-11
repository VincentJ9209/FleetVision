# FleetVision Dataset Registry

## Registry Boundary

- Registry checkpoint: Task 9 `PORTFOLIO_MAINTENANCE`; technical development remains `PAUSED` at Phase 05S-A2.
- This registry distinguishes protected historical baselines, working copies, unresolved legacy datasets, and export packages. Naming alone is not provenance.
- Frozen Test contents were not listed, fetched, read, hashed, or used. For the protected baseline, only the top-level structure names `train/`, `valid/`, `test/`, and `lineage/` were verified.
- First-pass permanent deletion remains prohibited. Dataset relocation in this task was metadata-only parent movement; no dataset bytes, labels, manifests, split definitions, or canonical content were rewritten.

| Dataset ID | Artifact / Location | Role | Canonical Status | Split / Holdout Boundary | Lineage Evidence | Protection | Allowed Use |
|---|---|---|---|---|---|---|---|
| `DS-INT-V1` | Drive `FleetVision/01_DATA/01_internal/internal_grouped_dataset_v1_20260717_212356/` (ID `15u6KNMwei6J1vEfG57DO-z9y9nlAyIEw`) | `HISTORICAL_BASELINE` | `PROTECTED_HISTORICAL_BASELINE`; not promoted as a new/current canonical dataset by this maintenance task | Repository contract records Train/Valid/Test = 137/29/29 and zero cross-split groups; direct Drive structure contains `train/`, `valid/`, `test/`, `lineage/`. Frozen Test contents were not accessed. | `docs/99_archive/legacy_project_management/PHASE05R_SCOPE_CONTRACT.md` records total 195 images, 100 positive / 95 null, 159 boxes, 57 vehicle groups, cross-split groups 0, external frozen overlap 0, ZIP SHA256 `B72812D97E08B312EBC239ADB43C7DE7DED29FB1B3098CD3BEA17C880813C58A`. The SHA is repository evidence for the historical packaged identity, not a fresh hash of the Drive folder. | `PROTECTED`; content mutation prohibited; Task 9 performed one metadata-only parent relocation with the same Drive item ID. | Historical lineage/reference and future governed work only. No Frozen Test tuning or relabeling; no content mutation under this reset. |
| `DS-RELABEL-V3-WORKING` | Drive `FleetVision/99_ARCHIVE/02_old_datasets/dataset_v3_relabel_working_20260720_091414/` (ID `1NDs9m9HCFMAKg9O9MCHnRgnG_sZ1sCKx`) | `WORKING_COPY` | `NOT_CANONICAL` | Working package contains train/valid only. Its manifest states `frozen_test_included=false` and `test_split_included=false`. | `README_RELABEL.txt` states this is a human relabel working copy, not formal Dataset v3, and the original internal baseline must not be modified. `dataset_v3_relabel_package_manifest.json` records 137 train images/labels, 29 valid images/labels, `source_dataset_modified=false`. | Preserve as historical working evidence; never overwrite the protected baseline. | Human relabel history only. Must not be treated as formal Dataset v3 or as canonical training input without a later controlled promotion gate. |
| `DS-RELABEL-V3-ZIP` | Drive `FleetVision/99_ARCHIVE/06_duplicate_candidates/dataset_v3_relabel_working_20260720_091414.zip` (ID `1No4IDs-VmR0oLY4IxzVZhltikPbUROQi`, size `7,032,317` bytes) | `ARCHIVE_RECONCILIATION` | `NOT_CANONICAL`; `DUPLICATE_CANDIDATE` | By name and timestamp it corresponds to the relabel working package, but byte/content equivalence is not asserted or tested in Task 9. | Drive metadata plus working-copy README/manifest. No ZIP contents were opened and no checksum comparison was performed. | Retain; `Delete Allowed=false`. | Duplicate-candidate/archive evidence only until an independent identity check and explicit deletion authorization. |
| `DS-GROUPED-LEGACY` | Drive old project root `grouped_dataset/` (ID `1UG9y4jEuJL28lk7pdIotFj-Hqqp5mgGg`) | `ARCHIVE_RECONCILIATION` | `UNRESOLVED_IDENTITY`; not canonical | Holdout/split lineage is not sufficiently grounded for a safe relocation. Task 9 did not enumerate nested contents because doing so was unnecessary for a `NOT_MOVED` decision and could cross protected evaluation boundaries. | Historical project context indicates legacy/flattened path artifacts, but current provenance is insufficient to promote or relocate safely. | `RECONCILE_REQUIRED`; retained in place. | No active training/evaluation use. Future reconciliation must establish lineage and holdout boundaries before any move or promotion. |
| `DS-YOLO-LABELS-ZIP` | Drive old project root `FleetVision_YOLO_Labels_Package.zip` (ID `1BDp1KKMZr1Km86kglHnY_Ux5wnYycR4V`, size `48,881` bytes) | `ARCHIVE_RECONCILIATION` | `UNRESOLVED_EXPORT_PROVENANCE`; not canonical | Split/holdout coverage is unknown from trusted evidence. File contents were not opened in Task 9. | Drive metadata only. No repository evidence safely maps this ZIP to a canonical annotation set or reproducible export. | `RECONCILE_REQUIRED`; retained in place; `Delete Allowed=false`. | No active training/evaluation use. May be classified later only from explicit lineage evidence, not filename. |

## Task 9 Safety Result

```text
metadata-only Drive move = 3
first-pass deletion count = 0
raw content mutation = 0
Frozen Test content access = 0
working copy promoted to canonical = false
training / fine-tuning = 0
```

Task 9 relocated only the three fully grounded items above: the relabel working folder, its ZIP duplicate candidate, and the protected historical baseline (last). `grouped_dataset/` and `FleetVision_YOLO_Labels_Package.zip` remain `NOT_MOVED` until provenance is sufficient.
