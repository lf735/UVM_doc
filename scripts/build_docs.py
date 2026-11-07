#!/usr/bin/env python3
"""
UVM 1.2 Documentation & Web Source Viewer Generator
Parses UVM 1.2 sources and reference docs to generate:
- Syntax-highlighted HTML views for all 155 SystemVerilog/C source files with clickable line numbers
- Modernized, responsive HTML documentation pages with bidirectional "View Source" deep links
- Comprehensive client-side search data (search_data.js) and navigation category tree
- Fully English, responsive, and GitHub Pages ready
"""

import os
import sys
import re
import html
import json
import shutil
import argparse
import posixpath
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
import build_examples
import syntax_highlighter as sh
import page_builder_common as pbc
SRC_DIR = BASE_DIR / "uvm-1.2" / "src"
DOCS_DIR = BASE_DIR / "uvm-1.2" / "docs" / "html"
DOCS_FILES_DIR = DOCS_DIR / "files"
DOCS_IMAGES_DIR = DOCS_DIR / "images"
OUTPUT_SRC_VIEW = BASE_DIR / "src_view"
OUTPUT_DOCS_VIEW = BASE_DIR / "docs_view"
OUTPUT_JS_DIR = BASE_DIR / "js"
OUTPUT_IMAGES_DIR = BASE_DIR / "images"

# AST Database Path & Cache
DB_JSON_PATH = BASE_DIR / "data" / "uvm_source_database.json"
UVM_DB = {}
if DB_JSON_PATH.exists():
    try:
        with open(DB_JSON_PATH, 'r', encoding='utf-8') as f:
            UVM_DB = json.load(f)
        print(f"Loaded UVM AST Database: {len(UVM_DB.get('classes', {}))} classes, {len(UVM_DB.get('macros', {}))} macros.")
    except Exception as e:
        print(f"Warning: Could not load {DB_JSON_PATH}: {e}")

# Bidirectional mapping between UVM classes and practical interactive examples
CLASS_TO_EXAMPLE_MAP = {
    # TLM-1
    "uvm_tlm_fifo": ("tlm-1/fifo.html", "TLM-1 FIFO with Non-Blocking Check"),
    "uvm_tlm_fifo_base": ("tlm-1/fifo.html", "TLM-1 FIFO with Non-Blocking Check"),
    "uvm_blocking_put_port": ("tlm-1/producer_consumer.html", "Blocking Put & Get Ports"),
    "uvm_blocking_get_port": ("tlm-1/producer_consumer.html", "Blocking Put & Get Ports"),
    "uvm_put_port": ("tlm-1/hierarchy.html", "Hierarchical TLM Port Forwarding"),
    "uvm_put_export": ("tlm-1/hierarchy.html", "Hierarchical TLM Port Forwarding"),
    "uvm_master_port": ("tlm-1/bidir.html", "Bidirectional TLM Transport"),
    "uvm_slave_port": ("tlm-1/bidir.html", "Bidirectional TLM Transport"),
    # TLM-2
    "uvm_tlm_b_transport": ("tlm-2/blocking_simple.html", "Blocking TLM-2 Transport (b_transport)"),
    "uvm_tlm_b_initiator_socket": ("tlm-2/blocking_simple.html", "Blocking TLM-2 Transport (b_transport)"),
    "uvm_tlm_b_target_socket": ("tlm-2/blocking_simple.html", "Blocking TLM-2 Transport (b_transport)"),
    "uvm_tlm_nb_transport_fw": ("tlm-2/nonblocking_simple.html", "Non-Blocking 4-Phase Protocol"),
    "uvm_tlm_nb_transport_bw": ("tlm-2/nonblocking_simple.html", "Non-Blocking 4-Phase Protocol"),
    "uvm_tlm_nb_initiator_socket": ("tlm-2/nonblocking_simple.html", "Non-Blocking 4-Phase Protocol"),
    "uvm_tlm_nb_target_socket": ("tlm-2/nonblocking_simple.html", "Non-Blocking 4-Phase Protocol"),
    "uvm_tlm_time": ("tlm-2/temporal_decoupling.html", "Temporal Decoupling & Quantum Keeper"),
    # Infrastructure
    "uvm_factory": ("infrastructure/factory.html", "Factory Overrides"),
    "uvm_default_factory": ("infrastructure/factory.html", "Factory Overrides"),
    "uvm_config_db": ("infrastructure/manual.html", "Manual Configuration DB"),
    "uvm_resource_db": ("infrastructure/manual.html", "Manual Configuration DB"),
    "uvm_callback": ("infrastructure/callbacks.html", "Callback Hooks"),
    "uvm_callbacks": ("infrastructure/callbacks.html", "Callback Hooks"),
    # Phasing & Objections
    "uvm_phase": ("phasing/basic.html", "Phased Execution Lifecycle"),
    "uvm_task_phase": ("phasing/basic.html", "Phased Execution Lifecycle"),
    "uvm_root": ("phasing/run_test.html", "Dynamic Test Selection"),
    "uvm_objection": ("phasing/objections.html", "Phase Objections & Drain Time"),
    "uvm_event": ("phasing/event_pool.html", "Event Synchronization (Pool)"),
    "uvm_event_pool": ("phasing/event_pool.html", "Event Synchronization (Pool)"),
    # Stimulus & Sequences
    "uvm_sequence": ("sequences/basic_read_write_sequence.html", "Basic Read/Write Sequence"),
    "uvm_sequence_base": ("sequences/basic_read_write_sequence.html", "Basic Read/Write Sequence"),
    "uvm_sequencer": ("sequences/basic_read_write_sequence.html", "Basic Read/Write Sequence"),
    "uvm_sequencer_base": ("sequences/basic_read_write_sequence.html", "Basic Read/Write Sequence"),
    "uvm_sequence_item": ("sequences/basic_read_write_sequence.html", "Basic Read/Write Sequence"),
    # Registers (RAL)
    "uvm_reg_block": ("registers/primer.html", "RAL Primer & Bus Adapter"),
    "uvm_reg": ("registers/primer.html", "RAL Primer & Bus Adapter"),
    "uvm_reg_field": ("registers/primer.html", "RAL Primer & Bus Adapter"),
    "uvm_reg_adapter": ("registers/primer.html", "RAL Primer & Bus Adapter"),
    "uvm_reg_predictor": ("registers/primer.html", "RAL Primer & Bus Adapter"),
    "uvm_reg_sequence": ("registers/sequence_api.html", "Register Sequence Convenience API"),
    "uvm_reg_fifo": ("registers/fifo_reg.html", "FIFO Registers"),
    "uvm_reg_cbs": ("registers/user-defined.html", "User-Defined Register Callbacks"),
    # Integrated Components & VIPs
    "uvm_driver": ("integrated/ubus.html", "UBUS Verification Component & TB"),
    "uvm_monitor": ("integrated/ubus.html", "UBUS Verification Component & TB"),
    "uvm_agent": ("integrated/ubus.html", "UBUS Verification Component & TB"),
    "uvm_scoreboard": ("integrated/ubus.html", "UBUS Verification Component & TB"),
    "uvm_env": ("integrated/ubus.html", "UBUS Verification Component & TB"),
    "uvm_component": ("basics/hello_world.html", "Hello World & TLM FIFO")
}

# Symbol extraction regexes
CLASS_DEF_REGEX = re.compile(r'^\s*(?:virtual\s+)?class\s+([a-zA-Z0-9_]+)')
METHOD_DEF_REGEX = re.compile(r'^\s*(?:virtual\s+|local\s+|protected\s+|static\s+)*(task|function)\s+(?:[\w:\[\]\$]+\s+)?([a-zA-Z0-9_]+)\s*\(')
MACRO_DEF_REGEX = re.compile(r'^\s*`define\s+([a-zA-Z0-9_]+)')

def highlight_outside_tags(text, highlight_fn):
    """Tokenize text outside HTML tags and HTML entity sequences."""
    parts = re.split(r'(<[^>]+>|&[a-zA-Z0-9#]+;)', text)
    for i in range(len(parts)):
        if not parts[i].startswith('<') and not (parts[i].startswith('&') and parts[i].endswith(';')):
            parts[i] = highlight_fn(parts[i])
    return "".join(parts)

def highlight_doc_code(raw_code):
    """Highlight a block of code from documentation preserving indentation and newlines."""
    return sh.highlight_doc_snippet(raw_code)

def highlight_before_params(text):
    def repl_text(t):
        tokens = re.split(r'(\b[a-zA-Z_][a-zA-Z0-9_]*\b|\()', t)
        words = [tok for tok in tokens if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', tok)]
        method_name = words[-1] if words else None
        res = []
        for tok in tokens:
            if not tok:
                continue
            if tok in sh.SV_CONTROL_KEYWORDS:
                res.append(f'<span class="sv-keyword">{tok}</span>')
            elif tok in sh.SV_DECL_KEYWORDS:
                res.append(f'<span class="sv-keyword-decl">{tok}</span>')
            elif tok in sh.SV_BUILTIN_TYPES:
                res.append(f'<span class="sv-type">{tok}</span>')
            elif tok in sh.SV_QUALIFIERS:
                res.append(f'<span class="sv-qualifier">{tok}</span>')
            elif tok in sh.SV_CONSTANTS:
                res.append(f'<span class="sv-constant">{tok}</span>')
            elif tok.startswith(('uvm_', 'UVM_')):
                res.append(f'<span class="sv-uvm-type">{tok}</span>')
            elif tok == method_name or tok in sh.KNOWN_UVM_METHODS:
                res.append(f'<span class="sv-proto-name">{tok}</span>')
            elif tok == '(':
                res.append(f'<span class="sv-op">(</span>')
            else:
                res.append(tok)
        return "".join(res)
    return highlight_outside_tags(text, repl_text)

def highlight_type_cell(text):
    def repl_text(t):
        def repl(m):
            w = m.group(0)
            if w in sh.SV_CONTROL_KEYWORDS:
                return f'<span class="sv-keyword">{w}</span>'
            elif w in sh.SV_DECL_KEYWORDS:
                return f'<span class="sv-keyword-decl">{w}</span>'
            elif w in sh.SV_BUILTIN_TYPES:
                return f'<span class="sv-type">{w}</span>'
            elif w in sh.SV_QUALIFIERS:
                return f'<span class="sv-qualifier">{w}</span>'
            elif w in sh.SV_CONSTANTS:
                return f'<span class="sv-constant">{w}</span>'
            elif w.startswith(('uvm_', 'UVM_')) or 'uvm' in w:
                return f'<span class="sv-uvm-type">{w}</span>'
            else:
                return f'<span class="sv-type">{w}</span>'
        return re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', repl, t)
    return highlight_outside_tags(text, repl_text)

def highlight_param_cell(text):
    def repl_text(t):
        def repl(m):
            w = m.group(1)
            punct = m.group(2) or ''
            return f'<span class="sv-param-name">{w}</span>' + (f'<span class="sv-op">{punct}</span>' if punct else '')
        return re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*\b)([,;]?)', repl, t)
    return highlight_outside_tags(text, repl_text)

