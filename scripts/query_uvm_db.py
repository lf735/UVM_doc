#!/usr/bin/env python3
"""
UVM 1.2 Database CLI Explorer & Query Tool
Allows rapid terminal navigation and queries across UVM 1.2 sources:
- stats: overview metrics of classes, methods, overrides, macros
- class <name>: inspect class details, inheritance, and methods (defined vs overridden)
- hierarchy <name>: visual tree of inheritance (ancestors & descendants)
- overrides <method_name>: list all classes overriding a specific method
- method <class>::<method>: detailed method signature, decl/impl lines, and doc
- macro <name>: macro definition, arguments, category, lines, and doc
- file <path>: file subsystem, includes graph (in/out), classes, and macros
- dpi: list all SystemVerilog DPI imports and matching C implementations
- search <query>: full-text search across symbols, docstrings, and categories
"""

import sys
import json
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


BASE_DIR = Path(__file__).resolve().parent.parent
DB_JSON_PATH = BASE_DIR / "data" / "uvm_source_database.json"

def load_db():
    if not DB_JSON_PATH.exists():
        print(f"Error: Database file not found at {DB_JSON_PATH}")
        print("Please run 'python scripts/build_uvm_source_db.py' first.")
        sys.exit(1)
    with open(DB_JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def show_stats(db):
    meta = db["metadata"]
    print("=" * 65)
    print(f"  UVM 1.2 Source Code Database Statistics")
    print("=" * 65)
    print(f"Total Source Files      : {meta['total_files']} (145 SV/SVH, 10 C/DPI)")
    print(f"Total Classes Indexed   : {meta['total_classes']}")
    print(f"Total Macros Indexed    : {meta['total_macros']} (excluding include guards)")
    print(f"Total Class Methods     : {meta['total_methods']}")
    print(f"Total Method Overrides  : {meta['total_overrides']}")
    print(f"Total Indexed Symbols   : {meta['total_symbols']}")
    print(f"DPI SV Imports          : {len(db['dpi']['sv_imports'])}")
    print(f"DPI C/C++ Functions     : {len(db['dpi']['c_functions'])}")
    print("-" * 65)
    
    # Subsystem breakdown
    subsys_counts = {}
    for f in db["files"].values():
        s = f["subsystem"]
        subsys_counts[s] = subsys_counts.get(s, 0) + 1
    print("Files by Subsystem:")
    for s, count in sorted(subsys_counts.items(), key=lambda x: -x[1]):
        print(f"  - {s:<12}: {count:>3} files")
    
    # Macro categories
    cat_counts = {}
    for m in db["macros"].values():
        c = m["category"]
        cat_counts[c] = cat_counts.get(c, 0) + 1
    print("\nMacros by Category:")
    for c, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  - {c:<16}: {count:>3} macros")
    print("=" * 65)

def show_class(db, class_name):
    classes = db["classes"]
    if class_name not in classes:
        # Case insensitive fallback
        matches = [c for c in classes if c.lower() == class_name.lower()]
        if matches:
            class_name = matches[0]
        else:
            print(f"Class '{class_name}' not found.")
            similar = [c for c in classes if class_name.lower() in c.lower()][:5]
            if similar:
                print(f"Did you mean: {', '.join(similar)}?")
            return

    c = classes[class_name]
    print("=" * 70)
    kind_str = "virtual class" if c["is_virtual"] else "class"
    print(f"{kind_str.upper()}: {c['name']}")
    print("=" * 70)
    print(f"Location    : {c['file']} (Lines {c['start_line']} - {c['end_line']})")
    if c.get("parameters_raw"):
        print(f"Parameters  : #({c['parameters_raw']})")
    print(f"Extends     : {c['extends_raw'] or 'None (Root class)'}")
    print(f"Depth       : {c['depth']}")
    
    # Lineage
    if c["ancestors"]:
        print(f"Ancestors   : {' -> '.join(c['ancestors'])}")
    if c["children"]:
        print(f"Direct Child: {', '.join(c['children'])}")
    print(f"Descendants : {len(c['descendants'])} total derived classes")

    if c.get("doc"):
        print("\nDescription:")
        print(f"  {c['doc']['summary']}")

    # Partition methods
    methods = c["methods"]
    defined = []
    overridden = []
    for mname, m in methods.items():
        if m["overrides"]:
            overridden.append(m)
        else:
            defined.append(m)

    print(f"\n--- Methods Defined in {c['name']} ({len(defined)}) ---")
    for m in sorted(defined, key=lambda x: x["name"]):
        mods = " ".join(m["modifiers"])
        if mods: mods += " "
        ret = f"{m['return_type']} " if m['return_type'] else ""
        impl_info = f"[impl L{m['impl']['start_line']}]" if m.get("impl") and not m["is_inline"] else ("[inline]" if m["is_inline"] else "[pure virtual]")
        print(f"  {m['kind']:<8} {mods}{ret}{m['name']}{m['parameters_raw']}  {impl_info}")
        if m.get("doc") and m["doc"].get("summary"):
            print(f"           Doc: {m['doc']['summary']}")

    print(f"\n--- Methods Overridden from Ancestors ({len(overridden)}) ---")
    for m in sorted(overridden, key=lambda x: x["name"]):
        mods = " ".join(m["modifiers"])
        if mods: mods += " "
        ret = f"{m['return_type']} " if m['return_type'] else ""
        from_str = f"(overrides {m['overridden_from']})"
        if m.get("is_override_of_pure_virtual"):
            from_str += " [implements pure virtual]"
        impl_info = f"[impl L{m['impl']['start_line']}]" if m.get("impl") and not m["is_inline"] else ("[inline]" if m["is_inline"] else "")
        print(f"  {m['kind']:<8} {mods}{ret}{m['name']}{m['parameters_raw']}  {from_str} {impl_info}")

    print("=" * 70)

def show_hierarchy(db, class_name):
    classes = db["classes"]
    if class_name not in classes:
        matches = [c for c in classes if c.lower() == class_name.lower()]
        if matches: class_name = matches[0]
        else:
            print(f"Class '{class_name}' not found.")
            return

    c = classes[class_name]
    print("\n--- Ascendance (Parents) ---")
    anc = c["ancestors"][::-1]  # from root to parent
    indent = 0
    for a in anc:
        print(f"{'  ' * indent}▲ {a}")
        indent += 1
    print(f"{'  ' * indent}● \033[1m{class_name}\033[0m (Current Class, Depth {c['depth']})")

    print("\n--- Descendance (Children) ---")
    def print_children(c_node, level):
        ch = classes[c_node]["children"]
        for child in ch:
            print(f"{'  ' * level}▼ {child}")
            print_children(child, level + 1)
    print_children(class_name, 1)
    print()

def show_overrides(db, method_name):
    overrides_idx = db["overrides_index"]
    mname = method_name.strip()
    if mname not in overrides_idx:
        matches = [m for m in overrides_idx if m.lower() == mname.lower()]
        if matches: mname = matches[0]
        else:
            print(f"No method overrides found for '{mname}'.")
            similar = [m for m in overrides_idx if mname.lower() in m.lower()][:5]
            if similar:
                print(f"Did you mean: {', '.join(similar)}?")
            return

    entry = overrides_idx[mname]
    declared = entry.get("declared_in", [])
    overridden = entry.get("overridden_in", [])

    print("=" * 70)
    print(f"Method Override Analysis for: '{mname}'")
    print("=" * 70)
    print(f"Originally Introduced in:")
    for d in declared:
        print(f"  - {d['class']}  ({d['file']}#L{d['line']})")

    print(f"\nOverridden in {len(overridden)} Derived Classes:")
    for o in sorted(overridden, key=lambda x: x["class"]):
        print(f"  - {o['class']:<30} (overridden from {o['overridden_from']:<20}) at {o['file']}#L{o['line']}")
    print("=" * 70)

def show_macro(db, macro_name):
    macros = db["macros"]
    mname = macro_name.strip().lstrip('`')
    if mname not in macros:
        matches = [m for m in macros if m.lower() == mname.lower()]
        if matches: mname = matches[0]
        else:
            print(f"Macro '`{mname}' not found.")
            similar = [m for m in macros if mname.lower() in m.lower()][:5]
            if similar:
                print(f"Did you mean: {', '.join(['`' + s for s in similar])}?")
            return

    m = macros[mname]
    print("=" * 70)
    print(f"MACRO: `{m['name']}")
    print("=" * 70)
    print(f"Location    : {m['file']} (Lines {m['start_line']} - {m['end_line']})")
    print(f"Category    : {m['category']}")
    print(f"Deprecated  : {'Yes' if m['is_deprecated'] else 'No'}")
    if m.get("parameters"):
        print(f"Parameters  : ({', '.join(m['parameters'])})")
    else:
        print(f"Parameters  : (None)")

    if m.get("doc"):
        print("\nDocumentation:")
        print(f"  {m['doc']['summary']}")
        if m['doc'].get('full_text'):
            print(f"\n  Details:\n  {m['doc']['full_text']}")

    if m.get("body_snippet"):
        print(f"\nDefinition Snippet:")
        for line in m["body_snippet"].splitlines()[:10]:
            print(f"  | {line}")
    print("=" * 70)

def show_file(db, file_query):
    files = db["files"]
    f_match = None
    for fpath in files:
        if file_query.lower() in fpath.lower():
            f_match = fpath
            break
    if not f_match:
        print(f"File matching '{file_query}' not found.")
        return

    f = files[f_match]
    print("=" * 70)
    print(f"FILE: {f['path']}")
    print("=" * 70)
    print(f"Subsystem   : {f['subsystem']}")
    print(f"Lines Total : {f['lines_total']} (Code: {f['lines_code']}, Comments: {f['lines_comment']}, Blank: {f['lines_blank']})")
    print(f"Deprecated  : {'Yes' if f['is_deprecated'] else 'No'}")

    if f.get("header_doc"):
        print("\nHeader Summary:")
        print(f"  {f['header_doc']['summary']}")

    if f["includes"]:
        print(f"\nIncludes ({len(f['includes'])}):")
        for inc in f["includes"]:
            print(f"  -> {inc['resolved']} (Line {inc['line']})")

    if f["included_by"]:
        print(f"\nIncluded By ({len(f['included_by'])}):")
        for inc in f["included_by"]:
            print(f"  <- {inc['source']} (Line {inc['line']})")

    if f["classes"]:
        print(f"\nClasses Defined ({len(f['classes'])}):")
        print(f"  {', '.join(f['classes'])}")

    if f["macros"]:
        print(f"\nMacros Defined ({len(f['macros'])}):")
        print(f"  {', '.join(['`' + m for m in f['macros']])}")
    print("=" * 70)

def show_dpi(db):
    dpi = db["dpi"]
    print("=" * 70)
    print("UVM 1.2 Direct Programming Interface (DPI-C) Catalog")
    print("=" * 70)
    print(f"Total SV Imports   : {len(dpi['sv_imports'])}")
    print(f"Total C Functions  : {len(dpi['c_functions'])}")
    print(f"Total Bindings     : {len(dpi['bindings'])}\n")

    for b in dpi["bindings"]:
        sv = b["sv_import"]
        c_list = b["c_implementations"]
        print(f"SystemVerilog: {sv['kind']} {sv['return_type']} {sv['name']}({sv['parameters_raw']})")
        print(f"  Declared in: {sv['file']}#L{sv['line']}")
        if c_list:
            print(f"  C Implementation(s):")
            for c in c_list:
                print(f"    - {c['name']} in {c['file']}#L{c['line']} (return: {c['return_type']})")
        else:
            print(f"  C Implementation(s): External simulator runtime or generic PLI")
        print("-" * 65)

def search_symbols(db, query):
    q = query.lower()
    symbols = db["symbols_index"]
    results = [s for s in symbols if q in s["name"].lower() or (s.get("summary") and q in s["summary"].lower())]
    print("=" * 70)
    print(f"Search results for '{query}' ({len(results)} matches):")
    print("=" * 70)
    for r in results[:25]:
        loc = f"{r['file']}#L{r['line']}"
        sum_str = f" - {r['summary'][:60]}..." if r.get('summary') else ""
        print(f"[{r['type'].upper():<8}] {r['name']:<35} ({loc}){sum_str}")
    if len(results) > 25:
        print(f"... and {len(results) - 25} more matches.")
    print("=" * 70)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()
    db = load_db()

    if cmd == "stats":
        show_stats(db)
    elif cmd == "class" and len(sys.argv) >= 3:
        show_class(db, sys.argv[2])
    elif cmd in ("hierarchy", "tree") and len(sys.argv) >= 3:
        show_hierarchy(db, sys.argv[2])
    elif cmd == "overrides" and len(sys.argv) >= 3:
        show_overrides(db, sys.argv[2])
    elif cmd == "macro" and len(sys.argv) >= 3:
        show_macro(db, sys.argv[2])
    elif cmd == "file" and len(sys.argv) >= 3:
        show_file(db, sys.argv[2])
    elif cmd == "dpi":
        show_dpi(db)
    elif cmd == "search" and len(sys.argv) >= 3:
        search_symbols(db, " ".join(sys.argv[2:]))
    else:
        print(f"Unknown command or missing argument: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
