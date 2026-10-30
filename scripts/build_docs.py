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
import re
import html
import json
import shutil
import posixpath
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "uvm-1.2" / "src"
DOCS_DIR = BASE_DIR / "uvm-1.2" / "docs" / "html"
DOCS_FILES_DIR = DOCS_DIR / "files"
DOCS_IMAGES_DIR = DOCS_DIR / "images"
OUTPUT_SRC_VIEW = BASE_DIR / "src_view"
OUTPUT_DOCS_VIEW = BASE_DIR / "docs_view"
OUTPUT_JS_DIR = BASE_DIR / "js"
OUTPUT_IMAGES_DIR = BASE_DIR / "images"

# SystemVerilog keywords (IEEE 1800)
SV_KEYWORDS = set([
    'accept_tr', 'alias', 'always', 'always_comb', 'always_ff', 'always_latch',
    'and', 'assert', 'assign', 'assume', 'automatic', 'before', 'begin', 'bind',
    'bins', 'binsof', 'bit', 'break', 'buf', 'bufif0', 'bufif1', 'byte', 'case',
    'casex', 'casez', 'cell', 'chandle', 'checker', 'class', 'clocking', 'cmos',
    'config', 'const', 'constraint', 'context', 'continue', 'cover', 'covergroup',
    'coverpoint', 'cross', 'deassign', 'default', 'defparam', 'design', 'disable',
    'dist', 'do', 'edge', 'else', 'end', 'endcase', 'endchecker', 'endclass',
    'endclocking', 'endconfig', 'endfunction', 'endgenerate', 'endgroup',
    'endinterface', 'endmodule', 'endpackage', 'endprimitive', 'endprogram',
    'endproperty', 'endsequence', 'endspecify', 'endtable', 'endtask', 'enum',
    'event', 'expect', 'export', 'extends', 'extern', 'final', 'first_match',
    'for', 'force', 'foreach', 'forever', 'fork', 'forkjoin', 'function',
    'generate', 'genvar', 'highz0', 'highz1', 'if', 'iff', 'ifnone', 'ignore_bins',
    'illegal_bins', 'implements', 'implies', 'import', 'incdir', 'include',
    'initial', 'inout', 'input', 'inside', 'instance', 'int', 'integer',
    'interconnect', 'interface', 'intersect', 'join', 'join_any', 'join_none',
    'large', 'let', 'liblist', 'library', 'local', 'localparam', 'logic',
    'longint', 'matches', 'medium', 'modport', 'module', 'nand', 'negedge',
    'nettype', 'new', 'nexttime', 'nmos', 'nor', 'noshowcancelled', 'not',
    'notif0', 'notif1', 'null', 'or', 'output', 'package', 'packed', 'parameter',
    'pmos', 'posedge', 'primitive', 'priority', 'program', 'property',
    'protected', 'pull0', 'pull1', 'pulldown', 'pullup', 'pulsestyle_ondetect',
    'pulsestyle_onevent', 'pure', 'rand', 'randc', 'randcase', 'randsequence',
    'rcmos', 'real', 'realtime', 'ref', 'reg', 'reject_on', 'release', 'repeat',
    'restrict', 'return', 'rnmos', 'rpmos', 'rtran', 'rtranif0', 'rtranif1',
    's_always', 's_eventually', 's_nexttime', 's_until', 's_until_with', 'scalared',
    'sequence', 'shortint', 'shortreal', 'showcancelled', 'signed', 'small',
    'soft', 'solve', 'specify', 'specparam', 'static', 'string', 'strong',
    'struct', 'super', 'supply0', 'supply1', 'sync_accept_on', 'sync_reject_on',
    'table', 'tagged', 'task', 'this', 'throughout', 'time', 'timeprecision',
    'timeunit', 'tran', 'tranif0', 'tranif1', 'tri', 'tri0', 'tri1', 'triand',
    'trior', 'trireg', 'type', 'typedef', 'union', 'unique', 'unique0',
    'unsigned', 'until', 'until_with', 'untyped', 'use', 'uwire', 'var', 'vectored',
    'virtual', 'void', 'wait', 'wait_order', 'wand', 'weak', 'weak0', 'weak1',
    'while', 'wildcard', 'wire', 'with', 'within', 'wor', 'xnor', 'xor'
])

# C/C++ keywords for DPI files
C_KEYWORDS = set([
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
    'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
    'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile',
    'while', 'include', 'define', 'ifdef', 'ifndef', 'endif', 'NULL', 'bool',
    'true', 'false', 'size_t', 'int32_t', 'uint32_t', 'int64_t', 'uint64_t'
])

TOKEN_REGEX = re.compile(
    r'(?P<BLOCK_COMMENT_START>/\*)|'
    r'(?P<LINE_COMMENT>//[^\n]*)|'
    r'(?P<STRING>"([^"\\]|\\.)*")|'
    r'(?P<CHAR>\'([^\'\\]|\\.)*\')|'
    r'(?P<MACRO>`[a-zA-Z_][a-zA-Z0-9_]*)|'
    r'(?P<NUMBER>\b\d+\'?[bBoOdDhH]?[0-9a-fA-F_xzXZ]*\b|\b\d+\b)|'
    r'(?P<IDENT>[a-zA-Z_][a-zA-Z0-9_]*)|'
    r'(?P<OP>[#+\-*/%=&|~^!<>?:;.,()\[\]{}])'
)

# Symbol extraction regexes
CLASS_DEF_REGEX = re.compile(r'^\s*(?:virtual\s+)?class\s+([a-zA-Z0-9_]+)')
METHOD_DEF_REGEX = re.compile(r'^\s*(?:virtual\s+|local\s+|protected\s+|static\s+)*(task|function)\s+(?:[\w:\[\]\$]+\s+)?([a-zA-Z0-9_]+)\s*\(')
MACRO_DEF_REGEX = re.compile(r'^\s*`define\s+([a-zA-Z0-9_]+)')

