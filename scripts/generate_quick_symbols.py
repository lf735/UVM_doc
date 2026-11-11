#!/usr/bin/env python3
"""
generate_quick_symbols.py
Extracts an ultra-fast, compact symbol dictionary from data/uvm_source_database.json
and generates js/uvm_symbol_quick.js for instant client-side symbol resolution,
Go to Definition, Hover Tooltips, and Monaco Language Services.
"""

import json
import os
import posixpath
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "uvm_source_database.json"
SEARCH_DATA_PATH = BASE_DIR / "js" / "search_data.js"
DOCS_VIEW_DIR = BASE_DIR / "docs_view"
OUT_PATH = BASE_DIR / "js" / "uvm_symbol_quick.js"
DOC_TOPICS_DIR = BASE_DIR / "js" / "doc_topics"

TOPIC_CLASS_TO_KIND = {
    "CMethod": "method",
    "CVariable": "variable",
    "CPort": "port",
    "CType": "type",
    "CEnumeration": "enum",
    "CParameter": "parameter",
}


def load_search_doc_map() -> dict:
    """Load exact doc URLs (with anchors) from js/search_data.js if available."""
    by_exact = {}
    by_name = {}
    if not SEARCH_DATA_PATH.exists():
        return {"by_exact": by_exact, "by_name": by_name}
    try:
        sd = SEARCH_DATA_PATH.read_text(encoding="utf-8")
        idx = sd.find("[", sd.find("searchIndex"))
        if idx == -1:
            return {"by_exact": by_exact, "by_name": by_name}
        arr, _ = json.JSONDecoder().raw_decode(sd[idx:])
        for item in arr:
            name = item.get("name")
            doc = item.get("doc")
            cat = item.get("category") or ""
            itype = item.get("type") or ""
            if not name or not doc:
                continue
            by_exact[(name, cat)] = doc
            if itype == "macro":
                by_exact[(name.lstrip("`"), cat)] = doc
            if name not in by_name:
                by_name[name] = doc
    except Exception as e:
        print(f"Warning: could not parse search_data.js for doc URLs: {e}")
    return {"by_exact": by_exact, "by_name": by_name}


def fallback_doc_url(src_file: str) -> str:
    """Map source relative path to docs_view URL if file exists."""
    if not src_file:
        return ""
    candidate = src_file.replace(".svh", "-svh.html").replace(".sv", "-sv.html")
    if (DOCS_VIEW_DIR / candidate).exists():
        return f"docs_view/{candidate}"
    return ""


def clean_summary(text: str, max_chars: int = 240) -> str:
    """Clean and truncate summary text for tooltips."""
    if not text:
        return ""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    full = " ".join(lines)
    full = full.replace("<", "").replace(">", "").replace("~", "")
    if len(full) > max_chars:
        return full[:max_chars - 3] + "..."
    return full


def _extract_div_block(html_text: str, start_idx: int) -> str:
    """Extract a balanced <div ...>...</div> block starting at start_idx."""
    div_tag_re = re.compile(r'<(/?)div\b[^>]*>', re.IGNORECASE)
    depth = 0
    for m in div_tag_re.finditer(html_text, start_idx):
        if m.group(1) == '/':
            depth -= 1
            if depth == 0:
                return html_text[start_idx:m.end()]
        else:
            depth += 1
    return ""


