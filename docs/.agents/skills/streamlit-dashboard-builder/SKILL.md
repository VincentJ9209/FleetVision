---
name: streamlit-dashboard-builder
description: Build Streamlit dashboards for reviewing vehicle damage predictions, bounding boxes, model confidence, and suspected new damage cases.
---

# Streamlit Dashboard Builder Skill

Use this skill when creating or improving the dashboard.

## Preferred File

- `src/app/streamlit_dashboard.py`

## Inputs

- `data/metadata/image_metadata.csv`
- `outputs/predictions/damage_predictions.csv`
- `outputs/reports/damage_comparison_results.csv`

## Required Features

- Summary metrics
- Confidence distribution
- Detections by angle
- Result distribution
- Image display with bbox overlay
- Filters by model_version, confidence, angle, result
- Review-required case list

## Rules

- Keep v1 simple and robust.
- If images are missing, show friendly warnings.
- Do not require PostgreSQL for first dashboard version unless explicitly requested.
- Make CSV-based dashboard work first.

