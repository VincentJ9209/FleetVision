---
name: yolo-trainer
description: Train, validate, and run inference with Ultralytics YOLOv8 Detect for vehicle exterior damage detection.
---

# YOLO Trainer Skill

Use this skill when creating YOLOv8 training, validation, inference, or Colab notebook workflows.

## Baseline Settings

- model: `yolov8s.pt`
- task: detect
- class: damage
- imgsz: 640
- epochs: 50 to 100
- conf thresholds to test: 0.25, 0.4, 0.6

## Preferred Files

- `src/vision/train_yolo.py`
- `src/vision/predict_damage.py`
- `notebooks/04_train_yolov8_detect_colab.ipynb`

## Rules

- Do not train claim / non-claim classification in v1.
- Do not claim new-damage detection accuracy without paired data.
- Save training configs.
- Save model version.
- Save metrics and sample predictions.
- Explain how to run in Colab.

## Metrics to Report

- precision
- recall
- mAP50
- mAP50-95
- confusion matrix if available
- sample predictions

