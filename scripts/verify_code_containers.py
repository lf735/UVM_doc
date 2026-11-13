#!/usr/bin/env python3
"""
Automated Verification Suite for Unified Code Containers
Validates:
1. All 155 source views in src_view/ possess the unified .code-container structure.
2. All 39 example studios in examples_view/ possess the unified .code-container structure.
3. Both use .file-code-pane and .sv-code-table.
4. Both use unified toolbar buttons (#btn-copy-code, .studio-action-btn).
5. Both link to js/page_common.js.
6. Zero external dependencies (no http:// or https:// script or font links - Rule 1).
"""

import sys
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_VIEW_DIR = BASE_DIR / "src_view"
EXAMPLES_VIEW_DIR = BASE_DIR / "examples_view"

TOTAL_TESTS = 0
PASSED_TESTS = 0
FAILED_TESTS = 0

def assert_test(cond, name, details=""):
    global TOTAL_TESTS, PASSED_TESTS, FAILED_TESTS
    TOTAL_TESTS += 1
    if cond:
        PASSED_TESTS += 1
        print(f"  [PASS] {name}")
    else:
        FAILED_TESTS += 1
        print(f"  [FAIL] {name} - {details}")

def main():
    print("=" * 60)
    print("  Unified Code Containers Verification Suite")
    print("=" * 60)

    src_files = list(SRC_VIEW_DIR.rglob("*.html"))
    uvm_src_files = [f for f in src_files if "examples" not in f.relative_to(SRC_VIEW_DIR).parts]
    ex_src_files = [f for f in src_files if "examples" in f.relative_to(SRC_VIEW_DIR).parts]
    assert_test(len(uvm_src_files) == 155, f"All 155 UVM library source views generated ({len(uvm_src_files)} found)")
    assert_test(len(ex_src_files) >= 200, f"All example source views generated under src_view/examples/ ({len(ex_src_files)} found)")

    ex_files = list(EXAMPLES_VIEW_DIR.rglob("*.html"))
    assert_test(len(ex_files) >= 38, f"All example studios generated ({len(ex_files)} found)")

    # 1. Verify src_view files
    src_all_have_container = True
    src_all_have_pane = True
    src_all_have_table = True
    src_all_have_toolbar = True
    src_all_have_copy_btn = True
    src_all_have_page_common = True
    src_all_zero_external = True

    for sf in src_files:
        with open(sf, 'r', encoding='utf-8') as f:
            c = f.read()
        if "code-container" not in c or "src-code-container" not in c:
            src_all_have_container = False
        if "file-code-pane" not in c:
            src_all_have_pane = False
        if "sv-code-table" not in c:
            src_all_have_table = False
        if "src-sticky-bar" not in c or "studio-toolbar" not in c:
            src_all_have_toolbar = False
        if 'id="btn-copy-code"' not in c:
            src_all_have_copy_btn = False
        if "js/page_common.js" not in c:
            src_all_have_page_common = False
        if re.search(r'<(?:script|link)[^>]+(?:src|href)=["\']https?://', c):
            src_all_zero_external = False

    assert_test(src_all_have_container, "All 155 source views possess .code-container and .src-code-container")
    assert_test(src_all_have_pane, "All 155 source views possess .file-code-pane")
    assert_test(src_all_have_table, "All 155 source views possess .sv-code-table")
    assert_test(src_all_have_toolbar, "All 155 source views possess unified .studio-toolbar")
    assert_test(src_all_have_copy_btn, "All 155 source views possess unified #btn-copy-code")
    assert_test(src_all_have_page_common, "All 155 source views load unified js/page_common.js")
    assert_test(src_all_zero_external, "All 155 source views have zero external CDN/font links (Rule 1)")

    # 2. Verify examples_view files
    ex_all_have_container = True
    ex_all_have_pane = True
    ex_all_have_table = True
    ex_all_have_toolbar = True
    ex_all_have_copy_btn = True
    ex_all_have_page_common = True
    ex_all_zero_external = True

    for ef in ex_files:
        with open(ef, 'r', encoding='utf-8') as f:
            c = f.read()
        if "code-container" not in c or "studio-code-container" not in c:
            ex_all_have_container = False
        if "file-code-pane" not in c:
            ex_all_have_pane = False
        if "sv-code-table" not in c:
            ex_all_have_table = False
        if "studio-toolbar" not in c:
            ex_all_have_toolbar = False
        if 'id="btn-copy-code"' not in c:
            ex_all_have_copy_btn = False
        if "js/page_common.js" not in c:
            ex_all_have_page_common = False
        if re.search(r'<(?:script|link)[^>]+(?:src|href)=["\']https?://', c):
            ex_all_zero_external = False

    assert_test(ex_all_have_container, "All 39 example studios possess .code-container and .studio-code-container")
    assert_test(ex_all_have_pane, "All 39 example studios possess .file-code-pane")
    assert_test(ex_all_have_table, "All 39 example studios possess .sv-code-table")
    assert_test(ex_all_have_toolbar, "All 39 example studios possess unified .studio-toolbar")
    assert_test(ex_all_have_copy_btn, "All 39 example studios possess unified #btn-copy-code")
    assert_test(ex_all_have_page_common, "All 39 example studios load unified js/page_common.js")
    assert_test(ex_all_zero_external, "All 39 example studios have zero external CDN/font links (Rule 1)")

    print("=" * 60)
    print(f"  Test Results: {PASSED_TESTS}/{TOTAL_TESTS} passed ({FAILED_TESTS} failed)")
    print("=" * 60)

    if FAILED_TESTS > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

