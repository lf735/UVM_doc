#!/usr/bin/env python3
"""
Automated Verification Suite for the UVM 1.2 Step-by-Step Interactive Tutorial.
Uses BeautifulSoup (bs4) to validate:
1. All 13 chapter HTML pages in tutorial_view/ and standalone src_view/tutorial/ views.
2. Code Studio, Simulation Console, Flow Stepper, ZIP payload, Diff payload, and Quizzes.
3. Chapter 13 Capstone 4-in-1 dynamic explorer (nodes, layers, chapter back-links, doc links).
4. Link and anchor integrity for 100% of docs_view/ and examples_view/ cross-links.
5. Integration in js/search_data.js, index.html, home.html, js/app.js, js/tutorial_page.js, and css/style.css.
6. RAG indexing of all 13 chapters in data/rag_chunks.json (when generated).
"""

import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
TUTORIAL_VIEW_DIR = BASE_DIR / "tutorial_view"
SRC_TUTORIAL_DIR = BASE_DIR / "src_view" / "tutorial"
SEARCH_DATA_FILE = BASE_DIR / "js" / "search_data.js"
RAG_CHUNKS_FILE = BASE_DIR / "data" / "rag_chunks.json"

TOTAL_TESTS = 0
PASSED_TESTS = 0
FAILED_TESTS = 0


def assert_test(cond: bool, name: str, details: str = "") -> None:
    global TOTAL_TESTS, PASSED_TESTS, FAILED_TESTS
    TOTAL_TESTS += 1
    if cond:
        PASSED_TESTS += 1
        print(f"  [PASS] {name}")
    else:
        FAILED_TESTS += 1
        print(f"  [FAIL] {name}" + (f" - {details}" if details else ""))


def check_anchor_exists(target_file: Path, anchor: str) -> bool:
    if not anchor:
        return True
    txt = target_file.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(txt, "html.parser")
    if soup.find(id=anchor) or soup.find(attrs={"name": anchor}):
        return True
    return f'id="{anchor}"' in txt or f'name="{anchor}"' in txt


