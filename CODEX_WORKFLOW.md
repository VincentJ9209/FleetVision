# FleetVision Codex 工作流

> 本文件先提供主工作流與任務順序。正式 prompt 可在確認資料夾結構後再逐階段補齊。

## 使用方式

1. 用 Cursor 開啟 FleetVision repo。
2. 確認 `AGENTS.md` 存在。
3. 每次只請 Codex 完成一個階段中的一個明確任務。
4. Codex 完成後先看 diff，再執行測試。
5. 通過後 commit。

## 階段順序

```text
Phase 00: Project setup
Phase 01: Metadata builder
Phase 02: Image review tool
Phase 03: Annotation guidelines and label validation
Phase 04: YOLO dataset builder
Phase 05: Colab training notebook
Phase 06: Evaluation and error analysis
Phase 07: PostgreSQL + Docker Compose
Phase 08: Prediction pipeline
Phase 09: Damage comparison module
Phase 10: Streamlit dashboard
Phase 11: Demo package and report
```

## Codex 任務原則

每個任務都應包含：

- 目標
- 輸入
- 輸出
- 檔案位置
- 執行方式
- 驗收標準
- 不要做什麼

## 不要一次要求 Codex 做完整專案

錯誤示範：

```text
幫我完成整個 FleetVision 專案。
```

正確示範：

```text
請根據 AGENTS.md 建立 src/fleetvision/data/build_metadata.py，
用來掃描 dataset/01_raw/ 底下三個來源資料夾，
輸出 outputs/metadata/image_metadata.csv。
請加入 CLI arguments、錯誤處理、summary print，並說明如何執行。
```
