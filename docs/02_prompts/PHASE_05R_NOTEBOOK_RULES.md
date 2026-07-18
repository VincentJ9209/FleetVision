# FleetVision Phase 05R Notebook Rules

<!-- FLEETVISION-MANAGED:PHASE05R-NOTEBOOK-RULES:BEGIN -->
## Notebook identity

Drive execution Notebook：

`/content/drive/MyDrive/AI_Class/00.Project/FleetVision/notebooks/FleetVision_Phase05_Model_Recovery.ipynb`

The Drive copy may contain execution outputs. A future GitHub template, if
separately authorized, must be a clean JSON-valid Notebook with
`execution_count = null` and empty outputs.

## One-Cell response contract

Every Notebook response must provide exactly one complete code Cell and state:

1. Cell ID.
2. Operation type.
3. Exact insertion or replacement position.
4. Purpose.
5. Preconditions.
6. Files and directories read.
7. Files and directories created or modified.
8. Whether training occurs.
9. Whether Frozen Test is accessed.
10. Acceptance criteria.
11. Expected user-returned output.

Allowed placement wording：

- `在 Cell R0-01 正下方新增 Cell R0-02`
- `完整覆蓋 Cell R0-02`
- for the first Cell only:
  `完整覆蓋 Notebook 目前唯一的空白 code Cell，命名為 R0-01`

Prohibited wording：

- previous／next Cell without a fixed ID;
- partial replacement;
- edit only selected lines;
- execute multiple unverified Cells.

## Required Cell header

Each code Cell begins with a concise header equivalent to:

```python
# Cell ID: R0-01
# 操作類型: READ_ONLY_AUDIT
# 主要目的: ...
# 插入位置: ...
# 前提: ...
# 讀取內容: ...
# 修改內容: NONE
# 模型訓練: NO
# Frozen Test: NO
# 驗收標準: ...
```

## Cell ID map

- `R0-*`：environment, paths and governance contract.
- `R1-*`：dataset and label audit.
- `R2-*`：baseline validation FP／FN analysis.
- `R3-*`：reviewed corrections and Dataset v2.
- `R4-*`：Candidate C03–C05 training.
- `R5-*`：validation quality Gate.
- `R6-*`：single-model Frozen Test.
- `R7-*`：CLI／API reintegration.

## Safety boundaries

- No Cell before `PHASE_05R_00D` remote verification.
- `dataset/01_raw/` is immutable.
- Protected external assets are never rewritten.
- R1–R5 must not mount, enumerate, preview or read Frozen Test content.
- Each training Cell runs one candidate only.
- Every governed artifact records path, count, configuration and SHA256.
- Errors fail closed; never silently skip missing inputs.
- Do not use narrative success in place of machine-readable evidence.
<!-- FLEETVISION-MANAGED:PHASE05R-NOTEBOOK-RULES:END -->
