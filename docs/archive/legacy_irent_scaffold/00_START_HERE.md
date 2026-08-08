# 00_START_HERE.md

# iRent 車損辨識專案：新手起步順序

你已決定採用：

```text
Cursor 為主
VS Code 為輔
Colab 訓練
PostgreSQL + Docker Compose
YOLOv8 Detect
Streamlit Dashboard
MLflow 實驗追蹤
```

本文件告訴你「下一步要怎麼開始」。

---

## 第 1 步：建立 GitHub Repo

建議 repo 名稱：

```text
irent-damage-detection
```

先建立空 repo，然後 clone 到本機。

```bash
git clone <your-repo-url>
cd irent-damage-detection
```

---

## 第 2 步：把本文件包放進 repo

把以下檔案放到 repo 根目錄：

```text
README.md
AGENTS.md
CODEX_WORKFLOW.md
PHASE_GUIDE.md
00_START_HERE.md
.agents/skills/
```

---

## 第 3 步：用 Cursor 開啟 repo

在 Cursor：

```text
File → Open Folder → 選擇 irent-damage-detection
```

確認 Cursor 可以看到：

```text
AGENTS.md
CODEX_WORKFLOW.md
PHASE_GUIDE.md
```

---

## 第 4 步：先貼 Prompt 0

打開：

```text
CODEX_WORKFLOW.md
```

複製：

```text
Prompt 0：建立專案骨架
```

貼到 Cursor。

不要一次貼所有 prompt。

---

## 第 5 步：執行與驗收

Prompt 0 完成後，檢查：

- [ ] 是否建立 `data/`
- [ ] 是否建立 `src/`
- [ ] 是否建立 `requirements.txt`
- [ ] 是否建立 `.env.example`
- [ ] 是否建立 `docker-compose.yml`
- [ ] 是否更新 README 執行說明

---

## 第 6 步：第一次 commit

```bash
git add .
git commit -m "chore: initialize project structure"
```

---

## 第 7 步：照階段執行

接下來照這個順序：

| 順序 | 文件 | 任務 |
|---:|---|---|
| 1 | CODEX_WORKFLOW.md | Prompt 1：Docker Compose + PostgreSQL |
| 2 | CODEX_WORKFLOW.md | Prompt 2：PostgreSQL schema |
| 3 | CODEX_WORKFLOW.md | Prompt 3：圖片 metadata |
| 4 | CODEX_WORKFLOW.md | Prompt 4：圖片人工分類 app |
| 5 | CODEX_WORKFLOW.md | Prompt 5：標註規則文件 |
| 6 | CODEX_WORKFLOW.md | Prompt 6：YOLO dataset 驗證 |
| 7 | CODEX_WORKFLOW.md | Prompt 7：YOLO 訓練腳本 |
| 8 | CODEX_WORKFLOW.md | Prompt 14：Colab 訓練 notebook |
| 9 | CODEX_WORKFLOW.md | Prompt 8：批次推論 |
| 10 | CODEX_WORKFLOW.md | Prompt 9：寫入 PostgreSQL |
| 11 | CODEX_WORKFLOW.md | Prompt 10：前後比對模組 |
| 12 | CODEX_WORKFLOW.md | Prompt 11：Dashboard |
| 13 | CODEX_WORKFLOW.md | Prompt 12：MLflow |
| 14 | CODEX_WORKFLOW.md | Prompt 15：專題報告 |

---

## 最重要的執行原則

每次只做一件事：

```text
貼一個 Prompt
→ 讓 Cursor 產生程式
→ 自己執行
→ 看錯誤
→ 請 Cursor 修正
→ 檢查輸出
→ commit
→ 下一個 Prompt
```

這樣最穩，也最適合新手學習。

---

## 現階段不要做的事

- 不要一開始就做 YOLOv8 Segmentation。
- 不要訓練索賠 / 不索賠分類。
- 不要宣稱已完成新增車損模型。
- 不要把車內照片丟進外觀車損模型。
- 不要手動把原圖硬拉成 640x640。
- 不要一次讓 Cursor 修改大量不相關檔案。

---

## 你第一週的目標

第一週只要完成這些就很成功：

1. Repo 建好。
2. Cursor 能讀 AGENTS.md。
3. Docker Compose 可啟動 PostgreSQL。
4. `image_metadata.csv` 建立完成。
5. Streamlit image review app 可以跑。
6. 開始篩出外觀照片。

不要急著訓練模型。

