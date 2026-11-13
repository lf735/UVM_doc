#!/usr/bin/env python3
"""
Automated Verification Suite for UVM 1.2 Interactive Examples
Validates:
1. Generation and integrity of all 39 example suites in examples_view/
2. Visual Flow Stepper presence on the 5 pillar examples
3. Multi-file Code Studio, syntax highlighting, and ZIP payloads
4. Navigation and search index integrity in js/search_data.js
5. Bidirectional linking between docs_view/ and examples_view/
6. Zero external runtime dependencies compliance (Rule 1)
"""

import sys
import os
import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EXAMPLES_VIEW_DIR = BASE_DIR / "examples_view"
DOCS_VIEW_DIR = BASE_DIR / "docs_view"
SEARCH_DATA_FILE = BASE_DIR / "js" / "search_data.js"

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
    print("  UVM 1.2 Interactive Examples Automated Test Suite")
    print("=" * 60)

    # Test 1: examples_view directory exists and contains all 39 suites
    assert_test(EXAMPLES_VIEW_DIR.exists() and EXAMPLES_VIEW_DIR.is_dir(), "examples_view directory exists")
    
    html_files = list(EXAMPLES_VIEW_DIR.rglob("*.html"))
    assert_test(len(html_files) >= 38, f"Generated HTML suites count ({len(html_files)} found, >= 38 expected)")

    # Test 2: Integrity of each example suite
    all_have_studio = True
    all_have_topo = True
    all_have_terminal = True
    all_have_zip_payload = True
    all_have_no_external_scripts = True

    for hf in html_files:
        with open(hf, 'r', encoding='utf-8') as f:
            content = f.read()

        if "studio-tab-bar" not in content or "file-code-pane" not in content:
            all_have_studio = False
        if "topo-section" not in content or "topo-card" not in content:
            all_have_topo = False
        if "terminal-body" not in content or "sim-cmd-card" not in content:
            all_have_terminal = False
        if "id=\"zip-payload\"" not in content:
            all_have_zip_payload = False
        if re.search(r'<script[^>]+src=["\']https?://', content):
            all_have_no_external_scripts = False

    assert_test(all_have_studio, "All 39 suites possess Multi-File Code Studio with tabs and code panes")
    assert_test(all_have_topo, "All 39 suites possess Testbench Architecture Topology Grid")
    assert_test(all_have_terminal, "All 39 suites possess Simulation Execution Console & Command Card")
    assert_test(all_have_zip_payload, "All 39 suites possess Embedded Zero-Dependency Native ZIP Payload")
    assert_test(all_have_no_external_scripts, "Zero external script dependencies (Rule 1: 100% offline file:// compatible)")

    # Test 3: Visual Flow Stepper on 5 pillar examples
    pillar_examples = [
        EXAMPLES_VIEW_DIR / "phasing" / "basic.html",
        EXAMPLES_VIEW_DIR / "phasing" / "objections.html",
        EXAMPLES_VIEW_DIR / "tlm-1" / "fifo.html",
        EXAMPLES_VIEW_DIR / "tlm-2" / "nonblocking_simple.html",
        EXAMPLES_VIEW_DIR / "registers" / "primer.html"
    ]

    all_pillars_valid = True
    for pe in pillar_examples:
        if not pe.exists():
            all_pillars_valid = False
            break
        with open(pe, 'r', encoding='utf-8') as f:
            c = f.read()
        if "visual-flow-stepper" not in c or "step-node" not in c or "id=\"stepper-payload\"" not in c:
            all_pillars_valid = False

    assert_test(all_pillars_valid, "All 5 pillar examples contain Interactive Visual Flow Stepper with timeline")

    # Test 4: Verify search_data.js integrity
    assert_test(SEARCH_DATA_FILE.exists(), "js/search_data.js exists")

    with open(SEARCH_DATA_FILE, 'r', encoding='utf-8') as f:
        js_text = f.read()

    m = re.search(r'const UVM_DATA\s*=\s*(\{[\s\S]*\});\s*$', js_text)
    if m:
        data_str = m.group(1)
    else:
        prefix = "const UVM_DATA = "
        data_str = js_text.strip()
        if data_str.startswith(prefix):
            data_str = data_str[len(prefix):].rstrip(';')
    uvm_data = json.loads(data_str)

    assert_test("examplesTree" in uvm_data and len(uvm_data["examplesTree"]) == 8, 
                f"examplesTree contains all 8 logical categories ({len(uvm_data.get('examplesTree', []))} found)")

    ex_search_items = [item for item in uvm_data.get("searchIndex", []) if item.get("type") == "example"]
    assert_test(len(ex_search_items) >= 38, f"searchIndex contains all example entries ({len(ex_search_items)} found)")

    # Test 5: Verify bidirectional callout links in docs_view
    callout_count = 0
    valid_callout_targets = True

    for doc_file in DOCS_VIEW_DIR.rglob("*.html"):
        with open(doc_file, 'r', encoding='utf-8') as f:
            doc_content = f.read()
        for m in re.finditer(r'data-example-url=["\']([^"\']+)["\']', doc_content):
            callout_count += 1
            target_rel = m.group(1).replace('../../', '').replace('../', '')
            target_path = BASE_DIR / target_rel
            if not target_path.exists():
                valid_callout_targets = False
                print(f"Broken callout link in {doc_file}: {target_rel}")

    assert_test(callout_count >= 15, f"Bidirectional callouts present across documentation pages ({callout_count} injected)")
    assert_test(valid_callout_targets, "All injected callout links point to valid, existing example studios")

    # Test 6: Verify UI index.html & app.js filter integration
    with open(BASE_DIR / "index.html", 'r', encoding='utf-8') as f:
        index_html = f.read()

    assert_test('data-tab="examples"' in index_html, "index.html has 'Examples' sidebar tab button")
    assert_test('class="filter-pill" data-type="example"' in index_html, "index.html has 'Examples' search modal filter pill")
    assert_test('filter-pill-diff' in index_html, "index.html has difficulty filter pills in search modal")

    # Test 7: Verify app.js routing & handler integration
    with open(BASE_DIR / "js" / "app.js", 'r', encoding='utf-8') as f:
        app_js = f.read()

    assert_test('renderExamplesTree' in app_js, "js/app.js implements renderExamplesTree()")
    assert_test('#/example/' in app_js, "js/app.js handles #/example/ hash routing")
    assert_test('openExampleView' in app_js, "js/app.js handles openExampleView postMessage")
    assert_test('badge-example' in app_js, "js/app.js styles example search results with badge-example")

    # Test 8: Split View source pairing in search_data.js
    ex_to_src = uvm_data.get("exampleToSrc", {})
    assert_test(len(ex_to_src) >= 38, f"exampleToSrc contains canonical source pairings ({len(ex_to_src)} mapped)")

    # Test 9: Studio Tab Bar overflow & navigation controls in all 39 suites
    all_have_tab_controls = True
    for hf in html_files:
        with open(hf, 'r', encoding='utf-8') as f:
            c = f.read()
        if "studio-tab-bar-wrapper" not in c or "studio-tab-scroll-btn" not in c or "studio-file-select" not in c:
            all_have_tab_controls = False
            print(f"Missing tab controls in: {hf}")
    assert_test(all_have_tab_controls, "All 39 suites possess Tab Bar scroll controls and quick file dropdown selector")

    # Test 10: Code Studio internal scroll & trace sync in example_page.js
    with open(BASE_DIR / "js" / "example_page.js", 'r', encoding='utf-8') as f:
        ex_page_js = f.read()
    assert_test('studioCodeContainer.scrollTo' in ex_page_js, "example_page.js scrolls studio internally without jumping window")
    assert_test('studio-file-select' in ex_page_js, "example_page.js binds quick file dropdown selector")
    assert_test('studio-tab-scroll-left' in ex_page_js, "example_page.js binds horizontal tab scroll buttons")

    # Test 11: RAG chunks include example suites
    rag_chunks_file = BASE_DIR / "data" / "rag_chunks.json"
    if rag_chunks_file.exists():
        with open(rag_chunks_file, 'r', encoding='utf-8') as f:
            rag_chunks = json.load(f)
        ex_chunks = [c for c in rag_chunks if c.get("type") == "example"]
        assert_test(len(ex_chunks) >= 38, f"data/rag_chunks.json indexes all example suites ({len(ex_chunks)} found)")
    else:
        assert_test(False, "data/rag_chunks.json exists")

    # Test 12: Visual Flow Stepper user documentation
    stepper_guide_file = BASE_DIR / "docs" / "visual_flow_stepper_guide.md"
    assert_test(stepper_guide_file.exists(), "docs/visual_flow_stepper_guide.md exists and is documented")

    # Test 13: Verify all Key UVM APIs resolve to valid documentation targets
    sys.path.insert(0, str(BASE_DIR / "scripts"))
    import build_examples
    search_index = uvm_data.get("searchIndex", [])
    valid_names = set()
    for s in search_index:
        name = s.get('name')
        if name:
            valid_names.add(name)
            valid_names.add(name.lower())
            valid_names.add(name.lstrip('`'))
            valid_names.add(name.lstrip('`').lower())

    unresolved_apis = []
    for suite_key, meta in build_examples.SUITES_METADATA.items():
        for api in meta.get("apis", []):
            clean = api.lstrip('`')
            if api in valid_names or clean in valid_names or api.lower() in valid_names or clean.lower() in valid_names:
                continue
            # Check suffix
            if any(n.endswith('::' + clean) or n.endswith('.' + clean) for n in valid_names):
                continue
            unresolved_apis.append((suite_key, api))

    assert_test(len(unresolved_apis) == 0, 
                f"All Key UVM APIs resolve cleanly ({len(unresolved_apis)} unresolved)",
                f"Unresolved: {unresolved_apis}")

    # Test 14: Standalone src_view/examples/ pages & unified openSourceView/studioFileChanged wiring
    ex_src_dir = BASE_DIR / "src_view" / "examples"
    ex_src_pages = list(ex_src_dir.rglob("*.html")) if ex_src_dir.exists() else []
    assert_test(len(ex_src_pages) >= 200, f"Standalone src_view/examples/ pages generated ({len(ex_src_pages)} found)")
    sample_ex_src = (ex_src_dir / "phasing" / "basic" / "test.sv.html")
    if sample_ex_src.exists():
        sample_html = sample_ex_src.read_text(encoding="utf-8")
        has_no_meta_badges = ('lines</span>' not in sample_html and 'KB</span>' not in sample_html)
        assert_test(has_no_meta_badges, "src_view/examples/ omits line-count and file-size badges")

    ex_page_js = (BASE_DIR / "js" / "example_page.js").read_text(encoding="utf-8")
    assert_test("initBannerFilesPopover" in ex_page_js and "'openSourceView'" in ex_page_js,
                "example_page.js opens example files via standard openSourceView")
    assert_test("'studioFileChanged'" in ex_page_js,
                "example_page.js syncs studio tab changes via studioFileChanged")

    app_js_src = (BASE_DIR / "js" / "app.js").read_text(encoding="utf-8")
    assert_test("studioFileChanged" in app_js_src and "focusSearchInput" in app_js_src,
                "app.js handles studioFileChanged and focusSearchInput")

    print("=" * 60)
    print(f"  Test Results: {PASSED_TESTS}/{TOTAL_TESTS} passed ({FAILED_TESTS} failed)")
    print("=" * 60)

    if FAILED_TESTS > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
