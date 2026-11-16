#!/usr/bin/env python3
"""
UVM 1.2 Documentation Graph-Enhanced Hierarchical RAG Generator (V2)
Supports:
- Surgical HTML cleaning (removes NaturalDocs navigation chrome, breadcrumbs, and TOC noise)
- Level 1: Parent Macro-Segments (Classes & Conceptual Architecture Guides) ~2,500 chars
- Level 2: Child Functional Chunks (Methods, Tasks, Macros, Subsections) ~800-1,200 chars
- Hybrid Semantic Enrichment:
  * Deterministic AST enrichment from data/uvm_source_database.json (inheritance, overrides, signatures, macros)
  * Co-occurrence & API coverage from examples_view/ and docs_view/overviews/
  * Curated domain intents & synonyms from config/rag_intent_catalog.json
- Lightweight Relational Graph Export: data/rag_graph.json (<= 400 KB) for client-side routing,
  dynamic inheritance resolution, edge score propagation, and Context Bundle assembly.
- Multi-Model Vector Store Alignment: computes matching vector binaries for all active models
  defined in config/rag_models.json (MiniLM-L6, BGE-Small-EN, BGE-Micro).
"""

import os
import re
import sys
import html
import json
import math
import struct
import argparse
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_VIEW_DIR = BASE_DIR / "docs_view"
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
SOURCE_DB_FILE = DATA_DIR / "uvm_source_database.json"

UVM_IDENT_RE = re.compile(r'\b(uvm_[a-z0-9_]+)\b')
UVM_MACRO_RE = re.compile(r'`(uvm_[a-z0-9_]+)\b')


