#!/usr/bin/env python3
"""
UVM 1.2 Source Code Database Generator
Analyzes exclusive source files in uvm-1.2/src to extract:
- File hierarchy and bidirectional include graph (includes <-> included_by)
- Class hierarchy with bidirectional inheritance links (parent <-> children)
- Class methods with exact line positions (declaration & out-of-body implementation)
- Overridden method detection (bidirectional child <-> ancestor overrides)
- Functional macros (excluding include guard macros) categorized with documentation
- Dedicated DPI / C sub-database linked to SystemVerilog DPI imports
- Full comment and docstring extraction (NaturalDocs)

Outputs:
- data/uvm_source_database.json (complete, hierarchical & bidirectional JSON)
- data/uvm_source_database.sqlite (normalized relational SQLite database)
- data/uvm_dpi_database.json (dedicated DPI-C database)
"""

import os
import re
import sys
import json
import sqlite3
from pathlib import Path
from collections import defaultdict

# Root workspace paths
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "uvm-1.2" / "src"
DATA_DIR = BASE_DIR / "data"

SUBSYSTEMS = [
    'base', 'comps', 'dap', 'dpi', 'macros',
    'reg', 'seq', 'tlm1', 'tlm2', 'deprecated'
]

def clean_doc_comment(raw_lines):
    """Parse NaturalDocs or inline comments into summary and full description."""
    if not raw_lines:
        return None
    cleaned = []
    for line in raw_lines:
        l = re.sub(r'^\s*(?://|/\*|\*)\s?', '', line)
        l = re.sub(r'\*/\s*$', '', l).rstrip()
        cleaned.append(l)

    meaningful = [l for l in cleaned if not re.match(r'^[=\-_~#*|\s]{3,}$', l)]
    if not meaningful:
        return None

    title = ""
    start_idx = 0
    for idx, l in enumerate(meaningful):
        m = re.match(r'^(?:CLASS|Function|Task|MACRO|Group|Variable|Topic|TITLE):\s*(.*)', l, re.IGNORECASE)
        if m:
            title = m.group(1).strip()
            start_idx = idx + 1
            break

    body_lines = meaningful[start_idx:]
    summary_parts = []
    in_summary = False
    for l in body_lines:
        if not l.strip():
            if in_summary:
                break
            continue
        in_summary = True
        summary_parts.append(l.strip())

    summary = " ".join(summary_parts).strip()
    full_text = "\n".join(body_lines).strip()

    return {
        "title": title,
        "summary": summary,
        "full_text": full_text
    }

def is_include_guard(macro_name, file_rel_path, lines, def_line_idx):
    """Determine if a macro is an anti-double inclusion guard."""
    fname = Path(file_rel_path).name.upper().replace('.', '_').replace('-', '_')
    mname = macro_name.upper()

    if mname.endswith('_SVH') or mname.endswith('_SV') or mname.endswith('_H') or mname == fname or mname.startswith('UVM_') and mname.endswith('_SVH'):
        window_start = max(0, def_line_idx - 5)
        window = lines[window_start:def_line_idx + 1]
        for w in window:
            if re.search(rf'^\s*`ifndef\s+{re.escape(macro_name)}\b', w):
                return True
    return False

def categorize_macro(name, file_rel_path):
    """Categorize a functional macro based on its name and location."""
    lname = name.lower()
    if 'deprecated' in file_rel_path or lname.startswith('uvm_sequence_utils'):
        return 'deprecated'
    if lname.startswith(('uvm_info', 'uvm_warning', 'uvm_error', 'uvm_fatal', 'uvm_message', 'uvm_report')):
        return 'reporting'
    if 'object_utils' in lname or 'component_utils' in lname or 'field_utils' in lname:
        return 'object_utils'
    if lname.startswith('uvm_field_'):
        return 'field_automation'
    if lname.startswith(('uvm_do', 'uvm_create', 'uvm_send', 'uvm_rand_send', 'uvm_declare_p_sequencer')):
        return 'sequence'
    if '_imp_decl' in lname or '_port_decl' in lname or 'tlm' in lname:
        return 'tlm'
    if 'callback' in lname or 'register_cb' in lname:
        return 'callbacks'
    if 'reg' in lname or 'uvm_reg' in lname:
        return 'reg'
    if lname.startswith(('uvm_version', 'uvm_major', 'uvm_minor', 'uvm_fix')):
        return 'version'
    if 'phase' in lname:
        return 'phase'
    return 'misc'

def parse_parameters(param_str):
    """Parse a SystemVerilog parameter or argument list into structured objects."""
    if not param_str or not param_str.strip():
        return []
    
    items = []
    current = []
    paren_depth = 0
    bracket_depth = 0
    for char in param_str:
        if char == '(':
            paren_depth += 1
        elif char == ')':
            paren_depth -= 1
        elif char == '[':
            bracket_depth += 1
        elif char == ']':
            bracket_depth -= 1
        elif char == ',' and paren_depth == 0 and bracket_depth == 0:
            items.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        items.append("".join(current).strip())

    params = []
    last_direction = "input"
    for item in items:
        if not item:
            continue
        default_val = None
        if '=' in item:
            parts = item.split('=', 1)
            item = parts[0].strip()
            default_val = parts[1].strip()

        m_dir = re.match(r'^(input|output|inout|ref)\s+(.*)', item)
        if m_dir:
            direction = m_dir.group(1)
            item = m_dir.group(2).strip()
            last_direction = direction
        else:
            direction = last_direction

        m_id = re.search(r'([a-zA-Z0-9_]+(?:\s*\[.*?\])?)$', item)
        if m_id:
            p_name = m_id.group(1).strip()
            p_type = item[:m_id.start()].strip()
            if not p_type:
                p_type = 'untyped'
        else:
            p_name = item
            p_type = 'untyped'

        params.append({
            "direction": direction,
            "type": p_type,
            "name": p_name,
            "default": default_val
        })
    return params