def highlight_prototype_table(proto_html):
    if 'PBeforeParameters' in proto_html:
        proto_html = re.sub(
            r'(<td\b[^>]*class=["\']?PBeforeParameters[^>]*>)([\s\S]*?)(</td>)',
            lambda m: m.group(1) + highlight_before_params(m.group(2)) + m.group(3),
            proto_html
        )
        proto_html = re.sub(
            r'(<td\b[^>]*class=["\']?PType[^>]*>)([\s\S]*?)(</td>)',
            lambda m: m.group(1) + highlight_type_cell(m.group(2)) + m.group(3),
            proto_html
        )
        proto_html = re.sub(
            r'(<td\b[^>]*class=["\']?PParameter[^>]*>)([\s\S]*?)(</td>)',
            lambda m: m.group(1) + highlight_param_cell(m.group(2)) + m.group(3),
            proto_html
        )
        proto_html = re.sub(
            r'(<td\b[^>]*class=["\']?PAfterParameters[^>]*>)([\s\S]*?)(</td>)',
            lambda m: m.group(1) + f'<span class="sv-op">{m.group(2)}</span>' + m.group(3),
            proto_html
        )
        proto_html = re.sub(
            r'(<td\b[^>]*class=["\']?PDefaultValuePrefix\b[^>]*>)([\s\S]*?)(</td>)',
            lambda m: m.group(1) + f'<span class="sv-op">{m.group(2)}</span>' + m.group(3),
            proto_html
        )
        proto_html = re.sub(
            r'(<td\b[^>]*class=["\']?PDefaultValue\b[^>]*>)([\s\S]*?)(</td>)',
            lambda m: m.group(1) + f'<span class="sv-default-val">{m.group(2)}</span>' + m.group(3),
            proto_html
        )
    else:
        def highlight_simple_proto(inner):
            def repl_text(t):
                tokens = re.split(r'(\b[a-zA-Z_][a-zA-Z0-9_]*\b|[()=,;])', t)
                parts = []
                for idx, tok in enumerate(tokens):
                    if not tok:
                        continue
                    if re.match(r'^\s+$', tok):
                        parts.append(tok)
                    elif tok in sh.SV_CONTROL_KEYWORDS:
                        parts.append(f'<span class="sv-keyword">{tok}</span>')
                    elif tok in sh.SV_DECL_KEYWORDS:
                        parts.append(f'<span class="sv-keyword-decl">{tok}</span>')
                    elif tok in sh.SV_BUILTIN_TYPES:
                        parts.append(f'<span class="sv-type">{tok}</span>')
                    elif tok in sh.SV_QUALIFIERS:
                        parts.append(f'<span class="sv-qualifier">{tok}</span>')
                    elif tok in sh.SV_CONSTANTS:
                        parts.append(f'<span class="sv-constant">{tok}</span>')
                    elif tok.startswith(('uvm_', 'UVM_')):
                        parts.append(f'<span class="sv-uvm-type">{tok}</span>')
                    elif tok in '()=,;':
                        parts.append(f'<span class="sv-op">{tok}</span>')
                    else:
                        next_tok = next((x for x in tokens[idx+1:] if x.strip()), '')
                        if next_tok.startswith('(') or tok in sh.KNOWN_UVM_METHODS:
                            parts.append(f'<span class="sv-proto-name">{tok}</span>')
                        else:
                            parts.append(f'<span class="sv-ident">{tok}</span>')
                return "".join(parts)
            return highlight_outside_tags(inner, repl_text)

        proto_html = re.sub(
            r'(<td\b[^>]*>)([\s\S]*?)(</td>)',
            lambda m: m.group(1) + highlight_simple_proto(m.group(2)) + m.group(3),
            proto_html
        )
    return proto_html

def process_doc_code_blocks(html_text):
    def replace_code_block(match):
        raw_code = match.group(1)
        clean_code = html.unescape(raw_code).strip('\r\n')
        return pbc.render_code_block(clean_code)

    return re.sub(r'(?:<blockquote>\s*)?<pre>([\s\S]*?)</pre>(?:\s*</blockquote>)?', replace_code_block, html_text, flags=re.IGNORECASE)

def process_doc_prototypes(html_text):
    return re.sub(r'<table\b[^>]*class=["\']?Prototype["\']?[^>]*>[\s\S]*?</table>', lambda m: highlight_prototype_table(m.group(0)), html_text, flags=re.IGNORECASE)

def wrap_doc_diagrams(body_html):
    """Wrap <img> elements in a structured card with label, border framing, and zoom/enlarge button."""
    def repl_img(m):
        full_tag = m.group(0)
        src_m = re.search(r'src=["\']([^"\']+)["\']', full_tag, re.IGNORECASE)
        if not src_m:
            return full_tag
        src = src_m.group(1)
        filename = posixpath.basename(src)
        name_no_ext = re.sub(r'\.[a-zA-Z0-9]+$', '', filename)
        label_words = [w.upper() if w.lower() in ('uvm', 'tlm', 'uml', 'if', 'ifs') else w.capitalize() for w in name_no_ext.split('_')]
        title = " ".join(label_words)
        return pbc.render_diagram_card(src, title)

    return re.sub(r'<img\b[^>]*>', repl_img, body_html, flags=re.IGNORECASE)

# Global Symbol Maps
SYMBOL_MAP = {}
FILE_SYMBOLS = {}
SRC_TO_DOC_MAP = {}
DOC_TO_SRC_MAP = {}
CLASS_TO_DOC_MAP = {}
DOC_HEADINGS_MAP = {}
GLOBAL_DOC_ANCHOR_MAPS = {}
DOC_BREADCRUMBS_MAP = {}

# Orphan doc files (classes in UVM 1.2 src without Accellera legacy HTML doc pages)
ORPHAN_DOC_FILES = [
    ("base/uvm_spell_chkr-svh.html", "base/uvm_spell_chkr.svh", "uvm_spell_chkr", "Spell Checker Utility"),
    ("base/uvm_resource_specializations-svh.html", "base/uvm_resource_specializations.svh", "uvm_resource_specializations", "Specialized Resource Types"),
    ("seq/uvm_sequence_builtin-svh.html", "seq/uvm_sequence_builtin.svh", "uvm_sequence_builtin", "Builtin Sequences"),
    ("seq/uvm_sequencer_analysis_fifo-svh.html", "seq/uvm_sequencer_analysis_fifo.svh", "uvm_sequencer_analysis_fifo", "Sequencer Analysis FIFO"),
    ("deprecated/uvm_resource_converter-svh.html", "deprecated/uvm_resource_converter.svh", "uvm_resource_converter", "Resource Converter (Deprecated)")
]

def init_doc_breadcrumbs_map(categories):
    """Build a mapping from normalized doc path to its breadcrumb ancestor chain."""
    global DOC_BREADCRUMBS_MAP
    DOC_BREADCRUMBS_MAP.clear()

    def traverse(nodes, chain):
        for node in nodes:
            curr_chain = list(chain)
            if node.get('type') == 'group':
                grp_entry = {'title': node.get('title'), 'overviewHref': node.get('overviewHref')}
                ov_href = node.get('overviewHref')
                if ov_href:
                    norm_ov = ov_href.replace('\\', '/')
                    if norm_ov.startswith('docs_view/'):
                        norm_ov = norm_ov[len('docs_view/'):]
                    DOC_BREADCRUMBS_MAP[norm_ov] = curr_chain
                new_chain = curr_chain + [grp_entry]
                if 'children' in node:
                    traverse(node['children'], new_chain)
            elif node.get('type') in ('file', 'index'):
                href = node.get('href')
                if href:
                    norm_href = href.replace('\\', '/')
                    if norm_href.startswith('docs_view/'):
                        norm_href = norm_href[len('docs_view/'):]
                    DOC_BREADCRUMBS_MAP[norm_href] = curr_chain
                if 'children' in node:
                    traverse(node['children'], curr_chain)

    traverse(categories, [])

def build_breadcrumbs_html(doc_rel, page_title, root_rel):
    """Generate clickable breadcrumbs navigation HTML for a documentation page."""
    norm_doc = doc_rel.replace('\\', '/')
    ancestors = DOC_BREADCRUMBS_MAP.get(norm_doc, None)

    # Fallback to subsystem folder name if not mapped in tree (ignore 'overviews')
    if ancestors is None:
        if '/' in norm_doc:
            folder = norm_doc.split('/')[0]
            if folder.lower() != 'overviews':
                ancestors = [{'title': folder.capitalize(), 'overviewHref': None}]
            else:
                ancestors = []
        else:
            ancestors = []

    clean_t = page_title.split(' - ')[0].replace('UVM Reference', '').strip() or Path(norm_doc).stem
    home_href = f"{root_rel}index.html#/doc/overviews/intro-txt.html"

    items_html = [
        f'<a href="{home_href}" class="doc-breadcrumb-item doc-breadcrumb-link doc-breadcrumb-home" data-doc-href="docs_view/overviews/intro-txt.html">Home</a>'
    ]

    for anc in ancestors:
        title = html.escape(anc['title'])
        ov = anc.get('overviewHref')
        if ov:
            norm_ov = ov.replace('\\', '/')
            if norm_ov.startswith('docs_view/'):
                clean_target = norm_ov[len('docs_view/'):]
            else:
                clean_target = norm_ov
            target_href = f"{root_rel}index.html#/doc/{clean_target}"
            items_html.append(
                f'<a href="{target_href}" class="doc-breadcrumb-item doc-breadcrumb-link" data-doc-href="{html.escape(norm_ov)}">{title}</a>'
            )
        else:
            items_html.append(f'<span class="doc-breadcrumb-item">{title}</span>')

    # If this page itself is intro-txt.html (Home), avoid Home / Home
    if norm_doc == 'overviews/intro-txt.html':
        items_html = ['<span class="doc-breadcrumb-item active">Home</span>']
    else:
        items_html.append(f'<span class="doc-breadcrumb-item active">{html.escape(clean_t)}</span>')

    sep_html = '\n  <span class="doc-breadcrumb-sep">/</span>\n  '
    return f'''<nav class="doc-breadcrumbs" aria-label="Breadcrumb navigation">
  {sep_html.join(items_html)}
</nav>'''