def _rewrite_topic_html(block_html: str, rel_doc: str) -> tuple:
    """Normalize wrapper IDs, internal anchor names, and links inside a parent topic HTML block."""
    rel_dir = posixpath.dirname(rel_doc)
    src_href = ""

    # Capture primary source link from the topic heading if present
    title_src_m = re.search(
        r'<h3\b[^>]*>[\s\S]*?<a\b[^>]*href=["\']([^"\']*src_view/[^"\']+)["\']',
        block_html,
        re.IGNORECASE,
    )
    if title_src_m:
        raw_src = title_src_m.group(1)
        idx_sv = raw_src.find("src_view/")
        if idx_sv != -1:
            src_href = raw_src[idx_sv:]

    # Strip id and data-doc-topic on outer wrapper <div ...> to prevent duplicate DOM IDs
    first_gt = block_html.find(">")
    if first_gt != -1:
        outer_open = block_html[:first_gt + 1]
        outer_open = re.sub(r'\s+id="[^"]*"', "", outer_open)
        outer_open = re.sub(r'\s+data-doc-topic="[^"]*"', "", outer_open)
        block_html = outer_open + block_html[first_gt + 1:]

    # Remove NaturalDocs synthetic link IDs and heading anchor names/ids
    block_html = re.sub(r'\s+id=link\d+\b', "", block_html)
    block_html = re.sub(r'\s+id="link\d+"', "", block_html)

    def clean_h3_anchor(hm):
        h3_txt = hm.group(0)
        h3_txt = re.sub(r'\s+(?:name|id)=["\'][^"\']*["\']', "", h3_txt)
        return h3_txt

    block_html = re.sub(r'<h3\b[^>]*>[\s\S]*?</h3>', clean_h3_anchor, block_html, count=1, flags=re.IGNORECASE)

    def rewrite_href(hm):
        quote = hm.group(1)
        href_val = hm.group(2)
        if not href_val or href_val.startswith(("http://", "https://", "javascript:", "mailto:")):
            return hm.group(0)
        if href_val.startswith("#"):
            norm_url = f"docs_view/{rel_doc}{href_val}"
            return f'href={quote}__ROOT_REL__{norm_url}{quote} data-doc-href={quote}{norm_url}{quote}'
        if "src_view/" in href_val:
            tail = href_val[href_val.find("src_view/"):]
            return f'href={quote}__ROOT_REL__{tail}{quote}'
        if "examples_view/" in href_val:
            tail = href_val[href_val.find("examples_view/"):]
            return f'href={quote}__ROOT_REL__{tail}{quote}'

        path_part, sep, frag = href_val.partition("#")
        resolved = posixpath.normpath(posixpath.join(rel_dir, path_part)) if path_part else rel_doc
        if resolved.startswith("docs_view/"):
            norm_path = resolved
        else:
            norm_path = f"docs_view/{resolved}"
        norm_url = f"{norm_path}{sep}{frag}"
        return f'href={quote}__ROOT_REL__{norm_url}{quote} data-doc-href={quote}{norm_url}{quote}'

    block_html = re.sub(r'href=(["\'])([^"\']+)\1', rewrite_href, block_html)
    return block_html, src_href


def _resolve_exact_member_src(
    db: dict,
    src_lines_cache: dict,
    owner: str,
    member_name: str,
    cur_src_href: str,
) -> str:
    """
    When a topic block's source link only points to #L1 or the class header line,
    resolve the exact line of that member's implementation, declaration, or comment block.
    """
    classes = db.get("classes", {})
    cinfo = classes.get(owner, {})
    c_line = cinfo.get("start_line")
    c_file = cinfo.get("file", "")

    needs_refine = (
        not cur_src_href
        or cur_src_href.endswith("#L1")
        or (c_line and cur_src_href.endswith(f"#L{c_line}"))
    )
    if not needs_refine:
        return cur_src_href

    # 1. Check methods_index exact match on owning class
    for cand in db.get("methods_index", {}).get(member_name, []):
        if cand.get("class") == owner and cand.get("file") and cand.get("line"):
            if cand["line"] != c_line and cand["line"] > 1:
                return f"src_view/{cand['file']}.html#L{cand['line']}"

    # 2. Check class-scoped symbols_index entry
    for sym in db.get("symbols_index", []):
        sname = sym.get("short_name") or sym.get("name") or ""
        if sym.get("class") == owner and sname == member_name and sym.get("file") and sym.get("line"):
            if sym["line"] != c_line and sym["line"] > 1:
                return f"src_view/{sym['file']}.html#L{sym['line']}"

    # 3. Scan the owning .svh file for implementation, declaration, or NaturalDocs header
    target_file = c_file
    if not target_file and cur_src_href.startswith("src_view/") and ".html" in cur_src_href:
        target_file = cur_src_href[len("src_view/"):].split(".html", 1)[0]
    if target_file:
        if target_file not in src_lines_cache:
            full_src = BASE_DIR / "uvm-1.2" / "src" / target_file
            src_lines_cache[target_file] = (
                full_src.read_text(encoding="utf-8", errors="replace").splitlines()
                if full_src.exists()
                else []
            )
        lines = src_lines_cache[target_file]
        if lines:
            esc_owner = re.escape(owner)
            esc_mem = re.escape(member_name)
            pat_impl = re.compile(rf'\b(?:function|task)\b[\w\s#:,\[\]]*\b{esc_owner}\s*::\s*{esc_mem}\b')
            pat_decl = re.compile(rf'\b(?:function|task|virtual|extern|pure|protected|local|static|typedef|enum|const)\b[^\n;]*\b{esc_mem}\b')
            pat_nd = re.compile(rf'//\s*(?:Function|Task|Variable|Property|Port|Type|Enum|Enumeration|Parameter|Constant)\s*:\s*{esc_mem}\b', re.IGNORECASE)

            for idx, ln in enumerate(lines):
                if pat_impl.search(ln):
                    return f"src_view/{target_file}.html#L{idx + 1}"
            start_i = max(0, (c_line or 1) - 1)
            for idx in range(start_i, len(lines)):
                clean_ln = re.sub(r'//.*', '', lines[idx])
                if pat_decl.search(clean_ln) and not clean_ln.lstrip().startswith('class '):
                    return f"src_view/{target_file}.html#L{idx + 1}"
            for idx in range(start_i, len(lines)):
                if pat_nd.search(lines[idx]):
                    return f"src_view/{target_file}.html#L{idx + 1}"

    return cur_src_href


