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

def test_notebook_normalizes_manifest_relative_paths_to_tar_namespace() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "notebooks/FleetVision_04_5K_Validation_Error_Analysis_8_4_93.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = "\n".join(
        line
        for cell in notebook["cells"]
        for line in cell.get("source", [])
    )

    assert 'prefix = "dataset/05_yolo/"' in source
    assert "return relative if relative.startswith(prefix) else prefix + relative" in source
    assert "manifest_valid = {}" in source
    assert "if extracted_set != manifest_set:" in source
    assert "if len(extracted_relpaths) != len(extracted_set):" in source
    assert "if set(extracted_relpaths) != set(manifest_valid):" not in source

def test_notebook_maps_prediction_results_by_input_order_not_result_path() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "notebooks/FleetVision_04_5K_Validation_Error_Analysis_8_4_93.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = "\n".join(
        line
        for cell in notebook["cells"]
        for line in cell.get("source", [])
    )

    assert "for result_index, result in enumerate(results):" in source
    assert "source_path = image_paths[result_index]" in source
    assert "reported_image_id = Path(result.path).name" in source
    assert "expected_synthetic_id = f'image{result_index}.jpg'" in source
    assert "image_id = source_path.name" in source
    assert "if len(processed_image_ids) != len(image_paths):" in source
    assert not any(
        line.strip() == "image_id = Path(result.path).name"
        for line in source.splitlines()
    )

def test_notebook_is_canonical_template_without_runtime_outputs_or_recovery_cells() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "notebooks/FleetVision_04_5K_Validation_Error_Analysis_8_4_93.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))

    code_cells = [
        (index, cell)
        for index, cell in enumerate(notebook["cells"])
        if cell.get("cell_type") == "code"
    ]
    executed_code_cells = [
        index
        for index, cell in code_cells
        if cell.get("execution_count") is not None
    ]
    output_code_cells = [
        index
        for index, cell in code_cells
        if cell.get("outputs")
    ]
    temporary_recovery_cells = [
        index
        for index, cell in code_cells
        if "".join(cell.get("source", [])).lstrip().startswith(
            ("# Cell 4-DIAG", "# Cell 4-R1")
        )
    ]

    assert not executed_code_cells, (
        f"Canonical Notebook contains execution counts: {executed_code_cells}"
    )
    assert not output_code_cells, (
        f"Canonical Notebook contains saved outputs: {output_code_cells}"
    )
    assert not temporary_recovery_cells, (
        f"Canonical Notebook contains temporary recovery cells: "
        f"{temporary_recovery_cells}"
    )
