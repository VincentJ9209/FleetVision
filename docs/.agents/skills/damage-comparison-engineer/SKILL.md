---
name: damage-comparison-engineer
description: Build rule-based pickup/return vehicle damage comparison logic using YOLO bounding boxes, IoU matching, confidence thresholds, and review-required rules.
---

# Damage Comparison Engineer Skill

Use this skill when building before-after comparison logic.

## Important Limitation

The current dataset has no real paired pickup/return photos. Therefore, this module is a rule-based scaffold and validation tool, not a fully trained new-damage model.

## Preferred File

- `src/vision/compare_damage.py`
- `tests/test_compare_damage.py`

## Matching Keys

- rental_id
- vehicle_id
- angle

## Decision Logic

- return confidence >= threshold and max IoU < iou_threshold → suspected_new_damage
- return confidence >= threshold and max IoU >= iou_threshold → existing_damage
- no return damage → no_new_damage
- poor quality or missing data → review_required

## Required Functions

- `calculate_iou(box_a, box_b)`
- `match_damage_boxes(...)`
- `compare_pickup_return(...)`

## Rules

- Add unit tests for IoU.
- Output clear reasons for review_required.
- Be explicit about limitations due to lack of paired data.

