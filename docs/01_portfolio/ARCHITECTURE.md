# Architecture

FleetVision separates team-system context from repository-backed implementation status.

```mermaid
flowchart LR
    A["Phase 1 Capture<br/>PARTIAL / TEAM CONTEXT"]
    B["Image + metadata contract<br/>IMPLEMENTED IN PHASE 2 INPUT VALIDATION"]
    C["Phase 2 FleetVision<br/>IMPLEMENTED DATA GOVERNANCE + REVIEW<br/>PARTIAL MODEL PIPELINE"]
    D["Pairing + before/after comparison boundary<br/>PLANNED"]
    E["Phase 3 human review / dashboard context<br/>PARTIAL"]

    A --> B --> C --> D --> E
```

## Status Semantics

| Boundary | Status | Evidence-backed interpretation |
|---|---|---|
| Phase 1 capture | `PARTIAL` / team context | The repository defines downstream metadata and image expectations but does not contain a completed first-stage capture product. |
| Image + metadata contract | `IMPLEMENTED` | Metadata scanning, stable identifiers, quality fields, configuration, and tests exist in [`build_metadata.py`](../../src/fleetvision/data/build_metadata.py). |
| Phase 2 data governance and review | `IMPLEMENTED` | Data intake, deduplication, canonicalization, QA, review state, and exports are implemented under [`src/fleetvision/`](../../src/fleetvision/). |
| Phase 2 YOLO dataset/training/inference | `PARTIAL` | Builders, configuration, and historical evidence exist, but current governed materialization, model selection, and production inference are not complete. |
| Pairing and before/after comparison | `PLANNED` | Focused IoU utility support exists in [`compare_damage.py`](../../src/fleetvision/vision/compare_damage.py), but the end-to-end comparison workflow is not implemented. |
| Phase 3 human review/dashboard | `PARTIAL` | Purpose-built local review apps exist; a complete customer-facing dashboard and product integration do not. |

## Phase 2 Internal Flow

```mermaid
flowchart TB
    A["Metadata inventory"] --> B["Deterministic review queue"]
    B --> C["Human review + reviewed records"]
    D["External source + license registry"] --> E["Controlled intake"]
    E --> F["Exact / perceptual dedup audit"]
    F --> G["Category canonicalization + bbox repair"]
    G --> H["Annotation + group-safe split QA"]
    C --> I["Governed dataset boundary"]
    H --> I
    I --> J["YOLOv8 Detect workflow — PARTIAL"]
    J --> K["Validation-only evaluation + error analysis"]
    K --> L["Human-review feedback worklists"]
```

Large/private artifacts stay outside Git; Git records code, configuration, tests, current state, decisions, and provenance references. See the [data pipeline](DATA_PIPELINE.md) and [protected-asset contract](../02_workflow/PROTECTED_ASSETS.md).
