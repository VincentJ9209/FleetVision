"""CLI for FleetVision Phase 04.5 controlled external dataset intake."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fleetvision.data.intake_external_dataset import (
    DatasetIntakeError,
    load_controlled_intake_config,
    run_controlled_intake,
)

DEFAULT_CONFIG = Path("configs/data/external_dataset_intake_config.yaml")


def resolve_project_root(value: Path | None) -> Path:
    if value is not None:
        return value.resolve()
    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "PROJECT_CONTEXT_BRIEF.md").is_file() and (candidate / "src").is_dir():
            return candidate
    return current


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest one pre-approved external dataset ZIP into FleetVision isolated raw storage."
    )
    parser.add_argument("--archive", type=Path, required=True, help="Roboflow COCO Segmentation ZIP path.")
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--project-evidence",
        type=Path,
        default=None,
        help="Reviewed local snapshot of the Roboflow project page.",
    )
    parser.add_argument(
        "--version-evidence",
        type=Path,
        default=None,
        help="Reviewed local snapshot of the Roboflow dataset version page.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = resolve_project_root(args.project_root)
    config_path = args.config if args.config.is_absolute() else project_root / args.config

    try:
        config = load_controlled_intake_config(config_path, project_root)
        result = run_controlled_intake(
            config,
            archive_path=args.archive,
            project_evidence_path=args.project_evidence,
            version_evidence_path=args.version_evidence,
        )
    except DatasetIntakeError as exc:
        print("Gate classification: EXTERNAL_DATASET_INTAKE_BLOCKED")
        print(f"ERROR: {exc}")
        print("YOLO_LABELS_CREATED: NO")
        print("DATASET_SPLIT_CREATED: NO")
        print("MODEL_TRAINING_EXECUTED: NO")
        return 2
    except Exception as exc:  # noqa: BLE001 - concise CLI boundary.
        print("Gate classification: EXTERNAL_DATASET_INTAKE_BLOCKED")
        print(f"UNEXPECTED_ERROR: {exc}")
        print("YOLO_LABELS_CREATED: NO")
        print("DATASET_SPLIT_CREATED: NO")
        print("MODEL_TRAINING_EXECUTED: NO")
        return 3

    summary = result["summary"]
    print("=== FleetVision Phase 04.5B Controlled External Dataset Intake ===")
    print(f"Gate classification: {result['gate_classification']}")
    print(f"Dataset ID: {config.dataset_id}")
    print(f"Raw dataset root: {result['raw_dataset_root']}")
    print(f"Metadata root: {result['metadata_root']}")
    print(f"Archive SHA256: {result['archive_sha256']}")
    print(
        "Inventory: "
        f"images={summary['image_record_count']}, "
        f"annotations={summary['annotation_count']}, "
        f"valid_bbox={summary['valid_bbox_count']}, "
        f"invalid_bbox={summary['invalid_bbox_count']}, "
        f"invalid_segmentation={summary['invalid_segmentation_count']}, "
        f"missing_images={summary['missing_image_count']}"
    )
    print(
        "Exact duplicate inventory: "
        f"groups={summary['exact_duplicate_group_count']}, "
        f"images={summary['exact_duplicate_image_count']}"
    )
    print(f"Lineage status: {summary['lineage_status']}")
    print(f"Training acceptance: {summary['training_acceptance']}")
    print("REGISTRY_UPDATED: NO")
    print("YOLO_LABELS_CREATED: NO")
    print("DATASET_SPLIT_CREATED: NO")
    print("MODEL_TRAINING_EXECUTED: NO")
    print("STOPPED_BEFORE_EXTERNAL_DATASET_AUDIT_AND_REGISTRY_PROMOTION_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
