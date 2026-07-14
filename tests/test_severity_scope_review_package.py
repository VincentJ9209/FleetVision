from __future__ import annotations

import pytest

from fleetvision.review.severity_scope_review_package import (
    ScopePackageVerificationError,
    discover_latest_f1_workspace,
    load_scope_review_app_config,
    load_verified_scope_package,
)
from scope_review_app_fixtures import create_scope_package


def test_loads_and_verifies_complete_f1_package(tmp_path) -> None:
    fixture = create_scope_package(tmp_path, case_count=130)
    config = load_scope_review_app_config(
        fixture.config_path,
        fixture.project_root,
    )
    root = discover_latest_f1_workspace(config)
    package = load_verified_scope_package(config, root)
    assert len(package.cases) == 130
    assert package.app_workspace_root.name == "scope_review_app"
    assert package.cases[0].original_path.is_file()
    assert package.cases[-1].overlay_path.is_file()


def test_rejects_modified_f1_template(tmp_path) -> None:
    fixture = create_scope_package(tmp_path, case_count=130)
    config = load_scope_review_app_config(
        fixture.config_path,
        fixture.project_root,
    )
    fixture.package.template_workbook_path.write_bytes(
        fixture.package.template_workbook_path.read_bytes() + b"tamper"
    )
    with pytest.raises(ScopePackageVerificationError, match="大小改變|SHA256"):
        load_verified_scope_package(config, fixture.root)
