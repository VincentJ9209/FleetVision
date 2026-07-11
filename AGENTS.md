# FleetVision Agent Instructions

This file applies to the repository root and all descendant directories.

## 1. Source of Truth

Before planning, inspecting, editing, testing, committing, or pushing, read the relevant current project governance files:

- `PROJECT_CONTEXT_BRIEF.md`
- `docs/00_project_management/MASTER_PHASE_MAP.md`
- `docs/00_project_management/PROJECT_STATUS.md`
- `docs/00_project_management/WORKFLOW_GOVERNANCE.md`
- `docs/00_project_management/DECISION_LOG.md`

Use `PROJECT_STATUS.md` to determine the current Phase and active gate. Do not rely on chat history as the primary project record.

If repository files conflict with a task prompt, stop and report the conflict before editing.

## 2. Start-of-Task Gate

Before taking any repository action, confirm:

1. Current Phase and active gate.
2. Required prerequisites are complete.
3. Immutable architecture decisions.
4. Allowed files and prohibited files.
5. Whether formal outputs or human-entered data are at risk.
6. Expected Git state before the task.
7. Required tests and completion evidence.
8. Whether commit or push is explicitly authorized.

Do not begin implementation when these items are unresolved.

## 3. Skill Gate

Before repository inspection, planning, editing, debugging, testing, review, commit, or push:

1. Inspect the skills available in the current agent environment.
2. Explicitly invoke every applicable installed skill.
3. Never claim a skill was used unless its instructions were actually loaded and followed.
4. If an applicable skill is unavailable, report:

   `SKILL_NOT_AVAILABLE: <skill-name>`

5. When a skill is unavailable, follow an equivalent disciplined workflow manually.

Evaluate at minimum whether the following workflows apply:

- `using-superpowers`: task startup and skill selection
- `brainstorming`: new behavior, new features, or design changes
- `systematic-debugging`: bugs, failures, unexpected behavior, or regressions
- `test-driven-development`: features, bug fixes, or behavior changes
- `writing-plans`: multi-step or multi-file implementation
- `verification-before-completion`: before claiming success, commit, or push
- `requesting-code-review`: major changes or pre-merge review
- `using-git-worktrees`: work requiring isolation from the active worktree

The final report must contain:

- `Skills used`
- How each skill was applied
- `Skills unavailable`
- Any applicable skill intentionally not used and the reason

## 4. Token and Context Efficiency

Use the smallest amount of context that preserves correctness.

- Do not repeat governance documents inside prompts.
- Read only files relevant to the current task.
- Prefer targeted repository searches over broad full-repository dumps.
- Do not reopen or reanalyze files already understood unless the task changed.
- Run targeted tests during development.
- Run regression or full tests only at the required completion gate.
- Do not repeatedly run the full suite without a new reason.
- Keep each task within one coherent Git checkpoint.
- Do not combine unrelated Phase work in one context or commit.
- If task scope changes materially, recommend a new context.
- If remaining context is insufficient for reliable completion, stop at a safe checkpoint and report it.

## 5. Immutable FleetVision Architecture

Unless a newer approved Decision Log entry explicitly changes these rules:

- Project root is `G:\Project\FleetVision`.
- The deprecated `irent-damage-detection` project must not be restored or reused.
- First damage model is YOLOv8 Detect.
- The first YOLO class is only `damage`.
- `minor_damage` and `claimable_damage` are not YOLO classes.
- Phase 03.5 inference is frozen and must not be rerun.
- CLIP is limited to approved photo-type suggestion behavior.
- Filename angle rules must never infer angle from `_1`, `_2`, `_3`, or `_4`.
- Phase 03.5 must not infer damage or severity.
- Do not assign insurance liability.
- Do not create YOLO labels, `dataset/05_yolo`, data splits, or model training outputs before the applicable Phase gate is approved.

## 6. Data and Human-Review Safety

The following are protected unless the active task explicitly authorizes them:

- `dataset/01_raw/`
- completed or active human-review Workbooks
- reviewer assignment manifests
- manual-review ZIP packages
- frozen backups and SHA256 manifests
- canonical CSV outputs
- external dataset source archives
- internal holdout definitions

Rules:

- Never modify files under `dataset/01_raw/`.
- Never overwrite human-entered review data.
- Never rebuild a canonical Workbook over an active or completed reviewer file.
- Never save a protected Workbook merely to inspect it.
- Use read-only access for inspection whenever possible.
- Use `pytest tmp_path`, Windows TEMP, or another isolated temporary directory for tests.
- A failed operation must not leave a partial canonical output.
- Preserve source files and create verified backups before promotion or replacement.
- Use SHA256 comparisons for high-risk file promotion.
- External data must remain separated from the frozen FleetVision internal holdout.
- Never mix external data into internal evaluation data.

## 7. Implementation Discipline

