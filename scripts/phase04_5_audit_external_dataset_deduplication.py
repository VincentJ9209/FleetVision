"""CLI for FleetVision Phase 04.5F image deduplication audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fleetvision.data.audit_external_dataset_deduplication import (
    CandidateOverflowError,
    ConfigInputError,
    DeduplicationAuditError,
    HashingIntegrityError,
    OutputPromotionError,
    build_deduplication_audit,
    load_deduplication_config,
)

DEFAULT_CONFIG = Path("configs/data/external_dataset_deduplication_config.yaml")


def find_project_root(start: Path | None = None) -> Path:
    """Find the FleetVision repository root from a starting path."""

    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "PROJECT_CONTEXT_BRIEF.md").is_file() and (candidate / "src/fleetvision").is_dir():
            return candidate
    return current


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate or execute the Phase 04.5F exact and perceptual image "
            "deduplication audit without modifying source images or the Registry."
        )
    )
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--execute", action="store_true", help="Write staged, atomically promoted audit outputs.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output only after a successful staged build.")
    return parser


def _print_final(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = find_project_root(args.project_root)
    config_path = args.config if args.config.is_absolute() else project_root / args.config
    if args.overwrite and not args.execute:
        _print_final(
            {
                "error": "--overwrite requires --execute",
                "exit_code": 2,
                "gate_classification": "DEDUPLICATION_AUDIT_BLOCKED",
            }
        )
        return 2

    error: Exception | None = None
    try:
        config = load_deduplication_config(config_path, project_root=project_root)
        result = build_deduplication_audit(
            config,
            execute=args.execute,
            overwrite=args.overwrite,
        )
    except ConfigInputError as exc:
        exit_code = 2
        error = exc
    except HashingIntegrityError as exc:
        exit_code = 3
        error = exc
    except CandidateOverflowError as exc:
        exit_code = 4
        error = exc
    except OutputPromotionError as exc:
        exit_code = 5
        error = exc
    except DeduplicationAuditError as exc:
        exit_code = 2
        error = exc
    except Exception as exc:  # noqa: BLE001 - final CLI safety boundary.
        exit_code = 5
        error = exc
    else:
        _print_final(
            {
                "dataset_id": result.dataset_id,
                "executed": result.executed,
                "exit_code": 0,
                "external_image_count": result.external_image_count,
                "gate_classification": result.gate_classification,
                "hash_error_count": result.hash_error_count,
                "hash_success_count": result.hash_success_count,
                "internal_image_count": result.internal_image_count,
                "output_root": str(result.output_root),
                "registry_modified": False,
                "training_acceptance": "NOT_YET_APPROVED",
            }
        )
        return 0

    _print_final(
        {
            "error": str(error),
            "error_type": type(error).__name__,
            "exit_code": exit_code,
            "gate_classification": "DEDUPLICATION_AUDIT_BLOCKED",
            "registry_modified": False,
            "training_acceptance": "NOT_YET_APPROVED",
        }
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
