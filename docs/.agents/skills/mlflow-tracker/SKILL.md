---
name: mlflow-tracker
description: Add MLflow experiment tracking for YOLO training runs, including parameters, metrics, artifacts, model versions, and comparison workflows.
---

# MLflow Tracker Skill

Use this skill when adding or modifying experiment tracking.

## Track These Params

- model
- epochs
- imgsz
- batch
- data_yaml
- run name
- dataset_version

## Track These Metrics

- precision
- recall
- mAP50
- mAP50-95

## Track These Artifacts

- best.pt
- data.yaml
- training_config.json
- confusion matrix
- sample predictions

## Rules

- MLflow integration should be optional via `--use_mlflow`.
- If MLflow server is unavailable, show a clear error.
- Do not break normal training without MLflow.
- Explain how to open MLflow UI.