def build_inherited_doc_bundles(db: dict, by_exact: dict) -> tuple:
    """
    Extract real documented member topic blocks directly from docs_view/**/*.html
    and generate per-class JSONP topic modules in js/doc_topics/<class>.js.
    Returns: (class_parents, class_doc_members)
    """
    class_doc_map = {}
    topics_by_class = {}
    seen_member_names = {}
    src_lines_cache = {}

    topic_open_re = re.compile(
        r'<div class="(C(?:Method|Variable|Port|Type|Enumeration|Parameter))" '
        r'id="(doc-nav-item-[^"]+)"[^>]*data-anchor="([^"]*)"[^>]*>'
    )
    widget_re = re.compile(r'<div class="class-hierarchy-widget" data-cname="([^"]+)"')
    cclass_re = re.compile(r'<div class="CClass" id="([^"]+)"[^>]*data-anchor="([^"]*)"')

    if DOCS_VIEW_DIR.exists():
        for root, _, files in os.walk(DOCS_VIEW_DIR):
            for fname in sorted(files):
                if not fname.endswith(".html"):
                    continue
                fpath = Path(root) / fname
                rel_doc = fpath.relative_to(DOCS_VIEW_DIR).as_posix()
                try:
                    html_text = fpath.read_text(encoding="utf-8")
                except Exception:
                    continue

                # Map class -> canonical doc page + anchor from CClass wrappers
                for cm in cclass_re.finditer(html_text):
                    cid, canchor = cm.group(1), cm.group(2)
                    clean_c = re.sub(r'#\([^)]*\)', '', canchor).strip()
                    if clean_c and clean_c not in class_doc_map:
                        class_doc_map[clean_c] = f"docs_view/{rel_doc}#{cid}"

                for wm in widget_re.finditer(html_text):
                    wcname = wm.group(1).strip()
                    if wcname and wcname not in class_doc_map:
                        class_doc_map[wcname] = f"docs_view/{rel_doc}#doc-nav-main"

                # Extract documented class member topic blocks in original doc order
                for tm in topic_open_re.finditer(html_text):
                    tclass, tid, anchor = tm.group(1), tm.group(2), tm.group(3)
                    if "." not in anchor:
                        continue
                    owner_raw, member_name = anchor.split(".", 1)
                    owner = re.sub(r'#\([^)]*\)', '', owner_raw).strip()
                    member_name = member_name.strip()
                    if not owner or not member_name:
                        continue

                    raw_block = _extract_div_block(html_text, tm.start())
                    if not raw_block:
                        continue

                    norm_html, src_href = _rewrite_topic_html(raw_block, rel_doc)
                    refined_src = _resolve_exact_member_src(db, src_lines_cache, owner, member_name, src_href)
                    if refined_src and refined_src != src_href:
                        if src_href:
                            norm_html = norm_html.replace(f"__ROOT_REL__{src_href}", f"__ROOT_REL__{refined_src}", 1)
                        line_m = re.search(r'#L(\d+)$', refined_src)
                        if line_m:
                            norm_html = re.sub(r'data-src-line="[^"]*"', f'data-src-line="{line_m.group(1)}"', norm_html, count=1)
                        src_href = refined_src

                    kind = TOPIC_CLASS_TO_KIND.get(tclass, "method")
                    doc_url = f"docs_view/{rel_doc}#{tid}"

                    seen_for_owner = seen_member_names.setdefault(owner, set())
                    if member_name in seen_for_owner:
                        continue
                    seen_for_owner.add(member_name)

                    topics_by_class.setdefault(owner, []).append({
                        "n": member_name,
                        "k": kind,
                        "d": doc_url,
                        "s": src_href,
                        "h": norm_html,
                    })

    # Build lightweight classParents & classDocMembers metadata for client MRO resolution
    class_parents = {}
    for cname, cinfo in db.get("classes", {}).items():
        parent_raw = cinfo.get("parent") or cinfo.get("extends_base") or ""
        parent_clean = re.sub(r'#\([^)]*\)', '', parent_raw).strip()
        doc_url = class_doc_map.get(cname) or by_exact.get((cname, "Classes"), "")
        if not doc_url and cinfo.get("file"):
            doc_url = fallback_doc_url(cinfo.get("file", ""))
        class_parents[cname] = {
            "parent": parent_clean,
            "doc": doc_url,
        }

    # Include any class present only in class_doc_map
    for cname, durl in class_doc_map.items():
        if cname not in class_parents:
            class_parents[cname] = {"parent": "", "doc": durl}

    class_doc_members = {
        owner: [{"n": t["n"], "k": t["k"]} for t in items]
        for owner, items in topics_by_class.items()
    }

    # Write per-class JSONP modules in js/doc_topics/
    DOC_TOPICS_DIR.mkdir(parents=True, exist_ok=True)
    expected_files = set()
    for owner, items in topics_by_class.items():
        safe_name = re.sub(r'[^A-Za-z0-9_]', '_', owner)
        fname = f"{safe_name}.js"
        expected_files.add(fname)
        payload_json = json.dumps(items, separators=(',', ':'), ensure_ascii=False)
        owner_json = json.dumps(owner)
        js_body = (
            f"// UVM 1.2 Inherited Doc Topics for {owner}\n"
            f"if(window.__registerUvmDocTopics){{window.__registerUvmDocTopics({owner_json},{payload_json});}}\n"
        )
        (DOC_TOPICS_DIR / fname).write_text(js_body, encoding="utf-8")

    # Remove stale topic bundles if any
    for old_f in DOC_TOPICS_DIR.glob("*.js"):
        if old_f.name not in expected_files:
            old_f.unlink()

    print(
        f"Generated {len(expected_files)} documented topic bundles in {DOC_TOPICS_DIR} "
        f"({sum(len(v) for v in topics_by_class.values())} member docs)."
    )
    return class_parents, class_doc_members


