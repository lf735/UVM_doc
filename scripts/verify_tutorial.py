#!/usr/bin/env python3
"""
Automated Verification Suite for the UVM 1.2 Step-by-Step Interactive Tutorial.
Data-driven from config/tutorial_manifest.yaml & tutorial_content/chapters/*.md
so adding, removing, or reordering chapters never breaks static count assertions.
"""

import json
import sys
from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

import build_tutorial  # noqa: E402

TUTORIAL_VIEW_DIR = BASE_DIR / "tutorial_view"
SRC_TUTORIAL_DIR = BASE_DIR / "src_view" / "tutorial"
SEARCH_DATA_FILE = BASE_DIR / "js" / "search_data.js"
TUTORIAL_META_FILE = BASE_DIR / "js" / "tutorial_meta.js"
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

    manifest, chapters = build_tutorial.load_tutorial_curriculum()
    expected_chapters = len(chapters)
    expected_parts = len({ch["part_id"] for ch in chapters})
    expected_slugs = {ch["slug"] for ch in chapters}

    assert_test(TUTORIAL_VIEW_DIR.is_dir(), "tutorial_view/ directory exists")
    html_files = sorted(TUTORIAL_VIEW_DIR.glob("*.html"))
    found_slugs = {hf.stem for hf in html_files}
    assert_test(
        found_slugs == expected_slugs,
        f"tutorial_view/ matches manifest 1:1 ({len(found_slugs)}/{expected_chapters} chapters)",
        f"missing={expected_slugs - found_slugs}, stale={found_slugs - expected_slugs}",
    )

    broken_links = []
    missing_studio_features = []
    missing_quizzes = []
    missing_diffs = []
    capstone_issues = []

    anchor_cache: dict[tuple[str, str], bool] = {}
    code_chapters = 0
    diff_chapters = 0

    for ch in chapters:
        slug = ch["slug"]
        hf = TUTORIAL_VIEW_DIR / f"{slug}.html"
        if not hf.is_file():
            continue
        raw = hf.read_text(encoding="utf-8")
        soup = BeautifulSoup(raw, "html.parser")

        if not soup.find(id="tut-quiz-payload") or not soup.find(id="tut-quiz-container"):
            missing_quizzes.append(hf.name)

        widget = ch.get("interactive_widget")
        if widget != "capstone":
            assert_test(bool(soup.select("pre.mermaid")), f"{hf.name} contains Mermaid diagram")

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

        if ch.get("src_dir"):
            code_chapters += 1
            for req_id in ("zip-payload", "stepper-payload", "visual-flow-stepper", "terminal-body", "code-find-widget", "btn-toggle-monaco"):
                if not soup.find(id=req_id):
                    missing_studio_features.append((hf.name, req_id))
            if not soup.select(".clickable-uvm-sym"):
                missing_studio_features.append((hf.name, "clickable-uvm-sym"))

        if ch.get("inherit_from"):
            diff_chapters += 1
            if not soup.find(id="tut-diff-payload") or not soup.find(id="tut-diff-container"):
                missing_diffs.append(hf.name)

        if widget == "vcycle":
            assert_test(
                bool(soup.find(id="tut-cy-graph")) and bool(soup.find(id="tut-graph-payload")),
                f"{hf.name} contains Cytoscape interactive V-Cycle diagram & payload",
            )
        if widget == "scm_matrix":
            assert_test(
                bool(soup.select(".tut-scm-tab")) and bool(soup.find(id="tut-scm-detail")),
                f"{hf.name} contains interactive Stimuli/Checks/Metrics matrix",
            )
        if widget == "capstone":
            if not soup.find(id="capstone-explorer") or not soup.find(id="tut-layer-slider"):
                capstone_issues.append("Missing #capstone-explorer or #tut-layer-slider")
            gp_el = soup.find(id="tut-graph-payload")
            if not gp_el:
                capstone_issues.append(f"Missing #tut-graph-payload in {hf.name}")
            else:
                gp = json.loads(gp_el.get("data-tut-graph", "{}"))
                nodes = gp.get("nodes", [])
                if len(nodes) < 15:
                    capstone_issues.append(f"Expected >= 15 capstone nodes, found {len(nodes)}")
                if len(gp.get("layers", [])) < 2:
                    capstone_issues.append("Expected >= 2 layer slider definitions")
                for n in nodes:
                    ch_url = n.get("chapterUrl", "")
                    doc_url = n.get("docUrl", "")
                    if ch_url and not (BASE_DIR / ch_url).is_file():
                        capstone_issues.append(f"Invalid node chapterUrl: {ch_url}")
                    if not doc_url or not (BASE_DIR / doc_url.split("#")[0]).is_file():
                        capstone_issues.append(f"Invalid node docUrl: {doc_url}")

    assert_test(len(missing_quizzes) == 0, f"All {expected_chapters} chapters include interactive Self-Check Quizzes", str(missing_quizzes))
    assert_test(len(missing_studio_features) == 0, f"All {code_chapters} code chapters include Code Studio, Stepper, Console & ZIP payloads", str(missing_studio_features))
    assert_test(len(missing_diffs) == 0, f"All {diff_chapters} incremental chapters include unified diff payloads & diff2html containers", str(missing_diffs))
    assert_test(len(broken_links) == 0, "100% of chapter doc/example cross-links resolve with valid anchors", str(broken_links))
    assert_test(len(capstone_issues) == 0, "Capstone 4-in-1 explorer, layers & click-back links valid", str(capstone_issues))

    # Standalone src_view/tutorial/ checks
    tut_src_dirs = {d.name for d in SRC_TUTORIAL_DIR.iterdir() if d.is_dir()} if SRC_TUTORIAL_DIR.is_dir() else set()
    expected_code_slugs = {ch["slug"] for ch in chapters if ch.get("src_dir")}
    assert_test(
        tut_src_dirs == expected_code_slugs,
        f"src_view/tutorial/ folders match manifest code chapters ({len(tut_src_dirs)}/{len(expected_code_slugs)})",
    )

    # Check js/tutorial_meta.js
    assert_test(TUTORIAL_META_FILE.is_file(), "js/tutorial_meta.js exists")

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
        assert_test(
            len(tut_tree) == expected_parts and total_tree_chapters == expected_chapters,
            f"search_data.js tutorialTree has {expected_parts} parts & {expected_chapters} chapters ({len(tut_tree)} parts, {total_tree_chapters} chapters)",
        )

        tut_search = [x for x in uvm_data.get("searchIndex", []) if x.get("type") == "tutorial"]
        assert_test(
            len(tut_search) == expected_chapters,
            f"searchIndex contains all {expected_chapters} tutorial entries ({len(tut_search)} found)",
        )

        tut_to_src = uvm_data.get("tutorialToSrc", {})
        assert_test(
            len(tut_to_src) == code_chapters,
            f"tutorialToSrc maps all {code_chapters} code chapters for Split View ({len(tut_to_src)} mapped)",
        )

    # Check SPA & frontend wiring
    index_html = (BASE_DIR / "index.html").read_text(encoding="utf-8")
    assert_test(
        'data-tab="tutorial"' in index_html and 'id="doc-tutorial-back-btn"' in index_html and 'data-type="tutorial"' in index_html,
        "index.html integrates Tutorial sidebar tab, Back button, and Search filter pill",
    )

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
        assert_test(
            len(tut_parents) == expected_chapters,
            f"data/rag_chunks.json indexes all {expected_chapters} tutorial chapters ({len(tut_parents)} found)",
        )

    print("=" * 64)
    print(f"  Test Results: {PASSED_TESTS}/{TOTAL_TESTS} passed ({FAILED_TESTS} failed)")
    print("=" * 64)
    return 1 if FAILED_TESTS > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
