---
name: dataset-auditor
description: Audit image datasets for computer vision projects. Build image metadata, detect corrupted images, compute dimensions, blur score, brightness, and dataset summaries.
---

# Dataset Auditor Skill

Use this skill when creating or modifying scripts related to image inventory, metadata, image quality checks, and dataset summaries.

## Required Files

Prefer creating or updating:

- `src/data/build_metadata.py`
- `src/vision/quality_check.py`
- `data/metadata/image_metadata.csv`
- `outputs/reports/data_inventory_summary.csv`

## Required Metadata Columns

- image_id
- file_path
- filename
- file_extension
- file_size_bytes
- image_width
- image_height
- aspect_ratio
- is_readable
- blur_score
- brightness
- photo_type
- angle
- has_visible_damage
- severity_label
- source_group
- split

## Rules

- Never modify original files in `data/raw/`.
- Handle corrupted images gracefully.
- Use pathlib, pandas, cv2, numpy.
- Print summary counts.
- Save outputs to `data/metadata/` or `outputs/reports/`.
- Use CLI arguments.

## Validation Checklist

- The script runs from project root.
- Output CSV exists.
- Bad images are recorded, not ignored silently.
- Total processed count is printed.
- CSV can be loaded by pandas.

