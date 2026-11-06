#!/usr/bin/env python3
"""
verify_code_editor_tools.py
Automated verification for code viewer IDE tools in UVM 1.2 Documentation.
Checks:
- Script inclusions (uvm_symbol_quick.js, page_common.js)
- DOM widgets (find widget, quick info, monaco pane)
- Action buttons (find, wrap, monaco)
- CSS styles for editor tools
- Symbol dictionary integrity
"""

import os
import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src_view"
EX_DIR = BASE_DIR / "examples_view"
JS_DIR = BASE_DIR / "js"
CSS_PATH = BASE_DIR / "css" / "style.css"


def test_quick_symbols():
    print("[1/5] Testing uvm_symbol_quick.js...")
    sym_file = JS_DIR / "uvm_symbol_quick.js"
    assert sym_file.exists(), "uvm_symbol_quick.js does not exist!"
    content = sym_file.read_text(encoding="utf-8")
    assert "window.UVM_SYMBOLS = {" in content, "Missing window.UVM_SYMBOLS declaration"
    json_str = content.replace("// UVM 1.2 Quick Symbol Index - Auto-generated\nwindow.UVM_SYMBOLS = ", "").strip().rstrip(";")
    data = json.loads(json_str)
    assert "classes" in data, "Missing classes in symbols"
    assert "macros" in data, "Missing macros in symbols"
    assert "methods" in data, "Missing methods in symbols"
    assert len(data["classes"]) >= 300, f"Expected >= 300 classes, found {len(data['classes'])}"
    assert len(data["macros"]) >= 700, f"Expected >= 700 macros, found {len(data['macros'])}"
    assert "uvm_component" in data["classes"], "uvm_component missing in classes"
    assert "uvm_info" in data["macros"], "uvm_info missing in macros"
    print(f"  OK: {len(data['classes'])} classes, {len(data['macros'])} macros, {len(data['methods'])} methods indexed.")


def test_css_styles():
    print("[2/5] Testing CSS styles for editor tools...")
    assert CSS_PATH.exists(), "style.css does not exist!"
    css = CSS_PATH.read_text(encoding="utf-8")
    required_selectors = [
        ".code-find-widget",
        "mark.find-match",
        "mark.find-match.find-match-current",
        ".token-highlight",
        ".ctrl-hoverable",
        ".code-quick-info-tooltip",
        "#monaco-editor-pane",
        ".code-wrap-active"
    ]
    for sel in required_selectors:
        assert sel in css, f"Missing CSS selector: {sel}"
    print("  OK: All editor tool CSS classes present.")


def test_js_controllers():
    print("[3/5] Testing js/page_common.js controllers...")
    js_path = JS_DIR / "page_common.js"
    assert js_path.exists(), "page_common.js does not exist!"
    js = js_path.read_text(encoding="utf-8")
    assert "initCodeFindWidget" in js, "Missing initCodeFindWidget in page_common.js"
    assert "initOccurrenceHighlighter" in js, "Missing initOccurrenceHighlighter in page_common.js"
    assert "initDefinitionResolver" in js, "Missing initDefinitionResolver in page_common.js"
    assert "initQuickInfoHover" in js, "Missing initQuickInfoHover in page_common.js"
    assert "initMonacoLoader" in js, "Missing initMonacoLoader in page_common.js"
    assert "initCodeEditorShortcuts" in js, "Missing initCodeEditorShortcuts in page_common.js"
    print("  OK: All JavaScript controllers present in page_common.js.")


def test_source_views():
    print("[4/5] Testing src_view/*.html pages...")
    src_files = list(SRC_DIR.glob("**/*.html"))
    assert len(src_files) == 155, f"Expected 155 source views, found {len(src_files)}"
    checked = 0
    for f in src_files:
        content = f.read_text(encoding="utf-8")
        assert "js/uvm_symbol_quick.js" in content, f"{f.name} missing uvm_symbol_quick.js"
        assert "js/page_common.js" in content, f"{f.name} missing page_common.js"
        assert 'id="code-find-widget"' in content, f"{f.name} missing #code-find-widget"
        assert 'id="code-quick-info"' in content, f"{f.name} missing #code-quick-info"
        assert 'id="monaco-editor-pane"' in content, f"{f.name} missing #monaco-editor-pane"
        assert 'id="btn-toggle-find"' in content, f"{f.name} missing #btn-toggle-find"
        assert 'id="btn-toggle-wrap"' in content, f"{f.name} missing #btn-toggle-wrap"
        assert 'id="btn-toggle-monaco"' in content, f"{f.name} missing #btn-toggle-monaco"
        checked += 1
    print(f"  OK: All {checked} source views verified.")


def test_example_studios():
    print("[5/5] Testing examples_view/*/*.html studios...")
    ex_files = list(EX_DIR.glob("**/*.html"))
    assert len(ex_files) == 39, f"Expected 39 example studios, found {len(ex_files)}"
    checked = 0
    for f in ex_files:
        content = f.read_text(encoding="utf-8")
        assert "js/uvm_symbol_quick.js" in content, f"{f.name} missing uvm_symbol_quick.js"
        assert "js/page_common.js" in content, f"{f.name} missing page_common.js"
        assert 'id="code-find-widget"' in content, f"{f.name} missing #code-find-widget"
        assert 'id="code-quick-info"' in content, f"{f.name} missing #code-quick-info"
        assert 'id="monaco-editor-pane"' in content, f"{f.name} missing #monaco-editor-pane"
        assert 'id="btn-toggle-find"' in content, f"{f.name} missing #btn-toggle-find"
        assert 'id="btn-toggle-wrap"' in content, f"{f.name} missing #btn-toggle-wrap"
        assert 'id="btn-toggle-monaco"' in content, f"{f.name} missing #btn-toggle-monaco"
        checked += 1
    print(f"  OK: All {checked} example studios verified.")


if __name__ == "__main__":
    print("=" * 60)
    print("  Running Verification for Code Editor Tools")
    print("=" * 60)
    test_quick_symbols()
    test_css_styles()
    test_js_controllers()
    test_source_views()
    test_example_studios()
    print("=" * 60)
    print("  ALL VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 60)
