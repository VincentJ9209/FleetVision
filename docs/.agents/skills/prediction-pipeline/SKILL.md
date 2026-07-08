---
name: prediction-pipeline
description: Build batch inference pipelines that run YOLOv8 on image folders and export structured prediction CSVs and annotated images.
---

# Prediction Pipeline Skill

Use this skill when building batch inference scripts for vehicle damage detection.

## Preferred File

- `src/vision/predict_damage.py`

## Required Outputs

- `outputs/predictions/damage_predictions.csv`
- `outputs/predictions/annotated_images/`

## Required CSV Columns

- image_id
- file_path
- class_id
- class_name
- confidence
- x1
- y1
- x2
- y2
- image_width
- image_height
- model_version

## Rules

- Handle no-detection images gracefully.
- Save annotated images.
- Print total image count, detection count, and output path.
- Keep outputs easy to load into PostgreSQL and Streamlit.