Make the smallest change that fully satisfies the approved goal.

- Follow existing repository patterns.
- Do not perform unrelated refactoring.
- Do not silently alter schemas, column names, label meanings, thresholds, or file paths.
- Do not hard-code values already controlled by configuration or workbook option sources.
- Preserve deterministic ordering.
- Preserve failure-no-overwrite behavior.
- Keep modules focused on one responsibility.
- Update tests for every behavior change.
- Update governance documents when a Phase status, risk, or architectural decision changes.
- Do not create duplicate tools when an existing builder, validator, exporter, or merger can be extended safely.

## 8. Repository Engineering and Environment Rules

### Code and Repository Conventions

- Production Python code belongs under `src/fleetvision/`.
- Notebooks are limited to exploration and approved Colab workflows; do not place primary business logic in notebooks.
- Functions, classes, filenames, configuration keys, and data column names use English.
- Documentation, guides, comments, and user-facing explanations may use Traditional Chinese.
- Do not hard-code user-specific absolute paths in application code.
- `G:\Project\FleetVision` is the current operator workspace, not an application-code constant.
- Manage filesystem paths through configuration, CLI arguments, or repository-relative paths.
- Primary scripts must be runnable from the repository root.
- Data-processing scripts must produce a clear execution summary.
- Important public functions should include type hints and concise docstrings.
- Critical logic, including schema validation, matching rules, IoU, label validation, promotion, and no-overwrite behavior, requires automated tests.
- Use only dataset directories approved by the current Phase Map and Project Status.
- Do not create future-phase dataset folders or artifacts before their gate is approved.

### Secrets and Large Artifacts

- Never commit `.env`, API tokens, credentials, private keys, or service-account files.
- A sanitized `.env.example` may be tracked.
- Do not commit large image collections, model weights, training runs, database dumps, local backups, or generated review packages.
- Database dumps belong in approved external backup storage, not Git.
- If PostgreSQL is introduced, keep the tracked schema in `sql/schema.sql`.
- Docker Compose is limited to approved local services and must not contain embedded secrets.

### Colab and Training

- Colab is reserved for approved GPU inference or training work.
- Do not use Colab to bypass the current Phase gate.
- Phase 03.5 inference remains frozen and must not be rerun.
- When a future training gate is approved, mount data from approved storage and return model outputs to approved external storage.
- Notebook templates may be tracked, but large training outputs must not be committed.

### Product Claim Boundary

- Do not claim that FleetVision can reliably determine true new damage until sufficient paired before-and-after rental data and validation exist.
- Do not equate visible damage detection with insurance claimability, liability, or final business adjudication.
## 9. Verification Gate

Before claiming a task is complete:

1. Run the required targeted tests.
2. Run relevant regression tests.
3. Run the full suite when required by the task or governance gate.
4. Run `git diff --check`.
5. Run `git status --short`.
6. Confirm only authorized files changed.
7. Confirm protected outputs were not modified.
8. Confirm no partial output remains from failed tests.
9. Inspect the final diff for accidental scope expansion.
10. Report exact test counts and failures or skips.

Do not report success based only on expected behavior. Use fresh command output.

## 10. Git Rules

- The main working branch is `main` unless the task explicitly states otherwise.
- Do not commit or push unless the current task explicitly authorizes it.
- Do not stage unrelated existing changes.
- Stage files by explicit path, not broad commands such as `git add .`.
- Keep code, tests, configuration, and governance documents in intentional checkpoints.
- Do not commit generated Excel files, ZIP packages, images, model artifacts, caches, temporary files, or local backups.
- CSV outputs are not committed unless explicitly designated as a tracked governance artifact.
- Preserve existing uncommitted work that is outside the authorized task.
- Before push, verify the commit subject, staged file list, tests, and remote branch.
- After push, verify `git status --short` and `git log -1 --oneline`.

## 11. Required Final Report

Every repository task report must include:

1. Current Phase and completed gate.
2. Skills used and how they were applied.
3. Skills unavailable.
4. Root cause or implementation approach.
5. Files changed.
6. Tests executed and exact results.
7. `git diff --check` result.
8. Final `git status --short`.
9. Commit hash and subject, when applicable.
10. Push result, when applicable.
11. Whether protected or formal outputs were touched.
12. Any deviation, remaining risk, blocker, or next gate.
13. Estimated token load: low, medium, or high.

Do not paste full diffs or full logs unless explicitly requested.

## 12. Stop Conditions

Stop without modifying files and report the issue when:

- the current Phase or prerequisite is unclear;
- governance documents contradict each other;
- the requested change violates an immutable decision;
- protected data would be overwritten;
- required source files are missing;
- the worktree contains unexpected changes;
- an applicable license is unknown or incompatible;
- a test failure cannot be explained;
- completing the task would require unauthorized scope expansion;
- commit or push authorization is absent.
