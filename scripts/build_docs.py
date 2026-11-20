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
import build_tutorial
import generate_quick_symbols
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
ND_TAG_REGEX = re.compile(r'^\s*(?://|/\*|\*)\s*(Variable|Type|Enum|Port|Export|Imp|Constant|Parameter)\s*:\s*([^\r\n]+)', re.IGNORECASE)
TYPEDEF_REGEX = re.compile(r'^\s*typedef\s+(?:enum|struct)?.*?\b([a-zA-Z0-9_]+)\s*;')

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
    catalog = sh._get_uvm_symbol_catalog()
    uvm_types = catalog['classes'] | catalog['types']
    uvm_consts = catalog['constants']
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
            elif tok in sh.SV_CONSTANTS or tok in uvm_consts or tok.startswith('UVM_'):
                res.append(f'<span class="sv-constant">{tok}</span>')
            elif tok in uvm_types or tok.startswith(('uvm_', 'ovm_')):
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
    catalog = sh._get_uvm_symbol_catalog()
    uvm_types = catalog['classes'] | catalog['types']
    uvm_consts = catalog['constants']
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
            elif w in sh.SV_CONSTANTS or w in uvm_consts or w.startswith('UVM_'):
                return f'<span class="sv-constant">{w}</span>'
            elif w in uvm_types or w.startswith(('uvm_', 'ovm_')):
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

