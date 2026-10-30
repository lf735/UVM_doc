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

def modernize_doc_files():
    """Modernize all 146 doc files from uvm-1.2/docs/html/files/ into docs_view/."""
    print("Modernizing UVM documentation pages...")
    if OUTPUT_DOCS_VIEW.exists():
        shutil.rmtree(OUTPUT_DOCS_VIEW)
    OUTPUT_DOCS_VIEW.mkdir(parents=True, exist_ok=True)

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

            # Syntax highlight documentation code blocks (<pre>)
            body_content = process_doc_code_blocks(body_content)

            # Syntax highlight method/class/task prototypes (<table class=Prototype>)
            body_content = process_doc_prototypes(body_content)

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
    <div class="doc-main-content">
      {body_content}
    </div>
  </div>

  <script>
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
        "srcToDoc": src_to_doc
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
