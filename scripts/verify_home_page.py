#!/usr/bin/env python3
"""
Verification script for the UVM 1.2 Home Page (home.html, js/home.js),
SPA default/hash routing, Personal Workspace (bookmarks & recent history),
and link integrity for all referenced docs and examples.
"""

import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def test_home_files_exist() -> None:
    for rel in ("home.html", "js/home.js", "index.html", "js/app.js", "css/style.css"):
        path = BASE_DIR / rel
        assert path.is_file(), f"Missing required file: {rel}"


def test_home_links_resolve() -> None:
    home_html = (BASE_DIR / "home.html").read_text(encoding="utf-8")

    doc_targets = re.findall(r'data-doc="([^"]+)"', home_html)
    assert len(doc_targets) >= 10, f"Expected >= 10 data-doc targets in home.html, found {len(doc_targets)}"
    for target in doc_targets:
        clean = target.split("#")[0]
        assert (BASE_DIR / clean).is_file(), f"Broken data-doc link in home.html: {target}"

    ex_targets = re.findall(r'data-example="([^"]+)"', home_html)
    assert len(ex_targets) >= 5, f"Expected >= 5 data-example targets in home.html, found {len(ex_targets)}"
    for target in ex_targets:
        clean = target.split("#")[0]
        assert (BASE_DIR / clean).is_file(), f"Broken data-example link in home.html: {target}"

    tab_targets = re.findall(r'data-tab="([^"]+)"', home_html)
    assert set(["docs", "source", "examples", "tutorial", "hierarchy", "index"]).issubset(set(tab_targets)), (
        f"Missing workspace tab buttons in home.html: {tab_targets}"
    )

    tut_targets = re.findall(r'data-tutorial="([^"]+)"', home_html)
    assert len(tut_targets) >= 4, f"Expected >= 4 data-tutorial targets in home.html, found {len(tut_targets)}"
    for target in tut_targets:
        clean = target.split("#")[0]
        assert (BASE_DIR / clean).is_file(), f"Broken data-tutorial link in home.html: {target}"


def test_shell_and_routing_integration() -> None:
    index_html = (BASE_DIR / "index.html").read_text(encoding="utf-8")
    assert 'href="#/home"' in index_html, "index.html brand-link must point to #/home"
    assert 'id="doc-bookmark-btn"' in index_html, "index.html must include #doc-bookmark-btn"
    assert 'id="doc-frame" class="pane-frame" src="home.html"' in index_html, (
        "index.html #doc-frame must default to src=\"home.html\""
    )

    app_js = (BASE_DIR / "js/app.js").read_text(encoding="utf-8")
    for token in (
        "let currentDocUrl = 'home.html'",
        "#/home",
        "openSearchModal",
        "switchSidebarTab",
        "uvm_pinned_bookmarks",
        "uvm_recent_history",
        "workspaceDataUpdated",
    ):
        assert token in app_js, f"Missing '{token}' in js/app.js"

    home_js = (BASE_DIR / "js/home.js").read_text(encoding="utf-8")
    for token in (
        "uvm_pinned_bookmarks",
        "uvm_recent_history",
        "openSearchModal",
        "switchSidebarTab",
        "openDocView",
        "openExampleView",
        "workspaceDataUpdated",
    ):
        assert token in home_js, f"Missing '{token}' in js/home.js"


def test_css_home_rules() -> None:
    css_text = (BASE_DIR / "css/style.css").read_text(encoding="utf-8")
    for selector in (
        ".home-container",
        ".home-hero",
        ".home-workspace-grid",
        ".home-arch-diagram",
        ".home-cards-grid",
        "#doc-bookmark-btn.is-bookmarked",
    ):
        assert selector in css_text, f"Missing CSS rule for '{selector}' in css/style.css"


def main() -> int:
    tests = [
        test_home_files_exist,
        test_home_links_resolve,
        test_shell_and_routing_integration,
        test_css_home_rules,
    ]
    for fn in tests:
        fn()
        print(f"  [OK] {fn.__name__}")
    print("All home page verification checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