def extract_doc_headings(html_text, rel_doc_path):
    """Extract ordered headings, methods, and groups for a documentation page."""
    headings = []

    # 1. Main Topic (Class / File Title)
    main_m = re.search(r'id=["\']?MainTopic["\']?[\s\S]*?<h[1-4] class=["\']?CTitle["\']?>([\s\S]*?)</h[1-4]>', html_text)
    main_title = None
    if main_m:
        main_title = html.unescape(re.sub(r'<[^>]+>', '', main_m.group(1)).strip())
        a_m = re.search(r'name=["\']([^"\']+)["\']', main_m.group(1))
        anchor = a_m.group(1) if a_m else 'MainTopic'
        headings.append({
            'title': main_title or 'Overview',
            'anchor': anchor,
            'type': 'main',
            'level': 1
        })

    # 2. Extract Headings and Summaries from Topics
    topic_matches = list(re.finditer(
        r'<div class=["\']?(C[A-Za-z0-9_]+)["\']?[^>]*>\s*<div class=["\']?CTopic["\']?[^>]*>([\s\S]*?)<(h[1-4])\b[^>]*class=["\']?CTitle["\']?[^>]*>([\s\S]*?)</\3>',
        html_text
    ))

    # Also check if MainTopic or first section has Contents or Summary
    main_summary_m = re.search(r'id=["\']?MainTopic["\']?[\s\S]*?<div class=["\']?Summary["\']?[^>]*>[\s\S]*?<div class=["\']?STitle["\']?>([^<]+)<', html_text)
    if main_summary_m:
        stitle = html.unescape(main_summary_m.group(1).strip())
        is_contents = (stitle.lower() == 'contents')
        headings.append({
            'title': 'Contents' if is_contents else 'Summary',
            'anchor': 'Contents' if is_contents else 'Summary',
            'type': 'contents' if is_contents else 'summary',
            'level': 1
        })
    elif ('class="Summary"' in html_text or 'class=Summary' in html_text) and not topic_matches:
        headings.append({
            'title': 'Summary',
            'anchor': 'Summary',
            'type': 'summary',
            'level': 1
        })

    has_h2 = any(m.group(3).upper() == 'H2' for m in topic_matches)
    current_group = None

    for m in topic_matches:
        cls = m.group(1)
        tag = m.group(3).upper()
        inner = m.group(4)
        title = html.unescape(re.sub(r'<[^>]+>', '', inner).strip())
        if not title:
            continue

        a_m = re.search(r'<a\s+name=["\']([^"\']+)["\']', inner)
        anchor = a_m.group(1) if a_m else ''

        # Avoid duplicate of main topic if it's the class/file declaration
        if main_title and title == main_title and cls != 'CGroup':
            continue

        is_h2 = (tag == 'H2')
        is_cgroup = ('CGroup' in cls)

        if has_h2:
            if is_h2:
                current_group = title
                headings.append({
                    'title': title,
                    'anchor': anchor or f"group_{len(headings)}",
                    'type': 'h2-group',
                    'level': 1
                })
            else:
                item_type = 'group-header' if is_cgroup else cls.lower().replace('c', '', 1)
                headings.append({
                    'title': title,
                    'anchor': anchor,
                    'type': item_type,
                    'group': current_group,
                    'level': 2 if current_group else 1
                })
        else:
            if is_cgroup:
                current_group = title
                headings.append({
                    'title': title,
                    'anchor': anchor or f"group_{len(headings)}",
                    'type': 'group',
                    'level': 1
                })
            else:
                item_type = cls.lower().replace('c', '', 1)
                headings.append({
                    'title': title,
                    'anchor': anchor,
                    'type': item_type,
                    'group': current_group,
                    'level': 2 if current_group else 1
                })

    return headings

def get_rel_root(depth):
    """Return relative path back to root based on folder depth."""
    return pbc.get_rel_root(depth)

def highlight_code_lines(code, filename):
    """
    Stateful tokenizer for SystemVerilog and C/C++ files.
    Returns a list of HTML table rows with line numbers and syntax highlighted tokens.
    """
    rows, _ = pbc.highlight_code_lines(code, filename, clickable_sym_links=False)
    return rows

def index_source_symbols():
    """Scan all source files to build SYMBOL_MAP with exact line numbers."""
    print("Indexing source symbols...")
    for root, dirs, files in os.walk(SRC_DIR):
        for f in sorted(files):
            full_path = Path(root) / f
            rel_path = full_path.relative_to(SRC_DIR).as_posix()
            try:
                with open(full_path, 'r', encoding='latin-1') as file:
                    lines = file.read().splitlines()
            except Exception as e:
                print(f"Error reading {full_path}: {e}")
                continue

            symbols_in_file = []

            for line_no, line in enumerate(lines, 1):
                mc = CLASS_DEF_REGEX.match(line)
                if mc:
                    cname = mc.group(1)
                    SYMBOL_MAP[cname] = {'file': rel_path, 'line': line_no, 'type': 'class'}
                    symbols_in_file.append({'name': cname, 'line': line_no, 'type': 'class'})

                mm = MACRO_DEF_REGEX.match(line)
                if mm:
                    mname = mm.group(1)
                    SYMBOL_MAP[f"`{mname}"] = {'file': rel_path, 'line': line_no, 'type': 'macro'}
                    SYMBOL_MAP[mname] = {'file': rel_path, 'line': line_no, 'type': 'macro'}
                    symbols_in_file.append({'name': f"`{mname}", 'line': line_no, 'type': 'macro'})

                mf = METHOD_DEF_REGEX.match(line)
                if mf:
                    mkind, mname = mf.group(1), mf.group(2)
                    symbols_in_file.append({'name': mname, 'line': line_no, 'type': mkind})

            FILE_SYMBOLS[rel_path] = symbols_in_file

    print(f"Total symbols indexed: {len(SYMBOL_MAP)} across {len(FILE_SYMBOLS)} files.")

def map_docs_to_sources():
    """Identify which doc file corresponds to which source file and map classes to docs."""
    for root, dirs, files in os.walk(DOCS_FILES_DIR):
        for f in files:
            if not f.endswith('.html'):
                continue
            doc_path = Path(root) / f
            doc_rel = doc_path.relative_to(DOCS_FILES_DIR).as_posix()
            try:
                with open(doc_path, 'r', encoding='latin-1') as df:
                    txt = df.read()
            except Exception as e:
                print(f"Error reading {doc_path} for mapping: {e}")
                continue

            m = re.search(r'href=["\'](?:(?:\.\./)+)src/([^"\']+)["\']', txt)
            if m:
                src_rel = m.group(1).replace('\\', '/')
                # Only map if it's an actual source code file in src
                if (SRC_DIR / src_rel).exists():
                    DOC_TO_SRC_MAP[doc_rel] = src_rel
                    SRC_TO_DOC_MAP[src_rel] = doc_rel

    # Register orphan doc files
    for doc_rel, src_rel, _, _ in ORPHAN_DOC_FILES:
        if (SRC_DIR / src_rel).exists():
            DOC_TO_SRC_MAP[doc_rel] = src_rel
            SRC_TO_DOC_MAP[src_rel] = doc_rel

    # Populate CLASS_TO_DOC_MAP
    for doc_rel, src_rel in DOC_TO_SRC_MAP.items():
        if src_rel in UVM_DB.get('files', {}):
            for cname in UVM_DB['files'][src_rel].get('classes', []):
                CLASS_TO_DOC_MAP[cname] = doc_rel
        for sym_name, sym_info in SYMBOL_MAP.items():
            if sym_info.get('type') == 'class' and sym_info.get('file') == src_rel:
                CLASS_TO_DOC_MAP[sym_name] = doc_rel

    print(f"Mapped {len(DOC_TO_SRC_MAP)} doc files to source files ({len(CLASS_TO_DOC_MAP)} classes mapped to docs).")

def generate_source_views():
    """Generate syntax-highlighted HTML views in src_view/ for all 155 source files."""
    print("Generating syntax-highlighted source views...")
    if OUTPUT_SRC_VIEW.exists():
        shutil.rmtree(OUTPUT_SRC_VIEW)
    OUTPUT_SRC_VIEW.mkdir(parents=True, exist_ok=True)

    count = 0
    for root, dirs, files in os.walk(SRC_DIR):
        for f in sorted(files):
            src_file = Path(root) / f
            rel_path = src_file.relative_to(SRC_DIR).as_posix()
            out_file = OUTPUT_SRC_VIEW / (rel_path + ".html")
            out_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                with open(src_file, 'r', encoding='latin-1') as sf:
                    code = sf.read()
            except Exception as e:
                print(f"Error reading {src_file}: {e}")
                continue

            depth = len(rel_path.split('/'))
            root_rel = get_rel_root(depth)

            rows = highlight_code_lines(code, f)
            doc_rel = SRC_TO_DOC_MAP.get(rel_path)
            syms = FILE_SYMBOLS.get(rel_path, [])

            html_content = pbc.render_source_viewer(
                rel_path=rel_path,
                code=code,
                rows=rows,
                syms=syms,
                doc_rel=doc_rel,
                root_rel=root_rel
            )

            with open(out_file, 'w', encoding='utf-8', newline='\n') as of:
                of.write(html_content)
            count += 1

    print(f"Generated {count} syntax-highlighted source views in {OUTPUT_SRC_VIEW}.")

