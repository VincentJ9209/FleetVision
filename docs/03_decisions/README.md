# FleetVision Active Decision Index

此索引只列出目前仍會約束工作的決策。完整決策沿革請見[封存決策紀錄](../99_archive/legacy_project_management/DECISION_LOG.md)。

- **YOLOv8 Detect 與單一 `damage` 類別**：第一版模型固定為 YOLOv8 Detect，`minor_damage` 與 `claimable_damage` 不得成為 YOLO 類別。
- **外部資料集治理先於訓練使用**：外部資料須完成來源、授權、類別映射、bbox QA 與接受證據，才可進入訓練決策。
- **內部 holdout 分離**：凍結的內部 holdout 必須與外部資料及訓練資料維持分離，不得混入。
- **群組安全與資料洩漏控制**：依車輛、租次、連拍及近重複關係切分，避免 train／validation／test 洩漏。
- **GitHub 為可追溯的真實來源**：專案狀態、決策與治理紀錄以已驗證的 Git 歷史為準。
- **測試評估後僅可做 validation 閾值與錯誤分析**：Frozen Test 為單次評估，不得用於 threshold tuning 或反覆模型選擇。
- **人工審核介面預設為 Streamlit + SQLite**：以本機繁體中文 Streamlit 與 SQLite 維護 live state；Excel 僅供完成匯出、交換與封存。
- **產品宣稱邊界**：不得宣稱可判定責任、理賠資格或最終商業裁決；輸出僅支援人工複核。
