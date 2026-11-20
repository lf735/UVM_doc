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
        "#monaco-editor-pane",
        ".monaco-fallback-pre",
        ".monaco-active-line-highlight",
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
    assert ("initCodeFindWidget" in js or "initMonacoFindTrigger" in js), "Missing Find controller in page_common.js"
    assert "initMonacoLoader" in js, "Missing initMonacoLoader in page_common.js"
    assert "registerUvmSystemVerilogLanguage" in js, "Missing registerUvmSystemVerilogLanguage in page_common.js"
    assert "defineUvmMonacoThemes" in js, "Missing defineUvmMonacoThemes in page_common.js"
    assert "initCodeEditorShortcuts" in js, "Missing initCodeEditorShortcuts in page_common.js"
    print("  OK: All JavaScript controllers present in page_common.js.")


def test_source_views():
    print("[4/5] Testing src_view/*.html pages...")
    src_files = list(SRC_DIR.glob("**/*.html"))
    uvm_src_files = [
        f for f in src_files
        if "examples" not in f.relative_to(SRC_DIR).parts
        and "tutorial" not in f.relative_to(SRC_DIR).parts
    ]
    ex_src_files = [f for f in src_files if "examples" in f.relative_to(SRC_DIR).parts]
    tut_src_files = [f for f in src_files if "tutorial" in f.relative_to(SRC_DIR).parts]
    assert len(uvm_src_files) == 155, f"Expected 155 UVM library source views, found {len(uvm_src_files)}"
    assert len(ex_src_files) >= 200, f"Expected example source views under src_view/examples/, found {len(ex_src_files)}"
    assert len(tut_src_files) >= 1, f"Expected tutorial source views under src_view/tutorial/, found {len(tut_src_files)}"
    checked = 0
    for f in src_files:
        content = f.read_text(encoding="utf-8")
        assert "js/uvm_symbol_quick.js" in content, f"{f.name} missing uvm_symbol_quick.js"
        assert "js/page_common.js" in content, f"{f.name} missing page_common.js"
        assert 'id="monaco-editor-pane"' in content, f"{f.name} missing #monaco-editor-pane"
        assert 'id="code-find-widget"' in content, f"{f.name} missing #code-find-widget"
        assert 'id="code-quick-info"' in content, f"{f.name} missing #code-quick-info"
        assert 'id="btn-toggle-find"' in content, f"{f.name} missing #btn-toggle-find"
        assert 'id="btn-toggle-wrap"' in content, f"{f.name} missing #btn-toggle-wrap"
        assert 'id="btn-toggle-monaco"' in content, f"{f.name} missing #btn-toggle-monaco"
        assert 'class="sv-code-table"' in content, f"{f.name} missing .sv-code-table"
        checked += 1
    print(f"  OK: All {checked} source views verified.")


def test_example_studios():
    print("[5/6] Testing examples_view/*/*.html studios...")
    ex_files = list(EX_DIR.glob("**/*.html"))
    assert len(ex_files) == 39, f"Expected 39 example studios, found {len(ex_files)}"
    checked = 0
    for f in ex_files:
        content = f.read_text(encoding="utf-8")
        assert "js/uvm_symbol_quick.js" in content, f"{f.name} missing uvm_symbol_quick.js"
        assert "js/page_common.js" in content, f"{f.name} missing page_common.js"
        assert 'id="monaco-editor-pane"' in content, f"{f.name} missing #monaco-editor-pane"
        assert 'id="code-find-widget"' in content, f"{f.name} missing #code-find-widget"
        assert 'id="code-quick-info"' in content, f"{f.name} missing #code-quick-info"
        assert 'id="btn-toggle-find"' in content, f"{f.name} missing #btn-toggle-find"
        assert 'id="btn-toggle-wrap"' in content, f"{f.name} missing #btn-toggle-wrap"
        assert 'id="btn-toggle-monaco"' in content, f"{f.name} missing #btn-toggle-monaco"
        assert 'class="sv-code-table"' in content, f"{f.name} missing .sv-code-table"
        checked += 1
    print(f"  OK: All {checked} example studios verified.")