def resolve_cross_doc_path(current_rel_path, target_rel_href):
    """Resolve a relative doc link against current doc file path."""
    cur_dir = posixpath.dirname(current_rel_path)
    combined = posixpath.join(cur_dir, target_rel_href) if cur_dir else target_rel_href
    return posixpath.normpath(combined)

def enrich_topic_body(w_body, w_start, is_main, a_name, rel_path, associated_src, root_rel):
    """Enrich topic HTML with exact AST source links, decl/impl buttons, derived classes, and badges."""
    clean_a = re.sub(r'#\([^)]*\)', '', a_name) if a_name else None
    cls_m = re.search(r'class=["\'](C[A-Za-z0-9_]+)["\']', w_start)
    cls_name = cls_m.group(1) if cls_m else 'CTopicWrap'

    if is_main or cls_name == 'CClass':
        target_cname = None
        if clean_a and clean_a in UVM_DB.get('classes', {}):
            target_cname = clean_a
        elif associated_src and associated_src in UVM_DB.get('files', {}):
            f_classes = UVM_DB['files'][associated_src].get('classes', [])
            if f_classes:
                target_cname = f_classes[0]

        if target_cname and target_cname in UVM_DB.get('classes', {}):
            c_info = UVM_DB['classes'][target_cname]
            decl_f = c_info['file']
            start_l = c_info['start_line']
            w_body = re.sub(r'href=["\'][^"\']*src_view/[^"\']*["\']', f'href="{root_rel}src_view/{decl_f}.html#L{start_l}"', w_body, count=1)
            w_body = re.sub(r'data-src-line=["\']\d+["\']', f'data-src-line="{start_l}"', w_body, count=1)
            w_body = re.sub(r'data-src-file=["\'][^"\']*["\']', f'data-src-file="{decl_f}"', w_body, count=1)

            children = c_info.get('children', [])
            if children:
                derived_box = pbc.render_derived_classes_card(
                    children, root_rel, CLASS_TO_DOC_MAP, UVM_DB, GLOBAL_DOC_ANCHOR_MAPS
                )
                w_body = re.sub(r'(</h[123]>)', r'\1' + derived_box, w_body, count=1)

            if target_cname in CLASS_TO_EXAMPLE_MAP:
                ex_rel, ex_title = CLASS_TO_EXAMPLE_MAP[target_cname]
                ex_box = pbc.render_example_callout(ex_rel, ex_title, root_rel)
                w_body = re.sub(r'(</h[123]>)', r'\1' + ex_box, w_body, count=1)

    elif cls_name in ('CMethod', 'CFunction', 'CTask'):
        decl_f = None
        decl_l = None
        impl_f = None
        impl_l = None
        overridden_from = None
        overridden_by = []

        if clean_a and '.' in clean_a:
            cn, mn = clean_a.split('.', 1)
            if cn in UVM_DB.get('classes', {}) and mn in UVM_DB['classes'][cn].get('methods', {}):
                minfo = UVM_DB['classes'][cn]['methods'][mn]
                decl_f = minfo['decl']['file']
                decl_l = minfo['decl']['start_line']
                impl = minfo.get('impl')
                if impl:
                    impl_f = impl['file']
                    impl_l = impl['start_line']
                overridden_from = minfo.get('overridden_from')
                overridden_by = minfo.get('overridden_by', [])
        elif clean_a and associated_src and associated_src in FILE_SYMBOLS:
            for sym in FILE_SYMBOLS[associated_src]:
                if sym['name'] == clean_a and sym['type'] in ('function', 'task'):
                    decl_f = associated_src
                    decl_l = sym['line']
                    break

        target_f = impl_f if (impl_f and impl_l) else decl_f
        target_l = impl_l if (impl_f and impl_l) else decl_l

        if target_f and target_l:
            w_body = re.sub(r'href=["\'][^"\']*src_view/[^"\']*["\']', f'href="{root_rel}src_view/{target_f}.html#L{target_l}"', w_body, count=1)
            w_body = re.sub(r'data-src-line=["\']\d+["\']', f'data-src-line="{target_l}"', w_body, count=1)
            w_body = re.sub(r'data-src-file=["\'][^"\']*["\']', f'data-src-file="{target_f}"', w_body, count=1)

            badges = []
            if overridden_from:
                badges.append(f'<span class="badge-override" title="Overrides base method from {overridden_from}">Overrides {overridden_from}</span>')
            if overridden_by:
                badges.append(f'<span class="badge-subclass" title="Overridden in {len(overridden_by)} derived class(es)">Overridden in {len(overridden_by)} subclasses</span>')

            if badges:
                meta_bar = f'<div class="method-meta-bar">{"".join(badges)}</div>'
                w_body = re.sub(r'(</h[23]>)', r'\1' + meta_bar, w_body, count=1)

    elif cls_name == 'CMacro':
        m_key = clean_a.lstrip('`').split('.')[-1] if clean_a else None
        if m_key and m_key in UVM_DB.get('macros', {}):
            minfo = UVM_DB['macros'][m_key]
            mf = minfo['file']
            ml = minfo['start_line']
            w_body = re.sub(r'href=["\'][^"\']*src_view/[^"\']*["\']', f'href="{root_rel}src_view/{mf}.html#L{ml}"', w_body, count=1)
            w_body = re.sub(r'data-src-line=["\']\d+["\']', f'data-src-line="{ml}"', w_body, count=1)
            w_body = re.sub(r'data-src-file=["\'][^"\']*["\']', f'data-src-file="{mf}"', w_body, count=1)
            pass

    return w_body

