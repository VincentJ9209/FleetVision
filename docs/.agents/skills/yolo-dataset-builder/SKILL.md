---
name: yolo-dataset-builder
description: Prepare and validate Ultralytics YOLO detection datasets, including image-label pairing, normalized bbox checks, train/val/test splits, and data.yaml creation.
---

# YOLO Dataset Builder Skill

Use this skill when creating YOLOv8 dataset preparation, export, validation, or split scripts.

## First Version Class Design

Use one class only:

```yaml
names:
  0: damage
```

Do not train `minor_damage` or `claim_damage` in v1.

## Expected Dataset Layout

```text
data/processed/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

## Required Tools

- `src/data/export_yolo_dataset.py`
- `src/vision/validate_yolo_dataset.py`
- `configs/data.yaml`

## Validation Rules

- Label rows must have 5 values.
- class_id must be valid.
- x_center, y_center, width, height must be between 0 and 1.
- width and height must be greater than 0.
- Missing labels and empty labels must be reported separately.

## Rules

- Do not manually distort original images to 640x640.
- Preserve original images where possible.
- Use group split if vehicle_id or rental_id exists.

