from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_ROOT = ROOT / "docs/00_project_management/project_dashboard"
INDEX = DASHBOARD_ROOT / "index.html"
CSS = DASHBOARD_ROOT / "assets/dashboard.css"
JS = DASHBOARD_ROOT / "assets/dashboard.js"
README = DASHBOARD_ROOT / "README.md"
SERVER = ROOT / "scripts/serve_project_dashboard.ps1"


def test_required_static_files_exist() -> None:
    required = [
        INDEX,
        CSS,
        JS,
        DASHBOARD_ROOT / "assets/icons.svg",
        DASHBOARD_ROOT / "data/project_status.json",
        DASHBOARD_ROOT / "data/project_history.json",
        DASHBOARD_ROOT / "schemas/project_status.schema.json",
        DASHBOARD_ROOT / "schemas/project_history.schema.json",
        README,
        SERVER,
    ]
    assert all(path.is_file() for path in required)


def test_html_has_semantic_landmarks_and_local_assets_only() -> None:
    html = INDEX.read_text(encoding="utf-8")
    for tag in ("<header", "<nav", "<main", "<aside", "<section", "<footer"):
        assert tag in html
    assert 'Content-Security-Policy' in html
    assert 'assets/dashboard.css' in html
    assert 'assets/dashboard.js' in html
    assert 'type="module"' in html
    assert "project_status.json" not in html
    assert "project_history.json" not in html
    assert not re.search(r"https?://", html, flags=re.IGNORECASE)


def test_assets_have_no_remote_runtime_or_unsafe_code() -> None:
    text = "\n".join(
        [
            INDEX.read_text(encoding="utf-8"),
            CSS.read_text(encoding="utf-8"),
            JS.read_text(encoding="utf-8"),
        ]
    )
    assert not re.search(r"https?://", text, flags=re.IGNORECASE)
    assert "eval(" not in text
    assert ".innerHTML" not in text
    assert "insertAdjacentHTML" not in text
    assert "document.write" not in text


def test_accessibility_and_reduced_motion_are_present() -> None:
    html = INDEX.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    assert "aria-live" in html
    assert "aria-label" in html
    assert ":focus-visible" in css
    assert "prefers-reduced-motion" in css


def test_server_wrapper_is_loopback_only_and_read_only() -> None:
    script = SERVER.read_text(encoding="utf-8")
    assert "Set-StrictMode -Version Latest" in script
    assert "--bind" in script
    assert "127.0.0.1" in script
    assert "http.server" in script
    forbidden = [
        "git add",
        "git commit",
        "git push",
        "Remove-Item",
        "Move-Item",
        "Set-Content",
        "Out-File",
    ]
    for token in forbidden:
        assert token not in script


def test_readme_warns_against_file_protocol() -> None:
    readme = README.read_text(encoding="utf-8")
    assert "file://" in readme
    assert "127.0.0.1" in readme
    assert "serve_project_dashboard.ps1" in readme