def main() -> int:
    print("=" * 64)
    print("  UVM 1.2 Step-by-Step Tutorial Verification Suite")
    print("=" * 64)

    assert_test(TUTORIAL_VIEW_DIR.is_dir(), "tutorial_view/ directory exists")
    html_files = sorted(TUTORIAL_VIEW_DIR.glob("ch*.html"))
    assert_test(len(html_files) == 13, f"All 13 tutorial chapters generated ({len(html_files)} found)")

    broken_links = []
    missing_studio_features = []
    missing_quizzes = []
    missing_diffs = []
    capstone_issues = []

    anchor_cache: dict[tuple[str, str], bool] = {}

    for hf in html_files:
        raw = hf.read_text(encoding="utf-8")
        soup = BeautifulSoup(raw, "html.parser")

        # Validate quizzes on every chapter
        if not soup.find(id="tut-quiz-payload") or not soup.find(id="tut-quiz-container"):
            missing_quizzes.append(hf.name)

        # Validate Mermaid diagrams exist
        assert_test(bool(soup.select("pre.mermaid")) or hf.name.startswith("ch13"), f"{hf.name} contains Mermaid or Capstone diagram")

        # Validate all doc and example links resolve with valid anchors
        for el in soup.select("[data-doc-href], [data-example-url]"):
            rel_target = el.get("data-doc-href") or el.get("data-example-url")
            if not rel_target:
                continue
            path_part, _, anchor = rel_target.partition("#")
            target_file = BASE_DIR / path_part
            if not target_file.is_file():
                broken_links.append((hf.name, rel_target, "missing file"))
                continue
            if anchor:
                key = (path_part, anchor)
                if key not in anchor_cache:
                    anchor_cache[key] = check_anchor_exists(target_file, anchor)
                if not anchor_cache[key]:
                    broken_links.append((hf.name, rel_target, f"missing anchor #{anchor}"))

        # Practical chapters ch03..ch13
        ch_num = int(hf.name[2:4])
        if ch_num >= 3:
            for req_id in ("zip-payload", "stepper-payload", "visual-flow-stepper", "terminal-body", "code-find-widget", "btn-toggle-monaco"):
                if not soup.find(id=req_id):
                    missing_studio_features.append((hf.name, req_id))
            if not soup.select(".clickable-uvm-sym"):
                missing_studio_features.append((hf.name, "clickable-uvm-sym"))
        if ch_num >= 4:
            if not soup.find(id="tut-diff-payload") or not soup.find(id="tut-diff-container"):
                missing_diffs.append(hf.name)

        if ch_num == 1:
            assert_test(bool(soup.find(id="tut-cy-graph")) and bool(soup.find(id="tut-graph-payload")),
                        "Ch.01 contains Cytoscape interactive V-Cycle diagram & payload")
        if ch_num == 2:
            assert_test(bool(soup.select(".tut-scm-tab")) and bool(soup.find(id="tut-scm-detail")),
                        "Ch.02 contains interactive Stimuli/Checks/Metrics matrix")
        if ch_num == 13:
            if not soup.find(id="capstone-explorer") or not soup.find(id="tut-layer-slider"):
                capstone_issues.append("Missing #capstone-explorer or #tut-layer-slider")
            gp_el = soup.find(id="tut-graph-payload")
            if not gp_el:
                capstone_issues.append("Missing #tut-graph-payload in Ch.13")
            else:
                gp = json.loads(gp_el.get("data-tut-graph", "{}"))
                nodes = gp.get("nodes", [])
                if len(nodes) < 15:
                    capstone_issues.append(f"Expected >= 15 capstone nodes, found {len(nodes)}")
                if len(gp.get("layers", [])) < 10:
                    capstone_issues.append("Expected >= 10 layer slider definitions")
                for n in nodes:
                    ch_url = n.get("chapterUrl", "")
                    doc_url = n.get("docUrl", "")
                    if not ch_url or not (BASE_DIR / ch_url).is_file():
                        capstone_issues.append(f"Invalid node chapterUrl: {ch_url}")
                    if not doc_url or not (BASE_DIR / doc_url.split("#")[0]).is_file():
                        capstone_issues.append(f"Invalid node docUrl: {doc_url}")

    assert_test(len(missing_quizzes) == 0, "All 13 chapters include interactive Self-Check Quizzes", str(missing_quizzes))
    assert_test(len(missing_studio_features) == 0, "Chapters 03-13 include Code Studio, Stepper, Console & ZIP payloads", str(missing_studio_features))
    assert_test(len(missing_diffs) == 0, "Chapters 04-13 include unified diff payloads & diff2html containers", str(missing_diffs))
    assert_test(len(broken_links) == 0, "100% of chapter doc/example cross-links resolve with valid anchors", str(broken_links))
    assert_test(len(capstone_issues) == 0, "Chapter 13 Capstone 4-in-1 explorer, layers & click-back links valid", str(capstone_issues))

    # Standalone src_view/tutorial/ checks
    tut_src_pages = list(SRC_TUTORIAL_DIR.rglob("*.html")) if SRC_TUTORIAL_DIR.is_dir() else []
    assert_test(len(tut_src_pages) >= 150, f"Standalone src_view/tutorial/ pages generated ({len(tut_src_pages)} found)")

    # Check search_data.js integration
    assert_test(SEARCH_DATA_FILE.is_file(), "js/search_data.js exists")
    if SEARCH_DATA_FILE.is_file():
        js_txt = SEARCH_DATA_FILE.read_text(encoding="utf-8")
        prefix = "const UVM_DATA = "
        idx = js_txt.find(prefix)
        data_str = js_txt[idx + len(prefix):].strip().rstrip(";")
        uvm_data = json.loads(data_str)

        tut_tree = uvm_data.get("tutorialTree", [])
        total_tree_chapters = sum(len(p.get("children", [])) for p in tut_tree)
        assert_test(len(tut_tree) == 5 and total_tree_chapters == 13,
                    f"search_data.js tutorialTree has 5 parts & 13 chapters ({len(tut_tree)} parts, {total_tree_chapters} chapters)")

        tut_search = [x for x in uvm_data.get("searchIndex", []) if x.get("type") == "tutorial"]
        assert_test(len(tut_search) == 13, f"searchIndex contains all 13 tutorial entries ({len(tut_search)} found)")

        tut_to_src = uvm_data.get("tutorialToSrc", {})
        assert_test(len(tut_to_src) >= 11, f"tutorialToSrc maps practical chapters for Split View ({len(tut_to_src)} mapped)")

    # Check SPA & frontend wiring
    index_html = (BASE_DIR / "index.html").read_text(encoding="utf-8")
    assert_test('data-tab="tutorial"' in index_html and 'id="doc-tutorial-back-btn"' in index_html and 'data-type="tutorial"' in index_html,
                "index.html integrates Tutorial sidebar tab, Back button, and Search filter pill")

    app_js = (BASE_DIR / "js" / "app.js").read_text(encoding="utf-8")
    for tok in ("openTutorialView", "renderTutorialTree", "#/tutorial/", "tutorialProgressUpdated", "badge-tutorial"):
        assert_test(tok in app_js, f"js/app.js contains {tok}")

    tut_js = (BASE_DIR / "js" / "tutorial_page.js").read_text(encoding="utf-8")
    for tok in ("cytoscape", "mermaid", "Diff2HtmlUI", "uvm_tutorial_progress", "initCytoscapeGraph"):
        assert_test(tok in tut_js, f"js/tutorial_page.js uses {tok}")

    css_txt = (BASE_DIR / "css" / "style.css").read_text(encoding="utf-8")
    for sel in (".badge-tutorial", ".doc-tutorial-back-btn", ".capstone-explorer", ".tut-quiz-card"):
        assert_test(sel in css_txt, f"css/style.css defines {sel}")

    # RAG chunks check (optional if rag_chunks.json hasn't been rebuilt yet, required once built)
    if RAG_CHUNKS_FILE.is_file():
        chunks = json.loads(RAG_CHUNKS_FILE.read_text(encoding="utf-8"))
        tut_parents = [c for c in chunks if c.get("type") == "tutorial" and c.get("level") == "parent"]
        assert_test(len(tut_parents) == 13, f"data/rag_chunks.json indexes all 13 tutorial chapters ({len(tut_parents)} found)")

    print("=" * 64)
    print(f"  Test Results: {PASSED_TESTS}/{TOTAL_TESTS} passed ({FAILED_TESTS} failed)")
    print("=" * 64)
    return 1 if FAILED_TESTS > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