DOC_TOKEN_REGEX = re.compile(
    r'(?P<BLOCK_COMMENT>/\*[\s\S]*?\*/)|'
    r'(?P<LINE_COMMENT>//[^\n]*)|'
    r'(?P<STRING>"([^"\\]|\\.)*")|'
    r'(?P<CHAR>\'([^\'\\]|\\.)*\')|'
    r'(?P<MACRO>`[a-zA-Z_][a-zA-Z0-9_]*)|'
    r'(?P<CMD_OPTION>\+[a-zA-Z0-9_]+(?:=[^\s,()]+)?)|'
    r'(?P<NUMBER>\b\d+\'?[bBoOdDhH]?[0-9a-fA-F_xzXZ]*\b|\b\d+(?:ns|ps|us|ms|s)?\b)|'
    r'(?P<IDENT>[a-zA-Z_][a-zA-Z0-9_]*)|'
    r'(?P<OP>::|->|<=|>=|==|!=|\+=|-=|\*=|&=|\|=|\^=|&&|\|\||#\(|[#+\-*/%=&|~^!<>?:;.,()\[\]{}])'
)

def highlight_outside_tags(text, highlight_fn):
    """Tokenize text outside HTML tags and HTML entity sequences."""
    parts = re.split(r'(<[^>]+>|&[a-zA-Z0-9#]+;)', text)
    for i in range(len(parts)):
        if not parts[i].startswith('<') and not (parts[i].startswith('&') and parts[i].endswith(';')):
            parts[i] = highlight_fn(parts[i])
    return "".join(parts)

def highlight_doc_code(raw_code):
    """Highlight a block of code from documentation preserving indentation and newlines."""
    code = html.unescape(raw_code)
    pos = 0
    code_len = len(code)
    parts = []

    while pos < code_len:
        m = DOC_TOKEN_REGEX.search(code, pos)
        if not m:
            parts.append(html.escape(code[pos:]))
            break
        
        start, end = m.span()
        if start > pos:
            parts.append(html.escape(code[pos:start]))
            
        kind = m.lastgroup
        val = m.group(kind)
        esc = html.escape(val)

        if kind in ('BLOCK_COMMENT', 'LINE_COMMENT'):
            parts.append(f'<span class="sv-comment">{esc}</span>')
        elif kind in ('STRING', 'CHAR'):
            parts.append(f'<span class="sv-string">{esc}</span>')
        elif kind == 'MACRO':
            parts.append(f'<span class="sv-macro">{esc}</span>')
        elif kind == 'CMD_OPTION':
            parts.append(f'<span class="sv-cmdline-opt">{esc}</span>')
        elif kind == 'NUMBER':
            parts.append(f'<span class="sv-number">{esc}</span>')
        elif kind == 'IDENT':
            if val in SV_KEYWORDS:
                parts.append(f'<span class="sv-keyword">{esc}</span>')
            elif val.startswith(('uvm_', 'UVM_')) or val in ('uvm_void', 'uvm_object', 'uvm_component', 'uvm_phase', 'uvm_report_object', 'uvm_driver', 'uvm_sequence', 'uvm_env', 'uvm_test', 'uvm_callbacks'):
                parts.append(f'<span class="sv-uvm-type">{esc}</span>')
            else:
                rest = code[end:].lstrip()
                if rest.startswith('(') and val not in ('if', 'for', 'while', 'case', 'return', 'super', 'this'):
                    parts.append(f'<span class="sv-method">{esc}</span>')
                else:
                    parts.append(f'<span class="sv-ident">{esc}</span>')
        elif kind == 'OP':
            parts.append(f'<span class="sv-op">{esc}</span>')
        else:
            parts.append(esc)
            
        pos = end

    return "".join(parts)

