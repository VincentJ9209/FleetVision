# FleetVision Phase Guides Index

This folder contains both the current FleetVision phase guides and older planning notes. Use this index as the source of truth when choosing which phase guide to follow.

## Active phase guides

| Phase | Active guide | Status meaning |
|---|---|---|
| Phase 00 | `phase_00_setup.md` | Project setup and validation |
| Phase 01 | `phase_01_metadata.md` | Metadata builder |
| Phase 02 | `phase_02_image_review.md` | Review queue builder |
| Phase 03 | `phase_03_annotation_guidelines.md` | Review label schema and validation |
| Phase 03.5 | `phase_03_5_auto_review_prelabeller.md` | CLIP auto pre-label suggestions |
| Phase 03.6 | `phase_03_6_external_asset_scout.md` | External dataset/model scout |
| Phase 04 | `phase_04_reviewed_dataset.md` | Reviewed dataset list builder |
| Phase 05 | `phase_05_annotation_preparation.md` | Annotation task manifest preparation |
| Phase 06 | `phase_06_yolo_dataset_builder.md` | YOLO labels raw to YOLOv8 dataset builder |

## Legacy or pre-refactor notes

The following files are older planning documents and should not override the active guides above:

- `phase_03_annotation.md`
- `phase_04_yolo_dataset.md`
- `phase_05_training.md`
- `phase_06_evaluation.md`
- `phase_07_database.md`
- `phase_08_prediction_pipeline.md`
- `phase_09_dashboard.md`
- `phase_10_presentation.md`

Keep them for reference only until the roadmap is fully reconciled.

## Completion definitions

Do not mark a phase complete just because tests pass.

- **Code Complete**: scripts, tests, CLI, configs, and docs are implemented.
- **Data Complete**: real data was processed and expected outputs exist.
- **Phase Complete**: Code Complete + Data Complete + acceptance checks passed.
