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
OUT_PATH = BASE_DIR / "js" / "uvm_symbol_quick.js"


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

    classes_dict = {}
    for name, c in db.get("classes", {}).items():
        doc_obj = c.get("doc", {}) or {}
        summary = clean_summary(doc_obj.get("summary") or doc_obj.get("full_text") or "")
        classes_dict[name] = {
            "type": "class",
            "file": c.get("file", ""),
            "line": c.get("start_line", 1),
            "doc": summary,
            "extends": c.get("extends_base") or "",
            "params": c.get("parameters_raw") or "",
            "is_virtual": bool(c.get("is_virtual"))
        }

    macros_dict = {}
    for raw_name, m in db.get("macros", {}).items():
        name = raw_name.lstrip("`")
        doc_obj = m.get("doc", {}) or {}
        summary = clean_summary(doc_obj.get("summary") or doc_obj.get("full_text") or "")
        macro_entry = {
            "type": "macro",
            "file": m.get("file", ""),
            "line": m.get("start_line", 1),
            "doc": summary,
            "args": m.get("parameters_raw") or ""
        }
        macros_dict[name] = macro_entry
        macros_dict[f"`{name}"] = macro_entry

    methods_dict = {}
    for mname, mlist in db.get("methods_index", {}).items():
        compact_list = []
        for m in mlist:
            compact_list.append({
                "class": m.get("class", ""),
                "file": m.get("file", ""),
                "line": m.get("line", 1),
                "kind": m.get("kind", "function"),
                "ret": m.get("return_type") or "void"
            })
        if compact_list:
            methods_dict[mname] = compact_list

    payload = {
        "metadata": {
            "version": "UVM 1.2",
            "classes_count": len(classes_dict),
            "macros_count": len(macros_dict),
            "methods_count": len(methods_dict)
        },
        "classes": classes_dict,
        "macros": macros_dict,
        "methods": methods_dict
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    json_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    js_content = f"// UVM 1.2 Quick Symbol Index - Auto-generated\nwindow.UVM_SYMBOLS = {json_str};\n"

    with open(OUT_PATH, "w", encoding="utf-8") as out:
        out.write(js_content)

    size_kb = round(os.path.getsize(OUT_PATH) / 1024, 1)
    print(f"Generated {OUT_PATH} ({size_kb} KB): {len(classes_dict)} classes, {len(macros_dict)} macros, {len(methods_dict)} methods indexed.")


if __name__ == "__main__":
    generate_quick_symbols()