def modernize_doc_files():
    """Modernize all 146 doc files from uvm-1.2/docs/html/files/ into docs_view/."""
    print("Modernizing UVM documentation pages...")
    if OUTPUT_DOCS_VIEW.exists():
        shutil.rmtree(OUTPUT_DOCS_VIEW)
    OUTPUT_DOCS_VIEW.mkdir(parents=True, exist_ok=True)

    # Pass 1: Build anchor to ID maps for all doc files
    global GLOBAL_DOC_ANCHOR_MAPS
    GLOBAL_DOC_ANCHOR_MAPS = {}
    global_doc_anchor_maps = GLOBAL_DOC_ANCHOR_MAPS
    for root, dirs, files in os.walk(DOCS_FILES_DIR):
        for f in sorted(files):
            if not f.endswith('.html'):
                continue
            doc_file = Path(root) / f
            rel_path = doc_file.relative_to(DOCS_FILES_DIR).as_posix()
            try:
                with open(doc_file, 'r', encoding='latin-1') as df:
                    raw_html = df.read()
            except Exception as e:
                print(f"Error reading {doc_path} for mapping: {e}")
                continue

            content_start = raw_html.find('<div id=Content>')
            content_end = raw_html.find('<!--START_ND_TOOLTIPS-->', content_start)
            if content_end == -1: content_end = raw_html.find('</div><!--Content-->', content_start)
            if content_end == -1: content_end = raw_html.find('</body>', content_start)
            body = raw_html[content_start:content_end] if content_start != -1 else raw_html

            a_map = {}
            main_m = re.search(r'<div\s+class=["\']?CTopic["\']?\s+id=["\']?MainTopic["\']?[^>]*>[\s\S]*?<a\s+name=["\']([^"\']+)["\']', body)
            if main_m:
                a_map[main_m.group(1)] = 'doc-nav-main'
                a_map['MainTopic'] = 'doc-nav-main'
            if '<div class=Summary>' in body or '<div class="Summary">' in body:
                a_map['Summary'] = 'doc-nav-summary'
            if 'class=STitle>Contents<' in body or 'class="STitle">Contents<' in body:
                a_map['Contents'] = 'doc-nav-contents'

            parts = re.split(r'(<div class=["\']C[A-Za-z0-9_]+["\']\s*>\s*<div class=["\']?CTopic["\']?[^>]*>)', body)
            seq = 0
            for i in range(1, len(parts), 2):
                w_start = parts[i]
                w_body = parts[i+1]
                is_main = ('id=MainTopic' in w_start or 'id="MainTopic"' in w_start)
                a_m = re.search(r'<a\s+name=["\']([^"\']+)["\']', w_body)
                a_name = a_m.group(1) if a_m else None
                if is_main:
                    if a_name:
                        a_map[a_name] = 'doc-nav-main'
                        clean_a = re.sub(r'#\([^)]*\)', '', a_name)
                        if clean_a != a_name:
                            a_map[clean_a] = 'doc-nav-main'
                else:
                    seq += 1
                    if a_name:
                        target_id = f"doc-nav-item-{seq}"
                        a_map[a_name] = target_id
                        clean_a = re.sub(r'#\([^)]*\)', '', a_name)
                        if clean_a != a_name:
                            a_map[clean_a] = target_id

            global_doc_anchor_maps[rel_path] = a_map

    count = 0
    for root, dirs, files in os.walk(DOCS_FILES_DIR):
        for f in sorted(files):
            if not f.endswith('.html'):
                continue
            doc_file = Path(root) / f
            rel_path = doc_file.relative_to(DOCS_FILES_DIR).as_posix()
            out_file = OUTPUT_DOCS_VIEW / rel_path
            out_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                with open(doc_file, 'r', encoding='latin-1') as df:
                    raw_html = df.read()
            except Exception as e:
                print(f"Error reading {doc_file}: {e}")
                continue

            depth = len(rel_path.split('/'))
            root_rel = get_rel_root(depth)

            # Extract Title
            title_m = re.search(r'<title>(.*?)</title>', raw_html, re.IGNORECASE)
            page_title = title_m.group(1).strip() if title_m else "UVM Reference"

            # Associated source file & line
            associated_src = DOC_TO_SRC_MAP.get(rel_path)
            target_line = 1
            if associated_src:
                for sym in FILE_SYMBOLS.get(associated_src, []):
                    if sym['type'] == 'class':
                        target_line = sym['line']
                        break

            # Extract main content div
            content_start = raw_html.find('<div id=Content>')
            content_end = raw_html.find('<!--START_ND_TOOLTIPS-->', content_start)
            if content_end == -1:
                content_end = raw_html.find('</div><!--Content-->', content_start)
            if content_end == -1:
                content_end = raw_html.find('</body>', content_start)

            if content_start != -1 and content_end != -1:
                body_content = raw_html[content_start:content_end]
            else:
                body_content = raw_html

            # Replace source links in body
            def replace_src(m):
                subpath = m.group(1).replace('\\', '/')
                # Only rewrite to src_view if file actually exists in src
                if (SRC_DIR / subpath).exists():
                    line_no = target_line if subpath == associated_src else 1
                    return f'href="{root_rel}src_view/{subpath}.html#L{line_no}" class="src-code-link" data-src-file="{subpath}" data-src-line="{line_no}"'
                else:
                    return f'href="#"'

            body_content = re.sub(
                r'href=["\'](?:(?:\.\./)+)src/([^"\']+)["\']',
                replace_src,
                body_content
            )

            # Clean old tooltips and event handlers
            body_content = re.sub(r'onmouse(?:over|out)="[^"]*"', '', body_content, flags=re.IGNORECASE)
            body_content = re.sub(r"onmouse(?:over|out)='[^']*'", '', body_content, flags=re.IGNORECASE)
            body_content = re.sub(r'class=FramedContentPage', 'class="doc-content-page"', body_content)

            # Inject static IDs and data-anchor into topic blocks
            parts = re.split(r'(<div class=["\']C[A-Za-z0-9_]+["\']\s*>\s*<div class=["\']?CTopic["\']?[^>]*>)', body_content)
            new_parts = [parts[0]]
            seq = 0
            local_map = global_doc_anchor_maps.get(rel_path, {})

            for i in range(1, len(parts), 2):
                w_start = parts[i]
                w_body = parts[i+1]
                is_main = ('id=MainTopic' in w_start or 'id="MainTopic"' in w_start)
                a_m = re.search(r'<a\s+name=["\']([^"\']+)["\']', w_body)
                a_name = a_m.group(1) if a_m else None
                cls_m = re.search(r'class=["\'](C[A-Za-z0-9_]+)["\']', w_start)
                cls_name = cls_m.group(1) if cls_m else 'CTopicWrap'

                # Enrich topic body with AST links, decl/impl buttons, derived classes, and badges
                w_body = enrich_topic_body(w_body, w_start, is_main, a_name, rel_path, associated_src, root_rel)

                if is_main:
                    safe_id = 'doc-nav-main'
                    if a_name:
                        w_body = re.sub(r'<a\s+name=["\']' + re.escape(a_name) + r'["\']', f'<a name="{a_name}" id="{a_name}"', w_body, count=1)
                    mod_start = f'<div class="{cls_name}" id="{safe_id}" data-doc-topic="{safe_id}"' + (f' data-anchor="{a_name}"' if a_name else '') + '><div class="CTopic" id="MainTopic">'
                else:
                    seq += 1
                    safe_id = f"doc-nav-item-{seq}"
                    if a_name:
                        w_body = re.sub(r'<a\s+name=["\']' + re.escape(a_name) + r'["\']', f'<a name="{a_name}" id="{a_name}"', w_body, count=1)
                        mod_start = f'<div class="{cls_name}" id="{safe_id}" data-doc-topic="{safe_id}" data-anchor="{a_name}"><div class="CTopic">'
                    else:
                        mod_start = f'<div class="{cls_name}" id="{safe_id}" data-doc-topic="{safe_id}"><div class="CTopic">'
                # Differentiate Contents vs Summary for each topic wrapper
                def tag_summary_block(m):
                    block = m.group(0)
                    st_m = re.search(r'class=["\']?STitle["\']?>([^<]+)<', block)
                    st_title = st_m.group(1).strip() if st_m else 'Summary'
                    if st_title.lower() == 'contents':
                        return f'<div class="Summary ContentsSummary" id="doc-nav-contents" data-anchor="Contents"><div class="STitle">Contents</div>'
                    else:
                        sum_id = f"doc-nav-summary-{safe_id}" if not is_main else "doc-nav-summary"
                        sum_anchor = f"Summary-{safe_id}" if not is_main else "Summary"
                        return f'<div class="Summary ClassSummary" id="{sum_id}" data-anchor="{sum_anchor}"><div class="STitle">{st_title}</div>'

                w_body = re.sub(r'<div class=["\']?Summary["\']?>[\s\S]*?<div class=["\']?STitle["\']?>[\s\S]*?</div>', tag_summary_block, w_body)

                new_parts.append(mod_start)
                new_parts.append(w_body)

            body_content = "".join(new_parts)

            # Rewrite all internal href links to use the exact destination element IDs
            def rewrite_doc_href(m):
                full_match = m.group(0)
                href_val = m.group(1)
                if href_val.startswith('#'):
                    anchor_target = href_val[1:]
                    if anchor_target in local_map:
                        dest_id = local_map[anchor_target]
                        return f'href="#{dest_id}" data-target-id="{dest_id}"'
                elif '#' in href_val and not href_val.startswith(('http://', 'https://', 'javascript:')) and 'src_view' not in href_val and 'src/' not in href_val:
                    file_part, anchor_target = href_val.split('#', 1)
                    target_rel_file = resolve_cross_doc_path(rel_path, file_part)
                    target_map = global_doc_anchor_maps.get(target_rel_file, {})
                    if anchor_target in target_map:
                        dest_id = target_map[anchor_target]
                        return f'href="{file_part}#{dest_id}" data-target-id="{dest_id}"'
                return full_match

            body_content = re.sub(r'href=["\']([^"\']+)["\']', rewrite_doc_href, body_content)

            # Syntax highlight documentation code blocks (<pre>)
            body_content = process_doc_code_blocks(body_content)

            # Syntax highlight method/class/task prototypes (<table class=Prototype>)
            body_content = process_doc_prototypes(body_content)

            # Wrap diagrams in clean framing card with enlarge/zoom button
            body_content = wrap_doc_diagrams(body_content)

            # Record headings for left navigation subheadings and search
            doc_key = f"docs_view/{rel_path}"
            DOC_HEADINGS_MAP[doc_key] = extract_doc_headings(body_content, rel_path)

            # Injected "View Source Code" badge only if real source exists
            view_source_banner = ""
            if associated_src and (SRC_DIR / associated_src).exists():
                src_view_url = f"{root_rel}src_view/{associated_src}.html#L{target_line}"
                view_source_banner = f'''<div class="doc-source-banner">
                  <div class="banner-info">
                    <svg class="banner-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    <span class="file-label">Source:</span>
                    <a href="{src_view_url}" class="banner-file-link src-code-link" data-src-url="{src_view_url}" title="Open source code at line {target_line}"><code>src/{html.escape(associated_src)}</code></a>
                  </div>
                  <div class="banner-actions">
                    <a href="{src_view_url}" class="banner-icon-btn src-code-link" data-src-url="{src_view_url}" title="Open source code at line {target_line}" aria-label="Open source code at line {target_line}">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                    </a>
                  </div>
                </div>'''

            # Breadcrumb navigation
            breadcrumbs_html = build_breadcrumbs_html(rel_path, page_title, root_rel)

            modern_html = pbc.render_html_shell(
                title=f"{page_title} | UVM 1.2 Documentation",
                body_content=body_content,
                root_rel=root_rel,
                breadcrumbs_html=breadcrumbs_html,
                banner_html=view_source_banner,
                extra_scripts=[f"{root_rel}js/doc_page.js"],
                include_toc=True
            )

            with open(out_file, 'w', encoding='utf-8', newline='\n') as of:
                of.write(modern_html)
            count += 1

    print(f"Modernized {count} documentation pages in {OUTPUT_DOCS_VIEW}.")

def modernize_index_pages():
    """Modernize NaturalDocs index pages (Classes.html, General*.html, etc.) into docs_view/index/."""
    index_src_dir = DOCS_DIR / "index"
    if not index_src_dir.exists():
        return
    output_index_dir = OUTPUT_DOCS_VIEW / "index"
    output_index_dir.mkdir(parents=True, exist_ok=True)
    print("Modernizing NaturalDocs index pages...")

    count = 0
    for f in sorted(index_src_dir.glob("*.html")):
        raw_html = f.read_text(encoding="latin-1")
        page_name = f.stem
        title = f"{page_name} Index" if not page_name.startswith("General") else f"General Index ({page_name})"

        content_start = raw_html.find('<div id=Index>')
        if content_start == -1: content_start = raw_html.find('<div id="Index">')
        content_end = raw_html.find('<!--START_ND_TOOLTIPS-->')
        if content_end == -1: content_end = raw_html.find('</div><!--Index-->')
        if content_end == -1: content_end = raw_html.find('</body>')

        body = raw_html[content_start:content_end] if content_start != -1 else raw_html

        def repl_href(m):
            url = m.group(1)
            if url.startswith('../files/'):
                doc_part = url[len('../files/'):]
                f_part, _, a_part = doc_part.partition('#')
                if a_part:
                    target_id = GLOBAL_DOC_ANCHOR_MAPS.get(f_part, {}).get(a_part, a_part)
                    return f'href="../{f_part}#{target_id}"'
                return f'href="../{f_part}"'
            return f'href="{url}"'

        body = re.sub(r'href="([^"]+)"', repl_href, body)

        breadcrumbs_html = build_breadcrumbs_html(f"index/{f.name}", page_name, "../../")

        modern_html = pbc.render_html_shell(
            title=f"{title} | UVM 1.2 Documentation",
            body_content=body,
            root_rel="../../",
            breadcrumbs_html=breadcrumbs_html,
            extra_scripts=["../../js/doc_page.js"],
            include_toc=False
        )

        out_file = output_index_dir / f.name
        out_file.write_text(modern_html, encoding='utf-8', newline='\n')
        count += 1

    print(f"Modernized {count} index pages in {output_index_dir}.")

