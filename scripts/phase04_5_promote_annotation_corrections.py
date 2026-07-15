from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn

from fleetvision.review.annotation_correction_promotion import (
    PromotionRequest,
    execute_atomic_promotion,
    prepare_promotion_preflight,
)
from fleetvision.review.annotation_correction_promotion_contract import (
    load_phase04_5n_config,
)


BLOCKED_CLASSIFICATION = "PHASE_04_5N_PROMOTION_BLOCKED"
PREFLIGHT_CLASSIFICATION = "PHASE_04_5N_PROMOTION_PREFLIGHT_VALIDATED"


def _emit_json(payload: dict[str, object], *, stream) -> None:
    print(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        file=stream,
    )


def _blocked_payload(
    *,
    message: str,
    error_type: str,
    execute: bool,
) -> dict[str, object]:
    return {
        "outcome": "BLOCKED",
        "classification": BLOCKED_CLASSIFICATION,
        "error_type": error_type,
        "error": message,
        "execute": execute,
        "canonical_coco_modified": False,
        "dataset_modified": False,
        "registry_modified": False,
        "fixed_splits_modified": False,
        "test_split_read": False,
        "model_inference_executed": False,
        "training_started": False,
        "retraining_status": "NOT_YET_APPROVED",
        "deployment_acceptance": "NOT_YET_APPROVED",
    }


class _StructuredArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        _emit_json(
            _blocked_payload(
                message=message,
                error_type="ArgumentError",
                execute="--execute" in sys.argv[1:],
            ),
            stream=sys.stderr,
        )
        raise SystemExit(1)


def _build_parser() -> argparse.ArgumentParser:
    parser = _StructuredArgumentParser(
        description="Phase 04.5N controlled annotation correction promotion",
    )
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--n1-workspace", type=Path, required=True)
    parser.add_argument("--expected-repository-head", required=True)
    parser.add_argument("--expected-canonical-sha256", required=True)
    parser.add_argument("--expected-staged-sha256", required=True)
    parser.add_argument("--authorization-phrase", default="")
    parser.add_argument("--timestamp", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    return parser


def _preflight_payload(preflight) -> dict[str, object]:
    return {
        "outcome": "PASS",
        "classification": PREFLIGHT_CLASSIFICATION,
        "execute": False,
        "repository_head": preflight.repository_state.head,
        "origin_main": preflight.repository_state.origin_main,
        "remote_main": preflight.repository_state.remote_main,
        "canonical_path": str(preflight.current_canonical_path),
        "canonical_before_sha256": preflight.current_canonical_sha256,
        "staged_coco_path": str(preflight.staged_coco_path),
        "staged_coco_sha256": preflight.staged_coco_sha256,
        "n1_workspace_root": str(preflight.verified_n1.root),
        "evidence_workspace_root": str(preflight.evidence_workspace_root),
        "changed_native_annotation_ids": list(
            preflight.verified_n1.changed_native_annotation_ids
        ),
        "timestamp": preflight.request.timestamp,
        "canonical_coco_modified": False,
        "test_split_read": False,
        "model_inference_executed": False,
        "dataset_materialization_executed": False,
        "registry_modified": False,
        "fixed_splits_modified": False,
        "training_started": False,
        "retraining_status": "NOT_YET_APPROVED",
        "deployment_acceptance": "NOT_YET_APPROVED",
    }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    execute = bool(args.execute)

    try:
        project_root = args.project_root.resolve()
        config = load_phase04_5n_config(args.config, project_root)
        request = PromotionRequest(
            project_root=project_root,
            n1_workspace_root=args.n1_workspace,
            expected_repository_head=args.expected_repository_head,
            expected_canonical_sha256=args.expected_canonical_sha256,
            expected_staged_sha256=args.expected_staged_sha256,
            authorization_phrase=args.authorization_phrase,
            execute=execute,
            timestamp=args.timestamp,
        )
        preflight = prepare_promotion_preflight(config, request)
        if not execute:
            payload = _preflight_payload(preflight)
        else:
            result = execute_atomic_promotion(config, preflight)
            payload = json.loads(result.result_path.read_text(encoding="utf-8"))
        _emit_json(payload, stream=sys.stdout)
        return 0
    except Exception as exc:
        _emit_json(
            _blocked_payload(
                message=str(exc),
                error_type=type(exc).__name__,
                execute=execute,
            ),
            stream=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
