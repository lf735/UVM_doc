#!/usr/bin/env python3
"""
verify_inherited_members.py
Automated verification for the Inherited Methods & Elements collapsible category:
- Ensures js/doc_topics/*.js bundles are extracted faithfully from parent docs_view/ HTML
- Ensures js/uvm_symbol_quick.js contains classParents & classDocMembers
- Validates MRO non-overridden resolution & oldest-to-newest ordering
- Validates coverage of both methods and non-method elements (variables, ports, types, params)
- Verifies js/page_common.js & css/style.css offline (file://) compatibility and click routing
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
QUICK_JS = BASE_DIR / "js" / "uvm_symbol_quick.js"
TOPICS_DIR = BASE_DIR / "js" / "doc_topics"
PAGE_COMMON = BASE_DIR / "js" / "page_common.js"
CSS_PATH = BASE_DIR / "css" / "style.css"


def load_quick_symbols() -> dict:
    raw = QUICK_JS.read_text(encoding="utf-8")
    marker = "window.UVM_SYMBOLS = "
    assert marker in raw, "window.UVM_SYMBOLS missing in uvm_symbol_quick.js"
    return json.loads(raw.split(marker, 1)[1].rstrip().rstrip(";"))


def load_topic_bundle(cls_name: str) -> list:
    safe_name = re.sub(r"[^A-Za-z0-9_]", "_", cls_name)
    bundle_path = TOPICS_DIR / f"{safe_name}.js"
    assert bundle_path.exists(), f"Missing doc topic bundle: {bundle_path}"
    txt = bundle_path.read_text(encoding="utf-8")
    prefix = f"window.__registerUvmDocTopics({json.dumps(cls_name)},"
    assert prefix in txt, f"Bundle {bundle_path.name} missing JSONP registration call"
    json_part = txt.split(prefix, 1)[1].rsplit(");", 1)[0]
    return json.loads(json_part)


def compute_inherited_oldest_to_newest(cname: str, class_parents: dict, class_doc_members: dict):
    """Mirrors JS MRO deduplication + oldest-to-newest display ordering."""
    node = class_parents.get(cname)
    assert node and node.get("parent"), f"{cname} missing parent in classParents"

    ancestors_nearest = []
    curr = node["parent"]
    visited = {cname}
    while curr and curr not in visited:
        visited.add(curr)
        ancestors_nearest.append(curr)
        curr = (class_parents.get(curr) or {}).get("parent", "")

    own = {"new"} | {m["n"] for m in class_doc_members.get(cname, [])}
    seen = set(own)
    retained_by_anc = {}
    for anc in ancestors_nearest:
        kept = []
        for m in class_doc_members.get(anc, []):
            if m["n"] in seen:
                continue
            seen.add(m["n"])
            kept.append(m)
        if kept:
            retained_by_anc[anc] = kept

    oldest_first = [anc for anc in reversed(ancestors_nearest) if anc in retained_by_anc]
    ordered_items = []
    for anc in oldest_first:
        for m in retained_by_anc[anc]:
            ordered_items.append((anc, m["n"], m["k"]))
    return oldest_first, ordered_items


def test_bundles_and_quick_index():
    print("[1/4] Testing classParents, classDocMembers & js/doc_topics/ bundles...")
    data = load_quick_symbols()
    class_parents = data.get("classParents", {})
    class_doc_members = data.get("classDocMembers", {})

    assert len(class_parents) >= 300, f"Expected >=300 classes in classParents, got {len(class_parents)}"
    assert len(class_doc_members) >= 180, f"Expected >=180 documented classes in classDocMembers, got {len(class_doc_members)}"

    bundle_files = list(TOPICS_DIR.glob("*.js"))
    assert len(bundle_files) == len(class_doc_members), (
        f"Bundle count ({len(bundle_files)}) must match classDocMembers ({len(class_doc_members)})"
    )

    # Verify non-method elements + authentic HTML blocks in parent bundles
    obj_items = load_topic_bundle("uvm_object")
    obj_by_name = {it["n"]: it for it in obj_items}
    assert "use_uvm_seeding" in obj_by_name and obj_by_name["use_uvm_seeding"]["k"] == "variable"
    assert '<div class="CVariable"' in obj_by_name["use_uvm_seeding"]["h"]
    assert "__ROOT_REL__src_view/base/uvm_object.svh.html#L" in obj_by_name["use_uvm_seeding"]["h"]
    assert obj_by_name["use_uvm_seeding"]["s"].startswith("src_view/base/uvm_object.svh.html#L")

    comp_items = load_topic_bundle("uvm_component")
    comp_names = {it["n"]: it for it in comp_items}
    for req in ("build_phase", "run_phase", "print_config_matches", "print_enabled", "tr_database"):
        assert req in comp_names, f"uvm_component bundle missing {req}"
        assert 'class="src-code-link"' in comp_names[req]["h"], f"uvm_component.{req} missing src-code-link"

    drv_items = load_topic_bundle("uvm_driver")
    drv_names = {it["n"]: it for it in drv_items}
    assert "seq_item_port" in drv_names and drv_names["seq_item_port"]["k"] == "port"
    assert "rsp_port" in drv_names and drv_names["rsp_port"]["k"] == "port"

    # Zero fallback links pointing only to #L1 or parent class header line
    with open(BASE_DIR / "data" / "uvm_source_database.json", encoding="utf-8") as df:
        classes_db = json.load(df).get("classes", {})
    fallback_src = []
    missing_doc = []
    for cname in class_doc_members:
        c_line = classes_db.get(cname, {}).get("start_line")
        for it in load_topic_bundle(cname):
            s = it.get("s", "")
            d = it.get("d", "")
            if not d or "#doc-nav-item-" not in d:
                missing_doc.append((cname, it["n"], d))
            if not s or s.endswith("#L1") or (c_line and s.endswith(f"#L{c_line}")):
                fallback_src.append((cname, it["n"], s, c_line))
    assert not missing_doc, f"Missing exact doc anchors: {missing_doc[:5]}"
    assert not fallback_src, f"Source links falling back to class header/#L1: {fallback_src[:5]}"
    print(f"  OK: {len(bundle_files)} bundles verified with exact source & doc links (0 class-only fallbacks).")
    return class_parents, class_doc_members


def test_mro_and_ordering(class_parents, class_doc_members):
    print("[2/4] Testing MRO deduplication & oldest-to-newest ordering...")
    # uvm_monitor inherits uvm_object -> uvm_report_object -> uvm_component
    ancestors_mon, items_mon = compute_inherited_oldest_to_newest("uvm_monitor", class_parents, class_doc_members)
    assert ancestors_mon == ["uvm_object", "uvm_report_object", "uvm_component"], f"Unexpected order: {ancestors_mon}"
    names_mon = [n for _, n, _ in items_mon]
    assert len(names_mon) == len(set(names_mon)), "Duplicate inherited members detected on uvm_monitor!"
    assert "new" not in names_mon, "Overridden new() must not appear in uvm_monitor inherited list"
    for expected in ("use_uvm_seeding", "print", "uvm_report_info", "build_phase", "print_enabled", "tr_database"):
        assert expected in names_mon, f"uvm_monitor missing inherited member {expected}"
    assert names_mon.index("use_uvm_seeding") < names_mon.index("uvm_report_info") < names_mon.index("build_phase"), (
        "Oldest ancestor items (uvm_object) must appear before uvm_report_object and uvm_component!"
    )

    # uvm_sequence inherits uvm_object -> uvm_transaction -> uvm_sequence_item -> uvm_sequence_base
    anc_seq, items_seq = compute_inherited_oldest_to_newest("uvm_sequence", class_parents, class_doc_members)
    assert anc_seq == ["uvm_object", "uvm_transaction", "uvm_sequence_item", "uvm_sequence_base"], (
        f"Unexpected sequence ancestors: {anc_seq}"
    )
    seq_names = [n for _, n, _ in items_seq]
    assert "do_not_randomize" in seq_names, "uvm_sequence missing inherited variable do_not_randomize"
    assert "start" in seq_names and "print" in seq_names
    assert seq_names.index("print") < seq_names.index("do_not_randomize"), (
        "uvm_object members must appear before uvm_sequence_base members!"
    )

    # uvm_driver inherits uvm_object -> uvm_report_object -> uvm_component (and excludes its own new)
    anc_drv, items_drv = compute_inherited_oldest_to_newest("uvm_driver", class_parents, class_doc_members)
    assert anc_drv == ["uvm_object", "uvm_report_object", "uvm_component"]
    drv_names = [n for _, n, _ in items_drv]
    assert "new" not in drv_names
    assert "build_phase" in drv_names and "use_uvm_seeding" in drv_names

    print(f"  OK: uvm_monitor resolves {len(items_mon)} unique inherited items cleanly ({' -> '.join(ancestors_mon)}).")


def test_client_controller():
    print("[3/4] Testing js/page_common.js dropdown category & file:// support...")
    js = PAGE_COMMON.read_text(encoding="utf-8")
    assert "querySelectorAll('.class-hierarchy-widget[data-cname]')" in js, "Missing multi-class iteration"
    assert "window.__registerUvmDocTopics" in js, "Missing JSONP bundle loader for file://"
    assert "loadUvmDocTopics" in js, "Missing dynamic script loader"
    assert "ancestorsOldestFirst" in js, "Missing oldest-to-newest ordering"
    assert "inherited-unified-list" in js, "Missing unified list container"
    assert "inherited-filter-input" not in js, "Filter bar should not be rendered per user specification"
    assert "inherited-ancestor-group" not in js, "Parent sub-sections should not be rendered per user specification"
    assert ".slice(0, 30)" not in js, "Arbitrary 30-item truncation should be removed"

    # Verify cross-doc & source routing inside initInheritedMethodsExplorer / initLinks
    fn_start = js.find("function initInheritedMethodsExplorer()")
    fn_end = js.find("// UVM Symbol Resolution")
    fn_body = js[fn_start:fn_end]
    assert "window.parent.UVM_DATA" not in fn_body, "initInheritedMethodsExplorer must not depend on window.parent.UVM_DATA"
    assert "item.d || ancDocRaw" in fn_body, "Origin badge must point to exact item definition item.d, not class alone"
    assert "anc + '::' + item.n" in fn_body, "Origin badge should display exact class::member label"
    assert "inherited-src-badge" not in fn_body, "Redundant .sv/.svh filename badge should not be rendered"
    assert "data-doc-href" in js, "Cross-doc routing attribute missing in initLinks"
    print("  OK: Client controller verified.")


def test_css():
    print("[4/4] Testing css/style.css styles...")
    css = CSS_PATH.read_text(encoding="utf-8")
    for sel in (".inherited-unified-list", ".inherited-topic-entry", ".inherited-origin-badge"):
        assert sel in css, f"Missing CSS rule {sel}"
    print("  OK: CSS rules verified.")


if __name__ == "__main__":
    print("=" * 60)
    print("  Running Inherited Methods & Elements Verification")
    print("=" * 60)
    cp, cdm = test_bundles_and_quick_index()
    test_mro_and_ordering(cp, cdm)
    test_client_controller()
    test_css()
    print("=" * 60)
    print("  ALL INHERITED DOC VERIFICATIONS PASSED!")
    print("=" * 60)
