from __future__ import annotations

import json
from pathlib import Path


def test_notebook_is_validation_only_and_contains_no_training_call() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "notebooks/FleetVision_04_5K_Validation_Error_Analysis_8_4_93.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = "\n".join(
        line
        for cell in notebook["cells"]
        for line in cell.get("source", [])
    )

    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) == 9
    assert "FleetVision Phase 04.5K" in source
    assert "VALIDATION_ERROR_ANALYSIS_AND_THRESHOLD_CANDIDATES_COMPLETED" in source
    assert "90A880513A42EF2DB1373902D98FF09D1756AB7A8A4EEA6A7AA231D4020B77BF" in source
    assert "model.train(" not in source
    assert "split='test'" not in source
    assert 'split="test"' not in source
    assert "dataset/05_yolo/images/valid/" in source
    assert "dataset/05_yolo/labels/valid/" in source
    assert "test_set_used_for_tuning" in source
    assert "False" in source


def test_all_notebook_code_cells_are_valid_python_syntax() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "notebooks/FleetVision_04_5K_Validation_Error_Analysis_8_4_93.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        compile(source, f"notebook_cell_{index}", "exec")
