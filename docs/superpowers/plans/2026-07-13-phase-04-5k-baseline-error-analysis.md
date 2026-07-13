# Phase 04.5K Baseline Error Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. This implementation was completed directly in an isolated build workspace because Codex and Cursor Agent were paused by the user.

**Goal:** Produce validation-only threshold candidates, traceable error records, representative review artifacts, and prioritized data-improvement recommendations for the Phase 04.5J YOLOv8s baseline.

**Architecture:** A tested pure-Python evaluation core is shared by a CSV-based local CLI and a self-contained Colab Notebook. The Notebook performs the only GPU inference, extracts validation files only, and packages evidence without model weights.

**Tech Stack:** Python 3.10+, pandas, NumPy, PyYAML, pytest, Ultralytics 8.4.93, Pillow, matplotlib.

## Global Constraints

- Model SHA256 must equal `90A880513A42EF2DB1373902D98FF09D1756AB7A8A4EEA6A7AA231D4020B77BF`.
- Allowed split is exactly `valid`.
- Expected validation set is 168 images and 325 annotations.
- Test set must not be read or used for tuning.
- No training or fine-tuning.
- Deployment acceptance remains `NOT_YET_APPROVED`.
- Do not modify canonical COCO, raw data, Registry, formal YOLO data, or annotations.

## Task 1 — Evaluation core

- Add IoU and deterministic matching.
- Add threshold evaluation and sweep.
- Add candidate selection and bbox-size classification.
- Add data-improvement aggregation.
- Verify with synthetic unit tests.

## Task 2 — Local analysis CLI

- Read prediction and GT CSV files.
- Validate fail-closed config and expected validation counts.
- Build metrics, object records, error summaries, priorities, report, manifest, and checksums in staging.
- Atomically promote the completed output.
- Verify success and count-mismatch failure paths.

## Task 3 — Controlled Colab workflow

- Locate and validate the unique Phase 04.5J PASS result.
- Verify `best.pt`, TAR, descriptor, and dataset manifest hashes.
- Extract validation paths only.
- Run one inference pass at confidence floor 0.001.
- Parse GT labels and invoke the tested evaluation core.
- Generate threshold chart, review worklist, overlays, report, manifest, Gate result, and ZIP Log.
- Statically verify no training call and no test-split evaluation call.

## Task 4 — Governance and handoff

- Add the Phase guide, design, plan, and checkpoint-recovery note.
- Package repo-relative files with a PowerShell 5.1 installer.
- Do not commit or push without explicit authorization.
