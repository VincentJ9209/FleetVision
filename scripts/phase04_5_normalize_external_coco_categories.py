"""CLI for FleetVision Phase 04.5F COCO category canonicalization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fleetvision.data.normalize_external_coco_categories import (
    CanonicalizationConfigError,
    CanonicalizationInputError,
    CanonicalizationOutputError,
    build_canonical_coco,
    load_canonicalization_config,
)

DEFAULT_CONFIG = Path("configs/data/external_coco_category_normalization_config.yaml")


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "PROJECT_CONTEXT_BRIEF.md").is_file() and (candidate / "src/fleetvision").is_dir():
            return candidate
    return current


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate or create canonical single-class COCO annotations from "
            "the immutable Phase 04.5 cleaned COCO source."
        )
    )
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def _print(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = find_project_root(args.project_root)
    config_path = args.config if args.config.is_absolute() else root / args.config
    if args.overwrite and not args.execute:
        _print({"exit_code": 2, "error": "--overwrite requires --execute"})
        return 2
    try:
        config = load_canonicalization_config(config_path, project_root=root)
        result = build_canonical_coco(
            config,
            execute=args.execute,
            overwrite=args.overwrite,
        )
    except (CanonicalizationConfigError, CanonicalizationInputError) as exc:
        _print(
            {
                "exit_code": 2,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "gate_classification": "COCO_CATEGORY_CANONICALIZATION_BLOCKED",
            }
        )
        return 2
    except CanonicalizationOutputError as exc:
        _print(
            {
                "exit_code": 3,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "gate_classification": "COCO_CATEGORY_CANONICALIZATION_BLOCKED",
            }
        )
        return 3

    _print(
        {
            "dataset_id": result.dataset_id,
            "executed": result.executed,
            "exit_code": 0,
            "gate_classification": result.gate_classification,
            "output_root": str(result.output_root),
            "total_images": result.total_images,
            "total_annotations": result.total_annotations,
            "canonical_class_count": result.canonical_class_count,
            "training_acceptance": "NOT_YET_APPROVED",
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