def test_clickable_uvm_symbols_integration():
    print("[6/6] Testing enriched clickable UVM symbols & disambiguation assets...")
    quick_js = (JS_DIR / "uvm_symbol_quick.js").read_text(encoding="utf-8")
    for key in ('"constants":', '"types":', '"vars":', '"doc_url":', '"classFields":'):
        assert key in quick_js, f"uvm_symbol_quick.js missing {key}"

    page_common = (JS_DIR / "page_common.js").read_text(encoding="utf-8")
    for sym_token in ("lookupUvmSymbol", "sym-disambig-popover", "openUvmDocFromMonaco", "openUvmDefFromMonaco"):
        assert sym_token in page_common, f"page_common.js missing {sym_token}"

    app_js = (JS_DIR / "app.js").read_text(encoding="utf-8")
    assert "ownerClass" in app_js, "app.js openDocView missing ownerClass support"

    css_text = CSS_PATH.read_text(encoding="utf-8")
    assert ".sym-disambig-popover" in css_text, "style.css missing .sym-disambig-popover"
    print("  OK: Enriched clickable UVM symbols and disambiguation popover verified.")


def test_monaco_and_symbol_anchor_regressions():
    print("[7/7] Testing Monaco integration & symbol doc-anchor regressions...")
    sym_file = JS_DIR / "uvm_symbol_quick.js"
    raw = sym_file.read_text(encoding="utf-8")
    json_str = raw.split("window.UVM_SYMBOLS = ", 1)[1].strip().rstrip(";")
    data = json.loads(json_str)

    missing_anchors = [
        (mname, entry.get("class"))
        for mname, mlist in data.get("methods", {}).items()
        for entry in mlist
        if "#" not in (entry.get("doc_url") or "")
    ]
    assert not missing_anchors, f"Found {len(missing_anchors)} method entries without #anchor: {missing_anchors[:5]}"

    new_entries = data.get("methods", {}).get("new", [])
    assert not any(e.get("class") == "Global" for e in new_entries), (
        "SV constructor 'new' must not be indexed under Global"
    )

    page_common = (JS_DIR / "page_common.js").read_text(encoding="utf-8")
    assert "id: 'uvm-systemverilog'" in page_common, "Monaco must use dedicated 'uvm-systemverilog' language ID"
    assert "['class', 'endclass']" not in page_common, (
        "Monaco brackets config must not include ['class', 'endclass'] (breaks typedef class)"
    )
    assert "...Object.keys(syms.methods || {})" not in page_common, (
        "Monarch uvmMethodsSet must not include all syms.methods keys (pollutes local variables)"
    )
    assert "bracketPairColorization: { enabled: false }" in page_common, (
        "Monaco bracketPairColorization must stay disabled for color parity"
    )
    assert "uvm.openDoc" in page_common and "uvm.openSource" in page_common, (
        "Monaco hover/action commands uvm.openDoc and uvm.openSource missing"
    )
    assert "SV_NATIVE_METHODS_JS" in page_common and "isMonacoTokenIgnoredAt" in page_common, (
        "False-positive guards missing in page_common.js"
    )
    assert "comment.tag', '@pop'" in page_common, (
        "Monarch comment_line must pop on end-of-line rules so comments never bleed"
    )

    css_text = CSS_PATH.read_text(encoding="utf-8")
    assert ".monaco-active-line-highlight" in css_text, "style.css missing .monaco-active-line-highlight"
    print("  OK: Monaco integration, Monarch grammar guards, and 100% anchored method doc URLs verified.")


if __name__ == "__main__":
    print("=" * 60)
    print("  Running Verification for Code Editor Tools")
    print("=" * 60)
    test_quick_symbols()
    test_css_styles()
    test_js_controllers()
    test_source_views()
    test_example_studios()
    test_clickable_uvm_symbols_integration()
    test_monaco_and_symbol_anchor_regressions()
    print("=" * 60)
    print("  ALL VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 60)
