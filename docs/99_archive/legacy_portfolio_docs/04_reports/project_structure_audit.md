# FleetVision Project Structure Audit

## Audit scope

This audit was created after reviewing a compressed FleetVision project folder with image files and `.venv` content intentionally excluded.

The goal is to keep the repo lightweight, reduce confusion between generated data and source code, and align current labels/configs with the active FleetVision workflow.

## Key findings

| Area | Finding | Decision |
|---|---|---|
| Archive hygiene | Uploaded package included `.git/`, `.env`, `.pytest_cache/`, `__pycache__/`, and `src/fleetvision.egg-info/` | Keep these out of future sharing packages |
| Generated data | `dataset/00_catalog/image_review_labels.csv`, `external_asset_registry.csv`, review queue, and metadata CSVs are local/generated data | Do not commit unless explicitly approved |
| Review schema | `configs/data/review_label_schema.yaml` had a malformed nested `angle_review.allowed_values` structure | Fixed to a direct string list |
| Angle labels | Active workflow uses `front`, `rear`, `left`, `right`, `front_left`, `front_right`, `rear_left`, `rear_right`, `unknown` | Standardize on underscore values; do not use spaces |
| Severity labels | Active workflow should use `none`, `minor`, `moderate`, `severe`, `unknown` | Keep `claimable` as a later business/claim decision, not a severity label |
| Validation encoding | UTF-8 BOM CSVs from Excel may make the first column look like `\ufeffreview_id` | Validator now reads review CSVs with `utf-8-sig` |
| Phase docs | Some older phase docs still exist from earlier roadmap versions | Use `docs/01_phase_guides/README.md` as the active phase guide index |

## Canonical label values

### `photo_type_review`

```text
exterior
interior
low_quality
irrelevant
unknown
```

### `angle_review`

```text
front
rear
left
right
front_left
front_right
rear_left
rear_right
unknown
```

### `severity_review`

```text
none
minor
moderate
severe
unknown
```

`severity_review` is metadata for prioritization, rules, and human review. It is not the YOLO class.

The first YOLO model remains:

```text
0 = damage
```

## Completion rule

Do not mark a phase complete just because tests pass.

| State | Meaning |
|---|---|
| Code Complete | scripts, tests, CLI, configs, and docs are implemented |
| Data Complete | real data was processed and expected outputs exist |
| Phase Complete | Code Complete + Data Complete + acceptance checks passed |

## Recommended local cleanup

Run from the project root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/cleanup_local_artifacts.ps1
python scripts/phase00_init_project.py --validate
pytest
git status --short
```

## Future package sharing rule

When sharing the project folder for review, exclude:

```text
.git/
.env
.venv/
.pytest_cache/
__pycache__/
src/fleetvision.egg-info/
dataset/01_raw/**/images/
large generated CSVs unless specifically needed
models/
runs/
mlruns/
*.zip
*.rar
```

Prefer sharing a lightweight source snapshot plus selected small CSV samples when needed.