def generate_quick_symbols():
    print(f"Loading database from {DB_PATH}...")
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    doc_maps = load_search_doc_map()
    by_exact = doc_maps["by_exact"]
    by_name = doc_maps["by_name"]

    def resolve_doc(name: str, owner: str = "", src_file: str = "") -> str:
        if owner:
            base_owner = owner.split("#", 1)[0].strip()
            for key_owner in (owner, base_owner):
                if (name, key_owner) in by_exact:
                    return by_exact[(name, key_owner)]
            for (n, c), d in by_exact.items():
                if n == name and c.split("#", 1)[0] == base_owner:
                    return d
            # For class-scoped symbols not in by_exact, stay on the owning source file's doc page
            file_doc = fallback_doc_url(src_file)
            if file_doc:
                return file_doc
        if name in by_name:
            return by_name[name]
        return fallback_doc_url(src_file)

    classes_dict = {}
    for name, c in db.get("classes", {}).items():
        doc_obj = c.get("doc", {}) or {}
        summary = clean_summary(doc_obj.get("summary") or doc_obj.get("full_text") or "")
        src_file = c.get("file", "")
        classes_dict[name] = {
            "type": "class",
            "file": src_file,
            "line": c.get("start_line", 1),
            "doc": summary,
            "doc_url": resolve_doc(name, "", src_file),
            "extends": c.get("extends_base") or "",
            "params": c.get("parameters_raw") or "",
            "is_virtual": bool(c.get("is_virtual"))
        }

    macros_dict = {}
    for raw_name, m in db.get("macros", {}).items():
        name = raw_name.lstrip("`")
        doc_obj = m.get("doc", {}) or {}
        summary = clean_summary(doc_obj.get("summary") or doc_obj.get("full_text") or "")
        src_file = m.get("file", "")
        doc_url = (
            by_exact.get((f"`{name}", "Macros"))
            or by_exact.get((name, "Macros"))
            or resolve_doc(f"`{name}", "", src_file)
            or resolve_doc(name, "", src_file)
        )
        macro_entry = {
            "type": "macro",
            "file": src_file,
            "line": m.get("start_line", 1),
            "doc": summary,
            "doc_url": doc_url,
            "args": m.get("parameters_raw") or ""
        }
        macros_dict[name] = macro_entry
        macros_dict[f"`{name}"] = macro_entry

    methods_dict = {}
    for mname, mlist in db.get("methods_index", {}).items():
        compact_list = []
        for m in mlist:
            cname = m.get("class", "")
            src_file = m.get("file", "")
            compact_list.append({
                "class": cname,
                "file": src_file,
                "line": m.get("line", 1),
                "kind": m.get("kind", "function"),
                "ret": m.get("return_type") or "void",
                "doc_url": resolve_doc(mname, cname, src_file)
            })
        if compact_list:
            methods_dict[mname] = compact_list

    # Index documented global functions/tasks from searchIndex (e.g. uvm_report_info, run_test, etc.)
    for (sname, scat), doc_url in by_exact.items():
        if scat in ("Global", "Globals") and not sname.startswith("`"):
            existing = methods_dict.setdefault(sname, [])
            if not any(e.get("class") == "Global" for e in existing):
                existing.insert(0, {
                    "class": "Global",
                    "file": "base/uvm_globals.svh",
                    "line": 1,
                    "kind": "function" if sname != "run_test" else "task",
                    "ret": "",
                    "doc_url": doc_url
                })

    constants_dict = {}
    types_dict = {}
    vars_dict = {}

    for s in db.get("symbols_index", []):
        stype = s.get("type")
        sname = s.get("short_name") or s.get("name") or ""
        if not sname:
            continue
        src_file = s.get("file", "")
        owner = s.get("class") or ""
        entry = {
            "type": stype,
            "class": owner,
            "file": src_file,
            "line": s.get("line", 1),
            "doc": clean_summary(s.get("summary") or ""),
            "doc_url": resolve_doc(sname, owner, src_file)
        }
        if stype == "constant":
            if sname not in constants_dict:
                constants_dict[sname] = entry
        elif stype in ("type", "enum"):
            if sname not in types_dict and sname not in classes_dict:
                types_dict[sname] = entry
        elif stype in ("variable", "port"):
            if sname not in vars_dict:
                vars_dict[sname] = entry

    # Ensure core UVM global variables & standard constants have reliable metadata
    core_globals = {
        "uvm_test_done": {
            "type": "variable",
            "class": "uvm_test_done_objection",
            "var_type": "uvm_objection",
            "file": "base/uvm_objection.svh",
            "line": 1118,
            "doc": "Built-in end-of-test objection singleton (uvm_test_done_objection).",
            "doc_url": resolve_doc("uvm_test_done_objection", "", "base/uvm_objection.svh")
        },
        "uvm_top": {
            "type": "variable",
            "class": "uvm_root",
            "var_type": "uvm_root",
            "file": "base/uvm_root.svh",
            "line": 71,
            "doc": "Global handle to the sole instance of uvm_root.",
            "doc_url": resolve_doc("uvm_root", "", "base/uvm_root.svh")
        }
    }
    for gname, ginfo in core_globals.items():
        vars_dict[gname] = ginfo

    class_parents, class_doc_members = build_inherited_doc_bundles(db, by_exact)

    payload = {
        "metadata": {
            "version": "UVM 1.2",
            "classes_count": len(classes_dict),
            "macros_count": len(macros_dict),
            "methods_count": len(methods_dict),
            "constants_count": len(constants_dict),
            "types_count": len(types_dict),
            "vars_count": len(vars_dict),
            "doc_classes_count": len(class_doc_members)
        },
        "classes": classes_dict,
        "macros": macros_dict,
        "methods": methods_dict,
        "constants": constants_dict,
        "types": types_dict,
        "vars": vars_dict,
        "classParents": class_parents,
        "classDocMembers": class_doc_members
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    json_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    js_content = f"// UVM 1.2 Quick Symbol Index - Auto-generated\nwindow.UVM_SYMBOLS = {json_str};\n"

    with open(OUT_PATH, "w", encoding="utf-8") as out:
        out.write(js_content)

    size_kb = round(os.path.getsize(OUT_PATH) / 1024, 1)
    print(
        f"Generated {OUT_PATH} ({size_kb} KB): {len(classes_dict)} classes, "
        f"{len(macros_dict)} macros, {len(methods_dict)} methods, "
        f"{len(constants_dict)} constants, {len(types_dict)} types, {len(vars_dict)} vars indexed."
    )


if __name__ == "__main__":
    generate_quick_symbols()

