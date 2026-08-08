# TOOL_DECISION.md

# 工具選型最終決策

## 1. IDE 決策

| 工具 | 定位 | 使用方式 |
|---|---|---|
| Cursor | 主力 IDE | 產生程式、修改多檔案、解釋錯誤、重構、產生測試 |
| VS Code | 輔助 IDE | 穩定 debug、查看檔案、學習標準開發流程 |
| Antigravity | 暫不納入主線 | 未來專案穩定後再用 branch 測試 agent-first workflow |

## 2. 為什麼 Cursor 為主

本專案是多檔案、多階段的 ML 工程專案，包含資料處理、Docker、DB、YOLO、Dashboard、MLflow。Cursor 適合用 prompt 驅動產生與修改多個檔案，能提高實作效率。

## 3. 為什麼 VS Code 仍保留

VS Code 是穩定、成熟、教學資源豐富的標準開發工具。當 Cursor 產生結果太複雜或你想回到基本流程 debug 時，VS Code 是很好的備用環境。

## 4. 為什麼 Antigravity 暫不主用

Antigravity 偏 agent-first workflow，適合進階任務與多 agent 流程。但你目前最重要的是先把完整專案跑通，因此先選穩定且可控的 Cursor + VS Code。

---

# 工具使用階段

| 階段 | 主工具 | 輔助工具 |
|---|---|---|
| 專案骨架 | Cursor | GitHub |
| Python 腳本 | Cursor | VS Code |
| 圖片 metadata | Cursor | pandas / OpenCV |
| 圖片審查 | Cursor | Streamlit |
| 標註 | CVAT / Label Studio | Cursor 寫 guideline |
| YOLO 訓練 | Colab | Cursor 產生 notebook |
| 資料庫 | Docker Compose + PostgreSQL | DBeaver / pgAdmin |
| 推論 pipeline | Cursor | YOLOv8 |
| Dashboard | Cursor + Streamlit | Plotly |
| 實驗追蹤 | MLflow | Docker Compose |
| 報告 | Cursor | README / docs |

---

# Cursor 使用守則

每次請 Cursor 工作時，都要求：

1. 先閱讀 AGENTS.md。
2. 不要一次改太多檔案。
3. 修改後列出檔案清單。
4. 提供執行指令。
5. 提供驗收方式。
6. 解釋新手應理解的概念。
7. 若有錯誤，請逐步修正，不要重寫整個專案。

---

# VS Code 使用情境

建議在以下情況開 VS Code：

- 想單純查看專案結構。
- 想用 Python debugger。
- 想安裝 Docker / Python / Jupyter extensions。
- Cursor 修改太多，你想人工檢查 diff。
- 想練習不依賴 AI 的基礎開發流程。

