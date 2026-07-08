# Phase 00：專案初始化

## 目的

建立 FleetVision 專案基礎環境，確保程式碼、資料、模型、輸出與文件各自有清楚位置，並避免把大型圖片、模型權重、`.env` 等本機資料誤送到 GitHub。

本階段只做「專案骨架與環境確認」，不訓練模型、不整理資料、不標註圖片。

---

## 本階段輸入

- `PROJECT_CONTEXT_BRIEF.md`
- `FleetVision_starter.zip`
- 本機電腦上的原始圖片與 Excel 檔

---

## 本階段輸出

- GitHub repo：`FleetVision`
- 本機 repo 根目錄：`FleetVision/`
- 可執行的 Phase 00 驗收腳本：`scripts/phase00_init_project.py`
- Python package 設定：`pyproject.toml`
- 可通過的基礎測試：`pytest`

---

## Step 1：建立 GitHub repo

在 GitHub 建立新 repo：

```text
FleetVision
```

建議先建立空 repo，不要勾選自動產生 README，避免和 starter package 內的 README 衝突。

---

## Step 2：clone repo 到桌機

Windows PowerShell 範例：

```powershell
cd D:\Projects
git clone https://github.com/<your-account>/FleetVision.git
cd FleetVision
```

如果你想放在其他位置也可以，但後續所有指令都要在 repo 根目錄執行。

---

## Step 3：放入 starter package

將 `FleetVision_starter.zip` 解壓後，確認 repo 根目錄長這樣：

```text
FleetVision/
├── README.md
├── AGENTS.md
├── CODEX_WORKFLOW.md
├── PROJECT_CONTEXT_BRIEF.md
├── pyproject.toml
├── requirements.txt
├── docker-compose.yml
├── docs/
├── .agents/
├── dataset/
├── notebooks/
├── src/
├── configs/
├── sql/
├── scripts/
├── tests/
├── outputs/
├── models/
└── demo/
```

注意：不要變成 `FleetVision/FleetVision_starter/README.md`。如果多了一層 `FleetVision_starter/`，請把裡面的內容搬到 repo 根目錄。

---

## Step 4：建立 Python 虛擬環境

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

`pip install -e ".[dev]"` 會讓 `src/fleetvision/` 以 editable package 方式被 Python 找到，也會安裝測試工具 `pytest`。

---

## Step 5：建立本機 `.env`

```bash
python scripts/phase00_init_project.py --create-env
```

此指令會從 `.env.example` 複製一份 `.env`。`.env` 是本機設定檔，不應提交到 GitHub。

---

## Step 6：放置原始資料

原始圖片放在：

```text
dataset/01_raw/01_general_fleet/images/
dataset/01_raw/02_claimable_damage/images/
dataset/01_raw/03_minor_damage/images/
```

Excel / catalog 類資料放在：

```text
dataset/00_catalog/raw_excels/
```

原始圖片與原始 Excel 可以放在本機專案資料夾中供程式掃描，但不要提交到 GitHub。

---

## Step 7：執行 Phase 00 驗收

先自動補齊缺漏資料夾與 `.gitkeep`：

```bash
python scripts/phase00_init_project.py --fix
```

再執行驗收：

```bash
python scripts/phase00_init_project.py --validate
```

看到以下訊息代表 Phase 00 骨架通過：

```text
Phase 00 validation passed.
```

若顯示 warning，通常是尚未初始化 Git，或本機已有 raw image / model artifact。warning 不一定代表錯誤，但 commit 前必須確認大型資料沒有被加入 Git。

---

## Step 8：執行基礎測試

```bash
pytest
```

目前測試會先檢查 damage comparison 內的 IoU 基礎邏輯。Phase 00 通過後，後續每個階段都應逐步增加測試。

---

## Step 9：首次 commit

先確認 Git 狀態：

```bash
git status
```

確認沒有 raw images、模型權重、`.env` 後：

```bash
git add .
git commit -m "chore: initialize FleetVision project structure"
git push origin main
```

---

## 驗收標準

- repo 根目錄為 `FleetVision/`，不是舊的 `irent-damage-detection/`。
- `README.md`、`AGENTS.md`、`docs/`、`dataset/`、`src/`、`configs/`、`sql/`、`tests/` 存在。
- `dataset/01_raw/` 已有三個原始資料入口。
- `pyproject.toml` 存在，且 `pip install -e ".[dev]"` 可安裝本專案。
- `python scripts/phase00_init_project.py --validate` 可執行。
- `pytest` 可執行並通過。
- GitHub 上不應出現大型圖片、模型權重、`.env`。

---

## 本階段不要做

- 不要把 `minor_damage` / `claimable_damage` 當成 YOLO 第一版類別。
- 不要訓練模型。
- 不要直接修改 `dataset/01_raw/` 原始圖片。
- 不要把 raw image、YOLO dataset、模型權重、`.env` commit 到 GitHub。
- 不要沿用任何舊的 `irent-damage-detection` 架構或命名。

---

## 下一階段

Phase 01：建立 metadata builder。

下一階段會實作：

```text
src/fleetvision/data/build_metadata.py
```

目標是掃描三個 raw image 來源，輸出：

```text
outputs/metadata/image_metadata.csv
```
