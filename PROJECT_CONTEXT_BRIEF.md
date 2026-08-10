# FleetVision Project Context Brief

## Project identity and scope

- Project: FleetVision／車損辨識
- Repository root: `G:\FleetVision\Project\FleetVision`
- Main branch: `main`
- Retired project: `irent-damage-detection` must not be restored or reused.

FleetVision is a second-stage, traceable and reproducible vehicle-exterior damage workflow. It receives before／after photos and metadata, validates the input contract, supports human-reviewable structured results, and is not a first-stage capture App or a large Dashboard.

The intended result vocabulary is `NO_NEW_DAMAGE`, `NEW_DAMAGE_CANDIDATE`, and `MANUAL_REVIEW_REQUIRED`. These are review-oriented outputs, not insurance liability, claimability, pricing, legal, or final business adjudications.

## Immutable architecture

- The first model is YOLOv8 Detect with one Bounding Box class: `damage`.
- `minor_damage` and `claimable_damage` may remain metadata or review concepts, but are not YOLO classes.
- CLIP is limited to approved `photo_type` suggestions; its approved threshold is `0.75`.
- Angle may use explicit filename rules or human review only; never infer it from `_1`, `_2`, `_3`, or `_4`.
- Damage and severity require human confirmation.
- Phase 03.5 inference is frozen and may not be rerun without a formal decision and full rerun plan.

## Data strategy and safety

Internal data represents the real rental-vehicle setting. Use group-safe separation to prevent vehicle, rental, burst, and near-duplicate leakage. Frozen internal holdout definitions remain fixed and separate from external data.

External data intake requires source and license provenance, class mapping to `damage`, bbox QA, SHA256/perceptual deduplication, cross-source review, and acceptance evidence before training use. Do not mutate raw assets, canonical assets, Registry assets, or human-review artifacts without an explicit Gate.

General vehicle-condition images require stratified negative sampling rather than wholesale training inclusion. Hard negatives should cover reflections, water marks, shadows, seams, contours, lamp reflections, stickers, normal body shapes, and low-light noise.

## System integration context

- Production Python belongs in `src/fleetvision/`; notebooks are for exploration or approved Colab workflows, not primary business logic.
- Human review defaults to a local Traditional Chinese Streamlit interface, SQLite live state, audit events, resumable backups, and no-overwrite completed exports.
- Excel is for completed export, exchange, archive, or a specifically approved offline-collaboration exception.
- Large images, models, training outputs, database dumps, review packages, and secrets stay outside Git.

## Current operational boundary

- Technical phase: `Phase 05S-A2 — Implementation Plan Approved and Documented`
- Technical development: `PAUSED`
- Current activity: `PORTFOLIO_MAINTENANCE`
- Last completed technical Gate: `PHASE_05S_A2_PLAN_DOCUMENT_APPLICATION_AND_CHECKPOINT`
- Next technical Gate: `PHASE_05S_A3_IMPLEMENTATION_AUTHORIZATION_BEFORE_CODE`
- A3 implementation, formal `04_team` scanning, Frozen Test access, training, fine-tuning, model inference, Dashboard work, and first-stage App work are not authorized during portfolio maintenance.

Use `START_HERE.md` and `docs/02_workflow/` for the current task lifecycle, durable status, handoff, and protected-asset rules. Repository evidence and live Git facts override chat history.