def generate_orphan_doc_pages():
    """Generate modern doc pages for the 15 classes across 5 files lacking legacy Accellera docs."""
    print("Generating documentation pages for orphan UVM classes...")
    count = 0
    for doc_rel, src_rel, main_cname, page_title in ORPHAN_DOC_FILES:
        out_file = OUTPUT_DOCS_VIEW / doc_rel
        out_file.parent.mkdir(parents=True, exist_ok=True)
        depth = len(doc_rel.split('/'))
        root_rel = get_rel_root(depth)
        subsys = doc_rel.split('/')[0].capitalize()

        classes_in_file = UVM_DB.get('files', {}).get(src_rel, {}).get('classes', [])
        first_cname = classes_in_file[0] if classes_in_file else main_cname
        first_line = UVM_DB.get('classes', {}).get(first_cname, {}).get('start_line', 1)

        src_view_url = f"{root_rel}src_view/{src_rel}.html#L{first_line}"
        breadcrumbs = build_breadcrumbs_html(doc_rel, page_title, root_rel)

        banner = f'''<div class="doc-source-banner">
  <div class="banner-info">
    <svg class="banner-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
    <span class="file-label">Source:</span>
    <a href="{src_view_url}" class="banner-file-link src-code-link" data-src-url="{src_view_url}" title="Open source code at line {first_line}"><code>src/{html.escape(src_rel)}</code></a>
  </div>
  <div class="banner-actions">
    <a href="{src_view_url}" class="banner-icon-btn src-code-link" data-src-url="{src_view_url}" title="Open source code at line {first_line}" aria-label="Open source code at line {first_line}">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
    </a>
  </div>
</div>'''

        body_parts = ['<div id="Content">']
        seq = 0
        a_map = {}

        for c_idx, cname in enumerate(classes_in_file):
            c_info = UVM_DB.get('classes', {}).get(cname, {})
            c_line = c_info.get('start_line', 1)
            raw_doc = c_info.get('doc', {}).get('summary', '') if c_info.get('doc') else ''
            if raw_doc and ('copyright' in raw_doc.lower() or 'all rights reserved' in raw_doc.lower()):
                raw_doc = ''
            c_doc = raw_doc or f"Class {cname} defined in src/{src_rel}."
            c_params = c_info.get('parameters_raw')
            c_parent = c_info.get('parent')
            children = c_info.get('children', [])

            is_main = (c_idx == 0)
            topic_id = 'doc-nav-main' if is_main else f'doc-nav-item-{c_idx}'
            a_map[cname] = topic_id
            if is_main:
                a_map['MainTopic'] = 'doc-nav-main'

            # Pills for derived classes if any
            pills = []
            for child in sorted(children):
                if child in CLASS_TO_DOC_MAP:
                    ch_doc = CLASS_TO_DOC_MAP[child]
                    target_id = GLOBAL_DOC_ANCHOR_MAPS.get(ch_doc, {}).get(child, 'doc-nav-main')
                    pills.append(f'<a href="{root_rel}docs_view/{ch_doc}#{target_id}" class="derived-class-pill" data-target-id="{target_id}" title="Documentation for {child}">{child}</a>')
                elif child in UVM_DB.get('classes', {}):
                    ch_f = UVM_DB['classes'][child]['file']
                    ch_l = UVM_DB['classes'][child]['start_line']
                    pills.append(f'<a href="{root_rel}src_view/{ch_f}.html#L{ch_l}" class="derived-class-pill src-code-link" data-src-file="{ch_f}" data-src-line="{ch_l}" title="Source for {child}">{child}</a>')
                else:
                    pills.append(f'<span class="derived-class-pill">{child}</span>')

            derived_box = f'''<div class="derived-classes-card collapsed">
  <div class="derived-classes-header" role="button" tabindex="0" title="Click to expand/collapse subclasses">
    <svg class="derived-classes-chevron" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
    <span>Direct Subclasses ({len(children)})</span>
  </div>
  <div class="derived-classes-list">{"".join(pills)}</div>
</div>''' if pills else ""

            body_parts.append(f'''<div class="CClass" id="{topic_id}" data-doc-topic="{topic_id}" data-anchor="{cname}">
<div class="CTopic" {"id='MainTopic'" if is_main else ""}>
  <h1 class="CTitle"><a href="{root_rel}src_view/{src_rel}.html#L{c_line}" class="src-code-link" data-src-file="{src_rel}" data-src-line="{c_line}">{cname}</a></h1>
  {derived_box}
  <div class="CBody">
    <p>{html.escape(c_doc)}</p>
    {f"<p><b>Base Class:</b> <code>{c_parent}</code></p>" if c_parent else ""}
    {f"<p><b>Parameters:</b> <code>#({c_params})</code></p>" if c_params else ""}
  </div>
</div>
</div>''')

            # Summary table of methods
            methods = c_info.get('methods', {})
            if methods:
                sum_id = f"doc-nav-summary-{cname}"
                body_parts.append(f'''<div class="Summary" id="{sum_id}" data-anchor="Summary-{cname}">
<div class="STitle">Methods Summary: {cname}</div>
<div class="SBody">
<table border="0" cellspacing="0" cellpadding="0" class="STable">''')
                for mname, minfo in methods.items():
                    seq += 1
                    m_item_id = f"doc-nav-item-m-{seq}"
                    minfo['_nav_id'] = m_item_id
                    a_map[f"{cname}.{mname}"] = m_item_id
                    a_map[mname] = m_item_id
                    m_ret = minfo.get('return_type') or ''
                    m_params = minfo.get("parameters_raw", "()")
                    body_parts.append(f'''<tr class="SMethod SIndent1">
  <td class="SEntry"><a href="#{m_item_id}" data-target-id="{m_item_id}">{mname}</a></td>
  <td class="SDescription"><code>{m_ret} {mname}{m_params}</code></td>
</tr>''')
                body_parts.append('</table></div></div>')

                # Method definitions
                body_parts.append(f'''<div class="CGroup"><div class="CTopic"><h2 class="CTitle">Methods: {cname}</h2></div></div>''')
                for mname, minfo in methods.items():
                    m_id = minfo.get('_nav_id', f"doc-nav-item-m-{seq}")
                    decl_l = minfo['decl']['start_line']
                    impl = minfo.get('impl')
                    impl_l = impl['start_line'] if impl else None
                    impl_f = impl['file'] if impl and impl.get('file') else None
                    target_m_f = impl_f if (impl_f and impl_l) else src_rel
                    target_m_l = impl_l if (impl_f and impl_l) else decl_l
                    m_kind = minfo.get('kind', 'function')
                    m_ret = minfo.get('return_type') or 'void'
                    m_params = minfo.get('parameters_raw', '()')
                    overridden_from = minfo.get('overridden_from')
                    overridden_by = minfo.get('overridden_by', [])

                    badges = []
                    if overridden_from:
                        badges.append(f'<span class="badge-override" title="Overrides base method from {overridden_from}">Overrides {overridden_from}</span>')
                    if overridden_by:
                        badges.append(f'<span class="badge-subclass" title="Overridden in {len(overridden_by)} derived class(es)">Overridden in {len(overridden_by)} subclasses</span>')

                    meta_bar = f'<div class="method-meta-bar">{"".join(badges)}</div>' if badges else ''
                    proto_html = f'<table border="0" cellspacing="0" cellpadding="0" class="Prototype"><tr><td><span class="sv-keyword">{m_kind}</span> <span class="sv-type">{m_ret}</span> <span class="sv-proto-name">{mname}</span> <span class="sv-params">{m_params}</span></td></tr></table>'
                    m_doc = minfo.get('doc', {}).get('summary', '') if minfo.get('doc') else f"Method <code>{mname}</code> of class <code>{cname}</code>."

                    body_parts.append(f'''<div class="CMethod" id="{m_id}" data-doc-topic="{m_id}" data-anchor="{cname}.{mname}">
<div class="CTopic">
  <h3 class="CTitle"><a name="{cname}.{mname}" id="{cname}.{mname}" href="{root_rel}src_view/{target_m_f}.html#L{target_m_l}" class="src-code-link" data-src-file="{target_m_f}" data-src-line="{target_m_l}">{mname}</a></h3>
  {meta_bar}
  <blockquote>{proto_html}</blockquote>
  <div class="CBody"><p>{m_doc}</p></div>
</div>
</div>''')

        body_parts.append('</div>')
        body_content = "\n".join(body_parts)

        # Update global maps
        GLOBAL_DOC_ANCHOR_MAPS[doc_rel] = a_map
        doc_key = f"docs_view/{doc_rel}"
        DOC_HEADINGS_MAP[doc_key] = extract_doc_headings(body_content, doc_rel)

        page_html = pbc.render_html_shell(
            title=f"{page_title} | UVM 1.2 Documentation",
            body_content=body_content,
            root_rel=root_rel,
            breadcrumbs_html=breadcrumbs,
            banner_html=banner,
            extra_scripts=[f"{root_rel}js/doc_page.js"],
            include_toc=True
        )

        with open(out_file, 'w', encoding='utf-8', newline='\n') as of:
            of.write(page_html)
        count += 1

    print(f"Generated {count} orphan documentation pages in {OUTPUT_DOCS_VIEW}.")

def copy_assets():
    """Copy documentation images and diagram assets to images/ and docs_view/images/."""
    print("Copying documentation images and diagram assets...")
    if DOCS_IMAGES_DIR.exists():
        OUTPUT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        docs_img_dir = OUTPUT_DOCS_VIEW / "images"
        docs_img_dir.mkdir(parents=True, exist_ok=True)
        img_count = 0
        for img in DOCS_IMAGES_DIR.glob("*.*"):
            shutil.copy2(img, OUTPUT_IMAGES_DIR / img.name)
            shutil.copy2(img, docs_img_dir / img.name)
            img_count += 1
        print(f"Copied {img_count} images to {OUTPUT_IMAGES_DIR} and {docs_img_dir}.")
    else:
        print(f"Warning: {DOCS_IMAGES_DIR} does not exist.")