def highlight_before_params(text):
    def repl_text(t):
        tokens = re.split(r'(\b[a-zA-Z_][a-zA-Z0-9_]*\b|\()', t)
        words = [tok for tok in tokens if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', tok)]
        method_name = words[-1] if words else None
        res = []
        for tok in tokens:
            if not tok:
                continue
            if tok in SV_KEYWORDS:
                res.append(f'<span class="sv-keyword">{tok}</span>')
            elif tok == method_name:
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
            if w in SV_KEYWORDS:
                return f'<span class="sv-keyword">{w}</span>'
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
                    elif tok in SV_KEYWORDS:
                        parts.append(f'<span class="sv-keyword">{tok}</span>')
                    elif tok.startswith(('uvm_', 'UVM_')):
                        parts.append(f'<span class="sv-uvm-type">{tok}</span>')
                    elif tok in '()=,;':
                        parts.append(f'<span class="sv-op">{tok}</span>')
                    else:
                        next_tok = next((x for x in tokens[idx+1:] if x.strip()), '')
                        if next_tok.startswith('('):
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
        
        # Determine language badge
        if any(clean_code.startswith(x) for x in ('prompt>', '<sim command', 'SIM_COMMAND')) or '+UVM_' in clean_code or '+uvm_' in clean_code:
            lang = "Command Line"
        elif clean_code.startswith('#') or 'extern "C"' in clean_code:
            lang = "C / DPI"
        else:
            lang = "SystemVerilog"
        
        highlighted = highlight_doc_code(clean_code)
        
        return f'''<div class="code-block-container">
  <div class="code-block-header">
    <div class="code-block-lang">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
      <span>{lang}</span>
    </div>
    <button class="code-copy-btn" title="Copy code" aria-label="Copy code to clipboard">
      <svg class="copy-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      <span class="copy-text">Copy</span>
    </button>
  </div>
  <pre class="code-block-content"><code>{highlighted}</code></pre>
</div>'''

    return re.sub(r'(?:<blockquote>\s*)?<pre>([\s\S]*?)</pre>(?:\s*</blockquote>)?', replace_code_block, html_text, flags=re.IGNORECASE)

def process_doc_prototypes(html_text):
    return re.sub(r'<table\b[^>]*class=["\']?Prototype["\']?[^>]*>[\s\S]*?</table>', lambda m: highlight_prototype_table(m.group(0)), html_text, flags=re.IGNORECASE)

# Global Symbol Maps
SYMBOL_MAP = {}
FILE_SYMBOLS = {}
SRC_TO_DOC_MAP = {}
DOC_TO_SRC_MAP = {}
DOC_HEADINGS_MAP = {}

def extract_doc_headings(html_text, rel_doc_path):
    """Extract ordered headings, methods, and groups for a documentation page."""
    headings = []

    # 1. Main Topic (Class / File Title)
    main_m = re.search(r'id=["\']?MainTopic["\']?[\s\S]*?<h[1-4] class=["\']?CTitle["\']?>([\s\S]*?)</h[1-4]>', html_text)
    main_title = None
    if main_m:
        main_title = re.sub(r'<[^>]+>', '', main_m.group(1)).strip()
        a_m = re.search(r'name=["\']([^"\']+)["\']', main_m.group(1))
        anchor = a_m.group(1) if a_m else 'MainTopic'
        headings.append({
            'title': main_title or 'Overview',
            'anchor': anchor,
            'type': 'main',
            'level': 1
        })

    # 2. Check Summary
    if 'class="Summary"' in html_text or 'class=Summary' in html_text:
        headings.append({
            'title': 'Summary',
            'anchor': 'Summary',
            'type': 'summary',
            'level': 1
        })

    # 3. Scan CTopic divs in #Content
    topic_matches = list(re.finditer(
        r'<div class=["\']?(C[A-Za-z0-9_]+)["\']?[^>]*>\s*<div class=["\']?CTopic["\']?[^>]*>[\s\S]*?<(h[1-4])\b[^>]*class=["\']?CTitle["\']?[^>]*>([\s\S]*?)</\2>',
        html_text
    ))

    has_h2 = any(m.group(2).upper() == 'H2' for m in topic_matches)
    current_group = None

    for m in topic_matches:
        cls = m.group(1)
        tag = m.group(2).upper()
        inner = m.group(3)
        title = re.sub(r'<[^>]+>', '', inner).strip()
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
    return "../" * depth if depth > 0 else "./"

def highlight_code_lines(code, filename):
    """
    Stateful tokenizer for SystemVerilog and C/C++ files.
    Returns a list of HTML table rows with line numbers and syntax highlighted tokens.
    """
    is_c = filename.endswith(('.c', '.cc', '.h'))
    keywords = C_KEYWORDS if is_c else SV_KEYWORDS
    lines = code.splitlines()
    rows = []
    in_block_comment = False

    for idx, line in enumerate(lines, 1):
        pos = 0
        line_len = len(line)
        line_parts = []

        while pos < line_len:
            if in_block_comment:
                end_pos = line.find('*/', pos)
                if end_pos != -1:
                    comment_text = line[pos:end_pos + 2]
                    line_parts.append(f'<span class="sv-comment">{html.escape(comment_text)}</span>')
                    pos = end_pos + 2
                    in_block_comment = False
                else:
                    comment_text = line[pos:]
                    line_parts.append(f'<span class="sv-comment">{html.escape(comment_text)}</span>')
                    pos = line_len
            else:
                m = TOKEN_REGEX.search(line, pos)
                if not m:
                    line_parts.append(html.escape(line[pos:]))
                    pos = line_len
                else:
                    start, end = m.span()
                    if start > pos:
                        line_parts.append(html.escape(line[pos:start]))
                    kind = m.lastgroup
                    val = m.group(kind)
                    esc = html.escape(val)

                    if kind == 'BLOCK_COMMENT_START':
                        end_pos = line.find('*/', end)
                        if end_pos != -1:
                            comment_text = line[start:end_pos + 2]
                            line_parts.append(f'<span class="sv-comment">{html.escape(comment_text)}</span>')
                            pos = end_pos + 2
                        else:
                            comment_text = line[start:]
                            line_parts.append(f'<span class="sv-comment">{html.escape(comment_text)}</span>')
                            in_block_comment = True
                            pos = line_len
                    elif kind == 'LINE_COMMENT':
                        line_parts.append(f'<span class="sv-comment">{esc}</span>')
                        pos = end
                    elif kind in ('STRING', 'CHAR'):
                        line_parts.append(f'<span class="sv-string">{esc}</span>')
                        pos = end
                    elif kind == 'MACRO':
                        line_parts.append(f'<span class="sv-macro">{esc}</span>')
                        pos = end
                    elif kind == 'NUMBER':
                        line_parts.append(f'<span class="sv-number">{esc}</span>')
                        pos = end
                    elif kind == 'IDENT':
                        if val in keywords:
                            line_parts.append(f'<span class="sv-keyword">{esc}</span>')
                        elif val.startswith('uvm_') or val.startswith('UVM_'):
                            line_parts.append(f'<span class="sv-uvm-type">{esc}</span>')
                        else:
                            line_parts.append(f'<span class="sv-ident">{esc}</span>')
                        pos = end
                    elif kind == 'OP':
                        line_parts.append(f'<span class="sv-op">{esc}</span>')
                        pos = end

        code_html = "".join(line_parts) or "&nbsp;"
        rows.append(f'<tr id="L{idx}"><td class="ln" data-line="{idx}"><a href="#L{idx}">{idx}</a></td><td class="code">{code_html}</td></tr>')

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
    """Identify which doc file corresponds to which source file."""
    for root, dirs, files in os.walk(DOCS_FILES_DIR):
        for f in files:
            if not f.endswith('.html'):
                continue
            doc_path = Path(root) / f
            doc_rel = doc_path.relative_to(DOCS_FILES_DIR).as_posix()
            try:
                with open(doc_path, 'r', encoding='latin-1') as df:
                    txt = df.read()
            except Exception:
                continue

            m = re.search(r'href=["\'](?:(?:\.\./)+)src/([^"\']+)["\']', txt)
            if m:
                src_rel = m.group(1).replace('\\', '/')
                # Only map if it's an actual source code file in src
                if (SRC_DIR / src_rel).exists():
                    DOC_TO_SRC_MAP[doc_rel] = src_rel
                    SRC_TO_DOC_MAP[src_rel] = doc_rel

    print(f"Mapped {len(DOC_TO_SRC_MAP)} doc files to source files.")

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
            line_count = len(rows)
            file_size_kb = round(len(code.encode('utf-8')) / 1024, 1)

            doc_rel = SRC_TO_DOC_MAP.get(rel_path)
            doc_btn = ""
            if doc_rel:
                doc_href = f"{root_rel}docs_view/{doc_rel}"
                doc_btn = f'''<a href="{doc_href}" class="btn btn-outline src-to-doc-btn" data-doc-url="{doc_href}" title="View Reference Documentation for this file">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                  <span>Documentation</span>
                </a>'''

            raw_href = f"{root_rel}uvm-1.2/src/{rel_path}"

            syms = FILE_SYMBOLS.get(rel_path, [])
            sym_options = "".join([f'<option value="#L{s["line"]}">{s["type"]}: {s["name"]} (L{s["line"]})</option>' for s in syms if s["type"] in ('class', 'macro')])
            sym_select = f'''<select class="sym-jump-select" onchange="if(this.value) window.location.hash = this.value">
              <option value="">Jump to Symbol ({len(syms)} symbols)...</option>
              {sym_options}
            </select>''' if sym_options else ""

            html_content = f'''<!DOCTYPE html>
<html lang="en" data-theme="light" class="src-page">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(rel_path)} | UVM 1.2 Source Code</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=Roboto:wght@400;500;700&family=Roboto+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{root_rel}css/style.css">
</head>
<body class="src-viewer-body">
  <div class="src-sticky-bar">
    <div class="src-breadcrumbs">
      <a href="{root_rel}index.html#/src" target="_parent" class="src-nav-home" title="UVM Source Tree">src</a>
      <span class="sep">/</span>
      <span class="src-cur-file">{html.escape(rel_path)}</span>
      <span class="badge badge-info">{line_count} lines</span>
      <span class="badge badge-secondary">{file_size_kb} KB</span>
    </div>
    <div class="src-actions">
      {sym_select}
      {doc_btn}
      <button class="btn btn-outline" id="copy-src-btn" title="Copy raw source code">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        <span>Copy Code</span>
      </button>
      <a href="{raw_href}" download class="btn btn-outline" title="Download raw source file">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        <span>Raw</span>
      </a>
    </div>
  </div>

  <div class="src-code-container">
    <table class="sv-code-table">
      <tbody>
        {"".join(rows)}
      </tbody>
    </table>
  </div>

  <textarea id="raw-source-text" style="display:none">{html.escape(code)}</textarea>

  <script>
    document.getElementById('copy-src-btn').addEventListener('click', function() {{
      const text = document.getElementById('raw-source-text').value;
      navigator.clipboard.writeText(text).then(() => {{
        const btn = document.getElementById('copy-src-btn');
        const span = btn.querySelector('span');
        const orig = span.textContent;
        span.textContent = 'Copied!';
        btn.classList.add('btn-success');
        setTimeout(() => {{ span.textContent = orig; btn.classList.remove('btn-success'); }}, 2000);
      }});
    }});

    function highlightTargetLine() {{
      const hash = window.location.hash;
      document.querySelectorAll('.sv-code-table tr.active-line').forEach(el => el.classList.remove('active-line'));
      if (hash && hash.startsWith('#L')) {{
        const target = document.querySelector(hash);
        if (target) {{
          target.classList.add('active-line');
          target.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
      }}
    }}
    window.addEventListener('hashchange', highlightTargetLine);
    window.addEventListener('DOMContentLoaded', highlightTargetLine);

    // Theme sync
    window.addEventListener('message', function(e) {{
      if (e.data && e.data.theme) {{
        document.documentElement.setAttribute('data-theme', e.data.theme);
      }}
    }});
    try {{
      const parentTheme = window.parent && window.parent.document && window.parent.document.documentElement.getAttribute('data-theme');
      if (parentTheme) {{
        document.documentElement.setAttribute('data-theme', parentTheme);
      }}
    }} catch (e) {{}}

    // Auto-restore into main app if opened directly outside iframe
    try {{
      if (window.self === window.top) {{
        window.location.replace('{root_rel}index.html#/src/{rel_path}.html' + window.location.hash);
      }}
    }} catch (e) {{}}

    // Intercept clicks on doc button or doc links
    document.addEventListener('click', function(e) {{
      const link = e.target.closest('a');
      if (!link) return;
      const href = link.getAttribute('href');
      if (!href || href === '#' || href.startsWith('javascript:')) return;

      if (link.classList.contains('src-to-doc-btn') || href.includes('docs_view/')) {{
        e.preventDefault();
        const targetHref = new URL(link.getAttribute('href'), window.location.href).href;
        if (window.parent && window.parent !== window) {{
          window.parent.postMessage({{
            type: 'openDocView',
            url: targetHref
          }}, '*');
        }}
        try {{
          if (window.parent && window.parent.openDocView) {{
            window.parent.openDocView(targetHref);
          }}
        }} catch (err) {{}}
      }}
    }});
  </script>
</body>
</html>'''

            with open(out_file, 'w', encoding='utf-8') as of:
                of.write(html_content)
            count += 1

    print(f"Generated {count} syntax-highlighted source views in {OUTPUT_SRC_VIEW}.")

def resolve_cross_doc_path(current_rel_path, target_rel_href):
    """Resolve a relative doc link against current doc file path."""
    cur_dir = posixpath.dirname(current_rel_path)
    combined = posixpath.join(cur_dir, target_rel_href) if cur_dir else target_rel_href
    return posixpath.normpath(combined)

def modernize_doc_files():
    """Modernize all 146 doc files from uvm-1.2/docs/html/files/ into docs_view/."""
    print("Modernizing UVM documentation pages...")
    if OUTPUT_DOCS_VIEW.exists():
        shutil.rmtree(OUTPUT_DOCS_VIEW)
    OUTPUT_DOCS_VIEW.mkdir(parents=True, exist_ok=True)

    # Pass 1: Build anchor to ID maps for all doc files
    global_doc_anchor_maps = {}
    for root, dirs, files in os.walk(DOCS_FILES_DIR):
        for f in sorted(files):
            if not f.endswith('.html'):
                continue
            doc_file = Path(root) / f
            rel_path = doc_file.relative_to(DOCS_FILES_DIR).as_posix()
            try:
                with open(doc_file, 'r', encoding='latin-1') as df:
                    raw_html = df.read()
            except Exception:
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

            parts = re.split(r'(<div class=["\']C[A-Za-z0-9_]+["\']\s*>\s*<div class=["\']?CTopic["\']?[^>]*>)', body)
            seq = 0
            for i in range(1, len(parts), 2):
                w_start = parts[i]
                w_body = parts[i+1]
                is_main = ('id=MainTopic' in w_start or 'id="MainTopic"' in w_start)
                a_m = re.search(r'<a\s+name=["\']([^"\']+)["\']', w_body)
                a_name = a_m.group(1) if a_m else None
                if is_main:
                    if a_name: a_map[a_name] = 'doc-nav-main'
                else:
                    seq += 1
                    if a_name: a_map[a_name] = f"doc-nav-item-{seq}"

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
                new_parts.append(mod_start)
                new_parts.append(w_body)

            body_content = "".join(new_parts)
            body_content = body_content.replace('<div class=Summary>', '<div class="Summary" id="doc-nav-summary" data-anchor="Summary">')
            body_content = body_content.replace('<div class="Summary">', '<div class="Summary" id="doc-nav-summary" data-anchor="Summary">')

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

            # Record headings for left navigation subheadings and search
            doc_key = f"docs_view/{rel_path}"
            DOC_HEADINGS_MAP[doc_key] = extract_doc_headings(body_content, rel_path)

            # Injected "View Source Code" badge only if real source exists
            view_source_banner = ""
            if associated_src and (SRC_DIR / associated_src).exists():
                src_view_url = f"{root_rel}src_view/{associated_src}.html#L{target_line}"
                view_source_banner = f'''<div class="doc-source-banner">
                  <div class="banner-info">
                    <span class="file-label">Source File:</span>
                    <a href="{src_view_url}" class="banner-file-link src-code-link" data-src-url="{src_view_url}"><code>src/{html.escape(associated_src)}</code></a>
                  </div>
                  <div class="banner-actions">
                    <a href="{src_view_url}" class="btn btn-primary btn-sm src-code-link" data-src-url="{src_view_url}" title="Open source code with syntax highlighting at line {target_line}">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                      <span>View Source (Line {target_line})</span>
                    </a>
                  </div>
                </div>'''

            modern_html = f'''<!DOCTYPE html>
<html lang="en" data-theme="light" class="doc-page">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(page_title)} | UVM 1.2 Documentation</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=Roboto:wght@400;500;700&family=Roboto+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{root_rel}css/style.css">
</head>
<body class="doc-body">
  <div class="doc-page-container">
    {view_source_banner}
    <div class="doc-layout-wrapper">
      <div class="doc-main-content">
        {body_content}
      </div>
      <aside class="doc-toc-sidebar" id="doc-toc-sidebar" aria-label="On this page">
        <div class="doc-toc-inner">
          <div class="doc-toc-header">
            <span class="doc-toc-title">On this page</span>
            <button class="doc-toc-toggle-all-btn" id="doc-toc-toggle-all" type="button" title="Collapse or expand all sections">
              <svg class="toc-toggle-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="4 14 12 6 20 14"/>
              </svg>
              <span class="toc-toggle-text">Collapse all</span>
            </button>
          </div>
          <nav class="doc-toc-nav" id="doc-toc-nav"></nav>
        </div>
      </aside>
    </div>
  </div>

  <script>
    // In-page Table of Contents (On this page) generator & Scrollspy
    (function initDocTOC() {{
      const contentEl = document.getElementById('Content');
      const tocSidebar = document.getElementById('doc-toc-sidebar');
      const tocNav = document.getElementById('doc-toc-nav');
      const toggleAllBtn = document.getElementById('doc-toc-toggle-all');
      if (!contentEl || !tocSidebar || !tocNav) return;

      const topItems = [];
      const groups = [];
      const standaloneItems = [];
      let currentGroup = null;
      let topicSeq = 0;

      // 1. Check main topic
      const mainTopic = contentEl.querySelector('#MainTopic .CTitle, #MainTopic h1, #MainTopic h2');
      if (mainTopic) {{
        const safeId = 'doc-nav-main';
        mainTopic.id = safeId;
        const mainA = mainTopic.querySelector('a[name]');
        const mainAnchor = mainA ? mainA.getAttribute('name') : 'MainTopic';
        mainTopic.setAttribute('data-anchor', mainAnchor);
        topItems.push({{
          id: safeId,
          anchor: mainAnchor,
          title: (mainTopic.innerText || mainTopic.textContent || 'Overview').trim(),
          type: 'main',
          el: mainTopic
        }});
      }}

      // 2. Check summary
      const summaryEl = contentEl.querySelector('.Summary');
      if (summaryEl) {{
        const safeId = 'doc-nav-summary';
        summaryEl.id = safeId;
        summaryEl.setAttribute('data-anchor', 'Summary');
        topItems.push({{
          id: safeId,
          anchor: 'Summary',
          title: 'Summary',
          type: 'summary',
          el: summaryEl
        }});
      }}

      // 3. Scan all topics in #Content
      const topicWrappers = contentEl.querySelectorAll('#Content > div');

      // Check if page contains H2 topics
      let hasH2 = false;
      for (let i = 0; i < topicWrappers.length; i++) {{
        const topic = topicWrappers[i].querySelector('.CTopic');
        if (!topic || topic.id === 'MainTopic') continue;
        const titleEl = topic.querySelector('.CTitle');
        if (titleEl && titleEl.tagName.toUpperCase() === 'H2') {{
          hasH2 = true;
          break;
        }}
      }}

      topicWrappers.forEach(function(wrap) {{
        const topic = wrap.querySelector('.CTopic');
        if (!topic || topic.id === 'MainTopic') return;
        const titleEl = topic.querySelector('.CTitle');
        if (!titleEl) return;
        const rawTitle = (titleEl.innerText || titleEl.textContent || '').trim();
        if (!rawTitle) return;

        const safeId = wrap.id || wrap.getAttribute('data-doc-topic') || ('doc-nav-item-' + (++topicSeq));
        wrap.id = safeId;
        wrap.setAttribute('data-doc-topic', safeId);
        if (topic) topic.id = topic.id || (safeId + '-topic');

        const aTag = wrap.querySelector('a[name]');
        const aName = wrap.getAttribute('data-anchor') || (aTag ? aTag.getAttribute('name') : '');
        if (aName) {{
          wrap.setAttribute('data-anchor', aName);
        }}

        const cls = wrap.className || '';
        const tag = titleEl.tagName.toUpperCase();
        const isH2 = tag === 'H2';
        const isCGroup = cls.indexOf('CGroup') !== -1;

        if (hasH2) {{
          if (isH2) {{
            currentGroup = {{
              id: safeId,
              anchor: aName || safeId,
              title: rawTitle,
              el: wrap,
              items: []
            }};
            groups.push(currentGroup);
          }} else {{
            const itemObj = {{
              id: safeId,
              anchor: aName || safeId,
              title: rawTitle,
              el: wrap,
              isGroupHeader: isCGroup,
              type: 'subitem'
            }};
            if (currentGroup) {{
              currentGroup.items.push(itemObj);
            }} else {{
              standaloneItems.push(itemObj);
            }}
          }}
        }} else {{
          if (isCGroup) {{
            currentGroup = {{
              id: safeId,
              anchor: aName || safeId,
              title: rawTitle,
              el: wrap,
              items: []
            }};
            groups.push(currentGroup);
          }} else {{
            const itemObj = {{
              id: safeId,
              anchor: aName || safeId,
              title: rawTitle,
              el: wrap,
              isGroupHeader: false,
              type: 'subitem'
            }};
            if (currentGroup) {{
              currentGroup.items.push(itemObj);
            }} else {{
              standaloneItems.push(itemObj);
            }}
          }}
        }}
      }});

      const totalItemsCount = topItems.length + standaloneItems.length + groups.length + groups.reduce(function(acc, g) {{ return acc + g.items.length; }}, 0);
      if (totalItemsCount <= 1) {{
        tocSidebar.style.display = 'none';
        return;
      }}

      // Show/hide the "toggle all" button depending on whether groups exist
      if (toggleAllBtn) {{
        if (groups.length === 0) {{
          toggleAllBtn.style.display = 'none';
        }} else {{
          toggleAllBtn.style.display = 'inline-flex';
        }}
      }}

      // Render TOC Tree HTML
      let html = '';

      // Top-level / standalone items (Overview, Summary, early methods)
      const initialItems = topItems.concat(standaloneItems);
      if (initialItems.length > 0) {{
        html += '<ul class="doc-toc-list">';
        initialItems.forEach(function(item) {{
          const cleanTitle = item.title.replace(/"/g, '&quot;');
          html += '<li class="doc-toc-item">';
          html += '<a href="#' + item.id + '" data-target-id="' + item.id + '" class="doc-toc-link" title="' + cleanTitle + '">';
          html += cleanTitle;
          html += '</a></li>';
        }});
        html += '</ul>';
      }}

      // Collapsible Groups
      groups.forEach(function(group) {{
        const cleanGroupTitle = group.title.replace(/"/g, '&quot;');
        const hasSubItems = group.items.length > 0;
        html += '<div class="doc-toc-group-block' + (hasSubItems ? '' : ' no-children') + '" id="block-' + group.id + '">';
        html += '<div class="doc-toc-group-header">';
        if (hasSubItems) {{
          html += '<button class="doc-toc-chevron-btn" type="button" aria-label="Toggle group ' + cleanGroupTitle + '" title="Toggle group">';
          html += '<svg class="doc-toc-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';
          html += '</button>';
        }} else {{
          html += '<span class="doc-toc-dot-indicator"></span>';
        }}
        html += '<a href="#' + group.id + '" data-target-id="' + group.id + '" class="doc-toc-link doc-toc-group-title" title="' + cleanGroupTitle + '">';
        html += cleanGroupTitle;
        html += '</a>';
        if (hasSubItems) {{
          html += '<span class="doc-toc-badge">' + group.items.length + '</span>';
        }}
        html += '</div>';

        if (hasSubItems) {{
          html += '<ul class="doc-toc-subitems">';
          group.items.forEach(function(sub) {{
            const cleanSubTitle = sub.title.replace(/"/g, '&quot;');
            const extraCls = sub.isGroupHeader ? ' doc-toc-subgroup-header' : '';
            html += '<li class="doc-toc-item doc-toc-subitem' + extraCls + '">';
            html += '<a href="#' + sub.id + '" data-target-id="' + sub.id + '" class="doc-toc-link' + (sub.isGroupHeader ? ' doc-toc-subgroup-link' : '') + '" title="' + cleanSubTitle + '">';
            html += cleanSubTitle;
            html += '</a></li>';
          }});
          html += '</ul>';
        }}
        html += '</div>';
      }});

      tocNav.innerHTML = html;

      // Flatten list of all navigable items for scrollspy & lookup
      const allNavItems = [];
      initialItems.forEach(function(item) {{
        const link = tocNav.querySelector('.doc-toc-link[data-target-id="' + item.id + '"]');
        allNavItems.push({{ id: item.id, anchor: item.anchor || item.id, title: item.title, el: item.el, link: link }});
      }});
      groups.forEach(function(group) {{
        const groupLink = tocNav.querySelector('.doc-toc-link[data-target-id="' + group.id + '"]');
        allNavItems.push({{ id: group.id, anchor: group.anchor || group.id, title: group.title, el: group.el, link: groupLink }});
        group.items.forEach(function(sub) {{
          const subLink = tocNav.querySelector('.doc-toc-link[data-target-id="' + sub.id + '"]');
          allNavItems.push({{ id: sub.id, anchor: sub.anchor || sub.id, title: sub.title, el: sub.el, link: subLink }});
        }});
      }});

      // Smooth scroll helper
      let isManualScrolling = false;
      let manualScrollTimer = null;

      function scrollToElement(targetEl) {{
        if (!targetEl) return;
        try {{
          targetEl.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }} catch (e) {{
          targetEl.scrollIntoView(true);
        }}
        targetEl.classList.add('doc-target-highlight');
        setTimeout(function() {{
          targetEl.classList.remove('doc-target-highlight');
        }}, 1600);
      }}

      // Click on any TOC link
      const tocLinks = tocNav.querySelectorAll('.doc-toc-link');
      tocLinks.forEach(function(link) {{
        link.addEventListener('click', function(e) {{
          e.preventDefault();
          isManualScrolling = true;
          clearTimeout(manualScrollTimer);

          const targetId = link.getAttribute('data-target-id');
          const target = document.getElementById(targetId) || document.querySelector('[data-doc-topic="' + targetId + '"]');

          // Highlight clicked link immediately
          tocLinks.forEach(function(l) {{ l.classList.remove('active'); }});
          link.classList.add('active');

          // If inside a collapsed group, un-collapse it so it is visible
          const parentGroupBlock = link.closest('.doc-toc-group-block');
          if (parentGroupBlock && parentGroupBlock.classList.contains('collapsed')) {{
            parentGroupBlock.classList.remove('collapsed');
            updateToggleAllBtn();
          }}

          if (target) {{
            scrollToElement(target);
          }}

          manualScrollTimer = setTimeout(function() {{
            isManualScrolling = false;
          }}, 800);
        }});
      }});

      // Unified click handler for internal anchor/topic links in #Content
      contentEl.addEventListener('click', function(e) {{
        const link = e.target.closest('a[href*="#"]');
        if (!link) return;
        const href = link.getAttribute('href');
        if (!href || href === '#' || href.startsWith('javascript:')) return;

        // If it's a source code link, let the source code link handler deal with it
        if (link.classList.contains('src-code-link') || href.includes('src_view/')) return;

        // Check if link is an in-page anchor link (starts with #)
        if (href.startsWith('#')) {{
          const targetId = link.getAttribute('data-target-id') || href.substring(1);
          let target = document.getElementById(targetId) || document.querySelector('[data-doc-topic="' + targetId + '"]');
          if (!target) {{
            try {{
              target = document.querySelector('[data-anchor="' + CSS.escape(targetId) + '"]') ||
                       document.querySelector('a[name="' + CSS.escape(targetId) + '"]');
            }} catch (err) {{}}
          }}
          if (target && target.tagName === 'A' && target.closest) {{
            target = target.closest('#Content > div') || target.closest('.CTopic') || target;
          }}
          if (target) {{
            e.preventDefault();
            isManualScrolling = true;
            clearTimeout(manualScrollTimer);
            scrollToElement(target);
            manualScrollTimer = setTimeout(function() {{
              isManualScrolling = false;
            }}, 800);

            const realId = target.id || target.getAttribute('data-doc-topic') || targetId;
            try {{
              history.replaceState(null, null, '#' + realId);
            }} catch (err) {{}}

            if (tocNav && realId) {{
              const mLink = tocNav.querySelector('.doc-toc-link[data-target-id="' + realId + '"]');
              if (mLink) {{
                tocLinks.forEach(function(l) {{ l.classList.remove('active'); }});
                mLink.classList.add('active');
                const pB = mLink.closest('.doc-toc-group-block');
                if (pB && pB.classList.contains('collapsed')) {{
                  pB.classList.remove('collapsed');
                  updateToggleAllBtn();
                }}
              }}
            }}
          }}
        }}
      }});

      // Group chevron expand/collapse toggles
      const chevronBtns = tocNav.querySelectorAll('.doc-toc-chevron-btn');
      chevronBtns.forEach(function(btn) {{
        btn.addEventListener('click', function(e) {{
          e.stopPropagation();
          const block = btn.closest('.doc-toc-group-block');
          if (block) {{
            block.classList.toggle('collapsed');
            updateToggleAllBtn();
          }}
        }});
      }});

      // Toggle all button logic
      function updateToggleAllBtn() {{
        if (!toggleAllBtn) return;
        const allBlocks = tocNav.querySelectorAll('.doc-toc-group-block');
        if (allBlocks.length === 0) return;
        const allCollapsed = Array.from(allBlocks).every(function(b) {{ return b.classList.contains('collapsed'); }});
        const textSpan = toggleAllBtn.querySelector('.toc-toggle-text');
        const icon = toggleAllBtn.querySelector('.toc-toggle-icon');
        if (allCollapsed) {{
          if (textSpan) textSpan.textContent = 'Expand all';
          if (icon) icon.innerHTML = '<polyline points="4 6 12 14 20 6"/>';
        }} else {{
          if (textSpan) textSpan.textContent = 'Collapse all';
          if (icon) icon.innerHTML = '<polyline points="4 14 12 6 20 14"/>';
        }}
      }}

      if (toggleAllBtn) {{
        toggleAllBtn.addEventListener('click', function() {{
          const allBlocks = tocNav.querySelectorAll('.doc-toc-group-block');
          const anyExpanded = Array.from(allBlocks).some(function(b) {{ return !b.classList.contains('collapsed'); }});
          if (anyExpanded) {{
            // Collapse all
            allBlocks.forEach(function(b) {{ b.classList.add('collapsed'); }});
          }} else {{
            // Expand all
            allBlocks.forEach(function(b) {{ b.classList.remove('collapsed'); }});
          }}
          updateToggleAllBtn();
        }});
      }}

      // ScrollSpy: highlight active link and expand parent group if needed
      let scrollTimer = null;
      function updateScrollSpy() {{
        if (isManualScrolling) return;

        let activeItem = null;
        for (let i = 0; i < allNavItems.length; i++) {{
          const item = allNavItems[i];
          if (!item.el) continue;
          const rect = item.el.getBoundingClientRect();
          if (rect.top <= 100) {{
            activeItem = item;
          }} else {{
            break;
          }}
        }}

        if (!activeItem && allNavItems.length > 0) {{
          activeItem = allNavItems[0];
        }}

        if (activeItem && activeItem.link) {{
          tocLinks.forEach(function(link) {{
            link.classList.toggle('active', link === activeItem.link);
          }});

          // Auto-expand group if active method is inside a collapsed group
          const parentBlock = activeItem.link.closest('.doc-toc-group-block');
          if (parentBlock && parentBlock.classList.contains('collapsed')) {{
            parentBlock.classList.remove('collapsed');
            updateToggleAllBtn();
          }}

          activeItem.link.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});

          // Sync active section to parent window (left sidebar navigation)
          if (window.parent && window.parent !== window) {{
            try {{
              window.parent.postMessage({{
                type: 'docSectionChanged',
                anchor: activeItem.anchor || activeItem.id,
                id: activeItem.id,
                title: activeItem.title
              }}, '*');
            }} catch (err) {{}}
          }}
        }}
      }}

      window.addEventListener('scroll', function() {{
        if (scrollTimer) return;
        scrollTimer = requestAnimationFrame(function() {{
          updateScrollSpy();
          scrollTimer = null;
        }});
      }}, {{ passive: true }});

      // Cross-frame listener to scroll directly to anchor/topic from left sidebar
      window.addEventListener('message', function(e) {{
        if (!e.data || typeof e.data !== 'object') return;
        if (e.data.type === 'scrollToSection') {{
          const anchor = e.data.anchor;
          const targetId = e.data.id;
          let target = null;
          if (anchor) {{
            if (anchor === 'MainTopic' || anchor === 'Overview') {{
              target = document.getElementById('doc-nav-main') || document.getElementById('MainTopic');
            }} else if (anchor === 'Summary') {{
              target = document.getElementById('doc-nav-summary') || document.querySelector('.Summary');
            }} else {{
              try {{
                target = document.querySelector('[data-anchor="' + CSS.escape(anchor) + '"]') ||
                         document.querySelector('a[name="' + CSS.escape(anchor) + '"]');
              }} catch (err) {{ }}
              if (!target) {{
                const allA = document.querySelectorAll('[data-anchor], a[name]');
                for (let i = 0; i < allA.length; i++) {{
                  if (allA[i].getAttribute('data-anchor') === anchor || allA[i].getAttribute('name') === anchor) {{
                    target = allA[i];
                    break;
                  }}
                }}
              }}
              if (target && target.tagName === 'A' && target.closest) {{
                target = target.closest('#Content > div') || target.closest('.CTopic') || target;
              }}
            }}
          }}
          if (!target && targetId) {{
            target = document.getElementById(targetId) || document.querySelector('[data-doc-topic="' + targetId + '"]');
          }}
          if (target) {{
            isManualScrolling = true;
            clearTimeout(manualScrollTimer);
            scrollToElement(target);
            manualScrollTimer = setTimeout(function() {{ isManualScrolling = false; }}, 800);
            const targetNavId = target.id || target.getAttribute('data-doc-topic');
            if (tocNav && targetNavId) {{
              const mLink = tocNav.querySelector('.doc-toc-link[data-target-id="' + targetNavId + '"]');
              if (mLink) {{
                tocLinks.forEach(function(l) {{ l.classList.remove('active'); }});
                mLink.classList.add('active');
                const pB = mLink.closest('.doc-toc-group-block');
                if (pB && pB.classList.contains('collapsed')) {{
                  pB.classList.remove('collapsed');
                  updateToggleAllBtn();
                }}
              }}
            }}
          }}
        }}
      }});

      // Handle direct hash navigation on initial load or hashchange
      function handleHashNav(hashVal) {{
        if (!hashVal) return;
        const raw = decodeURIComponent(hashVal.replace(/^#/, ''));
        if (!raw) return;
        setTimeout(function() {{
          window.postMessage({{ type: 'scrollToSection', anchor: raw, id: raw }}, '*');
        }}, 160);
      }}

      if (window.location.hash) {{
        handleHashNav(window.location.hash);
      }}

      window.addEventListener('hashchange', function() {{
        handleHashNav(window.location.hash);
      }});

      setTimeout(updateScrollSpy, 120);
    }})();

    // Code snippet copy button handler
    document.addEventListener('click', function(e) {{
      const btn = e.target.closest('.code-copy-btn');
      if (!btn) return;
      const container = btn.closest('.code-block-container');
      if (!container) return;
      const codeEl = container.querySelector('code');
      if (!codeEl) return;
      const text = codeEl.innerText || codeEl.textContent;
      navigator.clipboard.writeText(text).then(() => {{
        const copyText = btn.querySelector('.copy-text');
        const orig = copyText ? copyText.textContent : 'Copy';
        btn.classList.add('copied');
        if (copyText) copyText.textContent = 'Copied!';
        setTimeout(() => {{
          btn.classList.remove('copied');
          if (copyText) copyText.textContent = orig;
        }}, 2000);
      }}).catch(err => {{
        console.error('Copy failed: ', err);
      }});
    }});

    // Theme sync
    window.addEventListener('message', function(e) {{
      if (e.data && e.data.theme) {{
        document.documentElement.setAttribute('data-theme', e.data.theme);
      }}
    }});
    try {{
      const parentTheme = window.parent && window.parent.document && window.parent.document.documentElement.getAttribute('data-theme');
      if (parentTheme) {{
        document.documentElement.setAttribute('data-theme', parentTheme);
      }}
    }} catch (e) {{}}

    // Auto-restore into main app if opened directly outside iframe
    try {{
      if (window.self === window.top) {{
        window.location.replace('{root_rel}index.html#/doc/{rel_path}' + window.location.hash);
      }}
    }} catch (e) {{}}

    // Inform parent that doc is loaded
    try {{
      if (window.parent && window.parent !== window) {{
        window.parent.postMessage({{
          type: 'docNavigated',
          url: 'docs_view/{rel_path}'
        }}, '*');
      }}
    }} catch (e) {{}}

    // Intercept clicks on source code links
    document.addEventListener('click', function(e) {{
      const link = e.target.closest('a');
      if (!link) return;
      const href = link.getAttribute('href');
      if (!href || href === '#' || href.startsWith('javascript:')) return;

      if (link.classList.contains('src-code-link') || href.includes('src_view/')) {{
        e.preventDefault();
        const targetHref = new URL(link.getAttribute('href'), window.location.href).href;
        if (window.parent && window.parent !== window) {{
          window.parent.postMessage({{
            type: 'openSourceView',
            url: targetHref
          }}, '*');
        }}
        try {{
          if (window.parent && window.parent.openSourceView) {{
            window.parent.openSourceView(targetHref);
          }}
        }} catch (err) {{}}
      }}
    }});
  </script>
</body>
</html>'''

            with open(out_file, 'w', encoding='utf-8') as of:
                of.write(modern_html)
            count += 1

    print(f"Modernized {count} documentation pages in {OUTPUT_DOCS_VIEW}.")

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
                title = m_title.group(1).strip() if m_title else "Group"
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
                    entries.append({'type': 'group', 'title': title, 'children': children})
            elif '<div class=MFile>' in entry_html or '<div class=MIndex>' in entry_html:
                is_index = '<div class=MIndex>' in entry_html
                m = re.search(r'<a href="([^"]+)">([^<]+)</a>', entry_html)
                if m:
                    raw_href = m.group(1).strip()
                    norm_href = raw_href
                    if raw_href.startswith('files/'):
                        norm_href = 'docs_view/' + raw_href[len('files/'):]
                    entries.append({
                        'type': 'index' if is_index else 'file',
                        'title': m.group(2).strip(),
                        'href': norm_href
                    })
            i = end_pos
        return entries

    menu_start = html_text.find('<div id=Menu>')
    menu_end = html_text.find('<script', menu_start)
    menu_content = html_text[menu_start + len('<div id=Menu>'):menu_end]
    return parse_snippet(menu_content)

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
            search_items.append({
                'name': cname,
                'type': 'class',
                'category': src_file.split('/')[0].capitalize(),
                'src': f"src_view/{src_file}.html#L{info['line']}",
                'doc': f"docs_view/{doc_file}" if doc_file else None,
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

    return search_items

def generate_search_and_nav_data():
    """Generate js/search_data.js for client-side search and menu tree."""
    print("Generating search index and navigation data...")
    categories = parse_navigation_and_categories()
    source_tree = build_source_tree()
    search_items = build_search_index(categories)

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
        "searchIndex": search_items,
        "docToSrc": doc_to_src,
        "srcToDoc": src_to_doc,
        "docHeadings": DOC_HEADINGS_MAP
    }

    js_content = f"""/**
 * Generated UVM 1.2 Documentation Data & Navigation Index
 * Contains category tree, source tree, and full search index.
 */
const UVM_DATA = {json.dumps(payload, indent=2)};
"""
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"Generated {out_file} with {len(search_items)} searchable items.")

def main():
    print("=" * 60)
    print("  UVM 1.2 Documentation & Web Source Viewer Generator")
    print("=" * 60)

    index_source_symbols()
    map_docs_to_sources()
    generate_source_views()
    modernize_doc_files()
    copy_assets()
    generate_search_and_nav_data()

    print("=" * 60)
    print("  Documentation build complete successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
