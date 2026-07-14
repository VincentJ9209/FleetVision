# FleetVision Start Here

<!-- FLEETVISION-MANAGED:STARTUP-PROTOCOL:BEGIN -->
## Purpose

This file is the mandatory entry point for every new FleetVision conversation or work session.

## Required reading order

1. `/AGENTS.md`
2. `/PROJECT_CONTEXT_BRIEF.md`
3. `docs/00_project_management/WORKFLOW_GOVERNANCE.md`
4. `docs/00_project_management/HUMAN_REVIEW_INTERFACE_STANDARD.md`
5. `docs/00_project_management/PROTECTED_ASSETS.md`
6. `docs/00_project_management/PROJECT_STATUS.md`
7. `docs/00_project_management/HANDOFF_CURRENT.md`
8. `docs/00_project_management/MASTER_PHASE_MAP.md`
9. The current phase log referenced by `PROJECT_STATUS.md`
10. `docs/00_project_management/DECISION_LOG.md` when a prior architectural or governance decision is relevant

## Conflict precedence

When sources disagree, use this order:

1. Live Git facts: branch, local HEAD, `origin/main`, GitHub remote HEAD, and worktree status
2. SHA256 values calculated from the actual artifact
3. `PROJECT_STATUS.md`
4. `HANDOFF_CURRENT.md`
5. Current phase log
6. `MASTER_PHASE_MAP.md`
7. Historical chat summaries

Do not infer that an operation is repeatable. Any action marked one-time, promotion, canonical mutation, registry mutation, or production mutation requires an explicit precondition Gate.

## Startup acknowledgement

Before any mutation, report:

- repository and branch
- local HEAD, `origin/main`, and remote HEAD
- current technical Phase
- latest Gate and classification
- worktree classification
- protected assets
- next authorized action
- any detected conflict
<!-- FLEETVISION-MANAGED:STARTUP-PROTOCOL:END -->