def clean_html(raw_html: str) -> str:
    """Strip HTML tags, NaturalDocs navigation chrome, unescape entities, and normalize whitespace."""
    if not raw_html:
        return ""
    text = re.sub(r'<(script|style)\b[^>]*>[\s\S]*?</\1>', ' ', raw_html, flags=re.IGNORECASE)
    # Strip Summary table blocks entirely
    text = re.sub(r'<!--START_ND_SUMMARY[\s\S]*?<!--END_ND_SUMMARY-->', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<div class=["\']?Summary["\']?[\s\S]*?</table>\s*</div>\s*</div>', ' ', text, flags=re.IGNORECASE)
    # Strip NaturalDocs header breadcrumbs / page nav chrome
    text = re.sub(r'<div[^>]*class=["\']?(?:NDHeader|Breadcrumbs|PageNav|OnThisPage|TOC|NavBar)[^"\']*["\']?[^>]*>[\s\S]*?</div>', ' ', text, flags=re.IGNORECASE)
    # Replace block breaks with space
    text = re.sub(r'<(br|p|div|tr|li|h[1-6])\b[^>]*>', ' ', text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Unescape entities
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text).strip()

    # Surgical NaturalDocs text-level chrome removal
    text = re.sub(r'^.*?\bUVM 1\.2 Documentation\s+Home\s*/\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^.*?\bSource:\s*src/[^\s]+\s*', '', text)
    text = re.sub(r'\bOn this page\s+Collapse all\b', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:Collapse all|Expand all|On this page)\b', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text


def load_intents():
    """Load curated domain intent catalog."""
    catalog_file = CONFIG_DIR / "rag_intent_catalog.json"
    if not catalog_file.exists():
        print("Notice: config/rag_intent_catalog.json not found, proceeding without domain intent injection.")
        return []
    try:
        with open(catalog_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        entries = data.get("entries", [])
        print(f"Loaded {len(entries)} domain intent entries from config/rag_intent_catalog.json.")
        return entries
    except Exception as e:
        print(f"Warning: Could not parse intent catalog: {e}")
        return []


def load_source_db():
    """Load AST/relational source database from data/uvm_source_database.json."""
    if not SOURCE_DB_FILE.exists():
        print(f"Warning: {SOURCE_DB_FILE} not found; AST graph enrichment will be limited.")
        return {"classes": {}, "macros": {}, "files": {}}
    try:
        with open(SOURCE_DB_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
        print(f"Loaded AST source DB: {len(db.get('classes', {}))} classes, {len(db.get('macros', {}))} macros.")
        return db
    except Exception as e:
        print(f"Warning: Could not parse {SOURCE_DB_FILE}: {e}")
        return {"classes": {}, "macros": {}, "files": {}}


def match_intents(identifier_str, catalog, max_intents=4, max_synonyms=8):
    """Find matching intent keywords for an identifier (class name, file name, topic)."""
    id_lower = identifier_str.lower().replace("-", "_").replace(".", "_")
    matched_intents = []
    matched_synonyms = []
    for entry in catalog:
        for pat in entry.get("patterns", []):
            pat_clean = pat.lower().replace("-", "_")
            if pat_clean in id_lower:
                matched_intents.extend(entry.get("intents", []))
                matched_synonyms.extend(entry.get("synonyms", []))
                break
    return list(dict.fromkeys(matched_intents))[:max_intents], list(dict.fromkeys(matched_synonyms))[:max_synonyms]


def format_method_sig(method_info: dict) -> str:
    """Build a concise SystemVerilog signature string from AST method info."""
    if not method_info:
        return ""
    mods = []
    if method_info.get("is_pure_virtual"):
        mods.append("pure virtual")
    elif method_info.get("is_virtual"):
        mods.append("virtual")
    if method_info.get("is_static"):
        mods.append("static")
    kind = method_info.get("kind", "function")
    ret = method_info.get("return_type", "")
    name = method_info.get("name", "")
    params = method_info.get("parameters_raw", "()")
    prefix = " ".join(mods)
    parts = [p for p in [prefix, kind, ret, f"{name}{params}"] if p]
    return " ".join(parts)


def extract_chunks_and_graph():
    """Extract hierarchical semantic chunks and build lightweight relational graph."""
    print("Extracting V2 graph-enhanced hierarchical chunks from docs_view/, examples_view/, and AST...")
    if not DOCS_VIEW_DIR.exists():
        raise FileNotFoundError(f"docs_view directory not found at {DOCS_VIEW_DIR}")

    catalog = load_intents()
    source_db = load_source_db()
    db_classes = source_db.get("classes", {})
    db_macros = source_db.get("macros", {})
    db_files = source_db.get("files", {})

    chunks = []
    parent_count = 0
    child_count = 0

    # Graph tracking structures
    class_to_chunk = {}       # class_name -> { chunkId, docUrl, category }
    methods_index = defaultdict(list)  # method_name -> [{ class, chunkId, kind, virtual, pureVirtual, sig, docUrl }]
    macro_to_chunk = {}       # `macro_name -> { chunkId, docUrl }
    examples_meta = {}        # docUrl -> { chunkId, title, apis, difficulty, category }
    overview_meta = {}        # docUrl -> { chunkId, title, apis }
    api_to_overviews = defaultdict(list)
    api_to_examples = defaultdict(list)
    co_occurrence = defaultdict(lambda: defaultdict(int))

    # 1. Process Overviews (Highest Conceptual Architecture Value)
    overviews_dir = DOCS_VIEW_DIR / "overviews"
    if overviews_dir.exists():
        for f in sorted(overviews_dir.glob("*.html")):
            if f.name == "relnotes-txt.html":
                continue

            rel_file = f"docs_view/overviews/{f.name}"
            try:
                with open(f, 'r', encoding='utf-8') as ofile:
                    content = ofile.read()
            except Exception as e:
                print(f"Error reading {f}: {e}")
                continue

            title_m = re.search(r'<h1[^>]*class=["\']?CTitle["\']?>([\s\S]*?)</h1>', content, re.IGNORECASE)
            title = clean_html(title_m.group(1)) if title_m else f.stem.replace("-txt", "").capitalize()

            full_clean = clean_html(content)
            # Remove redundant leading title repetition if present
            if full_clean.lower().startswith(title.lower()):
                trimmed_body = full_clean[len(title):].lstrip(" :-|")
                if len(trimmed_body) > 80:
                    full_clean = f"{title}: {trimmed_body}"

            # Detect covered UVM APIs in this overview
            found_apis = []
            for m_id in UVM_IDENT_RE.findall(full_clean):
                if (m_id in db_classes or m_id in db_macros) and m_id not in found_apis:
                    found_apis.append(m_id)
            covered_apis = found_apis[:8]

            intents, synonyms = match_intents(f"{f.name} {title} {' '.join(covered_apis[:4])}", catalog, max_intents=3, max_synonyms=6)
            api_suffix = f" [APIs: {', '.join(covered_apis)}]" if covered_apis else ""
            intent_suffix = ""
            if intents or synonyms:
                intent_suffix = f" [Intents: {', '.join(intents)}] [Keywords: {', '.join(synonyms)}]"

            parent_id = len(chunks)
            parent_chunk = {
                "id": parent_id,
                "level": "parent",
                "parentId": None,
                "docUrl": rel_file,
                "url": f"{rel_file}#MainTopic",
                "anchor": "MainTopic",
                "title": title,
                "pageHeading": title,
                "class": title,
                "category": "Overviews",
                "type": "overview",
                "breadcrumb": f"Overviews > {title}",
                "coveredApis": covered_apis,
                "synonyms": synonyms,
                "text": full_clean[:2500],
                "context_header": f"[UVM 1.2 Overview: {title}]{intent_suffix}{api_suffix}"
            }
            chunks.append(parent_chunk)
            parent_count += 1

            overview_meta[rel_file] = {
                "chunkId": parent_id,
                "title": title,
                "apis": covered_apis
            }
            for api in covered_apis:
                if rel_file not in api_to_overviews[api]:
                    api_to_overviews[api].append(rel_file)

            # Level 2: Child Sections in Overview
            topics = re.findall(r'<div class=["\']?CTopic["\']?[^>]*>([\s\S]*?)</div>\s*</div>', content, re.IGNORECASE)
            for idx, top in enumerate(topics):
                sub_title_m = re.search(r'<h[1-4][^>]*class=["\']?CTitle["\']?>([\s\S]*?)</h[1-4]>', top, re.IGNORECASE)
                sub_title = clean_html(sub_title_m.group(1)) if sub_title_m else f"Section {idx+1}"
                if sub_title == title:
                    continue

                anchor_m = re.search(r'<a\s+name=["\']([^"\']+)["\']', top, re.IGNORECASE)
                anchor = anchor_m.group(1) if anchor_m else f"section_{idx}"

                clean_text = clean_html(top)
                if len(clean_text) < 70:
                    continue

                sec_apis = [a for a in UVM_IDENT_RE.findall(clean_text) if a in db_classes or a in db_macros][:8]
                c_intents, c_synonyms = match_intents(f"{title} {sub_title} {' '.join(sec_apis)}", catalog)
                c_intent_suffix = ""
                if c_intents or c_synonyms:
                    c_intent_suffix = f" [Intents: {', '.join(c_intents)}] [Keywords: {', '.join(c_synonyms)}]"

                child_chunk = {
                    "id": len(chunks),
                    "level": "child",
                    "parentId": parent_id,
                    "docUrl": rel_file,
                    "url": f"{rel_file}#{anchor}",
                    "anchor": anchor,
                    "title": f"{title} > {sub_title}",
                    "rawTitle": sub_title,
                    "class": title,
                    "category": "Overviews",
                    "type": "overview",
                    "breadcrumb": f"Overviews > {title} > {sub_title}",
                    "synonyms": c_synonyms,
                    "text": clean_text[:1200],
                    "context_header": f"[UVM 1.2 Architecture Guide] [Overview: {title}] [Section: {sub_title}]{c_intent_suffix}"
                }
                chunks.append(child_chunk)
                child_count += 1

    # 2. Process Classes, Methods, Macros in other directories (strictly skip overviews, images, and alphabetical index/)
    for root, dirs, files in os.walk(DOCS_VIEW_DIR):
        root_path = Path(root)
        if root_path.name in ["overviews", "images", "index"]:
            continue

        category = root_path.name.capitalize()
        for f in sorted(files):
            if not f.endswith(".html"):
                continue

            full_file = root_path / f
            rel_file = full_file.relative_to(BASE_DIR).as_posix()
            file_base = f.replace("-svh.html", "").replace(".html", "")

            try:
                with open(full_file, 'r', encoding='utf-8') as cfile:
                    content = cfile.read()
            except Exception as e:
                print(f"Error reading {full_file}: {e}")
                continue

            class_anchor_m = re.search(r'<div class=["\']?CClass["\']?[^>]*data-anchor=["\']?([^"\'>]+)["\']?', content, re.IGNORECASE)
            main_title_m = re.search(r'id=["\']?MainTopic["\']?[\s\S]*?<h[1-4] class=["\']?CTitle["\']?>([\s\S]*?)</h[1-4]>', content, re.IGNORECASE)

            if class_anchor_m:
                raw_class = class_anchor_m.group(1)
            elif file_base.startswith("uvm_"):
                raw_class = file_base
            elif main_title_m:
                raw_class = clean_html(main_title_m.group(1))
            else:
                raw_class = file_base

            # Normalize parameterized class names (e.g. "uvm_driver#(REQ,RSP)" -> "uvm_driver")
            canonical_class = re.sub(r'\s*#\(.*$', '', raw_class).strip()
            if canonical_class not in db_classes and file_base.startswith("uvm_") and file_base in db_classes:
                canonical_class = file_base

            page_heading = clean_html(main_title_m.group(1)) if main_title_m else raw_class

            # Extract intro before first functional member
            first_func_split = re.search(r'<div class=["\']?(CMethod|CPort|CTask|CFunction|CGroup|CVariable|CConstant)\b', content, re.IGNORECASE)
            intro_html_slice = content[:first_func_split.start()] if first_func_split else content
            parent_body = clean_html(intro_html_slice)
            if len(parent_body) < 60:
                main_body_m = re.search(r'<div class=["\']?CTopic["\']? id=["\']?MainTopic["\']?>([\s\S]*?)</div>\s*</div>', content, re.IGNORECASE)
                if main_body_m:
                    parent_body = clean_html(main_body_m.group(1))

            # AST lookup for this class
            ast_cls = db_classes.get(canonical_class)
            ast_header_parts = []
            cls_sig = ""
            is_deprecated = ("deprecated" in rel_file.lower())
            if ast_cls:
                ancestors = ast_cls.get("ancestors", [])
                if ancestors:
                    ast_header_parts.append(f"Extends: {' -> '.join(ancestors[:4])}")
                params_raw = (ast_cls.get("parameters_raw") or "").strip()
                if params_raw:
                    params_clean = re.sub(r'\s+', ' ', params_raw)
                    ast_header_parts.append(f"Params: {params_clean[:120]}")
                    cls_sig = f"{'virtual ' if ast_cls.get('is_virtual') else ''}class {canonical_class} #({params_clean})"
                else:
                    cls_sig = f"{'virtual ' if ast_cls.get('is_virtual') else ''}class {canonical_class}"
                if ast_cls.get("parent"):
                    cls_sig += f" extends {ast_cls['parent']}"
                is_deprecated = bool(ast_cls.get("is_deprecated", is_deprecated))

            ast_suffix = f" [{' | '.join(ast_header_parts)}]" if ast_header_parts else ""
            intents, synonyms = match_intents(f"{f} {canonical_class} {page_heading}", catalog)
            intent_suffix = ""
            if intents or synonyms:
                intent_suffix = f" [Intents: {', '.join(intents)}] [Keywords: {', '.join(synonyms)}]"

            # Strip redundant leading title from parent_body
            if parent_body.lower().startswith(page_heading.lower()):
                trimmed_pb = parent_body[len(page_heading):].lstrip(" :-|")
                if len(trimmed_pb) > 60:
                    parent_body = trimmed_pb

            parent_id = len(chunks)
            parent_chunk = {
                "id": parent_id,
                "level": "parent",
                "parentId": None,
                "docUrl": rel_file,
                "url": f"{rel_file}#MainTopic",
                "anchor": "MainTopic",
                "title": canonical_class,
                "pageHeading": page_heading,
                "class": canonical_class,
                "category": category,
                "type": "class",
                "breadcrumb": f"{category} > {canonical_class}",
                "sig": cls_sig,
                "isDeprecated": is_deprecated,
                "synonyms": synonyms,
                "text": parent_body[:2500] if parent_body else f"{canonical_class} ({page_heading}) class reference in {category}.",
                "context_header": f"[UVM 1.2 Class: {canonical_class}] [{page_heading}]{intent_suffix}{ast_suffix}"
            }
            chunks.append(parent_chunk)
            parent_count += 1

            if canonical_class in db_classes:
                class_to_chunk[canonical_class] = {
                    "chunkId": parent_id,
                    "docUrl": rel_file,
                    "category": category
                }

            # Level 2: Child Methods, Tasks, Functions, Macros
            topic_divs = re.finditer(r'<div class=["\']?(C[A-Za-z0-9_]+)["\']?[^>]*>\s*<div class=["\']?CTopic["\']?[^>]*>([\s\S]*?)</div>\s*</div>', content, re.IGNORECASE)
            for m in topic_divs:
                cls_type = m.group(1)
                topic_html = m.group(2)

                if any(x in topic_html for x in ['id="MainTopic"', 'id=MainTopic', 'data-anchor="Intro"', 'data-anchor="Summary"']):
                    continue
                if cls_type in ["CGroup", "CSection", "CGeneric"] and any(w in topic_html for w in ["Methods", "Variables", "Types", "Constants", "Port / Export / Imp Types", "Ports"]):
                    continue

                sub_m = re.search(r'<h[1-4]\b[^>]*class=["\']?CTitle["\']?>([\s\S]*?)</h[1-4]>', topic_html, re.IGNORECASE)
                if not sub_m:
                    continue
                sub_title = clean_html(sub_m.group(1))
                if not sub_title or sub_title == canonical_class or sub_title == page_heading or sub_title == "Intro":
                    continue

                anchor_m = re.search(r'<a\s+name=["\']([^"\']+)["\']', sub_m.group(1), re.IGNORECASE)
                anchor = anchor_m.group(1) if anchor_m else sub_title

                topic_text = clean_html(topic_html)
                if len(topic_text) < 55:
                    continue

                inferred_type = "method"
                if "macro" in cls_type.lower() or sub_title.startswith("`"):
                    inferred_type = "macro"
                elif "task" in cls_type.lower():
                    inferred_type = "task"
                elif "function" in cls_type.lower():
                    inferred_type = "function"
                elif "port" in cls_type.lower():
                    inferred_type = "port"
                elif "variable" in cls_type.lower() or "type" in cls_type.lower():
                    inferred_type = "variable"
                elif "class" in cls_type.lower():
                    inferred_type = "class"

                # AST lookup for method or macro
                sig_str = ""
                ast_method = None
                if ast_cls and sub_title in ast_cls.get("methods", {}):
                    ast_method = ast_cls["methods"][sub_title]
                    sig_str = format_method_sig(ast_method)
                elif inferred_type == "macro":
                    macro_key = sub_title.lstrip("`")
                    ast_mac = db_macros.get(macro_key) or db_macros.get(sub_title)
                    if ast_mac:
                        m_params = ast_mac.get("parameters_raw") or ""
                        sig_str = f"`{macro_key}{m_params}"

                sig_suffix = f" [Signature: {sig_str}]" if sig_str else ""
                if ast_method and ast_method.get("overrides") and ast_method.get("overridden_from"):
                    sig_suffix += f" [Overrides: {ast_method['overridden_from']}]"

                c_intents, c_synonyms = match_intents(f"{canonical_class} {sub_title}", catalog)
                c_intent_suffix = ""
                if c_intents or c_synonyms:
                    c_intent_suffix = f" [Intents: {', '.join(c_intents)}] [Keywords: {', '.join(c_synonyms)}]"

                display_title = f"{canonical_class}::{sub_title}" if inferred_type in ["method", "function", "task"] else sub_title
                child_id = len(chunks)
                child_url = f"{rel_file}#{anchor}"

                child_chunk = {
                    "id": child_id,
                    "level": "child",
                    "parentId": parent_id,
                    "docUrl": rel_file,
                    "url": child_url,
                    "anchor": anchor,
                    "title": display_title,
                    "rawTitle": sub_title,
                    "class": canonical_class,
                    "category": category,
                    "type": inferred_type,
                    "breadcrumb": f"{category} > {canonical_class} > {sub_title}",
                    "sig": sig_str,
                    "isDeprecated": is_deprecated,
                    "synonyms": c_synonyms,
                    "text": topic_text[:1200],
                    "context_header": f"[UVM 1.2 {inferred_type.capitalize()}] [{display_title}] Class: {canonical_class}. Category: {category}.{sig_suffix}{c_intent_suffix}"
                }
                chunks.append(child_chunk)
                child_count += 1

                if inferred_type in ["method", "function", "task"] and canonical_class in db_classes:
                    methods_index[sub_title].append({
                        "class": canonical_class,
                        "chunkId": child_id,
                        "kind": ast_method.get("kind", inferred_type) if ast_method else inferred_type,
                        "virtual": bool(ast_method.get("is_virtual")) if ast_method else False,
                        "pureVirtual": bool(ast_method.get("is_pure_virtual")) if ast_method else False,
                        "callsSuper": bool((ast_method.get("impl") or {}).get("calls_super")) if ast_method else False,
                        "sig": sig_str,
                        "docUrl": child_url
                    })
                elif inferred_type == "macro":
                    norm_macro = f"`{sub_title.lstrip('`')}"
                    macro_to_chunk[norm_macro] = {
                        "chunkId": child_id,
                        "docUrl": child_url,
                        "sig": sig_str
                    }
                elif inferred_type == "class":
                    child_cls_key = re.sub(r'\s*#\(.*$', '', sub_title).strip()
                    if child_cls_key in db_classes and child_cls_key not in class_to_chunk:
                        class_to_chunk[child_cls_key] = {
                            "chunkId": child_id,
                            "docUrl": rel_file,
                            "category": category
                        }

    # 3. Process Interactive Example Studios (examples_view/)
    examples_view_dir = BASE_DIR / "examples_view"
    sys.path.insert(0, str(BASE_DIR / "scripts"))
    try:
        import build_examples
        suites_meta = getattr(build_examples, "SUITES_METADATA", {})
        stepper_data = getattr(build_examples, "STEPPER_DATA", {})
    except Exception as e:
        print(f"Warning: could not import build_examples: {e}")
        suites_meta = {}
        stepper_data = {}

    if examples_view_dir.exists() and suites_meta:
        print(f"Extracting RAG chunks from {len(suites_meta)} interactive example studios...")
        for suite_key, meta in suites_meta.items():
            cat_slug = meta["category"].lower()
            file_name = f"{Path(suite_key).name}.html"
            rel_file = f"examples_view/{cat_slug}/{file_name}"
            full_file = examples_view_dir / cat_slug / file_name
            if not full_file.exists():
                continue

            title = meta["title"]
            cat_title = meta["category_title"]
            scope = meta["scope"]
            diff = meta["difficulty"]
            summary = meta["summary"]
            apis = meta.get("apis", [])

            # Collect focal UVM classes/macros used in this example (keep concise to avoid dilution)
            example_apis = list(dict.fromkeys([a for a in apis if a]))[:8]

            intents, synonyms = match_intents(
                f"{title} {' '.join(example_apis[:3])} {meta['category']} example testbench",
                catalog,
                max_intents=3,
                max_synonyms=6
            )
            intent_suffix = ""
            if intents or synonyms:
                intent_suffix = f" [Intents: {', '.join(intents)}] [Keywords: {', '.join(synonyms)}]"

            parent_id = len(chunks)
            parent_chunk = {
                "id": parent_id,
                "level": "parent",
                "parentId": None,
                "docUrl": rel_file,
                "url": f"{rel_file}#MainTopic",
                "anchor": "MainTopic",
                "title": f"Interactive Example: {title}",
                "pageHeading": title,
                "class": title,
                "category": f"Examples - {cat_title}",
                "type": "example",
                "breadcrumb": f"Examples > {cat_title} > {title}",
                "coveredApis": example_apis,
                "synonyms": synonyms,
                "text": f"{summary} Practical UVM 1.2 interactive example demonstrating {', '.join(example_apis)}. Scope: {scope}. Difficulty: {diff}. Complete multi-file SystemVerilog testbench with simulator execution log.",
                "context_header": f"[UVM 1.2 Example: {title}] [Category: {cat_title}] [APIs: {', '.join(example_apis[:5])}]{intent_suffix}"
            }
            chunks.append(parent_chunk)
            parent_count += 1

            examples_meta[rel_file] = {
                "chunkId": parent_id,
                "title": title,
                "apis": example_apis,
                "difficulty": diff,
                "category": cat_title
            }
            for api in example_apis:
                norm_api = api.lstrip("`")
                if rel_file not in api_to_examples[norm_api]:
                    api_to_examples[norm_api].append(rel_file)

            # Build co-occurrence matrix between UVM classes in this example
            cls_in_ex = [a for a in example_apis if a in db_classes]
            for i in range(len(cls_in_ex)):
                for j in range(i + 1, len(cls_in_ex)):
                    a_i, a_j = cls_in_ex[i], cls_in_ex[j]
                    co_occurrence[a_i][a_j] += 1
                    co_occurrence[a_j][a_i] += 1

            # Level 2: Child Stepper Chunk
            stepper_list = stepper_data.get(suite_key, [])
            if stepper_list:
                stepper_text = " ".join([f"Step {s['step']}: {s['title']} ({s['component']}) - {s['desc']} Expected log: {s['log_snippet']}." for s in stepper_list])
                child_chunk = {
                    "id": len(chunks),
                    "level": "child",
                    "parentId": parent_id,
                    "docUrl": rel_file,
                    "url": f"{rel_file}#FlowStepper",
                    "anchor": "FlowStepper",
                    "title": f"{title} > Simulation Flow Stepper",
                    "rawTitle": "Simulation Flow Stepper",
                    "class": title,
                    "category": f"Examples - {cat_title}",
                    "type": "stepper",
                    "breadcrumb": f"Examples > {cat_title} > {title} > Simulation Flow Stepper",
                    "text": stepper_text[:1200],
                    "context_header": f"[UVM 1.2 Simulation Flow Stepper Walkthrough] [Example: {title}] [Key APIs: {', '.join(example_apis)}] [Execution Lifecycle Steps]"
                }
                chunks.append(child_chunk)
                child_count += 1

            # Level 2: Child Topology & Code Studio Chunk
            topo_nodes = meta.get("topology", [])
            topo_str = " ".join([f"{n.get('name')} ({n.get('type')}{': ' + n.get('details') if n.get('details') else ''})" for n in topo_nodes])
            studio_chunk = {
                "id": len(chunks),
                "level": "child",
                "parentId": parent_id,
                "docUrl": rel_file,
                "url": f"{rel_file}#Studio",
                "anchor": "Studio",
                "title": f"{title} > Multi-File Code Studio & Topology",
                "rawTitle": "Testbench Topology & Code Studio",
                "class": title,
                "category": f"Examples - {cat_title}",
                "type": "studio",
                "breadcrumb": f"Examples > {cat_title} > {title} > Multi-File Code Studio",
                "text": f"Testbench architecture components: {topo_str}. Multi-file Code Studio includes runnable SystemVerilog code, testbench modules, and makefiles for Questa, VCS, and Xcelium.",
                "context_header": f"[UVM 1.2 Testbench Architecture & Code] [Example: {title}] [Key APIs: {', '.join(example_apis)}]"
            }
            chunks.append(studio_chunk)
            child_count += 1

    # 4. Assemble Lightweight Relational Graph (data/rag_graph.json)
    graph_classes = {}
    for cls_name, cls_info in db_classes.items():
        c_meta = class_to_chunk.get(cls_name, {})
        file_path = cls_info.get("file", "")
        subsystem = db_files.get(file_path, {}).get("subsystem", c_meta.get("category", "").lower())
        descendants = cls_info.get("descendants", [])
        ancestors = cls_info.get("ancestors", [])
        is_dep = bool(cls_info.get("is_deprecated", False) or subsystem == "deprecated")

        rel_examples = sorted(
            api_to_examples.get(cls_name, []),
            key=lambda u: len((examples_meta.get(u) or {}).get("apis", [])) or 99
        )
        rel_overviews = api_to_overviews.get(cls_name, [])
        has_doc = bool((cls_info.get("doc") or {}).get("full_text") and len(cls_info["doc"]["full_text"]) > 80)

        # Heuristic for internal helper classes
        is_internal = (
            cls_name.endswith("_imp") and not rel_examples and not rel_overviews
        ) or ("internal" in ((cls_info.get("doc") or {}).get("summary") or "").lower())

        # Architectural centrality in [0, 1]
        centrality = 0.10
        if rel_examples:
            centrality += min(0.35, 0.22 + 0.05 * len(rel_examples))
        if rel_overviews:
            centrality += 0.25
        if descendants:
            centrality += 0.25 * min(1.0, math.log1p(len(descendants)) / math.log(50))
        if has_doc:
            centrality += 0.15
        if is_dep:
            centrality *= 0.35
        if is_internal:
            centrality *= 0.65
        centrality = round(min(1.0, centrality), 3)

        # Overrides summary for this class
        cls_overrides = {}
        for m_name, m_info in (cls_info.get("methods") or {}).items():
            if m_info.get("overrides") and m_info.get("overridden_from"):
                cls_overrides[m_name] = {
                    "from": m_info["overridden_from"],
                    "callsSuper": bool((m_info.get("impl") or {}).get("calls_super"))
                }

        # Related macros from catalog/subsystem heuristics
        rel_macros = []
        if "uvm_component" in ancestors or cls_name == "uvm_component":
            rel_macros = ["`uvm_component_utils", "`uvm_component_param_utils"]
        elif "uvm_sequence_item" in ancestors or "uvm_object" in ancestors or cls_name == "uvm_object":
            rel_macros = ["`uvm_object_utils", "`uvm_field_int"]
        if "uvm_sequence" in ancestors or cls_name == "uvm_sequence":
            rel_macros.extend(["`uvm_do", "`uvm_do_with"])

        # Top co-occurring classes
        co_peers = sorted(co_occurrence.get(cls_name, {}).items(), key=lambda x: x[1], reverse=True)
        co_occurs_list = [p[0] for p in co_peers[:5]]

        params_raw = (cls_info.get("parameters_raw") or "").strip()
        params_clean = re.sub(r'\s+', ' ', params_raw)[:140] if params_raw else ""

        graph_classes[cls_name] = {
            "chunkId": c_meta.get("chunkId"),
            "docUrl": c_meta.get("docUrl"),
            "subsystem": subsystem,
            "parent": cls_info.get("parent"),
            "ancestors": ancestors,
            "children": cls_info.get("children", [])[:15],
            "depth": cls_info.get("depth", 0),
            "isVirtual": bool(cls_info.get("is_virtual")),
            "isDeprecated": is_dep,
            "isInternal": is_internal,
            "centrality": centrality,
            "params": params_clean,
            "ownMethods": list((cls_info.get("methods") or {}).keys()),
            "overrides": cls_overrides,
            "relatedMacros": rel_macros[:4],
            "relatedExamples": rel_examples[:4],
            "relatedOverviews": rel_overviews[:3],
            "coOccursWith": co_occurs_list
        }

    # Build macros graph node
    graph_macros = {}
    for m_name, m_info in db_macros.items():
        norm_name = f"`{m_name.lstrip('`')}"
        m_chunk = macro_to_chunk.get(norm_name, {})
        cat = m_info.get("category", "general")
        rel_cls = []
        if cat == "sequence":
            rel_cls = ["uvm_sequence", "uvm_sequence_base"]
        elif cat == "object_utils":
            rel_cls = ["uvm_object", "uvm_component"]
        elif cat == "field_automation":
            rel_cls = ["uvm_object", "uvm_sequence_item"]
        elif cat == "reporting":
            rel_cls = ["uvm_report_object", "uvm_component"]
        elif cat == "callbacks":
            rel_cls = ["uvm_callback", "uvm_callbacks"]
        graph_macros[norm_name] = {
            "chunkId": m_chunk.get("chunkId"),
            "docUrl": m_chunk.get("docUrl"),
            "category": cat,
            "isDeprecated": bool(m_info.get("is_deprecated")),
            "sig": m_chunk.get("sig") or f"{norm_name}{m_info.get('parameters_raw') or ''}",
            "relatedClasses": rel_cls
        }

    rag_graph = {
        "version": "2.0",
        "stats": {
            "classes": len(graph_classes),
            "methodsIndexed": len(methods_index),
            "macros": len(graph_macros),
            "examples": len(examples_meta),
            "overviews": len(overview_meta)
        },
        "nodes": {
            "classes": graph_classes,
            "methodsIndex": dict(methods_index),
            "macros": graph_macros,
            "examples": examples_meta,
            "overviews": dict(api_to_overviews),
            "overviewMeta": overview_meta
        },
        "aliases": {
            "vif": ["uvm_config_db", "virtual interface"],
            "config_db": ["uvm_config_db"],
            "resource_db": ["uvm_resource_db"],
            "ral": ["uvm_reg", "uvm_reg_block", "uvm_reg_map"],
            "tlm": ["uvm_analysis_port", "uvm_tlm_fifo", "uvm_tlm_analysis_fifo"],
            "factory": ["uvm_factory", "uvm_object_wrapper"],
            "objection": ["uvm_objection"],
            "scoreboard": ["uvm_scoreboard", "uvm_in_order_comparator", "uvm_analysis_imp"]
        },
        "deprecatedReplacements": {
            "`uvm_sequence_utils": "`uvm_object_utils",
            "`uvm_sequencer_utils": "`uvm_component_utils",
            "`uvm_declare_sequence_lib": "`uvm_object_utils"
        }
    }

    print(f"Hierarchical extraction complete: {len(chunks)} total chunks ({parent_count} parents, {child_count} children).")
    print(f"Graph built: {len(graph_classes)} classes, {len(methods_index)} unique method names, {len(graph_macros)} macros, {len(examples_meta)} examples, {len(overview_meta)} overviews.")
    return chunks, rag_graph


def embed_with_fastembed(model_name, texts):
    """Compute embeddings using fastembed."""
    from fastembed import TextEmbedding
    model = TextEmbedding(model_name)
    embeddings_gen = model.embed(texts, batch_size=64)
    return list(embeddings_gen)


def embed_with_onnx(repo_id, texts):
    """Compute embeddings directly using onnxruntime and tokenizers."""
    import numpy as np
    import onnxruntime as ort
    from tokenizers import Tokenizer
    from huggingface_hub import hf_hub_download

    print(f"Loading custom ONNX model from HuggingFace Hub: {repo_id}...")
    tok_path = hf_hub_download(repo_id=repo_id, filename="tokenizer.json")
    model_path = hf_hub_download(repo_id=repo_id, filename="onnx/model_quantized.onnx")

    tokenizer = Tokenizer.from_file(tok_path)
    session = ort.InferenceSession(model_path)

    embeddings = []
    batch_size = 64
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        encodings = tokenizer.encode_batch(batch_texts)

        max_len = max(len(e.ids) for e in encodings)
        input_ids = np.zeros((len(encodings), max_len), dtype=np.int64)
        attention_mask = np.zeros((len(encodings), max_len), dtype=np.int64)
        token_type_ids = np.zeros((len(encodings), max_len), dtype=np.int64)

        for b_idx, e in enumerate(encodings):
            l = len(e.ids)
            input_ids[b_idx, :l] = e.ids
            attention_mask[b_idx, :l] = e.attention_mask
            token_type_ids[b_idx, :l] = e.type_ids

        outputs = session.run(None, {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids
        })

        last_hidden_state = outputs[0]
        mask_expanded = np.expand_dims(attention_mask, -1)
        sum_embeddings = np.sum(last_hidden_state * mask_expanded, axis=1)
        sum_mask = np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        mean_pooled = sum_embeddings / sum_mask

        norms = np.linalg.norm(mean_pooled, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = mean_pooled / norms

        for vec in normalized:
            embeddings.append(vec.astype(np.float32))

    return embeddings


def save_chunks_and_graph(chunks, rag_graph):
    """Persist rag_chunks.json and compact rag_graph.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    chunks_file = DATA_DIR / "rag_chunks.json"
    with open(chunks_file, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"Saved {chunks_file} ({chunks_file.stat().st_size / 1024:.1f} KB).")

    graph_file = DATA_DIR / "rag_graph.json"
    with open(graph_file, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rag_graph, f, ensure_ascii=False, separators=(',', ':'))
    print(f"Saved {graph_file} ({graph_file.stat().st_size / 1024:.1f} KB).")


def generate_multi_model_embeddings(chunks):
    """Compute and save embeddings for each model configured in config/rag_models.json."""
    models_file = CONFIG_DIR / "rag_models.json"
    if not models_file.exists():
        models_cfg = [{"id": "all-minilm-l6-v2", "fastembedModel": "sentence-transformers/all-MiniLM-L6-v2", "default": True}]
    else:
        with open(models_file, 'r', encoding='utf-8') as f:
            models_cfg = json.load(f)

    texts = [f"{c['context_header']} {c['text']}" for c in chunks]

    for m in models_cfg:
        m_id = m.get("id")
        m_name = m.get("name", m_id)
        fast_name = m.get("fastembedModel")
        hf_repo = m.get("hfRepo")
        is_default = m.get("default", False)

        print(f"\n--- Generating Embeddings for Model: {m_name} ({m_id}) ---")
        try:
            if fast_name:
                embeddings = embed_with_fastembed(fast_name, texts)
            elif hf_repo:
                embeddings = embed_with_onnx(hf_repo, texts)
            else:
                print(f"Skipping model {m_id}: neither fastembedModel nor hfRepo specified.")
                continue
        except Exception as e:
            print(f"Error generating embeddings for {m_id}: {e}", file=sys.stderr)
            continue

        dim = len(embeddings[0])
        print(f"Computed {len(embeddings)} vectors of dimension {dim}.")

        model_bin = DATA_DIR / f"rag_embeddings_{m_id}.bin"
        with open(model_bin, 'wb') as f:
            for vec in embeddings:
                f.write(struct.pack(f"{len(vec)}f", *vec))
        print(f"Saved {model_bin} ({model_bin.stat().st_size / 1024:.1f} KB).")

        if is_default or m_id == "all-minilm-l6-v2":
            default_bin = DATA_DIR / "rag_embeddings.bin"
            with open(default_bin, 'wb') as f:
                for vec in embeddings:
                    f.write(struct.pack(f"{len(vec)}f", *vec))
            print(f"Saved default vector database {default_bin} ({default_bin.stat().st_size / 1024:.1f} KB).")


def main():
    parser = argparse.ArgumentParser(description="UVM 1.2 Graph-Enhanced RAG Builder (V2)")
    parser.add_argument("--graph-only", action="store_true", help="Only build rag_chunks.json and rag_graph.json without computing embeddings.")
    args = parser.parse_args()

    print("=" * 65)
    print("  UVM 1.2 Graph-Enhanced RAG & Multi-Model Embeddings Generator")
    print("=" * 65)

    chunks, rag_graph = extract_chunks_and_graph()
    if not chunks:
        print("Error: No chunks extracted!", file=sys.stderr)
        sys.exit(1)

    save_chunks_and_graph(chunks, rag_graph)

    if not args.graph_only:
        generate_multi_model_embeddings(chunks)

    print("=" * 65)
    print("  RAG V2 build completed successfully!")
    print("=" * 65)


if __name__ == "__main__":
    main()
