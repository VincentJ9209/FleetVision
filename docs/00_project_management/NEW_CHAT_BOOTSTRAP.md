# FleetVision New Chat Bootstrap

<!-- FLEETVISION-MANAGED:BOOTSTRAP-PROMPT:BEGIN -->
## Standard new-conversation prompt

```text
繼續 FleetVision／Project_FleetVision 車損辨識專案。

請先透過 GitHub main branch 讀取：
1. AGENTS.md
2. PROJECT_CONTEXT_BRIEF.md
3. docs/00_project_management/START_HERE.md

再依 START_HERE.md 的指定順序讀取目前專案狀態。

請先核對並回報：
- repository / branch
- local or repository HEAD
- origin/main / remote HEAD（可取得時）
- current technical phase
- latest gate outcome and classification
- worktree classification
- protected assets
- next authorized action
- detected conflicts

目前 repository-backed 狀態應指向：
- current technical phase: Phase 05S-A1 — Team Pairing Audit Design Review
- current gate: PHASE_05S_A1_DESIGN_REVIEW_BEFORE_IMPLEMENTATION_PLAN
- design path: docs/01_phase_guides/phase_05s_a1_team_pairing_audit_design.md
- only next authorized action: review the tracked Phase 05S-A1 design, then write a separate implementation plan

禁止在完成狀態核對與 design review 前執行：
- code implementation
- image scan
- training or fine-tuning
- Frozen Test search/listing/reading/hashing
- Dashboard or first-stage App work
- generated output commit

未完成狀態核對前，不得提出或執行修改。
Codex 與 Cursor Agent 維持停用，除非 Vincent 明確重新授權。
```
<!-- FLEETVISION-MANAGED:BOOTSTRAP-PROMPT:END -->

