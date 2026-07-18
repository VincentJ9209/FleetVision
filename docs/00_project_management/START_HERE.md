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
8. `docs/00_project_management/PHASE05R_SCOPE_CONTRACT.md`
9. `docs/01_phase_guides/phase_05r_model_recovery.md`
10. `docs/02_prompts/PHASE_05R_NOTEBOOK_RULES.md`
11. `docs/00_project_management/MASTER_PHASE_MAP.md`
12. The current phase log referenced by `PROJECT_STATUS.md`
13. `docs/00_project_management/DECISION_LOG.md` when a prior architectural or governance decision is relevant

## Conflict precedence

When sources disagree, use this order:

1. Live Git facts: branch, local HEAD, `origin/main`, GitHub remote HEAD, and worktree status
2. SHA256 values calculated from the actual artifact
3. `PROJECT_STATUS.md`
4. `HANDOFF_CURRENT.md`
5. Active scope contract
6. Current phase log
7. `MASTER_PHASE_MAP.md`
8. Historical chat summaries

A Phase 05R governance block is effective only when the commit containing it
has been pushed and remote verified. Before that condition, the prior
repository-backed state remains authoritative.

Do not infer that an operation is repeatable. Any action marked one-time,
promotion, canonical mutation, registry mutation, Frozen Test access or
production mutation requires an explicit precondition Gate.

## Startup acknowledgement

Before any mutation, report:

- repository and branch;
- local HEAD, `origin/main`, and remote HEAD;
- current technical Phase;
- latest Gate and classification;
- worktree classification;
- protected assets;
- active scope contract;
- Frozen Test access status;
- next authorized action;
- any detected conflict;
- commit／push authorization.

For Notebook work, also report the fixed Cell ID, exact placement, read／write
scope, training status and Frozen Test status.
<!-- FLEETVISION-MANAGED:STARTUP-PROTOCOL:END -->

