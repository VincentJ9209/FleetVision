---
name: project-orchestrator
description: Plan and coordinate the iRent damage detection project phases, file structure, task breakdown, and completion criteria.
---

# Project Orchestrator Skill

Use this skill when the user asks to plan, restructure, sequence, or validate the overall iRent project.

## Project Context

The project builds an iRent vehicle exterior damage detection system using:

- Cursor as primary IDE
- VS Code as backup
- Google Colab for YOLOv8 GPU training
- PostgreSQL + Docker Compose for data infrastructure
- Streamlit for dashboard
- MLflow for experiment tracking
- YOLOv8 Detect as first model version

## Rules

- Keep outputs beginner-friendly and executable.
- Do not skip validation steps.
- Do not suggest training claim / non-claim classification in v1.
- Always separate what can be done now from what requires paired pickup/return data later.
- Prefer small, testable phases.

## Expected Output

When planning, include:

1. Objective
2. Inputs
3. Steps
4. Output files
5. Validation checklist
6. Recommended Cursor prompt
7. Next commit message