def parse_navigation_and_categories():
    """Extract categories from menu.html and normalize URLs to docs_view."""
    menu_file = DOCS_DIR / "menu.html"
    if not menu_file.exists():
        print("Warning: menu.html not found.")
        return []

    with open(menu_file, 'r', encoding='latin-1') as f:
        html_text = f.read()

    def parse_snippet(snippet):
        entries = []
        i = 0
        length = len(snippet)
        while i < length:
            entry_start = snippet.find('<div class=MEntry>', i)
            if entry_start == -1:
                break
            depth = 0
            pos = entry_start
            end_pos = -1
            while pos < length:
                if snippet.startswith('<div', pos):
                    depth += 1
                    pos += 4
                elif snippet.startswith('</div>', pos):
                    depth -= 1
                    pos += 6
                    if depth == 0:
                        end_pos = pos
                        break
                else:
                    pos += 1
            if end_pos == -1:
                break
            entry_html = snippet[entry_start + len('<div class=MEntry>'):end_pos - 6]

            if '<div class=MGroup>' in entry_html:
                m_title = re.search(r'<div class=MGroup><a [^>]*>([^<]+)</a>', entry_html)
                title = html.unescape(m_title.group(1).strip()) if m_title else "Group"
                content_start = entry_html.find('<div class=MGroupContent')
                if content_start != -1:
                    inner_depth = 0
                    p = content_start
                    gc_end = -1
                    while p < len(entry_html):
                        if entry_html.startswith('<div', p):
                            inner_depth += 1
                            p += 4
                        elif entry_html.startswith('</div>', p):
                            inner_depth -= 1
                            p += 6
                            if inner_depth == 0:
                                gc_end = p
                                break
                        else:
                            p += 1
                    tag_close = entry_html.find('>', content_start) + 1
                    sub_html = entry_html[tag_close:gc_end - 6] if gc_end != -1 else ""
                    children = parse_snippet(sub_html)
                    # Check if the first child is an Overview page:
                    # If so, link it to the group (overviewHref) and remove it from children
                    overview_href = None
                    if children and children[0].get('type') == 'file' and children[0].get('title', '').strip().lower() == 'overview':
                        overview_href = children[0]['href']
                        children = children[1:]

                    entry_dict = {'type': 'group', 'title': title, 'children': children}
                    if overview_href:
                        entry_dict['overviewHref'] = overview_href
                    entries.append(entry_dict)
            elif '<div class=MFile>' in entry_html or '<div class=MIndex>' in entry_html:
                is_index = '<div class=MIndex>' in entry_html
                m = re.search(r'<a href="([^"]+)">([^<]+)</a>', entry_html)
                if m:
                    raw_href = m.group(1).strip()
                    norm_href = raw_href
                    if raw_href.startswith('files/'):
                        norm_href = 'docs_view/' + raw_href[len('files/'):]
                    elif raw_href.startswith('index/'):
                        norm_href = 'docs_view/' + raw_href
                    entries.append({
                        'type': 'index' if is_index else 'file',
                        'title': html.unescape(m.group(2).strip()),
                        'href': norm_href
                    })
            i = end_pos
        return entries

    menu_start = html_text.find('<div id=Menu>')
    menu_end = html_text.find('<script', menu_start)
    menu_content = html_text[menu_start + len('<div id=Menu>'):menu_end]
    categories = parse_snippet(menu_content)

    # Register orphan doc pages in navigation menu tree
    for cat in categories:
        if cat.get('title') == 'Base':
            cat['children'].extend([
                {'type': 'file', 'title': 'uvm_spell_chkr', 'href': 'docs_view/base/uvm_spell_chkr-svh.html'},
                {'type': 'file', 'title': 'uvm_resource_specializations', 'href': 'docs_view/base/uvm_resource_specializations-svh.html'}
            ])
        elif cat.get('title') == 'Sequences':
            cat['children'].extend([
                {'type': 'file', 'title': 'uvm_sequence_builtin', 'href': 'docs_view/seq/uvm_sequence_builtin-svh.html'},
                {'type': 'file', 'title': 'uvm_sequencer_analysis_fifo', 'href': 'docs_view/seq/uvm_sequencer_analysis_fifo-svh.html'}
            ])

    categories.append({
        'type': 'group',
        'title': 'Deprecated',
        'children': [
            {'type': 'file', 'title': 'uvm_resource_converter', 'href': 'docs_view/deprecated/uvm_resource_converter-svh.html'}
        ]
    })
    return categories

def build_source_tree():
    """Build JSON tree structure for browsing src_view files."""
    tree = {'name': 'src', 'type': 'dir', 'children': []}
    for root, dirs, files in os.walk(SRC_DIR):
        dirs.sort()
        rel_root = Path(root).relative_to(SRC_DIR).as_posix()
        curr_node = tree
        if rel_root != '.':
            parts = rel_root.split('/')
            for p in parts:
                match = next((c for c in curr_node['children'] if c['name'] == p and c['type'] == 'dir'), None)
                if not match:
                    match = {'name': p, 'type': 'dir', 'children': []}
                    curr_node['children'].append(match)
                curr_node = match

        for f in sorted(files):
            file_rel = (Path(root) / f).relative_to(SRC_DIR).as_posix()
            curr_node['children'].append({
                'name': f,
                'type': 'file',
                'path': file_rel,
                'url': f"src_view/{file_rel}.html",
                'doc_url': f"docs_view/{SRC_TO_DOC_MAP[file_rel]}" if file_rel in SRC_TO_DOC_MAP else None
            })
    return tree