def parse_doc_above(lines, line_idx):
    """Extract doc comments situated immediately above a declaration."""
    comment_lines = []
    idx = line_idx - 1
    # Allow small whitespace gap
    while idx >= 0 and not lines[idx].strip():
        idx -= 1
        if line_idx - idx > 3:
            return None

    while idx >= 0:
        l = lines[idx]
        stripped = l.strip()
        if stripped.startswith('//') or stripped.startswith('*') or stripped.startswith('/*') or stripped.endswith('*/'):
            comment_lines.insert(0, l)
            idx -= 1
        elif not stripped and comment_lines:
            # Blank line inside comment block
            comment_lines.insert(0, l)
            idx -= 1
        else:
            break

    return clean_doc_comment(comment_lines)

def build_database():
    print(f"Analyzing UVM 1.2 source files from: {SRC_DIR}")
    assert SRC_DIR.exists(), f"Source directory {SRC_DIR} does not exist"

    # Data containers
    files_db = {}
    includes_list = []
    macros_db = {}
    classes_db = {}
    out_of_body_impls = []
    dpi_imports = []
    dpi_c_functions = []

    # 1. Walk and scan all files
    all_files = sorted(list(SRC_DIR.rglob('*.*')))
    print(f"Discovered {len(all_files)} total files.")

    for fpath in all_files:
        rel_path = fpath.relative_to(SRC_DIR).as_posix()
        ext = fpath.suffix.lower()
        subsystem = rel_path.split('/')[0] if '/' in rel_path else 'root'

        try:
            content = fpath.read_text(encoding='latin-1')
        except Exception as e:
            print(f"Error reading {rel_path}: {e}")
            continue

        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for l in lines if not l.strip())
        comment_lines = sum(1 for l in lines if l.strip().startswith(('//', '/*', '*')))
        code_lines = total_lines - blank_lines - comment_lines

        # Extract file header comment
        file_header = None
        header_raw = []
        for l in lines[:40]:
            if l.strip().startswith(('//', '/*', '*')):
                header_raw.append(l)
            elif header_raw and not l.strip():
                continue
            elif header_raw:
                break
        if header_raw:
            file_header = clean_doc_comment(header_raw)

        files_db[rel_path] = {
            "path": rel_path,
            "filename": fpath.name,
            "subsystem": subsystem,
            "extension": ext,
            "lines_total": total_lines,
            "lines_code": code_lines,
            "lines_comment": comment_lines,
            "lines_blank": blank_lines,
            "is_deprecated": 'deprecated' in rel_path.lower(),
            "header_doc": file_header,
            "includes": [],
            "included_by": [],
            "classes": [],
            "macros": []
        }

        # Handle C / C++ files in DPI
        if ext in ('.c', '.cc', '.h'):
            # Parse C functions with support for multi-line, pointers, and extern/static
            for idx, line in enumerate(lines):
                line_str = line.strip()
                if line_str.startswith(('//', '/*', '*', '#')) or not line_str:
                    continue

                # Regex matching C function definitions
                m_c = re.match(
                    r'^(?:(?:extern|static|inline)\s+)*'
                    r'((?:const\s+)?(?:unsigned\s+)?[a-zA-Z0-9_]+(?:\s*\*+|\*+\s*)?)\s*'
                    r'([a-zA-Z0-9_]+)\s*\(([\s\S]*?)\)',
                    line
                )
                if m_c:
                    ret_type = m_c.group(1).strip()
                    fn_name = m_c.group(2).strip()
                    args = m_c.group(3).strip()

                    # Avoid control flow keywords (if, while, for, switch)
                    if fn_name in ('if', 'while', 'for', 'switch', 'return', 'sizeof', 'defined'):
                        continue

                    # Check simulator target from filename
                    sim_target = 'generic'
                    if 'questa' in rel_path.lower():
                        sim_target = 'questa'
                    elif 'vcs' in rel_path.lower():
                        sim_target = 'vcs'
                    elif 'inca' in rel_path.lower():
                        sim_target = 'inca'

                    doc = parse_doc_above(lines, idx)
                    dpi_c_functions.append({
                        "file": rel_path,
                        "line": idx + 1,
                        "name": fn_name,
                        "return_type": ret_type,
                        "parameters": args,
                        "simulator_target": sim_target,
                        "doc": doc
                    })
            continue

        # SystemVerilog scanning (.sv, .svh)
        i = 0
        while i < len(lines):
            line = lines[i]
            line_no = i + 1
            stripped = line.strip()

            # A. Includes: `include "..."
            m_inc = re.match(r'^\s*`include\s+["<](.*?)[\">]', line)
            if m_inc:
                target_inc = m_inc.group(1)
                # Resolve target path relative to src
                resolved = target_inc
                target_path = SRC_DIR / target_inc
                if not target_path.exists():
                    # check relative to current dir
                    cand = (fpath.parent / target_inc).resolve()
                    if cand.is_relative_to(SRC_DIR):
                        resolved = cand.relative_to(SRC_DIR).as_posix()

                includes_list.append({
                    "source": rel_path,
                    "target": target_inc,
                    "resolved": resolved,
                    "line": line_no
                })
                files_db[rel_path]["includes"].append({
                    "target": target_inc,
                    "resolved": resolved,
                    "line": line_no
                })

            # B. Macros: `define
            m_mac = re.match(r'^\s*`define\s+([a-zA-Z0-9_]+)(?:\((.*?)\))?', line)
            if m_mac and not stripped.startswith('//'):
                macro_name = m_mac.group(1)
                raw_params = m_mac.group(2)
                params_list = [p.strip() for p in raw_params.split(',')] if raw_params else []

                # Find end of macro (continuation \)
                end_line = line_no
                body_lines = [line]
                cur_i = i
                while cur_i < len(lines) and lines[cur_i].rstrip().endswith('\\'):
                    cur_i += 1
                    end_line = cur_i + 1
                    if cur_i < len(lines):
                        body_lines.append(lines[cur_i])

                # Check if it is an anti-double inclusion guard
                if is_include_guard(macro_name, rel_path, lines, i):
                    # Skip include guards from functional macro database
                    i = max(i, cur_i) + 1
                    continue

                doc = parse_doc_above(lines, i)
                category = categorize_macro(macro_name, rel_path)
                
                # Clean body snippet
                body_snippet = "\n".join([re.sub(r'\\$', '', l).strip() for l in body_lines]).strip()
                # strip `define name part
                body_snippet = re.sub(r'^`define\s+[a-zA-Z0-9_]+(?:\(.*?\))?\s*', '', body_snippet).strip()

                macro_obj = {
                    "name": macro_name,
                    "file": rel_path,
                    "start_line": line_no,
                    "end_line": end_line,
                    "parameters": params_list,
                    "parameters_raw": raw_params,
                    "category": category,
                    "body_snippet": body_snippet[:300] if body_snippet else "",
                    "is_deprecated": category == 'deprecated' or 'deprecated' in rel_path.lower(),
                    "doc": doc
                }
                macros_db[macro_name] = macro_obj
                files_db[rel_path]["macros"].append(macro_name)
                i = max(i, cur_i) + 1
                continue

            # C. DPI imports: import "DPI-C" ...
            if 'import "DPI-C"' in line:
                m_dpi = re.match(r'^\s*import\s+"DPI-C"\s+(?:context\s+)?(function|task)\s+(?:([a-zA-Z0-9_:\$\[\]]+)\s+)?([a-zA-Z0-9_]+)\s*\((.*?)\)\s*;', line)
                if m_dpi:
                    dpi_kind = m_dpi.group(1)
                    dpi_ret = m_dpi.group(2) or ("void" if dpi_kind == "function" else None)
                    dpi_name = m_dpi.group(3)
                    dpi_args = m_dpi.group(4)
                    dpi_doc = parse_doc_above(lines, i)
                    dpi_imports.append({
                        "file": rel_path,
                        "line": line_no,
                        "name": dpi_name,
                        "kind": dpi_kind,
                        "return_type": dpi_ret,
                        "parameters_raw": dpi_args,
                        "parameters": parse_parameters(dpi_args),
                        "doc": dpi_doc
                    })

            # D. Out-of-body method implementations: function/task [return_type] ClassName::MethodName(...)
            m_impl = re.match(r'^\s*(function|task)\s+(?:([\w:\[\]\$]+)\s+)?([a-zA-Z0-9_]+)::([a-zA-Z0-9_]+)\s*\(([\s\S]*?)(?:\)|$)', line)
            if m_impl and not stripped.startswith('//'):
                m_kind = m_impl.group(1)
                m_ret = m_impl.group(2) or ("void" if m_kind == "function" else None)
                c_name = m_impl.group(3)
                meth_name = m_impl.group(4)
                
                # Find start and end of this implementation
                impl_start_line = line_no
                end_token = f"end{m_kind}"
                impl_end_line = impl_start_line
                calls_super = False
                j = i + 1
                while j < len(lines):
                    l_sub = lines[j]
                    if f"super.{meth_name}" in l_sub:
                        calls_super = True
                    if re.match(rf'^\s*{end_token}\b', l_sub):
                        impl_end_line = j + 1
                        break
                    j += 1

                impl_doc = parse_doc_above(lines, i)

                out_of_body_impls.append({
                    "class_name": c_name,
                    "method_name": meth_name,
                    "kind": m_kind,
                    "return_type": m_ret,
                    "file": rel_path,
                    "start_line": impl_start_line,
                    "end_line": impl_end_line,
                    "calls_super": calls_super,
                    "doc": impl_doc
                })

            # E. Class declarations: [virtual] class ClassName ...
            m_cls = re.match(r'^\s*(virtual\s+)?class\s+([a-zA-Z0-9_]+)', line)
            if m_cls and 'typedef' not in line and not stripped.startswith('//'):
                is_virtual = bool(m_cls.group(1))
                class_name = m_cls.group(2)
                class_start_line = line_no

                # Collect full header up to ';'
                header_lines = [line]
                h_idx = i
                while ';' not in "".join(header_lines) and h_idx < len(lines) - 1:
                    h_idx += 1
                    header_lines.append(lines[h_idx])
                full_header = " ".join(header_lines)

                # Parse extends
                m_ext = re.search(r'\bextends\s+([a-zA-Z0-9_:]+)(?:\s*#\s*\((.*?)\))?', full_header)
                extends_full = None
                extends_base = None
                if m_ext:
                    extends_base = m_ext.group(1).split('::')[-1]
                    extends_full = m_ext.group(1) + (f"#({m_ext.group(2)})" if m_ext.group(2) else "")

                # Parse parameters #( ... )
                m_params = re.search(r'class\s+[a-zA-Z0-9_]+\s*#\s*\(([\s\S]*?)\)\s*(?:extends|;)', full_header)
                class_params_raw = m_params.group(1).strip() if m_params else None

                class_doc = parse_doc_above(lines, i)

                # Find matching endclass
                endclass_line = class_start_line
                class_depth = 1
                methods_in_class = {}
                k = h_idx + 1

                while k < len(lines):
                    k_line = lines[k]
                    k_no = k + 1
                    k_strip = k_line.strip()

                    # Nested class tracking
                    if re.match(r'^\s*(?:virtual\s+)?class\s+[a-zA-Z0-9_]+', k_line) and 'typedef' not in k_line and not k_strip.startswith('//'):
                        class_depth += 1

                    if re.match(r'^\s*endclass\b', k_line) and not k_strip.startswith('//'):
                        class_depth -= 1
                        if class_depth == 0:
                            endclass_line = k_no
                            break

                    # Methods declared inside class
                    m_mth = re.match(
                        r'^\s*(?:(extern|pure|virtual|local|protected|static)\s+)*'
                        r'(task|function)\s+'
                        r'(?:([\w:\[\]\$]+)\s+)?'
                        r'([a-zA-Z0-9_]+)\s*\(([\s\S]*?)(?:\)|$)',
                        k_line
                    )
                    if m_mth and not k_strip.startswith('//') and not k_strip.startswith('*') and '::' not in k_line:
                        # Extract modifiers
                        prefix = k_line[:m_mth.start(2)]
                        modifiers = re.findall(r'\b(extern|pure|virtual|local|protected|static)\b', prefix)
                        m_kind = m_mth.group(2)
                        m_ret = m_mth.group(3) or ("void" if m_kind == "function" else None)
                        m_name = m_mth.group(4)
                        m_args = m_mth.group(5)

                        # Modifiers flags
                        is_m_virtual = 'virtual' in modifiers
                        is_m_pure = 'pure' in modifiers
                        is_m_static = 'static' in modifiers
                        is_m_extern = 'extern' in modifiers
                        visibility = 'public'
                        if 'local' in modifiers:
                            visibility = 'local'
                        elif 'protected' in modifiers:
                            visibility = 'protected'

                        # Determine if inline or extern declaration
                        decl_start = k_no
                        decl_end = k_no
                        impl_file = None
                        impl_start = None
                        impl_end = None
                        is_inline = False
                        calls_super = False

                        # If multi-line arguments
                        full_decl_lines = [k_line]
                        decl_k = k
                        while ';' not in "".join(full_decl_lines) and f"end{m_kind}" not in "".join(full_decl_lines) and decl_k < len(lines) - 1:
                            decl_k += 1
                            full_decl_lines.append(lines[decl_k])
                        decl_end = decl_k + 1

                        # If not extern and not pure, find inline body
                        if not is_m_extern and not is_m_pure:
                            is_inline = True
                            impl_file = rel_path
                            impl_start = decl_start
                            # scan for endfunction/endtask
                            end_tok = f"end{m_kind}"
                            sub_k = decl_k
                            while sub_k < len(lines):
                                if f"super.{m_name}" in lines[sub_k]:
                                    calls_super = True
                                if re.match(rf'^\s*{end_tok}\b', lines[sub_k]):
                                    impl_end = sub_k + 1
                                    break
                                sub_k += 1
                            k = sub_k  # advance

                        m_doc = parse_doc_above(lines, k_no - (len(full_decl_lines) - 1))

                        methods_in_class[m_name] = {
                            "name": m_name,
                            "class": class_name,
                            "kind": m_kind,
                            "return_type": m_ret,
                            "modifiers": modifiers,
                            "visibility": visibility,
                            "is_virtual": is_m_virtual or is_m_pure,
                            "is_pure_virtual": is_m_pure,
                            "is_static": is_m_static,
                            "is_extern": is_m_extern,
                            "is_inline": is_inline,
                            "decl": {
                                "file": rel_path,
                                "start_line": decl_start,
                                "end_line": decl_end
                            },
                            "impl": {
                                "file": impl_file,
                                "start_line": impl_start,
                                "end_line": impl_end,
                                "is_inline": is_inline,
                                "calls_super": calls_super
                            } if is_inline else None,
                            "parameters": parse_parameters(m_args),
                            "parameters_raw": f"({m_args.strip()})" if (m_args and not m_args.strip().startswith('(')) else (m_args.strip() if m_args else "()"),
                            "doc": m_doc,
                            "overrides": False,
                            "overridden_from": None,
                            "root_ancestor": None,
                            "is_override_of_pure_virtual": False,
                            "overridden_by": []
                        }

                    k += 1

                classes_db[class_name] = {
                    "name": class_name,
                    "file": rel_path,
                    "start_line": class_start_line,
                    "end_line": endclass_line,
                    "is_virtual": is_virtual,
                    "parameters_raw": class_params_raw,
                    "extends_raw": extends_full,
                    "extends_base": extends_base,
                    "parent": extends_base,
                    "ancestors": [],
                    "children": [],
                    "descendants": [],
                    "depth": 0,
                    "is_deprecated": 'deprecated' in rel_path.lower(),
                    "doc": class_doc,
                    "methods": methods_in_class
                }
                files_db[rel_path]["classes"].append(class_name)
                i = k  # advance past class

            i += 1

    print(f"Initial extraction complete:")
    print(f"- Files indexed: {len(files_db)}")
    print(f"- Classes indexed: {len(classes_db)}")
    print(f"- Macros indexed: {len(macros_db)}")
    print(f"- Out-of-body implementations: {len(out_of_body_impls)}")
    print(f"- DPI imports: {len(dpi_imports)}")
    print(f"- DPI C functions: {len(dpi_c_functions)}")

    # 2. Build reverse includes: who includes who
    for inc in includes_list:
        resolved = inc["resolved"]
        if resolved in files_db:
            files_db[resolved]["included_by"].append({
                "source": inc["source"],
                "line": inc["line"]
            })

    # 3. Match out-of-body implementations with class methods
    matched_impls = 0
    for impl in out_of_body_impls:
        c_name = impl["class_name"]
        m_name = impl["method_name"]
        if c_name in classes_db and m_name in classes_db[c_name]["methods"]:
            m_entry = classes_db[c_name]["methods"][m_name]
            m_entry["impl"] = {
                "file": impl["file"],
                "start_line": impl["start_line"],
                "end_line": impl["end_line"],
                "is_inline": False,
                "calls_super": impl["calls_super"]
            }
            # Merge doc if decl had none
            if not m_entry["doc"] and impl["doc"]:
                m_entry["doc"] = impl["doc"]
            matched_impls += 1
        elif c_name in classes_db:
            # Method was implemented out-of-body without an explicit declaration found (or macro generated)
            classes_db[c_name]["methods"][m_name] = {
                "name": m_name,
                "class": c_name,
                "kind": impl["kind"],
                "return_type": impl["return_type"],
                "modifiers": [],
                "visibility": "public",
                "is_virtual": False,
                "is_pure_virtual": False,
                "is_static": False,
                "is_extern": True,
                "is_inline": False,
                "decl": {
                    "file": impl["file"],
                    "start_line": impl["start_line"],
                    "end_line": impl["start_line"]
                },
                "impl": {
                    "file": impl["file"],
                    "start_line": impl["start_line"],
                    "end_line": impl["end_line"],
                    "is_inline": False,
                    "calls_super": impl["calls_super"]
                },
                "parameters": [],
                "parameters_raw": "",
                "doc": impl["doc"],
                "overrides": False,
                "overridden_from": None,
                "root_ancestor": None,
                "is_override_of_pure_virtual": False,
                "overridden_by": []
            }
    print(f"Matched {matched_impls} out-of-body implementations to class method declarations.")

    # 4. Bidirectional Inheritance Graph Resolution
    # Build children links and compute depth / ancestors
    for cname, cinfo in classes_db.items():
        parent_name = cinfo["extends_base"]
        if parent_name and parent_name in classes_db:
            classes_db[parent_name]["children"].append(cname)

    # Sort children for consistency
    for cname, cinfo in classes_db.items():
        cinfo["children"].sort()

    # Compute ancestors, descendants, and depth
    def get_ancestors(cname, visited=None):
        if visited is None:
            visited = set()
        if cname in visited or cname not in classes_db:
            return []
        visited.add(cname)
        parent = classes_db[cname]["extends_base"]
        if not parent or parent not in classes_db:
            return [parent] if parent else []
        return [parent] + get_ancestors(parent, visited)

    def get_descendants(cname, visited=None):
        if visited is None:
            visited = set()
        if cname in visited or cname not in classes_db:
            return []
        visited.add(cname)
        desc = []
        for child in classes_db[cname]["children"]:
            desc.append(child)
            desc.extend(get_descendants(child, visited))
        return sorted(list(set(desc)))

    for cname, cinfo in classes_db.items():
        anc = get_ancestors(cname)
        cinfo["ancestors"] = anc
        cinfo["depth"] = len(anc)
        cinfo["descendants"] = get_descendants(cname)

    # 5. Method Override Resolution (Bidirectional Child <-> Ancestor)
    total_overrides = 0
    for cname, cinfo in classes_db.items():
        for mname, minfo in cinfo["methods"].items():
            # Check ancestors
            for anc_name in cinfo["ancestors"]:
                if anc_name in classes_db and mname in classes_db[anc_name]["methods"]:
                    anc_meth = classes_db[anc_name]["methods"][mname]
                    minfo["overrides"] = True
                    minfo["overridden_from"] = anc_name
                    # Find root ancestor
                    root = anc_name
                    for deep_anc in cinfo["ancestors"][cinfo["ancestors"].index(anc_name)+1:]:
                        if deep_anc in classes_db and mname in classes_db[deep_anc]["methods"]:
                            root = deep_anc
                    minfo["root_ancestor"] = root
                    minfo["is_override_of_pure_virtual"] = anc_meth["is_pure_virtual"]
                    minfo["ancestor_decl"] = {
                        "class": anc_name,
                        "file": anc_meth["decl"]["file"],
                        "line": anc_meth["decl"]["start_line"]
                    }

                    # Add reverse link to ancestor method: overridden_by
                    anc_meth["overridden_by"].append({
                        "class": cname,
                        "file": minfo["decl"]["file"],
                        "line": minfo["decl"]["start_line"],
                        "impl_line": minfo["impl"]["start_line"] if minfo["impl"] else None
                    })
                    total_overrides += 1
                    break

    print(f"Resolved {total_overrides} overridden method relationships across class hierarchies.")

    # 6. Global Inverted Indexes
    methods_index = defaultdict(list)
    overrides_index = defaultdict(lambda: {"declared_in": [], "overridden_in": []})

    for cname, cinfo in classes_db.items():
        for mname, minfo in cinfo["methods"].items():
            methods_index[mname].append({
                "class": cname,
                "kind": minfo["kind"],
                "return_type": minfo["return_type"],
                "file": minfo["decl"]["file"],
                "line": minfo["decl"]["start_line"],
                "overrides": minfo["overrides"]
            })
            if minfo["overrides"]:
                overrides_index[mname]["overridden_in"].append({
                    "class": cname,
                    "overridden_from": minfo["overridden_from"],
                    "file": minfo["decl"]["file"],
                    "line": minfo["decl"]["start_line"]
                })
            else:
                overrides_index[mname]["declared_in"].append({
                    "class": cname,
                    "file": minfo["decl"]["file"],
                    "line": minfo["decl"]["start_line"]
                })

    symbols_index = []
    for cname, cinfo in classes_db.items():
        symbols_index.append({
            "name": cname,
            "type": "class",
            "class": None,
            "file": cinfo["file"],
            "line": cinfo["start_line"],
            "summary": cinfo["doc"]["summary"] if cinfo["doc"] else ""
        })
        for mname, minfo in cinfo["methods"].items():
            symbols_index.append({
                "name": f"{cname}::{mname}",
                "short_name": mname,
                "type": minfo["kind"],
                "class": cname,
                "file": minfo["decl"]["file"],
                "line": minfo["decl"]["start_line"],
                "summary": minfo["doc"]["summary"] if minfo["doc"] else ""
            })

    for mname, minfo in macros_db.items():
        symbols_index.append({
            "name": mname,
            "type": "macro",
            "class": None,
            "file": minfo["file"],
            "line": minfo["start_line"],
            "summary": minfo["doc"]["summary"] if minfo["doc"] else ""
        })

    # 7. DPI Dedicated Database
    # Bind SystemVerilog DPI imports with C implementations
    dpi_bindings = []
    for dpi_imp in dpi_imports:
        c_matches = [cf for cf in dpi_c_functions if cf["name"] == dpi_imp["name"]]
        dpi_bindings.append({
            "sv_import": dpi_imp,
            "c_implementations": c_matches
        })

    dpi_database = {
        "metadata": {
            "title": "UVM 1.2 DPI (Direct Programming Interface) Database",
            "total_sv_imports": len(dpi_imports),
            "total_c_functions": len(dpi_c_functions),
            "total_bindings": len(dpi_bindings)
        },
        "sv_imports": dpi_imports,
        "c_functions": dpi_c_functions,
        "bindings": dpi_bindings
    }

    # 8. Main Database Object
    main_database = {
        "metadata": {
            "version": "UVM 1.2",
            "total_files": len(files_db),
            "total_classes": len(classes_db),
            "total_macros": len(macros_db),
            "total_methods": sum(len(c["methods"]) for c in classes_db.values()),
            "total_overrides": total_overrides,
            "total_symbols": len(symbols_index),
            "generated_at": "2026-10-31"
        },
        "files": files_db,
        "classes": classes_db,
        "macros": macros_db,
        "methods_index": methods_index,
        "overrides_index": overrides_index,
        "symbols_index": symbols_index,
        "dpi": dpi_database
    }

    # Ensure DATA_DIR exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 9. Write JSON Databases
    json_path = DATA_DIR / "uvm_source_database.json"
    js_path = DATA_DIR / "uvm_source_database.js"
    dpi_json_path = DATA_DIR / "uvm_dpi_database.json"

    print(f"Writing main JSON database to {json_path}...")
    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(main_database, jf, indent=2, ensure_ascii=False)

    print(f"Writing browser JS database to {js_path}...")
    with open(js_path, 'w', encoding='utf-8') as jsf:
        jsf.write("window.UVM_SOURCE_DATABASE = ")
        json.dump(main_database, jsf, indent=2, ensure_ascii=False)
        jsf.write(";\n")

    print(f"Writing DPI JSON database to {dpi_json_path}...")
    with open(dpi_json_path, 'w', encoding='utf-8') as djf:
        json.dump(dpi_database, djf, indent=2, ensure_ascii=False)

    # 10. Generate SQLite Relational Database
    sqlite_path = DATA_DIR / "uvm_source_database.sqlite"
    print(f"Building normalized SQLite database at {sqlite_path}...")
    if sqlite_path.exists():
        sqlite_path.unlink()

    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()

    # Tables DDL
    cur.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE files (
        path TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        subsystem TEXT NOT NULL,
        extension TEXT NOT NULL,
        lines_total INTEGER,
        lines_code INTEGER,
        lines_comment INTEGER,
        lines_blank INTEGER,
        is_deprecated INTEGER,
        header_summary TEXT,
        header_full TEXT
    );

    CREATE TABLE file_includes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_file TEXT NOT NULL,
        target_include TEXT NOT NULL,
        resolved_target TEXT,
        line_no INTEGER,
        FOREIGN KEY(source_file) REFERENCES files(path)
    );

    CREATE TABLE classes (
        name TEXT PRIMARY KEY,
        file TEXT NOT NULL,
        start_line INTEGER,
        end_line INTEGER,
        is_virtual INTEGER,
        parameters_raw TEXT,
        extends_raw TEXT,
        extends_base TEXT,
        parent TEXT,
        depth INTEGER,
        is_deprecated INTEGER,
        doc_summary TEXT,
        doc_full TEXT,
        ancestors_json TEXT,
        children_json TEXT,
        descendants_json TEXT,
        FOREIGN KEY(file) REFERENCES files(path)
    );

    CREATE TABLE class_methods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT NOT NULL,
        name TEXT NOT NULL,
        kind TEXT NOT NULL,
        return_type TEXT,
        modifiers TEXT,
        visibility TEXT,
        is_virtual INTEGER,
        is_pure_virtual INTEGER,
        is_static INTEGER,
        is_extern INTEGER,
        is_inline INTEGER,
        decl_file TEXT,
        decl_start_line INTEGER,
        decl_end_line INTEGER,
        impl_file TEXT,
        impl_start_line INTEGER,
        impl_end_line INTEGER,
        calls_super INTEGER,
        overrides INTEGER,
        overridden_from TEXT,
        root_ancestor TEXT,
        is_override_of_pure_virtual INTEGER,
        parameters_raw TEXT,
        parameters_json TEXT,
        doc_summary TEXT,
        doc_full TEXT,
        FOREIGN KEY(class_name) REFERENCES classes(name),
        FOREIGN KEY(decl_file) REFERENCES files(path)
    );

    CREATE TABLE method_overrides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_class TEXT NOT NULL,
        ancestor_class TEXT NOT NULL,
        method_name TEXT NOT NULL,
        decl_file TEXT,
        decl_line INTEGER,
        impl_line INTEGER,
        FOREIGN KEY(child_class) REFERENCES classes(name)
    );

    CREATE TABLE macros (
        name TEXT PRIMARY KEY,
        file TEXT NOT NULL,
        start_line INTEGER,
        end_line INTEGER,
        parameters_raw TEXT,
        parameters_json TEXT,
        category TEXT NOT NULL,
        is_deprecated INTEGER,
        body_snippet TEXT,
        doc_summary TEXT,
        doc_full TEXT,
        FOREIGN KEY(file) REFERENCES files(path)
    );

    CREATE TABLE dpi_functions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        source_type TEXT NOT NULL, -- 'sv_import' or 'c_function'
        file TEXT NOT NULL,
        line INTEGER,
        kind TEXT,
        return_type TEXT,
        parameters_raw TEXT,
        doc_summary TEXT
    );

    CREATE TABLE symbols_index (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        short_name TEXT,
        type TEXT NOT NULL,
        class_name TEXT,
        file TEXT NOT NULL,
        line INTEGER,
        summary TEXT
    );

    CREATE INDEX idx_files_subsystem ON files(subsystem);
    CREATE INDEX idx_classes_extends ON classes(extends_base);
    CREATE INDEX idx_classes_depth ON classes(depth);
    CREATE INDEX idx_methods_class ON class_methods(class_name);
    CREATE INDEX idx_methods_name ON class_methods(name);
    CREATE INDEX idx_methods_overrides ON class_methods(overrides);
    CREATE INDEX idx_macros_category ON macros(category);
    CREATE INDEX idx_symbols_name ON symbols_index(name);
    CREATE INDEX idx_symbols_type ON symbols_index(type);
    """)

    # Populate files
    for f in files_db.values():
        cur.execute("""
            INSERT INTO files VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f["path"], f["filename"], f["subsystem"], f["extension"],
            f["lines_total"], f["lines_code"], f["lines_comment"], f["lines_blank"],
            1 if f["is_deprecated"] else 0,
            f["header_doc"]["summary"] if f["header_doc"] else None,
            f["header_doc"]["full_text"] if f["header_doc"] else None
        ))

    # Populate file includes
    for inc in includes_list:
        cur.execute("""
            INSERT INTO file_includes (source_file, target_include, resolved_target, line_no)
            VALUES (?, ?, ?, ?)
        """, (inc["source"], inc["target"], inc["resolved"], inc["line"]))

    # Populate classes
    for c in classes_db.values():
        cur.execute("""
            INSERT INTO classes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c["name"], c["file"], c["start_line"], c["end_line"],
            1 if c["is_virtual"] else 0,
            c["parameters_raw"], c["extends_raw"], c["extends_base"],
            c["parent"], c["depth"], 1 if c["is_deprecated"] else 0,
            c["doc"]["summary"] if c["doc"] else None,
            c["doc"]["full_text"] if c["doc"] else None,
            json.dumps(c["ancestors"]),
            json.dumps(c["children"]),
            json.dumps(c["descendants"])
        ))

        # Populate class methods
        for m in c["methods"].values():
            cur.execute("""
                INSERT INTO class_methods (
                    class_name, name, kind, return_type, modifiers, visibility,
                    is_virtual, is_pure_virtual, is_static, is_extern, is_inline,
                    decl_file, decl_start_line, decl_end_line,
                    impl_file, impl_start_line, impl_end_line, calls_super,
                    overrides, overridden_from, root_ancestor, is_override_of_pure_virtual,
                    parameters_raw, parameters_json, doc_summary, doc_full
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c["name"], m["name"], m["kind"], m["return_type"],
                ",".join(m["modifiers"]), m["visibility"],
                1 if m["is_virtual"] else 0, 1 if m["is_pure_virtual"] else 0,
                1 if m["is_static"] else 0, 1 if m["is_extern"] else 0,
                1 if m["is_inline"] else 0,
                m["decl"]["file"], m["decl"]["start_line"], m["decl"]["end_line"],
                m["impl"]["file"] if m["impl"] else None,
                m["impl"]["start_line"] if m["impl"] else None,
                m["impl"]["end_line"] if m["impl"] else None,
                1 if (m["impl"] and m["impl"]["calls_super"]) else 0,
                1 if m["overrides"] else 0,
                m["overridden_from"], m["root_ancestor"],
                1 if m["is_override_of_pure_virtual"] else 0,
                m["parameters_raw"], json.dumps(m["parameters"]),
                m["doc"]["summary"] if m["doc"] else None,
                m["doc"]["full_text"] if m["doc"] else None
            ))

            # Populate method overrides table
            if m["overrides"]:
                cur.execute("""
                    INSERT INTO method_overrides (child_class, ancestor_class, method_name, decl_file, decl_line, impl_line)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    c["name"], m["overridden_from"], m["name"],
                    m["decl"]["file"], m["decl"]["start_line"],
                    m["impl"]["start_line"] if m["impl"] else None
                ))

    # Populate macros
    for m in macros_db.values():
        cur.execute("""
            INSERT INTO macros VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m["name"], m["file"], m["start_line"], m["end_line"],
            m["parameters_raw"], json.dumps(m["parameters"]),
            m["category"], 1 if m["is_deprecated"] else 0,
            m["body_snippet"],
            m["doc"]["summary"] if m["doc"] else None,
            m["doc"]["full_text"] if m["doc"] else None
        ))

    # Populate DPI functions
    for dpi_sv in dpi_imports:
        cur.execute("""
            INSERT INTO dpi_functions (name, source_type, file, line, kind, return_type, parameters_raw, doc_summary)
            VALUES (?, 'sv_import', ?, ?, ?, ?, ?, ?)
        """, (
            dpi_sv["name"], dpi_sv["file"], dpi_sv["line"], dpi_sv["kind"],
            dpi_sv["return_type"], dpi_sv["parameters_raw"],
            dpi_sv["doc"]["summary"] if dpi_sv["doc"] else None
        ))

    for dpi_c in dpi_c_functions:
        cur.execute("""
            INSERT INTO dpi_functions (name, source_type, file, line, kind, return_type, parameters_raw, doc_summary)
            VALUES (?, 'c_function', ?, ?, 'function', ?, ?, ?)
        """, (
            dpi_c["name"], dpi_c["file"], dpi_c["line"],
            dpi_c["return_type"], dpi_c["parameters"],
            dpi_c["doc"]["summary"] if dpi_c["doc"] else None
        ))

    # Populate symbols index
    for s in symbols_index:
        cur.execute("""
            INSERT INTO symbols_index (name, short_name, type, class_name, file, line, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            s["name"], s.get("short_name"), s["type"], s.get("class"),
            s["file"], s["line"], s.get("summary")
        ))

    conn.commit()
    conn.close()

    print(f"SQLite database built successfully: {sqlite_path}")
    print("\nSummary Statistics:")
    print(f"- Total Files: {len(files_db)}")
    print(f"- Total Classes: {len(classes_db)}")
    print(f"- Total Macros (excluding include guards): {len(macros_db)}")
    print(f"- Total Class Methods: {sum(len(c['methods']) for c in classes_db.values())}")
    print(f"- Total Overridden Methods: {total_overrides}")
    print(f"- Total Indexed Symbols: {len(symbols_index)}")
    print(f"- DPI SV Imports: {len(dpi_imports)}, C Functions: {len(dpi_c_functions)}")

if __name__ == "__main__":
    build_database()
