"""CLI for FleetVision Phase 04.5D-1 Registry v2 schema migration."""

from __future__ import annotations

import argparse
from pathlib import Path

from fleetvision.data.migrate_external_dataset_registry_v2 import (
    BLOCKED_CLASSIFICATION,
    RegistryMigrationError,
    migrate_external_dataset_registry_v2,
)

DEFAULT_CONFIG = Path("configs/data/external_dataset_registry_v2_migration_config.yaml")


def resolve_project_root(value: Path | None) -> Path:
    """Resolve an explicit root or discover the FleetVision repository root."""
    if value is not None:
        return value.resolve()
    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "PROJECT_CONTEXT_BRIEF.md").is_file() and (candidate / "src").is_dir():
            return candidate
    return current


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely validate or migrate the FleetVision external dataset Registry to v2."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--project-root", type=Path, default=None)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Validate and propose without writing (default).")
    mode.add_argument("--execute", action="store_true", help="Atomically replace the Registry after validation.")
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
        result = migrate_external_dataset_registry_v2(
            args.config,
            project_root,
            execute=args.execute,
        )
    except RegistryMigrationError as exc:
        print("=== FleetVision Phase 04.5D-1 External Dataset Registry v2 Migration ===")
        print(f"Mode: {mode}")
        print("REGISTRY_UPDATED: NO")
        _print_safety_flags()
        print(f"Gate classification: {BLOCKED_CLASSIFICATION}")
        print(f"ERROR: {exc}")
        print("STOPPED_BEFORE_EXTERNAL_DATASET_REGISTRY_PROMOTION_GATE")
        return 2
    except Exception as exc:  # noqa: BLE001 - concise CLI boundary.
        print("=== FleetVision Phase 04.5D-1 External Dataset Registry v2 Migration ===")
        print(f"Mode: {mode}")
        print("REGISTRY_UPDATED: NO")
        _print_safety_flags()
        print(f"Gate classification: {BLOCKED_CLASSIFICATION}")
        print(f"UNEXPECTED_ERROR: {exc}")
        print("STOPPED_BEFORE_EXTERNAL_DATASET_REGISTRY_PROMOTION_GATE")
        return 3

    summary = result.summary
    print("=== FleetVision Phase 04.5D-1 External Dataset Registry v2 Migration ===")
    print(f"Mode: {summary.mode}")
    print(f"Dataset ID: {summary.dataset_id}")
    print(f"Input registry rows: {summary.input_rows}")
    print(f"Input registry columns: {summary.input_columns}")
    print(f"Output registry columns: {summary.output_columns}")
    print(f"New columns added: {summary.new_columns_added}")
    print(f"Existing columns modified: {summary.existing_columns_modified}")
    print(f"Target rows matched: {summary.target_rows_matched}")
    print(f"Registry schema version: {summary.registry_schema_version}")
    print(f"Input SHA256: {summary.input_sha256}")
    print(f"Output SHA256: {summary.output_sha256}")
    print(f"REGISTRY_UPDATED: {'YES' if summary.registry_updated else 'NO'}")
    print(f"TRAINING_ACCEPTANCE: {summary.training_acceptance}")
    _print_safety_flags()
    print(f"Gate classification: {result.classification}")
    print("STOPPED_BEFORE_EXTERNAL_DATASET_REGISTRY_PROMOTION_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
