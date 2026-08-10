# Results and Limitations

## Repository-Backed Results

At this checkpoint, FleetVision can support the following claims from tracked code, configuration, and tests:

| Evidence | Supported claim |
|---|---|
| Metadata and queue builders | Deterministic metadata and review-work generation are implemented and tested. |
| External intake and registry controls | Archive identity, safe extraction, COCO validation, staged promotion, and failure controls are implemented. |
| Deduplication and annotation QA | Exact/perceptual duplicate auditing, category normalization, bounding-box repair, and split QA are implemented. |
| Streamlit/SQLite review workflows | Resumable transactional review state, audit events, backups, validation, and controlled exports are implemented. |
| Validation error analysis | One-to-one IoU matching, validation-only threshold sweeps, FP/FN taxonomy, and improvement worklists are implemented. |

These are software and workflow results. They do not establish model accuracy, production readiness, or performance on newly accessed Frozen Test data.

## Historical Model Evidence

The repository retains historical model and evaluation records, but model-specific metrics remain historical evidence until each value is reconciled to an exact weight, dataset/version, split, operating point, date, and evidence artifact. A folder named `final_selected` is not final-model evidence.

No unreconciled metric is presented here as current or final performance.

## Limitations

- **No production deployment:** FleetVision is a governed engineering and research portfolio, not a deployed SaaS product.
- **No automated adjudication:** visible damage evidence does not determine insurance claimability, liability, price, legal outcome, or final business action.
- **Incomplete before/after comparison:** same-vehicle, same-view pairing and true new-damage comparison are not complete.
- **Private artifacts remain external:** private datasets, model weights, source archives, videos, presentations, and generated packages are not distributed in Git.
- **Provenance reconciliation is in progress:** model, dataset, and results registries are finalized in later reset tasks before quantitative portfolio claims are upgraded.
- **Training and inference are not complete products:** tracked builders, configurations, and historical evidence do not equal a current production training or inference service.
- **Frozen Test is protected:** it is unavailable for tuning or further access without a separate explicit Gate.
- **Phase 1/3 ownership is bounded:** capture and dashboard are team/system context; the primary individual contribution is the Phase 2 workflow.

## Current Interpretation

The strongest portfolio evidence is the safety-oriented pipeline: traceable inputs, auditable human decisions, deterministic processing, protected evaluation boundaries, and tests for failure behavior. Current technical state remains Phase 05S-A2, `PAUSED`, with Phase 05S-A3 unauthorized.
