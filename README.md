# FleetVision

> An evidence-first computer-vision workflow for turning imperfect vehicle images into governed, reviewable damage-analysis data.

FleetVision is my Phase 2 contribution to a broader three-stage vehicle-condition system. It focuses on metadata quality, human review, external-dataset governance, annotation QA, deduplication, and reproducible evaluation—not automated insurance decisions or a production SaaS product.

## Problem

Vehicle-damage modelling fails when image provenance, review state, annotation quality, and split boundaries are ambiguous. FleetVision treats those controls as engineering requirements so that later model experiments can be traced to reviewed inputs and defensible evidence.

[Project overview](docs/01_portfolio/PROJECT_OVERVIEW.md)

## What I Built

- Deterministic metadata inventories and review queues.
- Traditional Chinese Streamlit review workflows backed by transactional SQLite state, audit events, backups, and no-overwrite exports.
- Registry- and license-aware external COCO intake with archive identity, safe extraction, staged promotion, and failure controls.
- SHA-256 and perceptual-hash deduplication audits with bounded review candidates.
- Geometry-preserving category normalization, bounding-box repair, annotation QA, and group-leakage checks.
- Validation-only threshold and error-analysis tooling with one-to-one IoU matching and FP/FN worklists.

The first detection contract is YOLOv8 Detect with one class: `damage`. Severity, claimability, liability, and true new-damage decisions are outside that model contract.

## Architecture

The broader team context is Phase 1 capture → Phase 2 FleetVision data/model workflow → pairing/comparison boundary → Phase 3 human review/dashboard. Repository evidence supports the Phase 2 governance and review workflows most strongly; before/after comparison remains incomplete, and Phase 1/3 are integration context rather than claims of individual implementation.

[Architecture and status semantics](docs/01_portfolio/ARCHITECTURE.md)

## Key Engineering Challenges

1. **Fail closed on external intake:** reject unsafe paths, invalid COCO references, identity mismatches, and partial promotion.
2. **Keep review state recoverable:** use SQLite transactions, resumable progress, audit synchronization, and controlled exports.
3. **Prevent leakage and duplicate inflation:** preserve group boundaries and separate exact duplicates from bounded perceptual candidates.
4. **Separate evidence from naming:** a folder called `final_selected` or `dataset_v3` is not accepted as provenance.
5. **Keep evaluation honest:** threshold analysis uses validation evidence only; Frozen Test is not available for tuning.

[Data pipeline](docs/01_portfolio/DATA_PIPELINE.md) · [Evaluation methodology](docs/01_portfolio/MODEL_EVALUATION.md)

## Evidence-Backed Results

The repository demonstrates implemented software contracts rather than a reconciled final model score:

- metadata and review-queue generation with deterministic tests;
- governed external-dataset intake, deduplication, canonicalization, and split QA;
- human-in-the-loop review state with integrity, backup, and export controls;
- validation error analysis that converts FP/FN evidence into review and data-improvement worklists;
- a broad automated suite that uses synthetic or temporary fixtures for most data-path checks.

Historical model metrics remain historical evidence until model, dataset, and result provenance is reconciled in later maintenance tasks. Test results verify repository behavior, not model accuracy or deployment readiness.

[Results and limitations](docs/01_portfolio/RESULTS_AND_LIMITATIONS.md)

## Demo / Portfolio Assets

The repository contains a lightweight [demo-package guide](demo/README_demo.md). Large videos, screenshots, presentations, private images, datasets, model weights, and generated review packages are intentionally stored outside Git and will be linked only after their Drive identity and sharing status are verified.

[Interview guide](docs/01_portfolio/INTERVIEW_GUIDE.md)

## Tech Stack

Python 3.10+, pandas, NumPy, OpenCV, Pillow, Streamlit, SQLite, Ultralytics YOLOv8, scikit-learn, pytest, PostgreSQL and MLflow scaffolding, Git/GitHub, and Google Drive for large private artifacts.

PostgreSQL and MLflow are supporting development services in [Docker Compose](docker-compose.yml); neither is presented as end-to-end application integration.

## Repository Tour

| Path | Purpose |
|---|---|
| [`src/fleetvision/data/`](src/fleetvision/data/) | Metadata, review queues, external intake, deduplication, canonicalization, and QA. |
| [`src/fleetvision/review/`](src/fleetvision/review/) | Streamlit/SQLite human-review workflows and governed exports. |
| [`src/fleetvision/evaluation/`](src/fleetvision/evaluation/) | Validation-only threshold and error analysis. |
| [`scripts/`](scripts/) | Thin CLI and operational entry points. |
| [`configs/`](configs/) | Versioned data, review, model, and QA contracts. |
| [`tests/`](tests/) | Unit, integration, CLI, safety, and regression tests. |
| [`docs/01_portfolio/`](docs/01_portfolio/) | Interview-first reading path. |
| [`docs/02_workflow/`](docs/02_workflow/) | Current status, handoff, safety, and artifact ledgers. |
| [`docs/03_decisions/`](docs/03_decisions/) | Active decision index. |

## Reproduce / Test

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q -p no:cacheprovider
```

The tracked test suite does not require private datasets or model weights. Data-processing commands require separately managed inputs, current configuration, and the applicable project Gate.

## Limitations

- No production deployment or complete application stack.
- No automated insurance, claimability, liability, pricing, or legal conclusion.
- Before/after same-vehicle, same-view damage comparison is not complete.
- Private datasets, model weights, source archives, and generated artifacts are not distributed in Git.
- YOLO dataset materialization, current model selection, and public metrics remain subject to governed evidence and provenance reconciliation.
- Frozen Test access, training, fine-tuning, and Phase 05S-A3 implementation are not authorized during portfolio maintenance.

## Current Status

| Field | Current value |
|---|---|
| Technical phase | `Phase 05S-A2 — Implementation Plan Approved and Documented` |
| Technical development | `PAUSED` |
| Current activity | `PORTFOLIO_MAINTENANCE` |
| Last completed technical Gate | `PHASE_05S_A2_PLAN_DOCUMENT_APPLICATION_AND_CHECKPOINT` |
| Next technical Gate | `PHASE_05S_A3_IMPLEMENTATION_AUTHORIZATION_BEFORE_CODE` |
| A3 authorized | `false` |

Portfolio maintenance does not advance the technical phase. Development resumes from [START_HERE.md](START_HERE.md), not from historical chat context.
