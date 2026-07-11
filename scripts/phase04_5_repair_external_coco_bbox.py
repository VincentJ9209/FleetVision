"""CLI for FleetVision Phase 04.5C external COCO bbox repair."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fleetvision.data.repair_external_coco_bbox import (
    BboxRepairError,
    build_external_coco_bbox_repair,
    find_project_root,
    resolve_path,
)

DEFAULT_CONFIG = Path("configs/data/external_coco_bbox_repair_config.yaml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Repair right/bottom COCO bbox overflow for one approved external dataset "
            "into dataset/02_interim without modifying raw sources."
        )
    )
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = find_project_root(args.project_root)
    config_path = resolve_path(args.config, project_root)

    try:
        result = build_external_coco_bbox_repair(config_path, project_root=project_root)
    except BboxRepairError as exc:
        print("Gate classification: EXTERNAL_COCO_BBOX_REPAIR_BLOCKED")
        print(f"ERROR: {exc}")
        print("RAW_SOURCE_MODIFIED: NO")
        print("REGISTRY_UPDATED: NO")
        print("YOLO_LABELS_CREATED: NO")
        print("DATASET_SPLIT_CREATED: NO")
        print("MODEL_TRAINING_EXECUTED: NO")
        return 2
    except Exception as exc:  # noqa: BLE001 - concise CLI boundary.
        print("Gate classification: EXTERNAL_COCO_BBOX_REPAIR_BLOCKED")
        print(f"UNEXPECTED_ERROR: {exc}")
        print("RAW_SOURCE_MODIFIED: NO")
        print("REGISTRY_UPDATED: NO")
        print("YOLO_LABELS_CREATED: NO")
        print("DATASET_SPLIT_CREATED: NO")
        print("MODEL_TRAINING_EXECUTED: NO")
        return 3

    summary = result["summary"]
    print("=== FleetVision Phase 04.5C External COCO BBox Repair ===")
    print(f"Gate classification: {result['gate_classification']}")
    print(f"Dataset ID: {result['dataset_id']}")
    print(
        "BBox repair: "
        f"input_annotations={summary['input_annotation_count']}, "
        f"repaired={summary['repaired_count']}, "
        f"dropped={summary['dropped_count']}, "
        f"output_annotations={summary['output_annotation_count']}, "
        f"invalid_after={summary['invalid_after_count']}"
    )
    print("RAW_SOURCE_MODIFIED: NO")
    print("REGISTRY_UPDATED: NO")
    print("YOLO_LABELS_CREATED: NO")
    print("DATASET_SPLIT_CREATED: NO")
    print("MODEL_TRAINING_EXECUTED: NO")
    print("STOPPED_BEFORE_EXTERNAL_DATASET_REGISTRY_PROMOTION_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
