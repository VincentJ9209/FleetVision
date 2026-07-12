"""CLI for FleetVision Phase 04.5D-2 Registry v2 intake promotion."""

from __future__ import annotations

import argparse
from pathlib import Path

from fleetvision.data.promote_external_dataset_registry_v2_intake import (
    BLOCKED_CLASSIFICATION,
    RegistryIntakePromotionError,
    promote_external_dataset_registry_v2_intake,
)

DEFAULT_CONFIG = Path(
    "configs/data/external_dataset_registry_v2_intake_promotion_config.yaml"
)


def resolve_project_root(value: Path | None) -> Path:
    """Resolve an explicit root or discover the FleetVision repository root."""

    if value is not None:
        return value.resolve()
    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (
            (candidate / "PROJECT_CONTEXT_BRIEF.md").is_file()
            and (candidate / "src").is_dir()
        ):
            return candidate
    return current


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely validate or promote FleetVision external-dataset intake "
            "results into Registry v2."
        )
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--project-root", type=Path, default=None)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and propose without writing (default).",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Atomically replace the Registry after validation.",
    )
    return parser


def _print_safety_flags() -> None:
    print("RAW_SOURCE_MODIFIED: NO")
    print("INTERIM_SOURCE_MODIFIED: NO")
    print("EXTERNAL_METADATA_MODIFIED: NO")
    print("YOLO_LABELS_CREATED: NO")
    print("DATASET_SPLIT_CREATED: NO")
    print("MODEL_TRAINING_EXECUTED: NO")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = resolve_project_root(args.project_root)
    mode = "EXECUTE" if args.execute else "DRY_RUN"

    try:
        result = promote_external_dataset_registry_v2_intake(
            args.config,
            project_root,
            execute=args.execute,
        )
    except RegistryIntakePromotionError as exc:
        print(
            "=== FleetVision Phase 04.5D-2 External Dataset Registry v2 "
            "Intake Promotion ==="
        )
        print(f"Mode: {mode}")
        print("REGISTRY_UPDATED: NO")
        _print_safety_flags()
        print("TRAINING_ACCEPTANCE: NOT_YET_APPROVED")
        print(f"Gate classification: {BLOCKED_CLASSIFICATION}")
        print(f"ERROR: {exc}")
        print("STOPPED_BEFORE_EXTERNAL_DATASET_REGISTRY_V2_INTAKE_PROMOTION")
        return 2
    except Exception as exc:  # noqa: BLE001 - concise CLI boundary.
        print(
            "=== FleetVision Phase 04.5D-2 External Dataset Registry v2 "
            "Intake Promotion ==="
        )
        print(f"Mode: {mode}")
        print("REGISTRY_UPDATED: NO")
        _print_safety_flags()
        print("TRAINING_ACCEPTANCE: NOT_YET_APPROVED")
        print(f"Gate classification: {BLOCKED_CLASSIFICATION}")
        print(f"ERROR: unexpected failure: {exc}")
        print("STOPPED_BEFORE_EXTERNAL_DATASET_REGISTRY_V2_INTAKE_PROMOTION")
        return 3

    print(
        "=== FleetVision Phase 04.5D-2 External Dataset Registry v2 "
        "Intake Promotion ==="
    )
    print(f"Mode: {result.summary.mode}")
    print(
        "REGISTRY_UPDATED: "
        f"{'YES' if result.summary.registry_updated else 'NO'}"
    )
    _print_safety_flags()
    print(
        "TRAINING_ACCEPTANCE: "
        f"{result.summary.training_acceptance}"
    )
    print(f"Gate classification: {result.classification}")
    print(f"DATASET_ID: {result.summary.dataset_id}")
    print(f"INPUT_ROWS: {result.summary.input_rows}")
    print(f"INPUT_COLUMNS: {result.summary.input_columns}")
    print(f"OUTPUT_COLUMNS: {result.summary.output_columns}")
    print(
        "PROMOTION_FIELDS_MODIFIED: "
        f"{result.summary.promotion_fields_modified}"
    )
    print(f"INPUT_SHA256: {result.summary.input_sha256}")
    print(f"PROPOSAL_SHA256: {result.summary.proposal_sha256}")
    print(f"OUTPUT_SHA256: {result.summary.output_sha256}")
    print("STOPPED_BEFORE_TRAINING_ACCEPTANCE_APPROVAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
