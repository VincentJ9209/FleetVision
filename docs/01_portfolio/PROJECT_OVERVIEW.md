# Project Overview

## Problem

Vehicle-damage detection is not only a model-selection problem. Image collections can contain inconsistent metadata, weak lineage, duplicates, unsafe train/test relationships, and annotations that have not passed human review. Those defects can make a strong-looking metric impossible to interpret.

FleetVision addresses the engineering layer between raw vehicle images and reviewable computer-vision evidence. The repository emphasizes deterministic data contracts, human confirmation, provenance, failure-no-overwrite behavior, and explicit evaluation boundaries.

## FleetVision Scope

FleetVision is the second stage of a broader vehicle-condition system. It receives image and metadata inputs, validates and organizes them, supports review and annotation workflows, governs external data, and provides model-evaluation tooling.

The intended downstream vocabulary—`NO_NEW_DAMAGE`, `NEW_DAMAGE_CANDIDATE`, and `MANUAL_REVIEW_REQUIRED`—is review-oriented. It is not an insurance, liability, pricing, legal, or final business adjudication contract.

## My Primary Contribution

My primary individual contribution is the Phase 2 data-and-model workflow represented in this repository:

- metadata inventory and deterministic review queues;
- reviewed-dataset and annotation-task preparation;
- external-dataset registry, intake, canonicalization, deduplication, and QA controls;
- Traditional Chinese human-review tooling with Streamlit and SQLite;
- validation-only model error analysis and evidence worklists;
- tests for schemas, deterministic ordering, path safety, integrity, rollback, and no-overwrite behavior.

Representative implementation paths include [`src/fleetvision/data/`](../../src/fleetvision/data/), [`src/fleetvision/review/`](../../src/fleetvision/review/), and [`src/fleetvision/evaluation/`](../../src/fleetvision/evaluation/).

## Three-Stage Team Context

1. **Phase 1 — Capture context:** collect vehicle images and metadata under a consistent contract.
2. **Phase 2 — FleetVision:** validate, review, govern, prepare, and evaluate vehicle-damage evidence. This is my primary contribution.
3. **Phase 3 — Review/dashboard context:** present governed outputs for human interpretation and operational follow-up.

Phase 1 capture and Phase 3 dashboard/review describe system integration surfaces. They are not presented as my individually completed applications unless repository evidence supports a specific Phase 2 review component.

## What Is Implemented Today

- Metadata and review-queue builders with tracked configuration and automated tests.
- Review worklists, package builders, validators, mergers, and controlled exports.
- Purpose-built Streamlit/SQLite review workflows with resumable state, audit events, backup, integrity checks, and no-overwrite exports.
- External COCO intake with provenance, archive identity, safe extraction, validation, staging, and promotion controls.
- Exact/perceptual deduplication audit support, category normalization, bounding-box repair, and annotation/split QA.
- Validation-only threshold sweeps, one-to-one IoU matching, FP/FN taxonomy, and improvement prioritization.

The authoritative current capability summary is [`PROJECT_STATUS.md`](../02_workflow/PROJECT_STATUS.md).

## What Is Not Implemented

- A production SaaS deployment or complete application stack.
- A completed before/after same-vehicle, same-view damage-comparison workflow.
- Automated severity, claimability, insurance liability, pricing, or legal decisions.
- A production-accepted final model supported by reconciled model, dataset, and metric provenance.
- End-to-end application integration for PostgreSQL, MLflow, or a customer-facing dashboard.

Technical development remains paused at Phase 05S-A2; Phase 05S-A3 requires separate authorization.