# Orphan doc files (files in UVM 1.2 src without Accellera legacy HTML doc pages)
ORPHAN_DOC_FILES = [
    ("base/uvm_spell_chkr-svh.html", "base/uvm_spell_chkr.svh", "uvm_spell_chkr", "Spell Checker Utility"),
    ("base/uvm_resource_specializations-svh.html", "base/uvm_resource_specializations.svh", "uvm_resource_specializations", "Specialized Resource Types"),
    ("base/uvm_version-svh.html", "base/uvm_version.svh", "uvm_version", "UVM Version & Revision"),
    ("seq/uvm_sequence_builtin-svh.html", "seq/uvm_sequence_builtin.svh", "uvm_sequence_builtin", "Builtin Sequences"),
    ("seq/uvm_sequencer_analysis_fifo-svh.html", "seq/uvm_sequencer_analysis_fifo.svh", "uvm_sequencer_analysis_fifo", "Sequencer Analysis FIFO"),
    ("macros/uvm_phase_defines-svh.html", "macros/uvm_phase_defines.svh", "uvm_phase_defines", "Phase Defines"),
    ("macros/uvm_printer_defines-svh.html", "macros/uvm_printer_defines.svh", "uvm_printer_defines", "Printer Defines"),
    ("macros/uvm_deprecated_defines-svh.html", "macros/uvm_deprecated_defines.svh", "uvm_deprecated_defines", "Deprecated Defines"),
    ("dpi/uvm_dpi-svh.html", "dpi/uvm_dpi.svh", "uvm_dpi", "DPI-C Interface"),
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

def _is_comment_only_line(s):
    """Return True if a stripped line contains only comment syntax (no code)."""
    if not s:
        return False
    if s.startswith('//'):
        return True
    if s.startswith('/*'):
        if '*/' in s:
            rem = re.sub(r'/\*.*?\*/', '', s).strip()
            return not rem or rem.startswith('//')
        return True
    if s.startswith('*'):
        return True
    return False

def build_doc_source_banner(src_rel, line_num, root_rel):
    """Render a compact single-link source banner for documentation pages."""
    src_view_url = f"{root_rel}src_view/{src_rel}.html#L{line_num}"
    info_html = (
        '<svg class="banner-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2">'
        '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>'
        '</svg>'
        '<span class="file-label">Source</span>'
        f'<a href="{src_view_url}" class="banner-file-link src-code-link" '
        f'data-src-url="{src_view_url}" title="Open source code at line {line_num}">'
        f'<code>src/{html.escape(src_rel)}</code>'
        '</a>'
    )
    return pbc.render_banner(info_html)

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

                # NaturalDocs tag detection (Variables, Types, Enums, Ports, etc.)
                mnd = ND_TAG_REGEX.match(line)
                if mnd:
                    tag_kind = mnd.group(1).lower()
                    raw_val = mnd.group(2).strip().rstrip('*/')
                    tokens = raw_val.split()
                    tag_name = tokens[-1] if tokens else ''
                    tag_name = re.sub(r'[^a-zA-Z0-9_`+*]', '', tag_name)
                    if tag_name:
                        decl_line = None
                        for j in range(line_no, min(line_no + 60, len(lines))):
                            l_str = lines[j].strip()
                            if not l_str or _is_comment_only_line(l_str):
                                continue
                            decl_line = j + 1
                            break
                        target_line = decl_line if decl_line is not None else line_no
                        symbols_in_file.append({
                            'name': tag_name,
                            'raw': raw_val,
                            'line': target_line,
                            'type': tag_kind
                        })
                        if tag_kind in ('type', 'enum'):
                            # Never overwrite an actual class definition!
                            if tag_name not in SYMBOL_MAP or SYMBOL_MAP[tag_name]['type'] != 'class':
                                SYMBOL_MAP[tag_name] = {'file': rel_path, 'line': target_line, 'type': tag_kind}

                # Direct typedef detection (ignore forward class declarations 'typedef class <name>;')
                mtd = TYPEDEF_REGEX.match(line)
                if mtd and not re.match(r'^\s*typedef\s+class\b', line):
                    tname = mtd.group(1)
                    if not any(s['name'] == tname and s['line'] == line_no for s in symbols_in_file):
                        symbols_in_file.append({'name': tname, 'raw': tname, 'line': line_no, 'type': 'type'})
                        # Never overwrite an actual class definition!
                        if tname not in SYMBOL_MAP or SYMBOL_MAP[tname]['type'] != 'class':
                            SYMBOL_MAP[tname] = {'file': rel_path, 'line': line_no, 'type': 'type'}

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

def strip_title_source_link(w_body):
    """Remove source code links from topic headings (CTitle) while preserving anchor name/id."""
    def clean_title_anchor(m):
        h_open = m.group(1)
        inner = m.group(2)
        h_close = m.group(3)

        def remove_link(am):
            a_open = am.group(1)
            a_text = am.group(2)
            a_close = am.group(3)
            name_m = re.search(r'\bname=["\']([^"\']+)["\']', a_open)
            id_m = re.search(r'\bid=["\']([^"\']+)["\']', a_open)
            name_val = name_m.group(1) if name_m else None
            id_val = id_m.group(1) if id_m else None

            attrs = []
            if name_val:
                attrs.append(f'name="{name_val}"')
            if id_val and id_val != name_val:
                attrs.append(f'id="{id_val}"')

            if attrs:
                return f'<a {" ".join(attrs)}>{a_text}{a_close}'
            else:
                return a_text

        cleaned_inner = re.sub(r'(<a\b[^>]*>)([\s\S]*?)(</a>)', remove_link, inner, count=1)
        return f'{h_open}{cleaned_inner}{h_close}'

    return re.sub(r'(<h[1-6]\s+class=["\']?CTitle["\']?[^>]*>)([\s\S]*?)(</h[1-6]>)', clean_title_anchor, w_body, count=1)

def _match_wildcard_classes(clean_a, raw_a, associated_src):
    """Return concrete classes in associated_src matching a wildcard TLM1 class topic."""
    if not clean_a or '*' not in clean_a or not associated_src:
        return []
    f_classes = UVM_DB.get('files', {}).get(associated_src, {}).get('classes', [])
    prefix, suffix = clean_a.split('*', 1)
    candidates = [c for c in f_classes if c.startswith(prefix) and c.endswith(suffix)]
    if not candidates:
        return []
    is_req_rsp = 'REQ' in (raw_a or '') and 'RSP' in (raw_a or '')
    matched = []
    for cname in candidates:
        params = UVM_DB.get('classes', {}).get(cname, {}).get('parameters_raw', '') or ''
        c_is_req_rsp = ('REQ' in params and 'RSP' in params)
        if is_req_rsp == c_is_req_rsp:
            matched.append(cname)
    return matched or candidates


def _tag_wildcard_src_link(w_body, pattern, group_key, member_name=None):
    """Mark the first src-code-link in w_body with wildcard metadata for interactive disambiguation."""
    extra = f' data-wildcard-pattern="{html.escape(pattern)}" data-wildcard-group="{html.escape(group_key)}"'
    if member_name:
        extra += f' data-wildcard-member="{html.escape(member_name)}"'
    return re.sub(
        r'class=(["\']?)([^"\'>]*\bsrc-code-link\b[^"\'>]*)\1',
        lambda m: f'class="{m.group(2)} wildcard-src-trigger"{extra}',
        w_body,
        count=1
    )


def enrich_topic_body(w_body, w_start, is_main, a_name, rel_path, associated_src, root_rel):
    """Enrich topic HTML with exact AST source links, decl/impl buttons, derived classes, and badges."""
    clean_a = re.sub(r'#\([^)]*\)', '', a_name) if a_name else None
    if clean_a:
        clean_a = clean_a.split('#')[0].strip()
    cls_m = re.search(r'class=["\'](C[A-Za-z0-9_]+)["\']', w_start)
    cls_name = cls_m.group(1) if cls_m else 'CTopicWrap'

    # Structural / non-code topics: remove source code links from titles
    if cls_name in ('CGroup', 'CSection', 'CFile'):
        w_body = strip_title_source_link(w_body)

    # STRICT: Only enrich class hierarchy & class details for genuine CClass topics!
    # Never decorate CSection / CGeneric / CFile topics, which caused the first class's hierarchy
    # to be duplicated onto the top-level section header when multiple classes exist on one page.
    elif cls_name == 'CClass':
        target_cname = None
        is_wildcard_class = bool(clean_a and '*' in clean_a)
        wildcard_group = ('REQ_RSP' if ('REQ' in (a_name or '') and 'RSP' in (a_name or '')) else 'T') if is_wildcard_class else None
        if clean_a and clean_a in UVM_DB.get('classes', {}):
            target_cname = clean_a
        elif is_wildcard_class:
            w_matched = _match_wildcard_classes(clean_a, a_name, associated_src)
            if w_matched:
                target_cname = w_matched[0]
        elif associated_src and associated_src in UVM_DB.get('files', {}):
            f_classes = UVM_DB['files'][associated_src].get('classes', [])
            for fc in f_classes:
                if clean_a and (fc.lower() == clean_a.lower() or clean_a.lower().startswith(fc.lower()) or fc.lower().startswith(clean_a.lower())):
                    target_cname = fc
                    break
            if not target_cname and len(f_classes) == 1:
                target_cname = f_classes[0]

        if not target_cname and clean_a:
            clean_lower = clean_a.lower().replace(' ', '')
            if 'export' in clean_lower and associated_src and 'tlm' in str(associated_src):
                target_cname = 'uvm_port_base'
            elif 'port' in clean_lower and associated_src and 'tlm' in str(associated_src):
                target_cname = 'uvm_port_base'
            elif 'imp' in clean_lower and associated_src and 'tlm' in str(associated_src):
                target_cname = 'uvm_port_base'

        if target_cname and target_cname in UVM_DB.get('classes', {}):
            c_info = UVM_DB['classes'][target_cname]
            decl_f = c_info['file']
            start_l = c_info['start_line']
            w_body = re.sub(r'href=["\'][^"\']*src_view/[^"\']*["\']', f'href="{root_rel}src_view/{decl_f}.html#L{start_l}"', w_body, count=1)
            w_body = re.sub(r'data-src-line=["\']\d+["\']', f'data-src-line="{start_l}"', w_body, count=1)
            w_body = re.sub(r'data-src-file=["\'][^"\']*["\']', f'data-src-file="{decl_f}"', w_body, count=1)
            if is_wildcard_class:
                w_body = _tag_wildcard_src_link(w_body, clean_a, wildcard_group)

            hierarchy_widget = pbc.render_class_hierarchy_card(
                target_cname, root_rel, CLASS_TO_DOC_MAP, UVM_DB, GLOBAL_DOC_ANCHOR_MAPS
            )
            if hierarchy_widget:
                # Replace the old hierarchy visualization in-place at the exact same location in the Summary table
                old_h_pattern = r'<div class=[\x22\x27]?ClassHierarchy[\x22\x27]?>[\s\S]*?</table>\s*</div>'
                if re.search(old_h_pattern, w_body):
                    w_body = re.sub(old_h_pattern, lambda m: hierarchy_widget, w_body, count=1)
                elif re.search(r'(<!--\s*PROTOTYPE\s*-->\s*<tr class=["\']SPrototype SIndent1["\']><td colspan=2 class=["\']SEntry SIndent1["\']>Class Declaration</td></tr>)', w_body):
                    h_row = f'''<tr class="SHierarchy SIndent1"><td colspan=2 class="SEntry SIndent1">Class Hierarchy</td></tr>
<tr class="SPrototype SIndent1"><td colspan=2 class="SDescription">
{hierarchy_widget}
</td></tr>
'''
                    w_body = re.sub(
                        r'(<!--\s*PROTOTYPE\s*-->\s*<tr class=["\']SPrototype SIndent1["\']><td colspan=2 class=["\']SEntry SIndent1["\']>Class Declaration</td></tr>)',
                        lambda m: h_row + m.group(1),
                        w_body,
                        count=1
                    )
                elif re.search(r'(<tr class=["\']SPrototype SIndent1["\']><td colspan=2 class=["\']SEntry SIndent1["\']>Class Declaration</td></tr>)', w_body):
                    h_row = f'''<tr class="SHierarchy SIndent1"><td colspan=2 class="SEntry SIndent1">Class Hierarchy</td></tr>
<tr class="SPrototype SIndent1"><td colspan=2 class="SDescription">
{hierarchy_widget}
</td></tr>
'''
                    w_body = re.sub(
                        r'(<tr class=["\']SPrototype SIndent1["\']><td colspan=2 class=["\']SEntry SIndent1["\']>Class Declaration</td></tr>)',
                        lambda m: h_row + m.group(1),
                        w_body,
                        count=1
                    )
                elif re.search(r'(<tr class=["\']?SMain["\']?>[\s\S]*?</tr>)', w_body):
                    h_row = f'''<tr class="SHierarchy SIndent1"><td colspan=2 class="SEntry SIndent1">Class Hierarchy</td></tr>
<tr class="SPrototype SIndent1"><td colspan=2 class="SDescription">
{hierarchy_widget}
</td></tr>'''
                    w_body = re.sub(
                        r'(<tr class=["\']?SMain["\']?>[\s\S]*?</tr>)',
                        lambda m: m.group(1) + '\n' + h_row,
                        w_body,
                        count=1
                    )
                else:
                    # Fallback for topics without Summary table
                    w_body = re.sub(r'(</h[123]>)', lambda m: m.group(1) + hierarchy_widget, w_body, count=1)

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

        if a_name and '*' in a_name and '.' in a_name:
            w_cn, w_mn = a_name.split('.', 1)
            w_clean_cn = re.sub(r'#\([^)]*\)', '', w_cn).strip()
            w_group = 'REQ_RSP' if ('REQ' in w_cn and 'RSP' in w_cn) else 'T'
            w_body = _tag_wildcard_src_link(w_body, w_clean_cn, w_group, member_name=w_mn)

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

    elif cls_name in ('CVariable', 'CType', 'CEnumeration', 'CPort', 'CParameter', 'CConstant', 'CGeneric'):
        target_f = associated_src
        target_l = None

        if clean_a and associated_src and associated_src in FILE_SYMBOLS:
            f_syms = FILE_SYMBOLS[associated_src]
            # Symbol name can be scoped (e.g. uvm_comparer.policy -> policy, uvm_callbacks#(T,CB).T -> T)
            sym_clean = clean_a.split('.')[-1].strip()
            norm_clean = sym_clean.split('_')[-1] if '_' in sym_clean and any(s['name'] == sym_clean.split('_')[-1] for s in f_syms) else sym_clean

            # Try exact match, normalized match, substring match
            sym_match = next((s for s in f_syms if s['name'] == sym_clean), None)
            if not sym_match and norm_clean != sym_clean:
                sym_match = next((s for s in f_syms if s['name'] == norm_clean), None)
            if not sym_match:
                sym_match = next((s for s in f_syms if s['name'] == clean_a), None)
            if not sym_match and '*' in sym_clean:
                if 'uvm_field' in sym_clean and 'flag' in sym_clean:
                    sym_match = next((s for s in f_syms if s['name'] == 'UVM_ALL_ON'), None)
                if not sym_match:
                    w_prefix = sym_clean.split('*', 1)[0].lstrip('`')
                    if w_prefix:
                        sym_match = next((s for s in f_syms if s['name'].startswith(w_prefix)), None)
            if not sym_match:
                sym_match = next((s for s in f_syms if sym_clean in s['name'] or s['name'] in sym_clean), None)

            if sym_match:
                target_l = sym_match['line']

        # Fallback to global SYMBOL_MAP for global types / enums / constants
        if not target_l and clean_a:
            sym_clean = clean_a.split('.')[-1].strip()
            if sym_clean in SYMBOL_MAP:
                target_f = SYMBOL_MAP[sym_clean]['file']
                target_l = SYMBOL_MAP[sym_clean]['line']
            elif clean_a in SYMBOL_MAP:
                target_f = SYMBOL_MAP[clean_a]['file']
                target_l = SYMBOL_MAP[clean_a]['line']

        if target_f and target_l:
            w_body = re.sub(r'href=["\'][^"\']*src_view/[^"\']*["\']', f'href="{root_rel}src_view/{target_f}.html#L{target_l}"', w_body, count=1)
            w_body = re.sub(r'data-src-line=["\']\d+["\']', f'data-src-line="{target_l}"', w_body, count=1)
            w_body = re.sub(r'data-src-file=["\'][^"\']*["\']', f'data-src-file="{target_f}"', w_body, count=1)
        elif cls_name == 'CGeneric':
            w_body = strip_title_source_link(w_body)

    return w_body

def _clean_ast_doc(doc_obj, fallback):
    """Extract clean summary text from AST doc object, stripping license boilerplate."""
    raw = doc_obj.get('summary', '') if isinstance(doc_obj, dict) else (doc_obj or '')
    if raw:
        low = raw.lower()
        if any(tok in low for tok in ('copyright', 'all rights reserved', 'apache license', 'licensed under')):
            raw = ''
    return html.escape(raw.strip()) if raw and raw.strip() else fallback


def _render_undocumented_notice(root_rel, src_file, src_line):
    """Render a visual notice linking directly to the SystemVerilog source line when undocumented."""
    src_href = f"{root_rel}src_view/{src_file}.html#L{src_line}"
    return (
        f'<span class="undocumented-notice">'
        f'<svg class="undoc-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
        f'<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>'
        f'<span>Not officially documented &mdash; '
        f'<a href="{src_href}" class="src-code-link undoc-src-link" data-src-file="{html.escape(src_file)}" data-src-line="{src_line}">see source code</a>'
        f'</span></span>'
    )


def _is_internal_symbol(name):
    """Return True for UVM internal implementation symbols (m_*, M_*)."""
    return bool(name) and (name.startswith('m_') or name.startswith('M_') or name in ('get_t', 'process_container_c', 'sev_id_struct'))


def _render_internal_collapsible(title_label, inner_html, section_id=None, note_html=None):
    """Wrap internal symbols in a clearly marked collapsible <details> section."""
    note = note_html or 'Internal UVM implementation symbols (<code>m_*</code> / <code>M_*</code>) extracted from source. Not part of the public IEEE 1800.2 / Accellera API.'
    id_attr = f' id="{section_id}"' if section_id else ''
    return f'''<details class="internal-details-section"{id_attr}>
  <summary class="internal-section-header">
    <span class="internal-header-title">
      <svg class="internal-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
      <span>{html.escape(title_label)}</span>
    </span>
    <span class="badge-internal">Internal</span>
  </summary>
  <p class="internal-section-note">{note}</p>
  <div class="internal-section-body">
{inner_html}
  </div>
</details>'''


def _render_ast_method_entry(cname, mname, minfo, fallback_src, root_rel, item_id, is_internal=False, show_ast_badge=True):
    """Render a standardized .CMethod block from UVM AST database metadata."""
    decl = minfo.get('decl') or {}
    decl_f = decl.get('file') or fallback_src
    decl_l = decl.get('start_line') or 1
    impl = minfo.get('impl')
    impl_l = impl.get('start_line') if isinstance(impl, dict) else None
    impl_f = impl.get('file') if isinstance(impl, dict) and impl.get('file') else None
    target_f = impl_f if (impl_f and impl_l) else decl_f
    target_l = impl_l if (impl_f and impl_l) else decl_l

    m_kind = minfo.get('kind', 'function')
    m_ret = minfo.get('return_type') or ('void' if m_kind == 'function' else '')
    m_params = minfo.get('parameters_raw', '()')
    overridden_from = minfo.get('overridden_from')
    overridden_by = minfo.get('overridden_by', [])

    badges = []
    if is_internal:
        badges.append('<span class="badge-internal" title="Internal UVM implementation member">Internal</span>')
    if overridden_from:
        badges.append(f'<span class="badge-override" title="Overrides base method from {html.escape(overridden_from)}">Overrides {html.escape(overridden_from)}</span>')
    if overridden_by:
        badges.append(f'<span class="badge-subclass" title="Overridden in {len(overridden_by)} derived class(es)">Overridden in {len(overridden_by)} subclasses</span>')

    meta_bar = f'<div class="method-meta-bar">{"".join(badges)}</div>' if badges else ''
    ret_part = f'<span class="sv-type">{html.escape(m_ret)}</span> ' if m_ret else ''
    proto_html = (
        f'<table border="0" cellspacing="0" cellpadding="0" class="Prototype"><tr><td>'
        f'<span class="sv-keyword">{html.escape(m_kind)}</span> {ret_part}'
        f'<span class="sv-proto-name">{html.escape(mname)}</span> '
        f'<span class="sv-params">{html.escape(m_params)}</span>'
        f'</td></tr></table>'
    )
    m_doc = _clean_ast_doc(minfo.get('doc'), _render_undocumented_notice(root_rel, target_f, target_l))
    anchor = f"{cname}.{mname}"

    return f'''<div class="CMethod" id="{item_id}" data-doc-topic="{item_id}" data-anchor="{html.escape(anchor)}">
<div class="CTopic">
  <h3 class="CTitle"><a name="{html.escape(anchor)}" id="{html.escape(anchor)}" href="{root_rel}src_view/{target_f}.html#L{target_l}" class="src-code-link" data-src-file="{target_f}" data-src-line="{target_l}">{html.escape(mname)}</a></h3>
  {meta_bar}
  <blockquote>{proto_html}</blockquote>
  <div class="CBody"><p>{m_doc}</p></div>
</div>
</div>'''


def _render_ast_symbol_entry(sym_name, sym_type, sym_file, sym_line, root_rel, item_id, owner_cls=None, extra_desc=None, is_internal=False):
    """Render a non-method symbol (port, variable, type, macro, function) from AST."""
    anchor = f"{owner_cls}.{sym_name}" if owner_cls else sym_name
    cls_css = 'CMacro' if sym_type == 'macro' else ('CPort' if sym_type == 'port' else ('CType' if sym_type == 'type' else 'CVariable'))
    badges = [f'<span class="badge-subclass">{html.escape(sym_type.capitalize())}</span>']
    if is_internal:
        badges.append('<span class="badge-internal" title="Internal UVM implementation symbol">Internal</span>')
    meta_bar = f'<div class="method-meta-bar">{"".join(badges)}</div>'
    desc = extra_desc or _render_undocumented_notice(root_rel, sym_file, sym_line)

    return f'''<div class="{cls_css}" id="{item_id}" data-doc-topic="{item_id}" data-anchor="{html.escape(anchor)}">
<div class="CTopic">
  <h3 class="CTitle"><a name="{html.escape(anchor)}" id="{html.escape(anchor)}" href="{root_rel}src_view/{sym_file}.html#L{sym_line}" class="src-code-link" data-src-file="{sym_file}" data-src-line="{sym_line}">{html.escape(sym_name)}</a></h3>
  {meta_bar}
  <div class="CBody"><p>{desc}</p></div>
</div>
</div>'''


def _render_ast_class_block(cname, src_rel, root_rel, seq_counter, a_map, is_main=False, is_internal=False):
    """Render a complete .CClass block (hierarchy, summary, public & internal members) from UVM_DB."""
    c_info = UVM_DB.get('classes', {}).get(cname, {})
    c_file = c_info.get('file') or src_rel
    c_line = c_info.get('start_line', 1)
    c_doc = _clean_ast_doc(c_info.get('doc'), _render_undocumented_notice(root_rel, c_file, c_line))
    c_params = c_info.get('parameters_raw')
    c_parent = c_info.get('parent')

    seq_counter[0] += 1
    topic_id = 'doc-nav-main' if is_main else f'doc-nav-item-ast-{seq_counter[0]}'
    a_map[cname] = topic_id
    if is_main:
        a_map['MainTopic'] = topic_id

    hierarchy_widget = pbc.render_class_hierarchy_card(
        cname, root_rel, CLASS_TO_DOC_MAP, UVM_DB, GLOBAL_DOC_ANCHOR_MAPS
    )

    badges = []
    if is_internal:
        badges.append('<span class="badge-internal" title="Internal UVM implementation class">Internal</span>')
    meta_bar = f'<div class="method-meta-bar">{"".join(badges)}</div>' if badges else ''

    parts = [f'''<div class="CClass" id="{topic_id}" data-doc-topic="{topic_id}" data-anchor="{html.escape(cname)}">
<div class="CTopic" {"id='MainTopic'" if is_main else ""}>
  <h2 class="CTitle"><a name="{html.escape(cname)}" id="{html.escape(cname)}" href="{root_rel}src_view/{c_file}.html#L{c_line}" class="src-code-link" data-src-file="{c_file}" data-src-line="{c_line}">{html.escape(cname)}</a></h2>
  {meta_bar}
  {hierarchy_widget}
  <div class="CBody">
    <p>{c_doc}</p>
    {f"<p><b>Base Class:</b> <code>{html.escape(c_parent)}</code></p>" if c_parent else ""}
    {f"<p><b>Parameters:</b> <code>#({html.escape(c_params)})</code></p>" if c_params else ""}
  </div>
</div>''']

    methods = c_info.get('methods', {})
    pub_methods = [(m, mi) for m, mi in methods.items() if not _is_internal_symbol(m)]
    int_methods = [(m, mi) for m, mi in methods.items() if _is_internal_symbol(m)]

    if pub_methods:
        sum_id = f"doc-nav-summary-{cname}"
        parts.append(f'''<div class="Summary ClassSummary" id="{sum_id}" data-anchor="{html.escape(cname)}.Summary">
<div class="STitle">Methods Summary: {html.escape(cname)}</div>
<div class="SBorder">
<table border="0" cellspacing="0" cellpadding="0" class="STable">''')
        for mname, minfo in pub_methods:
            seq_counter[0] += 1
            m_item_id = f"doc-nav-item-ast-{seq_counter[0]}"
            minfo['_ast_nav_id'] = m_item_id
            a_map[f"{cname}.{mname}"] = m_item_id
            m_ret = minfo.get('return_type') or ''
            m_params = minfo.get('parameters_raw', '()')
            parts.append(f'''<tr class="SMethod SIndent1">
  <td class="SEntry"><a href="#{m_item_id}" data-target-id="{m_item_id}">{html.escape(mname)}</a></td>
  <td class="SDescription"><code>{html.escape(m_ret)} {html.escape(mname)}{html.escape(m_params)}</code></td>
</tr>''')
        parts.append('</table></div></div>')
        parts.append('</div>')

        for mname, minfo in pub_methods:
            m_id = minfo.get('_ast_nav_id')
            parts.append(_render_ast_method_entry(cname, mname, minfo, c_file, root_rel, m_id, is_internal=False))
    else:
        parts.append('</div>')

    if int_methods:
        int_html_parts = []
        for mname, minfo in int_methods:
            seq_counter[0] += 1
            m_id = f"doc-nav-item-ast-{seq_counter[0]}"
            a_map[f"{cname}.{mname}"] = m_id
            int_html_parts.append(_render_ast_method_entry(cname, mname, minfo, c_file, root_rel, m_id, is_internal=True))
        parts.append(_render_internal_collapsible(
            f"Internal Methods: {cname} ({len(int_methods)})",
            "\n".join(int_html_parts)
        ))

    block_html = "\n".join(parts)
    if is_internal:
        return _render_internal_collapsible(f"Internal Class: {cname}", block_html)
    return block_html


def _inject_rows_into_class_summary(slice_html, sum_rows, cname, seq_counter):
    """Inject Summary rows into the class's .Summary.ClassSummary STable (not CDescriptionList or Prototype)."""
    rows_html = "\n".join(sum_rows)
    cs_m = re.search(r'<div\s+class=["\']Summary ClassSummary["\'][^>]*>', slice_html)
    if cs_m:
        tbl_m = re.search(r'<table\b[^>]*class=["\']?STable["\']?[^>]*>', slice_html[cs_m.end():])
        if tbl_m:
            pos = cs_m.end() + tbl_m.end()
            depth = 1
            tag_re = re.compile(r'<table\b|</table>', re.IGNORECASE)
            for tm in tag_re.finditer(slice_html, pos):
                if tm.group(0).lower().startswith('<table'):
                    depth += 1
                else:
                    depth -= 1
                    if depth == 0:
                        close_idx = tm.start()
                        return slice_html[:close_idx] + "\n" + rows_html + "\n" + slice_html[close_idx:]
    # Class had no ClassSummary block (e.g. only ContentsSummary): create one inside CClass
    seq_counter[0] += 1
    sum_id = f"doc-nav-summary-ast-{seq_counter[0]}"
    sum_anchor = f"{cname}.Summary"
    new_summary = (
        f'\n<div class="Summary ClassSummary" id="{sum_id}" data-anchor="{html.escape(sum_anchor)}">'
        f'<div class="STitle">Summary</div>'
        f'<div class="SBorder"><table border="0" cellspacing="0" cellpadding="0" class="STable">\n'
        f'{rows_html}\n</table></div></div>'
    )
    end_nd = '<!--END_ND_SUMMARY-->'
    if end_nd in slice_html:
        return slice_html.replace(end_nd, end_nd + new_summary, 1)
    cbody_end = slice_html.find('</div></div></div>')
    if cbody_end != -1:
        return slice_html[:cbody_end] + new_summary + slice_html[cbody_end:]
    return slice_html + new_summary


def _inject_wildcard_selector(body_content, rel_path, associated_src, local_map, global_doc_anchor_maps):
    """Inject a page-level variant selector bar and JSON manifest on TLM1 wildcard doc pages."""
    wildcard_map = {
        'tlm1/uvm_ports.svh': 'uvm_*_port',
        'tlm1/uvm_exports.svh': 'uvm_*_export',
        'tlm1/uvm_imps.svh': 'uvm_*_imp',
    }
    pattern = wildcard_map.get(associated_src)
    if not pattern:
        return body_content, ''
    f_classes = UVM_DB.get('files', {}).get(associated_src, {}).get('classes', [])
    if not f_classes:
        return body_content, ''

    t_topic = None
    req_topic = None
    for m in re.finditer(r'<div class="CClass" id="([^"]+)"[^>]*data-anchor="([^"]+)"', body_content):
        tid, anc = m.group(1), m.group(2)
        if 'REQ' in anc and 'RSP' in anc:
            req_topic = tid
        elif not t_topic:
            t_topic = tid

    variants = []
    t_opts = []
    req_opts = []
    for cname in f_classes:
        ci = UVM_DB.get('classes', {}).get(cname, {})
        params = ci.get('parameters_raw', '') or ''
        grp = 'REQ_RSP' if ('REQ' in params and 'RSP' in params) else 'T'
        doc_topic = (req_topic if grp == 'REQ_RSP' else t_topic) or t_topic or 'doc-nav-main'
        local_map[cname] = cname
        global_doc_anchor_maps.setdefault(rel_path, {})[cname] = cname
        v_obj = {
            'name': cname,
            'file': associated_src,
            'line': ci.get('start_line', 1),
            'group': grp,
            'params': params,
            'docTopic': doc_topic
        }
        variants.append(v_obj)
        opt = f'<option value="{html.escape(cname)}">{html.escape(cname)}</option>'
        if grp == 'REQ_RSP':
            req_opts.append(opt)
        else:
            t_opts.append(opt)

    opts_html = f'<option value="">{html.escape(pattern)} (All)</option>'
    if t_opts:
        opts_html += f'<optgroup label="Unidirectional #(T)">{"".join(t_opts)}</optgroup>'
    if req_opts:
        opts_html += f'<optgroup label="Bidirectional #(REQ,RSP)">{"".join(req_opts)}</optgroup>'

    payload_json = json.dumps({
        'pattern': pattern,
        'page': rel_path,
        'variants': variants
    }).replace('</', '<\\/')

    manifest_script = f'<script type="application/json" id="uvm-wildcard-variants">{payload_json}</script>'
    in_page_bar = (
        f'<div class="wildcard-selector-bar" id="wildcard-selector-bar">'
        f'<div class="wildcard-selector-controls">'
        f'<span class="wildcard-badge">Variant</span>'
        f'<select id="wildcard-page-variant-select" class="wildcard-variant-select" '
        f'aria-label="Select concrete UVM variant" title="Switch wildcard variant">{opts_html}</select>'
        f'</div>'
        f'<span class="wildcard-hint" id="wildcard-hint">Showing all {len(variants)} {html.escape(pattern)} variants</span>'
        f'</div>'
    )
    if '<!--START_ND_SUMMARY' in body_content:
        body_content = body_content.replace('<!--START_ND_SUMMARY', in_page_bar + '\n<!--START_ND_SUMMARY', 1)
    elif '<div class=CBody>' in body_content:
        body_content = body_content.replace('<div class=CBody>', '<div class=CBody>' + in_page_bar, 1)
    elif '<div class="CBody">' in body_content:
        body_content = body_content.replace('<div class="CBody">', '<div class="CBody">' + in_page_bar, 1)

    select_html = (
        f'<span class="doc-breadcrumb-sep doc-breadcrumb-variant-sep">/</span>'
        f'<select id="wildcard-variant-select" class="doc-breadcrumb-variant-select" '
        f'aria-label="Select concrete UVM variant" title="Switch wildcard variant">{opts_html}</select>'
    )
    return body_content + '\n' + manifest_script, select_html


def inject_missing_ast_content(body_content, rel_path, associated_src, root_rel, local_map):
    """
    Inject missing AST-extracted members (public into Summary + body with Source AST badge,
    internal m_* into collapsible Internal section) and missing classes/macros for associated_src.
    """
    if not associated_src or associated_src not in UVM_DB.get('files', {}):
        return body_content

    existing_anchors = set()
    for m in re.finditer(r'(?:data-anchor|name)=["\']([^"\']+)["\']', body_content):
        a = m.group(1)
        existing_anchors.add(a)
        existing_anchors.add(re.sub(r'#\([^)]*\)', '', a))

    seq_counter = [1000]

    # Pre-index class-scoped non-method symbols (ports, variables, types) from UVM_DB
    class_extra_syms = {}
    file_macros_list = []
    for sym in UVM_DB.get('symbols_index', []):
        s_cls = sym.get('class')
        s_type = sym.get('type')
        s_file = sym.get('file')
        if s_cls and s_type in ('port', 'variable', 'type'):
            class_extra_syms.setdefault(s_cls, []).append(sym)
        elif s_file == associated_src and s_type == 'macro':
            file_macros_list.append(sym)

    # 1. Identify classes already documented on this page and inject missing members
    class_blocks = list(re.finditer(r'<div class=["\']CClass["\'][^>]*data-anchor=["\']([^"\']+)["\']', body_content))
    documented_cnames = []
    for idx_cb, cb_m in enumerate(class_blocks):
        raw_cname = cb_m.group(1)
        clean_cname = re.sub(r'#\([^)]*\)', '', raw_cname).split('#')[0].strip()
        if clean_cname in UVM_DB.get('classes', {}):
            documented_cnames.append((cb_m.start(), clean_cname))

    # Process in reverse order so string insertions preserve earlier offsets
    for idx_pos in range(len(documented_cnames) - 1, -1, -1):
        cb_start, cname = documented_cnames[idx_pos]
        cb_end = documented_cnames[idx_pos + 1][0] if (idx_pos + 1 < len(documented_cnames)) else len(body_content)
        slice_html = body_content[cb_start:cb_end]

        c_info = UVM_DB['classes'][cname]
        c_file = c_info.get('file') or associated_src
        methods = c_info.get('methods', {})

        pub_missing_methods = []
        int_missing_methods = []
        for mname, minfo in methods.items():
            if f"{cname}.{mname}" in existing_anchors or mname in existing_anchors:
                continue
            if _is_internal_symbol(mname):
                int_missing_methods.append((mname, minfo))
            else:
                pub_missing_methods.append((mname, minfo))

        pub_missing_syms = []
        int_missing_syms = []
        for sym in class_extra_syms.get(cname, []):
            sname = sym.get('short_name') or sym.get('name', '').split('::')[-1]
            if not sname or f"{cname}.{sname}" in existing_anchors or sname in existing_anchors:
                continue
            if _is_internal_symbol(sname):
                int_missing_syms.append((sname, sym))
            else:
                pub_missing_syms.append((sname, sym))

        if not (pub_missing_methods or int_missing_methods or pub_missing_syms or int_missing_syms):
            continue

        # Build public Summary rows + public detail blocks
        sum_rows = []
        pub_detail_blocks = []
        if pub_missing_methods or pub_missing_syms:
            seq_counter[0] += 1
            grp_id = f"doc-nav-group-ast-{seq_counter[0]}"
            grp_anchor = f"{cname}.Additional_APIs"
            local_map[grp_anchor] = grp_id
            sum_rows.append(f'<tr class="SGroup SIndent1"><td class=SEntry><a href="#{grp_id}" data-target-id="{grp_id}">Additional APIs</a></td><td class=SDescription></td></tr>')
            pub_detail_blocks.append(
                f'<div class="CGroup" id="{grp_id}" data-doc-topic="{grp_id}" data-anchor="{html.escape(grp_anchor)}">'
                f'<div class="CTopic"><h3 class="CTitle"><a name="{html.escape(grp_anchor)}" id="{html.escape(grp_anchor)}">Additional APIs</a></h3></div></div>'
            )
            for mname, minfo in pub_missing_methods:
                seq_counter[0] += 1
                m_id = f"doc-nav-item-ast-{seq_counter[0]}"
                local_map[f"{cname}.{mname}"] = m_id
                existing_anchors.add(f"{cname}.{mname}")
                m_ret = minfo.get('return_type') or ''
                m_params = minfo.get('parameters_raw', '()')
                sum_rows.append(f'<tr class="SMethod SIndent2"><td class=SEntry><a href="#{m_id}" data-target-id="{m_id}">{html.escape(mname)}</a></td><td class=SDescription><code>{html.escape(m_ret)} {html.escape(mname)}{html.escape(m_params)}</code></td></tr>')
                pub_detail_blocks.append(_render_ast_method_entry(cname, mname, minfo, c_file, root_rel, m_id, is_internal=False))

            for sname, sym in pub_missing_syms:
                seq_counter[0] += 1
                s_id = f"doc-nav-item-ast-{seq_counter[0]}"
                local_map[f"{cname}.{sname}"] = s_id
                existing_anchors.add(f"{cname}.{sname}")
                stype = sym.get('type', 'variable')
                sfile = sym.get('file') or c_file
                sline = sym.get('line') or 1
                sum_rows.append(f'<tr class="SMethod SIndent2"><td class=SEntry><a href="#{s_id}" data-target-id="{s_id}">{html.escape(sname)}</a></td><td class=SDescription>{html.escape(stype)} in <code>{html.escape(cname)}</code></td></tr>')
                pub_detail_blocks.append(_render_ast_symbol_entry(sname, stype, sfile, sline, root_rel, s_id, owner_cls=cname, is_internal=False))

        # Inject Summary rows into the class's .Summary.ClassSummary STable
        if sum_rows:
            slice_html = _inject_rows_into_class_summary(slice_html, sum_rows, cname, seq_counter)

        # Build collapsible Internal section if any m_* members are missing
        internal_block_html = ""
        if int_missing_methods or int_missing_syms:
            int_parts = []
            for mname, minfo in int_missing_methods:
                seq_counter[0] += 1
                m_id = f"doc-nav-item-ast-{seq_counter[0]}"
                local_map[f"{cname}.{mname}"] = m_id
                existing_anchors.add(f"{cname}.{mname}")
                int_parts.append(_render_ast_method_entry(cname, mname, minfo, c_file, root_rel, m_id, is_internal=True))
            for sname, sym in int_missing_syms:
                seq_counter[0] += 1
                s_id = f"doc-nav-item-ast-{seq_counter[0]}"
                local_map[f"{cname}.{sname}"] = s_id
                existing_anchors.add(f"{cname}.{sname}")
                int_parts.append(_render_ast_symbol_entry(
                    sname, sym.get('type', 'variable'), sym.get('file') or c_file, sym.get('line') or 1,
                    root_rel, s_id, owner_cls=cname, is_internal=True
                ))
            total_int = len(int_missing_methods) + len(int_missing_syms)
            internal_block_html = _render_internal_collapsible(
                f"Internal / Implementation Details: {cname} ({total_int})",
                "\n".join(int_parts)
            )

        appended_html = "\n".join(pub_detail_blocks) + ("\n" + internal_block_html if internal_block_html else "")
        if appended_html.strip():
            # Insert before trailing </div><!--Content--> if at end of document
            end_marker = '</div><!--Content-->'
            if idx_pos == len(documented_cnames) - 1 and end_marker in slice_html:
                slice_html = slice_html.replace(end_marker, "\n" + appended_html + "\n" + end_marker, 1)
            else:
                slice_html = slice_html + "\n" + appended_html

        body_content = body_content[:cb_start] + slice_html + body_content[cb_end:]

    # 2. Inject missing classes defined in associated_src (e.g. uvm_callbacks_base, uvm_test_done_objection, m_*)
    file_classes = UVM_DB['files'][associated_src].get('classes', [])
    missing_file_classes = [
        c for c in file_classes
        if c not in existing_anchors and not re.match(r'^uvm_.*_(port|export|imp)$', c)
    ]
    missing_class_blocks = []
    for mc in missing_file_classes:
        is_int_cls = _is_internal_symbol(mc)
        missing_class_blocks.append(_render_ast_class_block(mc, associated_src, root_rel, seq_counter, local_map, is_main=False, is_internal=is_int_cls))
        existing_anchors.add(mc)

    # 3. Inject missing macros defined in associated_src
    file_macros = UVM_DB['files'][associated_src].get('macros', [])
    pub_macro_blocks = []
    int_macro_blocks = []
    for mname in file_macros:
        if mname in existing_anchors or f"`{mname}" in existing_anchors:
            continue
        m_info = UVM_DB.get('macros', {}).get(mname, {})
        m_line = (m_info.get('start_line') or m_info.get('line') or 1) if isinstance(m_info, dict) else 1
        m_params = m_info.get('params_raw', '') if isinstance(m_info, dict) else ''
        m_doc = _clean_ast_doc(m_info.get('doc') if isinstance(m_info, dict) else None, _render_undocumented_notice(root_rel, associated_src, m_line))
        if m_params:
            m_doc = f"<code>`{html.escape(mname)}({html.escape(m_params)})</code> &mdash; {m_doc}"
        seq_counter[0] += 1
        mac_id = f"doc-nav-item-ast-{seq_counter[0]}"
        local_map[mname] = mac_id
        existing_anchors.add(mname)
        is_int_mac = _is_internal_symbol(mname)
        block = _render_ast_symbol_entry(mname, 'macro', associated_src, m_line, root_rel, mac_id, extra_desc=m_doc, is_internal=is_int_mac)
        if is_int_mac:
            int_macro_blocks.append(block)
        else:
            pub_macro_blocks.append(block)

    extra_tail = []
    if missing_class_blocks:
        extra_tail.extend(missing_class_blocks)
    if pub_macro_blocks:
        seq_counter[0] += 1
        mac_grp_id = f"doc-nav-group-ast-{seq_counter[0]}"
        extra_tail.append(
            f'<div class="CGroup" id="{mac_grp_id}" data-doc-topic="{mac_grp_id}" data-anchor="Additional_Macros">'
            f'<div class="CTopic"><h3 class="CTitle"><a name="Additional_Macros" id="Additional_Macros">Additional Macros</a></h3></div></div>'
        )
        extra_tail.extend(pub_macro_blocks)
    if int_macro_blocks:
        extra_tail.append(_render_internal_collapsible(
            f"Internal Macros ({len(int_macro_blocks)})",
            "\n".join(int_macro_blocks)
        ))

    if extra_tail:
        tail_html = "\n".join(extra_tail)
        if '</div><!--Content-->' in body_content:
            body_content = body_content.replace('</div><!--Content-->', "\n" + tail_html + "\n</div><!--Content-->", 1)
        else:
            body_content = body_content + "\n" + tail_html

    return body_content


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
                        a_map[a_name] = a_name
                        clean_a = re.sub(r'#\([^)]*\)', '', a_name)
                        if clean_a != a_name:
                            a_map[clean_a] = a_name
                else:
                    seq += 1
                    if a_name:
                        target_id = a_name
                        a_map[a_name] = target_id
                        clean_a = re.sub(r'#\([^)]*\)', '', a_name)
                        if clean_a != a_name:
                            a_map[clean_a] = target_id

            assoc_src = DOC_TO_SRC_MAP.get(rel_path)
            if assoc_src and assoc_src in UVM_DB.get('files', {}):
                for fc in UVM_DB['files'][assoc_src].get('classes', []):
                    if fc not in a_map:
                        a_map[fc] = fc

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
                        if a_name:
                            sum_anchor = f"{a_name}.Summary"
                        elif is_main:
                            sum_anchor = "Summary"
                        else:
                            sum_anchor = f"Summary-{safe_id}"
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

            # Inject missing AST-extracted members, classes, macros, and collapsible internal sections
            body_content = inject_missing_ast_content(body_content, rel_path, associated_src, root_rel, local_map)

            # Inject page-level wildcard variant selector into doc-breadcrumbs on TLM1 wildcard pages
            body_content, wildcard_breadcrumb_html = _inject_wildcard_selector(
                body_content, rel_path, associated_src, local_map, global_doc_anchor_maps
            )

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
                view_source_banner = build_doc_source_banner(associated_src, target_line, root_rel)

            # Breadcrumb navigation
            breadcrumbs_html = build_breadcrumbs_html(rel_path, page_title, root_rel)
            if wildcard_breadcrumb_html and '</nav>' in breadcrumbs_html:
                breadcrumbs_html = breadcrumbs_html.replace('</nav>', f'  {wildcard_breadcrumb_html}\n</nav>', 1)

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

        breadcrumbs = build_breadcrumbs_html(doc_rel, page_title, root_rel)
        banner = build_doc_source_banner(src_rel, first_line, root_rel)

        body_parts = ['<div id="Content">']
        seq = 0
        a_map = {}

        if src_rel == 'dpi/uvm_dpi.svh':
            dpi_db = UVM_DB.get('dpi', {})
            bindings = dpi_db.get('bindings', [])
            c_funcs = dpi_db.get('c_functions', [])
            body_parts.append(f'''<div class="CSection" id="doc-nav-main" data-doc-topic="doc-nav-main" data-anchor="uvm_dpi">
<div class="CTopic" id="MainTopic">
  <h1 class="CTitle"><a name="uvm_dpi" id="uvm_dpi" href="{root_rel}src_view/{src_rel}.html#L1" class="src-code-link" data-src-file="{src_rel}" data-src-line="1">{html.escape(page_title)}</a></h1>
  <div class="method-meta-bar"><span class="badge-subclass">{len(bindings)} SV&harr;C Bindings</span></div>
  <div class="CBody"><p>SystemVerilog <code>import "DPI-C"</code> declarations and C/C++ simulator implementations extracted from <code>src/dpi/</code>.</p></div>
</div>
</div>''')
            if bindings:
                body_parts.append('<div class="Summary" id="doc-nav-summary" data-anchor="uvm_dpi.Summary"><div class="STitle">DPI-C Imports Summary</div><div class="SBorder"><table border="0" cellspacing="0" cellpadding="0" class="STable">')
                for b in bindings:
                    sv = b.get('sv_import', {})
                    bname = sv.get('name', '')
                    if not bname:
                        continue
                    seq += 1
                    bid = f"doc-nav-item-dpi-{seq}"
                    sv['_nav_id'] = bid
                    a_map[bname] = bid
                    ret = sv.get('return_type') or 'void'
                    params = sv.get('parameters_raw') or ''
                    body_parts.append(f'<tr class="SMethod SIndent1"><td class="SEntry"><a href="#{bid}" data-target-id="{bid}">{html.escape(bname)}</a></td><td class="SDescription"><code>{html.escape(ret)} {html.escape(bname)}({html.escape(params)})</code></td></tr>')
                body_parts.append('</table></div></div>')
                body_parts.append('<div class="CGroup"><div class="CTopic"><h2 class="CTitle">DPI-C Bindings (SystemVerilog &harr; C)</h2></div></div>')
                for b in bindings:
                    sv = b.get('sv_import', {})
                    bname = sv.get('name', '')
                    if not bname:
                        continue
                    bid = sv.get('_nav_id')
                    sv_f = sv.get('file') or src_rel
                    sv_l = sv.get('line') or 1
                    ret = sv.get('return_type') or 'void'
                    params = sv.get('parameters_raw') or ''
                    bdoc = _clean_ast_doc(sv.get('doc'), f"DPI-C imported function <code>{html.escape(bname)}</code>.")
                    c_impls = b.get('c_implementations', [])
                    c_links = []
                    for ci in c_impls:
                        cf = ci.get('file', '')
                        cl = ci.get('line', 1)
                        tgt = ci.get('simulator_target', 'c')
                        c_links.append(f'<a href="{root_rel}src_view/{cf}.html#L{cl}" class="src-code-link badge-subclass" data-src-file="{cf}" data-src-line="{cl}">{html.escape(tgt)}: {html.escape(cf)}#L{cl}</a>')
                    c_links_html = f'<div class="method-meta-bar">{"".join(c_links)}</div>' if c_links else ''
                    proto_html = f'<table border="0" cellspacing="0" cellpadding="0" class="Prototype"><tr><td><span class="sv-keyword">import "DPI-C" function</span> <span class="sv-type">{html.escape(ret)}</span> <span class="sv-proto-name">{html.escape(bname)}</span> <span class="sv-params">({html.escape(params)})</span></td></tr></table>'
                    body_parts.append(f'''<div class="CMethod" id="{bid}" data-doc-topic="{bid}" data-anchor="{html.escape(bname)}">
<div class="CTopic">
  <h3 class="CTitle"><a name="{html.escape(bname)}" id="{html.escape(bname)}" href="{root_rel}src_view/{sv_f}.html#L{sv_l}" class="src-code-link" data-src-file="{sv_f}" data-src-line="{sv_l}">{html.escape(bname)}</a></h3>
  <div class="method-meta-bar"><span class="badge-subclass">DPI-C</span></div>
  {c_links_html}
  <blockquote>{proto_html}</blockquote>
  <div class="CBody"><p>{bdoc}</p></div>
</div>
</div>''')
            if c_funcs:
                c_parts = []
                for cf_info in c_funcs:
                    cname_fn = cf_info.get('name', '')
                    if not cname_fn:
                        continue
                    seq += 1
                    cid = f"doc-nav-item-dpi-c-{seq}"
                    cfile = cf_info.get('file', 'dpi/uvm_common.c')
                    cline = cf_info.get('line', 1)
                    cret = cf_info.get('return_type', 'void')
                    cparams = cf_info.get('parameters', '')
                    ctgt = cf_info.get('simulator_target', 'generic')
                    cdoc = _clean_ast_doc(cf_info.get('doc'), f"C function <code>{html.escape(cname_fn)}({html.escape(cparams)})</code> &rarr; <code>{html.escape(cret)}</code> ({html.escape(ctgt)}).")
                    c_parts.append(_render_ast_symbol_entry(cname_fn, 'function', cfile, cline, root_rel, cid, owner_cls='c', extra_desc=cdoc, is_internal=True))
                if c_parts:
                    body_parts.append(_render_internal_collapsible(
                        f"C/C++ Implementation Functions ({len(c_parts)})",
                        "\n".join(c_parts),
                        note_html="Low-level C/C++ DPI helper and simulator-specific functions in <code>src/dpi/</code>."
                    ))
        elif not classes_in_file:
            # File-level macros / functions / constants (e.g. uvm_version.svh, macros/*_defines.svh)
            file_info = UVM_DB.get('files', {}).get(src_rel, {})
            f_macros = file_info.get('macros', [])
            f_syms = [s for s in UVM_DB.get('symbols_index', []) if s.get('file') == src_rel and s.get('type') != 'macro']
            body_parts.append(f'''<div class="CSection" id="doc-nav-main" data-doc-topic="doc-nav-main" data-anchor="{html.escape(main_cname)}">
<div class="CTopic" id="MainTopic">
  <h1 class="CTitle"><a name="{html.escape(main_cname)}" id="{html.escape(main_cname)}" href="{root_rel}src_view/{src_rel}.html#L1" class="src-code-link" data-src-file="{src_rel}" data-src-line="1">{html.escape(page_title)}</a></h1>
  <div class="CBody"><p>Definitions and macros from <code>src/{html.escape(src_rel)}</code>.</p></div>
</div>
</div>''')
            pub_items = []
            int_items = []
            sum_rows = []
            for mname in f_macros:
                m_info = UVM_DB.get('macros', {}).get(mname, {})
                mline = (m_info.get('start_line') or m_info.get('line') or 1) if isinstance(m_info, dict) else 1
                mparams = m_info.get('params_raw', '') if isinstance(m_info, dict) else ''
                mdoc = _clean_ast_doc(m_info.get('doc') if isinstance(m_info, dict) else None, _render_undocumented_notice(root_rel, src_rel, mline))
                if mparams:
                    mdoc = f"<code>`{html.escape(mname)}({html.escape(mparams)})</code> &mdash; {mdoc}"
                seq += 1
                mid = f"doc-nav-item-ast-{seq}"
                a_map[mname] = mid
                is_int = _is_internal_symbol(mname)
                entry = _render_ast_symbol_entry(mname, 'macro', src_rel, mline, root_rel, mid, extra_desc=mdoc, is_internal=is_int)
                if is_int:
                    int_items.append(entry)
                else:
                    sum_rows.append(f'<tr class="SMethod SIndent1"><td class="SEntry"><a href="#{mid}" data-target-id="{mid}">`{html.escape(mname)}</a></td><td class="SDescription">Macro (line {mline})</td></tr>')
                    pub_items.append(entry)
            for s in f_syms:
                sname = s.get('short_name') or s.get('name', '')
                if not sname:
                    continue
                seq += 1
                sid = f"doc-nav-item-ast-{seq}"
                a_map[sname] = sid
                is_int = _is_internal_symbol(sname)
                entry = _render_ast_symbol_entry(sname, s.get('type', 'function'), src_rel, s.get('line', 1), root_rel, sid, is_internal=is_int)
                if is_int:
                    int_items.append(entry)
                else:
                    sum_rows.append(f'<tr class="SMethod SIndent1"><td class="SEntry"><a href="#{sid}" data-target-id="{sid}">{html.escape(sname)}</a></td><td class="SDescription">{html.escape(s.get("type", "symbol"))} (line {s.get("line", 1)})</td></tr>')
                    pub_items.append(entry)
            if sum_rows:
                body_parts.append(f'<div class="Summary" id="doc-nav-summary" data-anchor="{html.escape(main_cname)}.Summary"><div class="STitle">Summary</div><div class="SBorder"><table border="0" cellspacing="0" cellpadding="0" class="STable">{"".join(sum_rows)}</table></div></div>')
            if pub_items:
                body_parts.append(f'<div class="CGroup"><div class="CTopic"><h2 class="CTitle">Definitions</h2></div></div>')
                body_parts.extend(pub_items)
            if int_items:
                body_parts.append(_render_internal_collapsible(
                    f"Internal / Implementation Macros & Symbols ({len(int_items)})",
                    "\n".join(int_items)
                ))

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
            a_map[cname] = cname
            if is_main:
                a_map['MainTopic'] = cname

            hierarchy_widget = pbc.render_class_hierarchy_card(
                cname, root_rel, CLASS_TO_DOC_MAP, UVM_DB, GLOBAL_DOC_ANCHOR_MAPS
            )

            body_parts.append(f'''<div class="CClass" id="{topic_id}" data-doc-topic="{topic_id}" data-anchor="{cname}">
<div class="CTopic" {"id='MainTopic'" if is_main else ""}>
  <h1 class="CTitle"><a href="{root_rel}src_view/{src_rel}.html#L{c_line}" class="src-code-link" data-src-file="{src_rel}" data-src-line="{c_line}">{cname}</a></h1>
  {hierarchy_widget}
  <div class="CBody">
    <p>{html.escape(c_doc)}</p>
    {f"<p><b>Base Class:</b> <code>{c_parent}</code></p>" if c_parent else ""}
    {f"<p><b>Parameters:</b> <code>#({c_params})</code></p>" if c_params else ""}
  </div>
</div>
</div>''')

            # Summary table of methods (split public vs internal m_*)
            methods = c_info.get('methods', {})
            pub_methods = [(m, mi) for m, mi in methods.items() if not _is_internal_symbol(m)]
            int_methods = [(m, mi) for m, mi in methods.items() if _is_internal_symbol(m)]
            if pub_methods:
                sum_id = f"doc-nav-summary-{cname}"
                body_parts.append(f'''<div class="Summary" id="{sum_id}" data-anchor="{cname}.Summary">
<div class="STitle">Methods Summary: {cname}</div>
<div class="SBody">
<table border="0" cellspacing="0" cellpadding="0" class="STable">''')
                for mname, minfo in pub_methods:
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
                for mname, minfo in pub_methods:
                    m_id = minfo.get('_nav_id', f"doc-nav-item-m-{seq}")
                    body_parts.append(_render_ast_method_entry(cname, mname, minfo, src_rel, root_rel, m_id, is_internal=False, show_ast_badge=False))

            if int_methods:
                int_parts = []
                for mname, minfo in int_methods:
                    seq += 1
                    m_id = f"doc-nav-item-m-{seq}"
                    a_map[f"{cname}.{mname}"] = m_id
                    int_parts.append(_render_ast_method_entry(cname, mname, minfo, src_rel, root_rel, m_id, is_internal=True, show_ast_badge=True))
                body_parts.append(_render_internal_collapsible(
                    f"Internal / Implementation Details: {cname} ({len(int_methods)})",
                    "\n".join(int_parts)
                ))

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
                {'type': 'file', 'title': 'uvm_resource_specializations', 'href': 'docs_view/base/uvm_resource_specializations-svh.html'},
                {'type': 'file', 'title': 'uvm_version', 'href': 'docs_view/base/uvm_version-svh.html'}
            ])
        elif cat.get('title') == 'Sequences':
            cat['children'].extend([
                {'type': 'file', 'title': 'uvm_sequence_builtin', 'href': 'docs_view/seq/uvm_sequence_builtin-svh.html'},
                {'type': 'file', 'title': 'uvm_sequencer_analysis_fifo', 'href': 'docs_view/seq/uvm_sequencer_analysis_fifo-svh.html'}
            ])
        elif cat.get('title') == 'Macros':
            cat['children'].extend([
                {'type': 'file', 'title': 'Phase Defines', 'href': 'docs_view/macros/uvm_phase_defines-svh.html'},
                {'type': 'file', 'title': 'Printer Defines', 'href': 'docs_view/macros/uvm_printer_defines-svh.html'}
            ])

    categories.append({
        'type': 'group',
        'title': 'DPI-C Interface',
        'children': [
            {'type': 'file', 'title': 'uvm_dpi', 'href': 'docs_view/dpi/uvm_dpi-svh.html'}
        ]
    })

    categories.append({
        'type': 'group',
        'title': 'Deprecated',
        'children': [
            {'type': 'file', 'title': 'uvm_resource_converter', 'href': 'docs_view/deprecated/uvm_resource_converter-svh.html'},
            {'type': 'file', 'title': 'uvm_deprecated_defines', 'href': 'docs_view/macros/uvm_deprecated_defines-svh.html'}
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

def find_actual_decl_in_file(rel_file, sym_name, sym_type=None):
    clean = sym_name.split('::')[-1].split('#')[0].lstrip('+`').strip()
    if not clean or not rel_file:
        return 1
    p = SRC_DIR / rel_file
    if not p.exists():
        return 1
    try:
        lines = p.read_text(encoding='latin-1').splitlines()
    except Exception:
        return 1

    pat = re.compile(r'\b' + re.escape(clean) + r'\b')
    candidates = []
    for idx, l in enumerate(lines, 1):
        s = l.strip()
        is_comment = _is_comment_only_line(s)
        if not is_comment and pat.search(l):
            candidates.append((idx, l))

    if candidates:
        if sym_type in ('constant', 'parameter'):
            for idx, l in candidates:
                if re.search(r'\b(parameter|localparam|const)\b', l):
                    return idx
            for idx, l in candidates:
                if re.search(r'\b(enum|typedef)\b', l) or '=' in l or ',' in l:
                    return idx
        elif sym_type in ('type', 'enum'):
            for idx, l in candidates:
                if re.search(r'\btypedef\b', l):
                    return idx
        elif sym_type == 'port':
            for idx, l in candidates:
                if re.search(r'\b(port|export|imp)\b', l):
                    return idx
        return candidates[0][0]

    comment_line = None
    for idx, l in enumerate(lines, 1):
        if pat.search(l):
            comment_line = idx
            break
    if comment_line:
        in_block_comment = False
        for idx in range(comment_line, min(comment_line + 60, len(lines) + 1)):
            s = lines[idx - 1].strip()
            if '/*' in s:
                in_block_comment = True
            if '*/' in s:
                in_block_comment = False
                continue
            if in_block_comment or s.startswith('//') or s.startswith('*') or not s:
                continue
            return idx
        return comment_line
    return 1

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

    # Ensure all classes in UVM_DB are present as classes
    for cname, cinfo in sorted(UVM_DB.get('classes', {}).items()):
        if not any(x['name'] == cname and x['type'] == 'class' for x in search_items):
            src_file = cinfo.get('file', '')
            doc_file = SRC_TO_DOC_MAP.get(src_file)
            doc_anchor = GLOBAL_DOC_ANCHOR_MAPS.get(doc_file, {}).get(cname) if doc_file else None
            doc_url = f"docs_view/{doc_file}#{doc_anchor}" if (doc_file and doc_anchor) else (f"docs_view/{doc_file}" if doc_file else None)
            search_items.append({
                'name': cname,
                'type': 'class',
                'category': src_file.split('/')[0].capitalize() if src_file else 'Base',
                'src': f"src_view/{src_file}.html#L{cinfo.get('start_line', 1)}" if src_file else None,
                'doc': doc_url,
                'desc': f"UVM Class: {cname}"
            })

    # 2. Add macros
    for mname, info in sorted(SYMBOL_MAP.items()):
        if info['type'] == 'macro' and mname.startswith('`'):
            src_file = info['file']
            doc_file = SRC_TO_DOC_MAP.get(src_file)
            doc_map = GLOBAL_DOC_ANCHOR_MAPS.get(doc_file, {}) if doc_file else {}
            # Look up macro anchor in GLOBAL_DOC_ANCHOR_MAPS (matches exact doc-nav-item id or name)
            doc_anchor = doc_map.get(mname) or doc_map.get(mname.lstrip('`')) or doc_map.get('`' + mname)
            doc_url = f"docs_view/{doc_file}#{doc_anchor}" if (doc_file and doc_anchor) else (f"docs_view/{doc_file}" if doc_file else None)
            search_items.append({
                'name': mname,
                'type': 'macro',
                'category': 'Macros',
                'src': f"src_view/{src_file}.html#L{info['line']}",
                'doc': doc_url,
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

    # Ensure TLM1 wildcard meta-classes (uvm_*_port/export/imp) appear in Search & Index A-Z
    wildcard_index_entries = [
        ('uvm_*_port#(T)', 'tlm1/uvm_ports-svh.html', 'uvm_*_port#(T)', 'tlm1/uvm_ports.svh', 81),
        ('uvm_*_port#(REQ,RSP)', 'tlm1/uvm_ports-svh.html', 'uvm_*_port#(REQ,RSP)', 'tlm1/uvm_ports.svh', 203),
        ('uvm_*_export#(T)', 'tlm1/uvm_exports-svh.html', 'uvm_*_export#(T)', 'tlm1/uvm_exports.svh', 80),
        ('uvm_*_export#(REQ,RSP)', 'tlm1/uvm_exports-svh.html', 'uvm_*_export#(REQ,RSP)', 'tlm1/uvm_exports.svh', 200),
        ('uvm_*_imp#(T,IMP)', 'tlm1/uvm_imps-svh.html', 'uvm_*_imp#(T,IMP)', 'tlm1/uvm_imps.svh', 82),
        ('uvm_*_imp#(REQ,RSP,IMP,REQ_IMP,RSP_IMP)', 'tlm1/uvm_imps-svh.html', 'uvm_*_imp#(REQ,RSP,IMP,REQ_IMP,RSP_IMP)', 'tlm1/uvm_imps.svh', 232),
    ]
    for w_name, w_doc, w_raw_anchor, w_src, w_line in wildcard_index_entries:
        if not any(x['name'] == w_name for x in search_items):
            w_target = GLOBAL_DOC_ANCHOR_MAPS.get(w_doc, {}).get(w_raw_anchor, w_raw_anchor)
            search_items.append({
                'name': w_name,
                'type': 'class',
                'category': 'Tlm1',
                'doc': f"docs_view/{w_doc}#{w_target}",
                'src': f"src_view/{w_src}.html#L{w_line}",
                'desc': f"TLM1 Wildcard Class Family defined in src/{w_src}"
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
            htype = h.get('type')
            if htype in ('method', 'variable', 'type', 'enumeration', 'port', 'constant', 'parameter'):
                sym_name = h.get('title')
                if not sym_name:
                    continue
                dedup_key = (sym_name, class_name)
                if dedup_key in seen_methods:
                    continue
                seen_methods.add(dedup_key)

                anchor = h.get('anchor', '')
                doc_link = f"{doc_key}#{anchor}" if anchor else doc_key

                mkind = 'function' if htype == 'method' else htype
                src_link = None
                src_rel = DOC_TO_SRC_MAP.get(doc_rel)
                if src_rel:
                    syms = FILE_SYMBOLS.get(src_rel, [])
                    sym_clean = sym_name.split('.')[-1].strip()
                    norm_clean = sym_clean.split('_')[-1] if '_' in sym_clean and any(s['name'] == sym_clean.split('_')[-1] for s in syms) else sym_clean

                    sym_match = None
                    if htype == 'method':
                        sym_match = next((s for s in syms if s['name'] == sym_name and s['type'] in ('task', 'function')), None)
                        if not sym_match:
                            sym_match = next((s for s in syms if s['name'] == sym_name), None)
                    else:
                        sym_match = next((s for s in syms if s['name'] == sym_clean), None)
                        if not sym_match and norm_clean != sym_clean:
                            sym_match = next((s for s in syms if s['name'] == norm_clean), None)
                        if not sym_match:
                            sym_match = next((s for s in syms if s['name'] == sym_name), None)
                        if not sym_match:
                            sym_match = next((s for s in syms if sym_clean in s['name'] or s['name'] in sym_clean), None)

                    if sym_match:
                        src_link = f"src_view/{src_rel}.html#L{sym_match['line']}"
                        if htype == 'method' and sym_match['type'] in ('task', 'function'):
                            mkind = sym_match['type']
                        elif htype != 'method':
                            mkind = sym_match['type']
                    else:
                        # Fallback to global SYMBOL_MAP
                        if sym_clean in SYMBOL_MAP:
                            src_link = f"src_view/{SYMBOL_MAP[sym_clean]['file']}.html#L{SYMBOL_MAP[sym_clean]['line']}"
                        else:
                            cls_match = next((s for s in syms if s['type'] == 'class'), None)
                            line_no = cls_match['line'] if cls_match else 1
                            src_link = f"src_view/{src_rel}.html#L{line_no}"

                if mkind == 'function' and sym_name in known_tasks:
                    mkind = 'task'

                type_label_map = {
                    'task': 'Task',
                    'function': 'Function',
                    'variable': 'Variable',
                    'type': 'Type',
                    'enumeration': 'Enum',
                    'port': 'Port',
                    'constant': 'Constant',
                    'parameter': 'Parameter'
                }
                desc_label = type_label_map.get(mkind, mkind.capitalize())
                search_items.append({
                    'name': sym_name,
                    'type': mkind,
                    'category': class_name,
                    'src': src_link,
                    'doc': doc_link,
                    'desc': f"{desc_label} in {class_name}" + (f" ({h['group']})" if h.get('group') else "")
                })

    # 7. Extract Constants, Variables, Types, and Ports from NaturalDocs indices and UVM_DB
    seen_search_keys = set((item['name'], item.get('category')) for item in search_items)

    db_symbols_by_name = {}
    for s in UVM_DB.get('symbols_index', []):
        s_name = s.get('short_name') or s['name']
        s_cls = s.get('class')
        s_file = s.get('file')
        if s_cls:
            db_symbols_by_name[(s_name, s_cls)] = s
        if s_file:
            db_symbols_by_name[(s_name, s_file)] = s
        if s_name not in db_symbols_by_name:
            db_symbols_by_name[s_name] = s

    docs_index_dir = DOCS_DIR / "index"
    index_configs = [
        ("Constants.html", "constant", "Constant"),
        ("Types.html", "type", "Type"),
        ("Variables.html", "variable", "Variable"),
        ("Ports.html", "port", "Port")
    ]

    for fname, sym_type, type_label in index_configs:
        fpath = docs_index_dir / fname
        if not fpath.exists():
            continue
        try:
            with open(fpath, 'r', encoding='latin-1') as f:
                c_html = f.read()
        except Exception:
            continue

        tooltips = {}
        for m in re.finditer(r'<div class=CToolTip id="?([^">]+)"?>\s*<div class=[^>]+>([\s\S]*?)</div>\s*</div>', c_html):
            tid = m.group(1).replace('"', '').strip()
            clean_txt = re.sub(r'<[^>]+>', ' ', m.group(2)).strip()
            tooltips[tid] = re.sub(r'\s+', ' ', clean_txt)

        # Direct entries
        for m in re.finditer(r'<td class=IEntry><a href="([^"]+)"(?:[^>]*onMouseOver="ShowTip\(event,\s*\'([^\']+)\'[^"]*")?[^>]*class=ISymbol>([^<]+)</a></td>', c_html):
            raw_href = m.group(1).replace('../files/', '')
            file_part, _, a_part = raw_href.partition('#')
            tid = m.group(2)
            name = html.unescape(m.group(3).strip())
            desc = tooltips.get(tid, "") or f"UVM {type_label}: {name}"

            dedup_key = (name, None)
            if dedup_key in seen_search_keys:
                continue
            seen_search_keys.add(dedup_key)

            target_id = a_part
            doc_map = GLOBAL_DOC_ANCHOR_MAPS.get(file_part, {})
            if a_part in doc_map:
                target_id = doc_map[a_part]
            doc_link = f"docs_view/{file_part}#{target_id}" if target_id else f"docs_view/{file_part}"

            # Source link resolution
            src_link = None
            src_rel = DOC_TO_SRC_MAP.get(file_part)
            if not src_rel:
                src_rel = file_part.replace('-svh.html', '.svh').replace('-sv.html', '.sv').replace('-txt.html', '.txt')

            # 1. Look up in UVM_DB symbols_index
            db_match = db_symbols_by_name.get((name, src_rel)) or db_symbols_by_name.get(name)
            if db_match and db_match.get('file') and db_match.get('line') and db_match.get('line') > 1:
                src_rel = db_match['file']
                src_link = f"src_view/{src_rel}.html#L{db_match['line']}"
            elif src_rel in FILE_SYMBOLS:
                clean_n = name.lstrip('+`')
                s_match = next((s for s in FILE_SYMBOLS[src_rel] if s['name'] == clean_n or s['name'] == name), None)
                if s_match and s_match.get('line') and s_match['line'] > 1:
                    src_link = f"src_view/{src_rel}.html#L{s_match['line']}"

            if not src_link and (SRC_DIR / src_rel).exists():
                decl_line = find_actual_decl_in_file(src_rel, name, sym_type)
                src_link = f"src_view/{src_rel}.html#L{decl_line}"
            elif not src_link:
                src_link = f"src_view/{src_rel}.html#L1"

            search_items.append({
                'name': name,
                'type': sym_type,
                'category': file_part.split('/')[0].capitalize(),
                'src': src_link,
                'doc': doc_link,
                'desc': desc
            })

        # Subindex entries
        for m in re.finditer(r'<td class=IEntry><span class=ISymbol>([^<]+)</span>\s*<div class=ISubIndex>([\s\S]*?)</div>', c_html):
            sname = html.unescape(m.group(1).strip())
            sub_html = m.group(2)
            for lm in re.finditer(r'<a\s+href="([^"]+)"(?:[^>]*onMouseOver="ShowTip\(event,\s*\'([^\']+)\'[^"]*")?[^>]*class=IParent>([^<]+)</a>', sub_html):
                raw_href = lm.group(1).replace('../files/', '')
                file_part, _, a_part = raw_href.partition('#')
                tid = lm.group(2)
                parent_class = html.unescape(lm.group(3).strip())
                desc = tooltips.get(tid, "") or f"{type_label} in {parent_class}"

                dedup_key = (sname, parent_class)
                if dedup_key in seen_search_keys:
                    continue
                seen_search_keys.add(dedup_key)

                target_id = a_part
                doc_map = GLOBAL_DOC_ANCHOR_MAPS.get(file_part, {})
                if a_part in doc_map:
                    target_id = doc_map[a_part]
                doc_link = f"docs_view/{file_part}#{target_id}" if target_id else f"docs_view/{file_part}"

                src_link = None
                src_rel = DOC_TO_SRC_MAP.get(file_part)
                if parent_class in UVM_DB.get('classes', {}):
                    src_rel = UVM_DB['classes'][parent_class]['file']
                if not src_rel:
                    src_rel = file_part.replace('-svh.html', '.svh').replace('-sv.html', '.sv').replace('-txt.html', '.txt')

                # 1. Look up in UVM_DB symbols_index
                db_match = db_symbols_by_name.get((sname, parent_class)) or db_symbols_by_name.get((sname, src_rel)) or db_symbols_by_name.get(sname)
                if db_match and db_match.get('file') and db_match.get('line') and db_match.get('line') > 1:
                    src_rel = db_match['file']
                    src_link = f"src_view/{src_rel}.html#L{db_match['line']}"
                elif src_rel in FILE_SYMBOLS:
                    clean_n = sname.lstrip('+`')
                    s_match = next((s for s in FILE_SYMBOLS[src_rel] if s['name'] == clean_n or s['name'] == sname), None)
                    if s_match and s_match.get('line') and s_match['line'] > 1:
                        src_link = f"src_view/{src_rel}.html#L{s_match['line']}"
                    elif parent_class in UVM_DB.get('classes', {}):
                        src_link = f"src_view/{src_rel}.html#L{UVM_DB['classes'][parent_class]['start_line']}"

                if not src_link and (SRC_DIR / src_rel).exists():
                    decl_line = find_actual_decl_in_file(src_rel, sname, sym_type)
                    src_link = f"src_view/{src_rel}.html#L{decl_line}"
                elif not src_link:
                    src_link = f"src_view/{src_rel}.html#L1"

                search_items.append({
                    'name': sname,
                    'type': sym_type,
                    'category': parent_class,
                    'src': src_link,
                    'doc': doc_link,
                    'desc': desc
                })

    # Also add any remaining symbols from UVM_DB symbols_index
    for s in UVM_DB.get('symbols_index', []):
        stype = s.get('type')
        if stype in ('constant', 'variable', 'type', 'port', 'enum'):
            sname = s.get('short_name') or s['name']
            cname = s.get('class')
            dedup_key = (sname, cname)
            if dedup_key in seen_search_keys:
                continue
            seen_search_keys.add(dedup_key)

            src_file = s.get('file', '')
            src_link = f"src_view/{src_file}.html#L{s['line']}" if src_file else None
            doc_file = SRC_TO_DOC_MAP.get(src_file)
            doc_link = f"docs_view/{doc_file}" if doc_file else None

            search_items.append({
                'name': sname,
                'type': stype,
                'category': cname or (src_file.split('/')[0].capitalize() if src_file else 'Reference'),
                'src': src_link,
                'doc': doc_link,
                'desc': s.get('summary') or f"UVM {stype.capitalize()}: {sname}"
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

def build_class_hierarchy_data():
    """Build complete class hierarchy tree from UVM AST database."""
    classes = UVM_DB.get('classes', {})
    if not classes:
        return {"nodes": {}, "roots": []}

    def is_descendant_of(cname, ancestor):
        curr = cname
        visited = set()
        while curr and curr in classes and curr not in visited:
            visited.add(curr)
            p = classes[curr].get('parent')
            if p == ancestor:
                return True
            curr = p
        return False

    def get_role(cname):
        if cname == 'uvm_component' or is_descendant_of(cname, 'uvm_component'):
            return 'component'
        if cname == 'uvm_sequence_base' or is_descendant_of(cname, 'uvm_sequence_base') or 'sequence' in cname or 'seq_item' in cname:
            return 'sequence'
        if cname.startswith('uvm_reg') or cname.startswith('uvm_vreg') or cname.startswith('uvm_mem'):
            return 'reg'
        if 'tlm' in cname or 'port' in cname or 'export' in cname or 'fifo' in cname:
            return 'tlm'
        if 'phase' in cname or is_descendant_of(cname, 'uvm_phase'):
            return 'phase'
        if cname == 'uvm_object' or is_descendant_of(cname, 'uvm_object'):
            return 'object'
        return 'utility'

    nodes = {}
    for cname, cinfo in classes.items():
        parent = cinfo.get('parent')
        clean_parent = re.sub(r'#\(.*?\)', '', parent).strip() if parent else None
        if clean_parent and clean_parent not in classes:
            p_simple = clean_parent.split()[0] if clean_parent.split() else ''
            if p_simple in classes:
                clean_parent = p_simple

        children = [ch for ch in cinfo.get('children', []) if ch in classes]
        children.sort()

        doc_path = CLASS_TO_DOC_MAP.get(cname)
        target_id = cname
        if doc_path and doc_path in GLOBAL_DOC_ANCHOR_MAPS:
            target_id = GLOBAL_DOC_ANCHOR_MAPS[doc_path].get(cname, cname)

        src_f = cinfo.get('file', '')
        start_l = cinfo.get('start_line', 1)
        src_url = f"src_view/{src_f}.html#L{start_l}" if src_f else None

        methods_dict = cinfo.get('methods', {})

        raw_summary = cinfo.get('doc', {}).get('summary', '') if cinfo.get('doc') else ''
        if raw_summary and ('copyright' in raw_summary.lower() or 'all rights reserved' in raw_summary.lower()):
            raw_summary = ''

        nodes[cname] = {
            "name": cname,
            "parent": clean_parent,
            "children": children,
            "doc": f"docs_view/{doc_path}#{target_id}" if doc_path else None,
            "src": src_url,
            "methodsCount": len(methods_dict),
            "role": get_role(cname),
            "isVirtual": cinfo.get('is_virtual', False),
            "summary": raw_summary[:160]
        }

    # Identify roots
    roots = []
    for cname, node in nodes.items():
        if not node["parent"] or node["parent"] not in nodes:
            roots.append(cname)

    def count_descendants(cname, visited=None):
        if visited is None: visited = set()
        if cname in visited or cname not in nodes: return 0
        visited.add(cname)
        total = len(nodes[cname]["children"])
        for ch in nodes[cname]["children"]:
            total += count_descendants(ch, visited)
        return total

    roots.sort(key=lambda r: (0 if r == 'uvm_void' else 1, -count_descendants(r), r))

    return {
        "nodes": nodes,
        "roots": roots
    }

def generate_search_and_nav_data():
    """Generate js/search_data.js for client-side search and menu tree."""
    print("Generating search index and navigation data...")
    categories = parse_navigation_and_categories()
    source_tree = build_source_tree()
    search_items = build_search_index(categories)
    class_hierarchy = build_class_hierarchy_data()

    # Generate and integrate interactive examples
    examples_catalog = build_examples.generate_all_examples()
    search_items.extend(examples_catalog.get("searchItems", []))
    examples_tree = examples_catalog.get("examplesTree", [])
    example_to_src = examples_catalog.get("exampleToSrc", {})

    # Generate and integrate step-by-step interactive tutorial
    tutorial_catalog = build_tutorial.generate_all_tutorial()
    search_items.extend(tutorial_catalog.get("searchItems", []))
    tutorial_tree = tutorial_catalog.get("tutorialTree", [])
    tutorial_to_src = tutorial_catalog.get("tutorialToSrc", {})

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
        "tutorialTree": tutorial_tree,
        "classHierarchy": class_hierarchy,
        "searchIndex": search_items,
        "docToSrc": doc_to_src,
        "srcToDoc": src_to_doc,
        "exampleToSrc": example_to_src,
        "tutorialToSrc": tutorial_to_src,
        "docHeadings": DOC_HEADINGS_MAP
    }

    js_content = f"""/**
 * Generated UVM 1.2 Documentation Data & Navigation Index
 * Contains category tree, source tree, and full search index.
 */
const UVM_DATA = {json.dumps(payload, separators=(',', ':'))};
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
        generate_quick_symbols.generate_quick_symbols()
    else:
        generate_source_views()
        modernize_doc_files()
        modernize_index_pages()
        generate_orphan_doc_pages()
        copy_assets()
        generate_search_and_nav_data()
        generate_quick_symbols.generate_quick_symbols()

    print("=" * 60)
    print("  Documentation build complete successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
