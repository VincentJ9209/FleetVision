# FleetVision Phase 05R Start Prompt

<!-- FLEETVISION-MANAGED:PHASE05R-START-PROMPT:BEGIN -->
Use this prompt only after the Phase 05R governance activation commit has been
pushed and remote verified.

## Required startup

1. Read `AGENTS.md` and `PROJECT_CONTEXT_BRIEF.md`.
2. Read `docs/00_project_management/START_HERE.md`.
3. Follow its required reading order.
4. Verify live Git facts:
   - repository root;
   - branch;
   - local HEAD;
   - `origin/main`;
   - GitHub remote `main`;
   - staged, modified and untracked paths.
5. Confirm protected assets:
   - `outputs/metadata/external_assets/`;
   - `dataset/01_raw/`;
   - Frozen Test.
6. Report current technical Phase, Gate, classification and one next action.

## Active scope

- Phase：`05R — Model Recovery & Dataset Quality Audit`
- First executable Gate：`PHASE_05R_01_DATASET_LABEL_QUALITY_AUDIT`
- Notebook：
  `/content/drive/MyDrive/AI_Class/00.Project/FleetVision/notebooks/FleetVision_Phase05_Model_Recovery.ipynb`
- Model type：YOLO Detect
- Classes：one class, `damage`
- Annotation：bbox
- Codex：`CONDITIONALLY_PAUSED`

## Execution rules

- Work on one controlled step only.
- For Notebook work, provide one complete Cell per response.
- State exact Cell ID and exact insertion／replacement position.
- State inputs, outputs, modifications, training status and Frozen Test access.
- Never provide partial in-Cell edits.
- Never access Frozen Test before its Gate.
- Never modify raw or protected assets.
- Do not automatically commit or push.
- Stop read-only when evidence conflicts.

## First action

Begin only with the current authorized Gate shown in
`PROJECT_STATUS.md`. Do not infer authorization from this prompt.
<!-- FLEETVISION-MANAGED:PHASE05R-START-PROMPT:END -->
