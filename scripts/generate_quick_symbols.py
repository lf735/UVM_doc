#!/usr/bin/env python3
"""
generate_quick_symbols.py
Extracts an ultra-fast, compact symbol dictionary from data/uvm_source_database.json
and generates js/uvm_symbol_quick.js for instant client-side symbol resolution,
Go to Definition, Hover Tooltips, and Monaco Language Services.
"""

import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "uvm_source_database.json"
SEARCH_DATA_PATH = BASE_DIR / "js" / "search_data.js"
DOCS_VIEW_DIR = BASE_DIR / "docs_view"
OUT_PATH = BASE_DIR / "js" / "uvm_symbol_quick.js"


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

    payload = {
        "metadata": {
            "version": "UVM 1.2",
            "classes_count": len(classes_dict),
            "macros_count": len(macros_dict),
            "methods_count": len(methods_dict),
            "constants_count": len(constants_dict),
            "types_count": len(types_dict),
            "vars_count": len(vars_dict)
        },
        "classes": classes_dict,
        "macros": macros_dict,
        "methods": methods_dict,
        "constants": constants_dict,
        "types": types_dict,
        "vars": vars_dict
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

