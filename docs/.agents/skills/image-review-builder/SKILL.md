---
name: image-review-builder
description: Build Streamlit tools for manually reviewing and classifying images as exterior, interior, irrelevant, low_quality, or unknown.
---

# Image Review Builder Skill

Use this skill when building a simple image review interface for filtering the mixed iRent image dataset.

## Goal

Create a lightweight app that helps users classify images into:

- exterior
- interior
- irrelevant
- low_quality
- unknown

## Preferred File

- `src/app/image_review_app.py`

## Inputs

- `data/metadata/image_metadata.csv`

## Outputs

- `data/metadata/image_review_labels.csv`

## UI Requirements

- Show one image at a time.
- Display filename, image size, blur_score, brightness.
- Provide classification buttons.
- Save progress after each click.
- Allow filtering unreviewed images.
- Show reviewed count and remaining count.

## Rules

- Keep the app simple.
- Do not build a complex database-backed app in v1.
- If an image path is missing, show a friendly warning.
- Make sure progress is not lost when Streamlit reruns.