def build_search_index(categories):
    """Build unified search data with classes, macros, methods, files, and categories."""
    search_items = []

    # 1. Add all classes
    for cname, info in sorted(SYMBOL_MAP.items()):
        if info['type'] == 'class':
            src_file = info['file']
            doc_file = SRC_TO_DOC_MAP.get(src_file)
            doc_anchor = GLOBAL_DOC_ANCHOR_MAPS.get(doc_file, {}).get(cname) if doc_file else None
            doc_url = f"docs_view/{doc_file}#{doc_anchor}" if (doc_file and doc_anchor) else (f"docs_view/{doc_file}" if doc_file else None)
            search_items.append({
                'name': cname,
                'type': 'class',
                'category': src_file.split('/')[0].capitalize(),
                'src': f"src_view/{src_file}.html#L{info['line']}",
                'doc': doc_url,
                'desc': f"UVM Class defined in src/{src_file}:{info['line']}"
            })

    # 2. Add macros
    for mname, info in sorted(SYMBOL_MAP.items()):
        if info['type'] == 'macro' and mname.startswith('`'):
            src_file = info['file']
            doc_file = SRC_TO_DOC_MAP.get(src_file)
            search_items.append({
                'name': mname,
                'type': 'macro',
                'category': 'Macros',
                'src': f"src_view/{src_file}.html#L{info['line']}",
                'doc': f"docs_view/{doc_file}" if doc_file else None,
                'desc': f"UVM Macro defined in src/{src_file}:{info['line']}"
            })

    # 3. Add source files
    for src_rel in sorted(FILE_SYMBOLS.keys()):
        doc_file = SRC_TO_DOC_MAP.get(src_rel)
        search_items.append({
            'name': src_rel,
            'type': 'file',
            'category': 'Source Code',
            'src': f"src_view/{src_rel}.html",
            'doc': f"docs_view/{doc_file}" if doc_file else None,
            'desc': f"Source file in src/{src_rel}"
        })

    # 4. Extract symbols from Classes.html index if available
    class_index_file = DOCS_DIR / "index" / "Classes.html"
    if class_index_file.exists():
        with open(class_index_file, 'r', encoding='latin-1') as cf:
            c_html = cf.read()
        entries = re.findall(r'<div class=IEntry><a href="([^"]+)"[^>]*class=ISymbol>([^<]+)</a></div>', c_html)
        for link, name in entries:
            clean_link = link.replace('../files/', '')
            # Verify clean_link exists in docs_view
            if not (OUTPUT_DOCS_VIEW / clean_link.split('#')[0]).exists():
                continue
            src_link = None
            if name in SYMBOL_MAP:
                s_info = SYMBOL_MAP[name]
                src_link = f"src_view/{s_info['file']}.html#L{s_info['line']}"
            if not any(x['name'] == name for x in search_items):
                search_items.append({
                    'name': name,
                    'type': 'class',
                    'category': 'Reference',
                    'doc': f"docs_view/{clean_link}",
                    'src': src_link,
                    'desc': f"UVM Class Reference: {name}"
                })

    # 5. Extract methods from Methods*.html index files
    method_index_files = sorted((DOCS_DIR / "index").glob("Methods*.html"))
    tip_to_kind = {}
    for mf in method_index_files:
        try:
            with open(mf, 'r', encoding='latin-1') as f:
                m_html = f.read()
        except Exception as e:
            print(f"Error reading {mf} for tooltips: {e}")
            continue
        for m in re.finditer(r'<div class=CToolTip id="?([^">]+)"?>([\s\S]*?)</div>\s*</div>', m_html):
            tid = m.group(1).replace('"', '').strip()
            body = m.group(2)
            clean = re.sub(r'<[^>]+>', ' ', body)
            if re.search(r'\btask\b', clean, re.IGNORECASE):
                tip_to_kind[(mf.name, tid)] = 'task'
            elif re.search(r'\bfunction\b', clean, re.IGNORECASE):
                tip_to_kind[(mf.name, tid)] = 'function'

    known_tasks = {
        'run_phase', 'pre_reset_phase', 'reset_phase', 'post_reset_phase',
        'pre_configure_phase', 'configure_phase', 'post_configure_phase',
        'pre_main_phase', 'main_phase', 'post_main_phase',
        'pre_shutdown_phase', 'shutdown_phase', 'post_shutdown_phase',
        'body', 'pre_body', 'post_body', 'pre_do', 'mid_do', 'post_do',
        'wait_for', 'wait_for_relevant', 'get_next_item', 'try_next_item', 'item_done',
        'wait_for_sequences', 'do_read', 'do_write', 'read', 'write', 'get', 'put', 'peek',
        'transport', 'b_transport', 'execute', 'run', 'wait_trigger', 'wait_ptrigger'
    }

    seen_methods = set()
    for mf in method_index_files:
        try:
            with open(mf, 'r', encoding='latin-1') as f:
                c_html = f.read()
        except Exception as e:
            print(f"Error reading {mf} for search index: {e}")
            continue

        matches = re.finditer(r'<span class=ISymbol>([^<]+)</span>\s*<div class=ISubIndex>([\s\S]*?)</div>', c_html)
        for m in matches:
            mname = html.unescape(m.group(1).strip())
            sub_html = m.group(2)
            link_matches = re.finditer(r'<a\s+href="([^"]+)"(?:[^>]*onMouseOver="ShowTip\(event,\s*\'([^\']+)\'[^"]*")?[^>]*class=IParent>([^<]+)</a>', sub_html)
            for lm in link_matches:
                href = lm.group(1)
                tt_id = lm.group(2)
                parent_class = html.unescape(lm.group(3).strip())
                clean_link = href.replace('../files/', '')
                parts = clean_link.split('#', 1)
                file_part = parts[0]
                raw_anchor = parts[1] if len(parts) > 1 else ''

                if not (OUTPUT_DOCS_VIEW / file_part).exists():
                    continue

                dedup_key = (mname, parent_class)
                if dedup_key in seen_methods:
                    continue
                seen_methods.add(dedup_key)

                # Determine whether it is a task or a function
                mkind = None
                if tt_id and (mf.name, tt_id) in tip_to_kind:
                    mkind = tip_to_kind[(mf.name, tt_id)]

                target_id = raw_anchor
                doc_map = GLOBAL_DOC_ANCHOR_MAPS.get(file_part, {})
                if raw_anchor in doc_map:
                    target_id = doc_map[raw_anchor]
                else:
                    clean_anchor = re.sub(r'#\([^)]*\)', '', raw_anchor)
                    if clean_anchor in doc_map:
                        target_id = doc_map[clean_anchor]
                    else:
                        suffix = f".{mname}"
                        found_id = None
                        for a_key, a_val in doc_map.items():
                            if a_key == mname or a_key.endswith(suffix):
                                found_id = a_val
                                break
                        if found_id:
                            target_id = found_id

                doc_link = f"docs_view/{file_part}#{target_id}" if target_id else f"docs_view/{file_part}"

                src_link = None
                src_rel = DOC_TO_SRC_MAP.get(file_part)
                # Check UVM_DB for implementation line first
                if parent_class and parent_class in UVM_DB.get('classes', {}) and mname in UVM_DB['classes'][parent_class].get('methods', {}):
                    minfo_search = UVM_DB['classes'][parent_class]['methods'][mname]
                    s_impl = minfo_search.get('impl')
                    if s_impl and s_impl.get('start_line'):
                        s_f = s_impl.get('file') or (minfo_search.get('decl', {}).get('file')) or src_rel
                        src_link = f"src_view/{s_f}.html#L{s_impl['start_line']}"
                    elif minfo_search.get('decl', {}).get('start_line'):
                        s_f = minfo_search['decl'].get('file') or src_rel
                        src_link = f"src_view/{s_f}.html#L{minfo_search['decl']['start_line']}"

                if not src_link and src_rel:
                    syms = FILE_SYMBOLS.get(src_rel, [])
                    sym_match = next((s for s in syms if s['name'] == mname and s['type'] in ('task', 'function')), None)
                    if not sym_match:
                        sym_match = next((s for s in syms if s['name'] == mname), None)
                    if sym_match:
                        src_link = f"src_view/{src_rel}.html#L{sym_match['line']}"
                        if not mkind or mkind == 'unknown':
                            if sym_match['type'] in ('task', 'function'):
                                mkind = sym_match['type']
                    else:
                        cls_match = next((s for s in syms if s['type'] == 'class'), None)
                        line_no = cls_match['line'] if cls_match else 1
                        src_link = f"src_view/{src_rel}.html#L{line_no}"

                if not mkind or mkind == 'unknown':
                    if mname in known_tasks:
                        mkind = 'task'
                    else:
                        mkind = 'function'

                desc_label = 'Task' if mkind == 'task' else 'Function'
                search_items.append({
                    'name': mname,
                    'type': mkind,
                    'category': parent_class,
                    'src': src_link,
                    'doc': doc_link,
                    'desc': f"{desc_label} in {parent_class}"
                })

    # 6. Complement with any methods from DOC_HEADINGS_MAP not yet indexed
    for doc_key, headings in DOC_HEADINGS_MAP.items():
        doc_rel = doc_key.replace("docs_view/", "")
        class_name = None
        for h in headings:
            if h.get('type') == 'main':
                class_name = h.get('title')
                break
        if not class_name:
            class_name = doc_rel.split('/')[-1].replace('-svh.html', '').replace('-txt.html', '')

        for h in headings:
            if h.get('type') == 'method':
                mname = h.get('title')
                if not mname:
                    continue
                dedup_key = (mname, class_name)
                if dedup_key in seen_methods:
                    continue
                seen_methods.add(dedup_key)

                anchor = h.get('anchor', '')
                doc_link = f"{doc_key}#{anchor}" if anchor else doc_key

                mkind = 'function'
                src_link = None
                src_rel = DOC_TO_SRC_MAP.get(doc_rel)
                if src_rel:
                    syms = FILE_SYMBOLS.get(src_rel, [])
                    sym_match = next((s for s in syms if s['name'] == mname and s['type'] in ('task', 'function')), None)
                    if not sym_match:
                        sym_match = next((s for s in syms if s['name'] == mname), None)
                    if sym_match:
                        src_link = f"src_view/{src_rel}.html#L{sym_match['line']}"
                        if sym_match['type'] in ('task', 'function'):
                            mkind = sym_match['type']
                    else:
                        cls_match = next((s for s in syms if s['type'] == 'class'), None)
                        line_no = cls_match['line'] if cls_match else 1
                        src_link = f"src_view/{src_rel}.html#L{line_no}"

                if mkind == 'function' and mname in known_tasks:
                    mkind = 'task'

                desc_label = 'Task' if mkind == 'task' else 'Function'
                search_items.append({
                    'name': mname,
                    'type': mkind,
                    'category': class_name,
                    'src': src_link,
                    'doc': doc_link,
                    'desc': f"{desc_label} in {class_name}" + (f" ({h['group']})" if h.get('group') else "")
                })

    return search_items

def populate_doc_headings_from_docs_view():
    """Populate DOC_HEADINGS_MAP from existing files in OUTPUT_DOCS_VIEW for fast search-only generation."""
    print("Reading headings from existing docs_view...")
    if not OUTPUT_DOCS_VIEW.exists():
        print(f"Warning: {OUTPUT_DOCS_VIEW} does not exist. DOC_HEADINGS_MAP will be empty.")
        return

    count = 0
    for root, dirs, files in os.walk(OUTPUT_DOCS_VIEW):
        for f in files:
            if not f.endswith('.html'):
                continue
            full_path = Path(root) / f
            rel_path = full_path.relative_to(OUTPUT_DOCS_VIEW).as_posix()
            doc_key = f"docs_view/{rel_path}"
            try:
                with open(full_path, 'r', encoding='utf-8') as df:
                    txt = df.read()
                DOC_HEADINGS_MAP[doc_key] = extract_doc_headings(txt, rel_path)
                count += 1
            except Exception as e:
                print(f"Error reading {full_path}: {e}")
    print(f"Extracted headings from {count} documentation pages.")

def generate_search_and_nav_data():
    """Generate js/search_data.js for client-side search and menu tree."""
    print("Generating search index and navigation data...")
    categories = parse_navigation_and_categories()
    source_tree = build_source_tree()
    search_items = build_search_index(categories)

    # Generate and integrate interactive examples
    examples_catalog = build_examples.generate_all_examples()
    search_items.extend(examples_catalog.get("searchItems", []))
    examples_tree = examples_catalog.get("examplesTree", [])
    example_to_src = examples_catalog.get("exampleToSrc", {})

    # Pre-calculate Doc <-> Source cross-referencing maps
    def get_target_line(src):
        for sym in FILE_SYMBOLS.get(src, []):
            if sym['type'] in ('class', 'macro'):
                return sym['line']
        return 1

    doc_to_src = {doc: f"src_view/{src}.html#L{get_target_line(src)}" for doc, src in DOC_TO_SRC_MAP.items()}
    src_to_doc = {f"{src}.html": f"docs_view/{doc}" for src, doc in SRC_TO_DOC_MAP.items()}

    OUTPUT_JS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_JS_DIR / "search_data.js"

    # Strict JSON formatting for the payload
    payload = {
        "categories": categories,
        "sourceTree": source_tree,
        "examplesTree": examples_tree,
        "searchIndex": search_items,
        "docToSrc": doc_to_src,
        "srcToDoc": src_to_doc,
        "exampleToSrc": example_to_src,
        "docHeadings": DOC_HEADINGS_MAP
    }

    js_content = f"""/**
 * Generated UVM 1.2 Documentation Data & Navigation Index
 * Contains category tree, source tree, and full search index.
 */
const UVM_DATA = {json.dumps(payload, indent=2)};
"""
    with open(out_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(js_content)
    print(f"Generated {out_file} with {len(search_items)} searchable items.")

def main():
    parser = argparse.ArgumentParser(description="UVM 1.2 Documentation & Web Source Viewer Generator")
    parser.add_argument("--search-only", action="store_true", help="Only regenerate js/search_data.js without re-rendering HTML views")
    args = parser.parse_args()

    print("=" * 60)
    print("  UVM 1.2 Documentation & Web Source Viewer Generator")
    print("=" * 60)

    index_source_symbols()
    map_docs_to_sources()

    # Pre-parse navigation tree to initialize breadcrumb hierarchy
    nav_categories = parse_navigation_and_categories()
    init_doc_breadcrumbs_map(nav_categories)

    if args.search_only:
        populate_doc_headings_from_docs_view()
        generate_search_and_nav_data()
    else:
        generate_source_views()
        modernize_doc_files()
        modernize_index_pages()
        generate_orphan_doc_pages()
        copy_assets()
        generate_search_and_nav_data()

    print("=" * 60)
    print("  Documentation build complete successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
