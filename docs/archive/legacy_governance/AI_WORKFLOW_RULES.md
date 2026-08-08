# FleetVision AI Workflow Rules

This document applies to all ChatGPT and Codex work for the FleetVision project.

## 1. Purpose

Keep FleetVision execution focused, token-efficient, and aligned with the actual phase objective.

These rules are mandatory whenever ChatGPT or Codex plans, implements, reviews, or summarizes FleetVision work.

## 2. Tool Assignment Principle

Use the lowest-cost capable tool first.

| Tool | Primary responsibility |
|---|---|
| ChatGPT | Planning, phase-gate decisions, concise instructions, patch-only preparation, workflow diagnosis |
| Cursor / PowerShell | Local file operations, CSV inspection, command execution, tests, Git, small edits, deterministic scripts |
| Colab | GPU inference, model training, large image batches, compute-heavy ML work |
| Codex | Complex cross-file engineering, architecture changes, difficult debugging, parser or pipeline implementation that is unsafe to do manually |

Codex must not be used by default for work that Cursor, PowerShell, or a small patch can complete safely.

## 3. Token-Cost Gate

Before starting any task, ChatGPT or Codex must classify the expected token cost.

| Cost level | Examples | Required action |
|---|---|---|
| Low | Small config change, command suggestion, simple file copy, one-file edit | Proceed directly |
| Medium | Small patch, validator adjustment, focused script update | Prefer ChatGPT patch or Cursor execution |
| High | Large CSV generation, printing thousands of rows, broad file rewrites, exhaustive logs | Stop and delegate to Cursor / PowerShell unless there is a strong reason to stay in Codex |
| Very high | Emitting large generated datasets, full CSV contents, raw metadata dumps, full notebook outputs | Do not execute in Codex; provide local commands instead |

High-token work must be converted into local commands whenever possible.

Example:

```text
Do not ask Codex to generate or print image_review_labels.csv with 27,660 rows.
Use Cursor / PowerShell / Python locally to create or modify the file.
```

## 4. Codex Delegation Rule

When a task may consume many tokens, Codex must first decide one of the following:

```text
A. Execute in Codex because cross-file reasoning is necessary.
B. Delegate to Cursor / PowerShell and provide exact commands.
C. Ask the user whether to execute in Codex or delegate to Cursor.
```

Codex should choose B by default for:

- Large CSV operations
- Dataset row generation
- File copying or renaming
- Log inspection beyond a small excerpt
- Git operations
- Re-running existing scripts
- Applying simple config changes
- Notebook parameter changes

Codex should choose A only for:

- Multi-file implementation with tests
- Complex parser design
- Pipeline integration
- Non-trivial bug reproduction and fix
- Changes where local manual editing is error-prone

## 5. Output Style Rule

Responses must be concise, direct, and execution-oriented while preserving correctness.

Preferred response structure:

```text
1. Current status
2. Decision / diagnosis
3. Exact next command or action
4. Expected result
```

Avoid:

- Long background explanations unless the user asks
- Repeating already-known project context
- Printing large file contents
- Showing full generated CSVs
- Providing many alternative paths at once
- Ending with vague follow-ups

When commands are needed, provide copy-ready commands.

## 6. Phase Alignment Rule

Before each phase task starts, restate the phase objective in one or two lines and confirm scope.

Before implementation, check:

```text
What is the current phase objective?
What is explicitly out of scope?
What file(s) may be changed?
What data output proves success?
Should this be done in Cursor, ChatGPT patch, Colab, or Codex?
```

After completion, report status using three levels:

| Status | Meaning |
|---|---|
| Code Complete | Code, CLI, config, docs, and tests are ready |
| Data Complete | Real project data was processed and valid outputs exist |
| Phase Complete | Code Complete + Data Complete + acceptance checks passed |

Do not mark a phase as fully complete just because tests passed.

## 7. Phase Completion Checklist

At the end of each task or phase, verify:

```text
1. Did the actual output match the phase goal?
2. Were generated data files kept out of Git when appropriate?
3. Did pytest / relevant CLI checks pass?
4. Is git status clean or intentionally showing only local data files?
5. Is the next step data execution, manual review, Colab work, or new engineering?
```

If expected outputs are missing, state the missing data artifact clearly and stop before advancing to the next phase.

## 8. Patch-Only Rule

For ChatGPT-generated project updates:

- Prefer patch-only ZIPs.
- Include only files to add or replace.
- Do not include raw data, generated CSVs, images, model weights, or environment files.
- Do not overwrite unrelated project files.
- Tell the user exactly which files should appear in `git status --short`.

## 9. Large Data Handling Rule

Large data must stay local or in Drive/Colab, not in chat output.

For large CSV/image operations, provide commands such as:

```powershell
python scripts/example.py --input ... --output ...
Import-Csv path\file.csv | Group-Object column | Select-Object Name,Count
Get-Content -TotalCount 30 path\errors.csv
```

Only request small excerpts, summaries, counts, or error samples.

## 10. Mandatory Codex Prompt Addendum

Every future Codex prompt should include:

```text
Read and follow AI_WORKFLOW_RULES.md.
Before executing any high-token operation, decide whether it should be delegated to Cursor / PowerShell instead of being performed in Codex.
Keep responses concise and execution-oriented.
Before and after the task, verify alignment with the current phase objective.
Do not print large generated files, large CSV contents, or exhaustive logs.
```
