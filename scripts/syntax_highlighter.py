#!/usr/bin/env python3
"""
UVM 1.2 Syntax Highlighter Module
Provides state-of-the-art tokenization and syntax highlighting for:
- SystemVerilog (IEEE 1800-2017) with deep UVM 1.2 awareness
- C / C++ DPI sources and headers
- Makefiles
- HTML documentation code blocks & prototype tables
"""

import re
import html
from typing import List, Tuple, Optional, Set, Dict

# ==============================================================================
# SystemVerilog Keyword & Token Classifications
# ==============================================================================

SV_CONTROL_KEYWORDS: Set[str] = {
    'begin', 'end', 'if', 'else', 'case', 'casex', 'casez', 'default', 'endcase',
    'for', 'foreach', 'while', 'do', 'repeat', 'forever', 'return',
    'break', 'continue', 'wait', 'wait_order', 'fork', 'join',
    'join_any', 'join_none', 'disable', 'randcase', 'randsequence',
    'expect', 'matches'
}

SV_DECL_KEYWORDS: Set[str] = {
    'class', 'endclass', 'module', 'endmodule', 'interface', 'endinterface',
    'package', 'endpackage', 'program', 'endprogram', 'function', 'endfunction',
    'task', 'endtask', 'extends', 'implements', 'typedef', 'enum', 'struct',
    'union', 'covergroup', 'endgroup', 'property', 'endproperty', 'sequence',
    'endsequence', 'generate', 'endgenerate', 'clocking', 'endclocking',
    'import', 'export', 'checker', 'endchecker', 'config', 'endconfig',
    'primitive', 'endprimitive', 'table', 'endtable', 'specify', 'endspecify',
    'bind', 'alias', 'assign', 'deassign', 'force', 'release', 'defparam',
    'design', 'instance', 'cell', 'use', 'liblist', 'library', 'nettype',
    'initial', 'final', 'always', 'always_comb', 'always_ff', 'always_latch',
    'cover', 'coverpoint', 'cross', 'bins', 'binsof', 'illegal_bins', 'ignore_bins',
    'assert', 'assume', 'restrict', 'constraint', 'solve', 'before', 'with',
    'inside', 'dist', 'tagged', 'accept_tr', 'reject_on', 'sync_accept_on',
    'sync_reject_on', 'first_match', 'throughout', 'within', 'intersect',
    'nexttime', 's_nexttime', 'always_s', 's_always', 'eventually', 's_eventually',
    'until', 's_until', 'until_with', 's_until_with', 'implements'
}

SV_BUILTIN_TYPES: Set[str] = {
    'bit', 'logic', 'reg', 'wire', 'tri', 'tri0', 'tri1', 'wand', 'wor',
    'triand', 'trior', 'trireg', 'uwire', 'supply0', 'supply1',
    'byte', 'shortint', 'int', 'longint', 'integer', 'time',
    'shortreal', 'real', 'realtime', 'string', 'chandle', 'event', 'void',
    'signed', 'unsigned', 'type', 'var'
}

SV_QUALIFIERS: Set[str] = {
    'virtual', 'local', 'protected', 'pure', 'static', 'const',
    'automatic', 'rand', 'randc', 'ref', 'input', 'output', 'inout',
    'extern', 'packed', 'untyped', 'interconnect', 'modport',
    'priority', 'unique', 'unique0', 'soft', 'strong', 'weak',
    'weak0', 'weak1', 'pull0', 'pull1', 'pulldown', 'pullup',
    'highz0', 'highz1', 'small', 'medium', 'large', 'scalared',
    'vectored', 'pulsestyle_onevent', 'pulsestyle_ondetect',
    'showcancelled', 'noshowcancelled', 'edge', 'posedge', 'negedge'
}

SV_CONSTANTS: Set[str] = {
    'null', 'this', 'super', '$root', '$unit',
    # UVM predefined verbosities
    'UVM_NONE', 'UVM_LOW', 'UVM_MEDIUM', 'UVM_HIGH', 'UVM_FULL', 'UVM_DEBUG',
    # UVM actions & severities
    'UVM_INFO', 'UVM_WARNING', 'UVM_ERROR', 'UVM_FATAL',
    'UVM_NO_ACTION', 'UVM_DISPLAY', 'UVM_LOG', 'UVM_COUNT', 'UVM_EXIT', 'UVM_CALL', 'UVM_STOP', 'UVM_RM_RECORD',
    # UVM configuration & fields
    'UVM_ALL_ON', 'UVM_DEFAULT', 'UVM_PASSIVE', 'UVM_ACTIVE',
    'UVM_COPY', 'UVM_COMPARE', 'UVM_PRINT', 'UVM_RECORD', 'UVM_PACK', 'UVM_UNPACK',
    'UVM_NOCOPY', 'UVM_NOCOMPARE', 'UVM_NOPRINT', 'UVM_NORECORD', 'UVM_NOPACK',
    'UVM_REFERENCE', 'UVM_PHYSICAL', 'UVM_ABSTRACT', 'UVM_READ', 'UVM_WRITE',
    'UVM_HEX', 'UVM_DEC', 'UVM_BIN', 'UVM_OCT', 'UVM_STRING', 'UVM_TIME',
    # TLM-2 standard command and responses
    'UVM_TLM_READ_COMMAND', 'UVM_TLM_WRITE_COMMAND', 'UVM_TLM_IGNORE_COMMAND',
    'UVM_TLM_OK_RESPONSE', 'UVM_TLM_INCOMPLETE_RESPONSE', 'UVM_TLM_GENERIC_ERROR_RESPONSE',
    'UVM_TLM_ADDRESS_ERROR_RESPONSE', 'UVM_TLM_COMMAND_ERROR_RESPONSE',
    'UVM_TLM_BURST_ERROR_RESPONSE', 'UVM_TLM_BYTE_ENABLE_ERROR_RESPONSE',
    'UVM_TLM_ACCEPTED', 'UVM_TLM_UPDATED', 'UVM_TLM_COMPLETED'
}

SV_PREPROCESSOR_DIRECTIVES: Set[str] = {
    '`define', '`undef', '`ifdef', '`ifndef', '`else', '`elsif', '`endif',
    '`include', '`timescale', '`default_nettype', '`line', '`resetall',
    '`celldefine', '`endcelldefine', '`protect', '`endprotect'
}

# Known UVM lifecycle, phase and core API methods for accurate semantic highlighting
KNOWN_UVM_METHODS: Set[str] = {
    'build_phase', 'connect_phase', 'end_of_elaboration_phase',
    'start_of_simulation_phase', 'run_phase', 'pre_reset_phase', 'reset_phase',
    'post_reset_phase', 'pre_configure_phase', 'configure_phase',
    'post_configure_phase', 'pre_main_phase', 'main_phase', 'post_main_phase',
    'pre_shutdown_phase', 'shutdown_phase', 'post_shutdown_phase',
    'extract_phase', 'check_phase', 'report_phase', 'final_phase',
    'phase_started', 'phase_ready_to_end', 'phase_ended',
    'raise_objection', 'drop_objection', 'set_drain_time',
    'start_item', 'finish_item', 'start', 'body', 'pre_body', 'post_body',
    'create', 'get_type', 'type_id', 'run_test',
    'set_config_int', 'set_config_string', 'set_config_object',
    'get_config_int', 'get_config_string', 'get_config_object',
    'set_report_verbosity_level', 'set_report_id_verbosity',
    'set_report_severity_action', 'set_report_id_action',
    'print', 'clone', 'copy', 'compare', 'pack', 'unpack', 'record',
    'sprint', 'convert2string', 'do_print', 'do_copy', 'do_compare',
    'do_pack', 'do_unpack', 'do_record', 'sample', 'get_full_name',
    'get_name', 'get_parent', 'get_num_children', 'lookup',
    'b_transport', 'nb_transport_fw', 'nb_transport_bw', 'can_put', 'can_get',
    'try_put', 'try_get', 'put', 'get', 'peek', 'try_peek', 'write'
}

# All SystemVerilog keywords unified for fast checks
ALL_SV_KEYWORDS: Set[str] = (
    SV_CONTROL_KEYWORDS | SV_DECL_KEYWORDS | SV_BUILTIN_TYPES | SV_QUALIFIERS
)

# ==============================================================================
# C / C++ (DPI) Classifications
# ==============================================================================

C_KEYWORDS: Set[str] = {
    'auto', 'break', 'case', 'const', 'continue', 'default', 'do',
    'else', 'enum', 'extern', 'for', 'goto', 'if', 'inline', 'register',
    'restrict', 'return', 'sizeof', 'static', 'struct', 'switch',
    'typedef', 'union', 'volatile', 'while', 'asm', 'class', 'public',
    'private', 'protected', 'virtual', 'friend', 'operator', 'template',
    'this', 'throw', 'try', 'catch', 'namespace', 'using', 'new', 'delete'
}

C_TYPES: Set[str] = {
    'char', 'double', 'float', 'int', 'long', 'short', 'signed', 'unsigned',
    'void', 'bool', 'size_t', 'ssize_t', 'intptr_t', 'uintptr_t',
    'int8_t', 'int16_t', 'int32_t', 'int64_t',
    'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
    'svScope', 'svBit', 'svLogic', 'svBitVecVal', 'svLogicVecVal',
    's_vpi_value', 'p_vpi_value', 's_vpi_time', 'p_vpi_time',
    's_cb_data', 'p_cb_data', 'vpiHandle'
}

C_CONSTANTS: Set[str] = {'NULL', 'null', 'true', 'false', 'TRUE', 'FALSE'}

# ==============================================================================
# Regular Expressions for Tokenization
# ==============================================================================

# SystemVerilog tokenizer pattern
SV_TOKEN_REGEX = re.compile(
    r'(?P<BLOCK_COMMENT_START>/\*)|'
    r'(?P<LINE_COMMENT>//[^\n]*)|'
    r'(?P<STRING>"([^"\\]|\\.)*")|'
    r'(?P<CHAR>\'([^\'\\]|\\.)*\')|'
    r'(?P<MACRO>`[a-zA-Z_][a-zA-Z0-9_]*)|'
    r'(?P<SYSTEM_TF>\$[a-zA-Z_][a-zA-Z0-9_$]*)|'
    r'(?P<BASED_NUM>\b\d+\s*\'[sS]?[bBoOdDhH]\s*[0-9a-fA-F_xzXZ]+\b)|'
    r'(?P<TICK_LITERAL>\'[01xzXZ]\b|\'[sS]?[bBoOdDhH]\s*[0-9a-fA-F_xzXZ]+\b)|'
    r'(?P<TIME_NUM>\b\d+(?:\.\d+)?\s*(?:fs|ps|ns|us|ms|s)\b)|'
    r'(?P<FLOAT_NUM>\b\d+\.\d+(?:[eE][+-]?\d+)?\b)|'
    r'(?P<INT_NUM>\b\d+\b)|'
    r'(?P<IDENT>[a-zA-Z_][a-zA-Z0-9_]*)|'
    r'(?P<OP>::|->>|->|<=|>=|===|!==|==\?|!=\?|==|!=|&&|\|\||\+:|-:|\+:=|-:=|'
    r'\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<=|>>=|<<<=|>>>=|<<<|>>>|<<|>>|\+\+|--|'
    r'\|->|\|=>|##|@@|#\(|[#+\-*/%=&|~^!<>?:;.,()\[\]{}])'
)

# C / C++ tokenizer pattern
C_TOKEN_REGEX = re.compile(
    r'(?P<BLOCK_COMMENT_START>/\*)|'
    r'(?P<LINE_COMMENT>//[^\n]*)|'
    r'(?P<STRING>"([^"\\]|\\.)*")|'
    r'(?P<CHAR>\'([^\'\\]|\\.)*\')|'
    r'(?P<PREPROC>#[a-zA-Z_][a-zA-Z0-9_]*)|'
    r'(?P<FLOAT_NUM>\b\d+\.\d+(?:[eE][+-]?\d+)?\b)|'
    r'(?P<HEX_NUM>\b0[xX][0-9a-fA-F]+\b)|'
    r'(?P<INT_NUM>\b\d+\b)|'
    r'(?P<IDENT>[a-zA-Z_][a-zA-Z0-9_]*)|'
    r'(?P<OP>::|->|<=|>=|==|!=|&&|\|\||\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<=|>>=|'
    r'<<|>>|\+\+|--|[#+\-*/%=&|~^!<>?:;.,()\[\]{}])'
)

# Comment tags inside comments
COMMENT_TAG_REGEX = re.compile(r'\b(TODO|FIXME|NOTE|IMPORTANT|WARNING|TIP|BUG|CLASS|FUNCTION|TASK|MACRO|GROUP|@param|@return|@see)\b:?')

# String escape & format specifiers
STRING_ESCAPE_REGEX = re.compile(r'(%[0-9]*[a-zA-Z%]|\\(?:[ntrbfv\\"\']|[0-7]{1,3}|x[0-9a-fA-F]{1,2}))')


def highlight_comment_content(raw_comment: str) -> str:
    """Escapes comment text while highlighting actionable tags like TODO, NOTE, CLASS."""
    parts = []
    pos = 0
    for m in COMMENT_TAG_REGEX.finditer(raw_comment):
        start, end = m.span()
        if start > pos:
            parts.append(html.escape(raw_comment[pos:start]))
        parts.append(f'<span class="sv-comment-tag">{html.escape(m.group(0))}</span>')
        pos = end
    if pos < len(raw_comment):
        parts.append(html.escape(raw_comment[pos:]))
    return f'<span class="sv-comment">{"".join(parts)}</span>'


def highlight_string_content(raw_string: str) -> str:
    """Escapes string literal while highlighting format specifiers (%s, %0d) and escape characters."""
    parts = []
    pos = 0
    for m in STRING_ESCAPE_REGEX.finditer(raw_string):
        start, end = m.span()
        if start > pos:
            parts.append(html.escape(raw_string[pos:start]))
        parts.append(f'<span class="sv-string-escape">{html.escape(m.group(0))}</span>')
        pos = end
    if pos < len(raw_string):
        parts.append(html.escape(raw_string[pos:]))
    return f'<span class="sv-string">{"".join(parts)}</span>'


# ==============================================================================
# SystemVerilog Highlighter
# ==============================================================================

def tokenize_sv_line(
    line: str,
    in_block_comment: bool,
    clickable_sym_links: bool = False
) -> Tuple[List[str], bool]:
    """
    Tokenizes a single line of SystemVerilog code into HTML syntax spans.
    Returns: (list_of_html_spans, new_in_block_comment_state)
    """
    pos = 0
    line_len = len(line)
    line_parts: List[str] = []

    while pos < line_len:
        if in_block_comment:
            end_pos = line.find('*/', pos)
            if end_pos != -1:
                comment_text = line[pos:end_pos + 2]
                line_parts.append(highlight_comment_content(comment_text))
                pos = end_pos + 2
                in_block_comment = False
            else:
                comment_text = line[pos:]
                line_parts.append(highlight_comment_content(comment_text))
                pos = line_len
        else:
            m = SV_TOKEN_REGEX.search(line, pos)
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
                        line_parts.append(highlight_comment_content(comment_text))
                        pos = end_pos + 2
                    else:
                        comment_text = line[start:]
                        line_parts.append(highlight_comment_content(comment_text))
                        in_block_comment = True
                        pos = line_len
                elif kind == 'LINE_COMMENT':
                    line_parts.append(highlight_comment_content(val))
                    pos = end
                elif kind == 'STRING' or kind == 'CHAR':
                    line_parts.append(highlight_string_content(val))
                    pos = end
                elif kind == 'MACRO':
                    if val in SV_PREPROCESSOR_DIRECTIVES:
                        line_parts.append(f'<span class="sv-preproc">{esc}</span>')
                    else:
                        line_parts.append(f'<span class="sv-macro">{esc}</span>')
                    pos = end
                elif kind == 'SYSTEM_TF':
                    line_parts.append(f'<span class="sv-system-tf">{esc}</span>')
                    pos = end
                elif kind in ('BASED_NUM', 'TICK_LITERAL', 'TIME_NUM', 'FLOAT_NUM', 'INT_NUM'):
                    line_parts.append(f'<span class="sv-number">{esc}</span>')
                    pos = end
                elif kind == 'OP':
                    line_parts.append(f'<span class="sv-op">{esc}</span>')
                    pos = end
                elif kind == 'IDENT':
                    # Precise classification of identifiers
                    if val in SV_CONTROL_KEYWORDS:
                        line_parts.append(f'<span class="sv-keyword">{esc}</span>')
                    elif val in SV_DECL_KEYWORDS:
                        line_parts.append(f'<span class="sv-keyword-decl">{esc}</span>')
                    elif val in SV_BUILTIN_TYPES:
                        line_parts.append(f'<span class="sv-type">{esc}</span>')
                    elif val in SV_QUALIFIERS:
                        line_parts.append(f'<span class="sv-qualifier">{esc}</span>')
                    elif val in SV_CONSTANTS:
                        line_parts.append(f'<span class="sv-constant">{esc}</span>')
                    elif val.startswith(('uvm_', 'ovm_')) or val == 'uvm_pkg':
                        if clickable_sym_links:
                            line_parts.append(
                                f'<span class="sv-uvm-type clickable-uvm-sym" data-sym="{esc}" '
                                f'title="Click to view {esc} documentation">{esc}</span>'
                            )
                        else:
                            line_parts.append(f'<span class="sv-uvm-type">{esc}</span>')
                    elif val in KNOWN_UVM_METHODS:
                        line_parts.append(f'<span class="sv-method">{esc}</span>')
                    else:
                        # Contextual lookahead & lookbehind: is it followed by '(' or declared after function/task?
                        rest = line[end:].lstrip()
                        prev_text = line[:start].rstrip()
                        if rest.startswith('('):
                            line_parts.append(f'<span class="sv-method">{esc}</span>')
                        elif prev_text.endswith('::') and (rest.startswith(';') or re.search(r'\b(function|task)\b', line[:start])):
                            line_parts.append(f'<span class="sv-method">{esc}</span>')
                        elif re.search(r'\b(function|task)\b', line[:start]) and rest.startswith(';'):
                            line_parts.append(f'<span class="sv-method">{esc}</span>')
                        else:
                            line_parts.append(f'<span class="sv-ident">{esc}</span>')
                    pos = end

    return line_parts, in_block_comment


# ==============================================================================
# C / C++ (DPI) Highlighter
# ==============================================================================

def tokenize_c_line(line: str, in_block_comment: bool) -> Tuple[List[str], bool]:
    """Tokenizes a single line of C / C++ DPI code into HTML syntax spans."""
    pos = 0
    line_len = len(line)
    line_parts: List[str] = []

    while pos < line_len:
        if in_block_comment:
            end_pos = line.find('*/', pos)
            if end_pos != -1:
                comment_text = line[pos:end_pos + 2]
                line_parts.append(highlight_comment_content(comment_text))
                pos = end_pos + 2
                in_block_comment = False
            else:
                comment_text = line[pos:]
                line_parts.append(highlight_comment_content(comment_text))
                pos = line_len
        else:
            m = C_TOKEN_REGEX.search(line, pos)
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
                        line_parts.append(highlight_comment_content(comment_text))
                        pos = end_pos + 2
                    else:
                        comment_text = line[start:]
                        line_parts.append(highlight_comment_content(comment_text))
                        in_block_comment = True
                        pos = line_len
                elif kind == 'LINE_COMMENT':
                    line_parts.append(highlight_comment_content(val))
                    pos = end
                elif kind == 'STRING' or kind == 'CHAR':
                    line_parts.append(highlight_string_content(val))
                    pos = end
                elif kind == 'PREPROC':
                    line_parts.append(f'<span class="sv-preproc">{esc}</span>')
                    pos = end
                elif kind in ('HEX_NUM', 'FLOAT_NUM', 'INT_NUM'):
                    line_parts.append(f'<span class="sv-number">{esc}</span>')
                    pos = end
                elif kind == 'OP':
                    line_parts.append(f'<span class="sv-op">{esc}</span>')
                    pos = end
                elif kind == 'IDENT':
                    if val in C_KEYWORDS:
                        line_parts.append(f'<span class="sv-keyword">{esc}</span>')
                    elif val in C_TYPES:
                        line_parts.append(f'<span class="sv-type">{esc}</span>')
                    elif val in C_CONSTANTS:
                        line_parts.append(f'<span class="sv-constant">{esc}</span>')
                    elif val.startswith(('sv', 'vpi', 'uvm_')):
                        line_parts.append(f'<span class="sv-uvm-type">{esc}</span>')
                    else:
                        rest = line[end:].lstrip()
                        if rest.startswith('('):
                            line_parts.append(f'<span class="sv-method">{esc}</span>')
                        else:
                            line_parts.append(f'<span class="sv-ident">{esc}</span>')
                    pos = end

    return line_parts, in_block_comment


# ==============================================================================
# Makefile Highlighter
# ==============================================================================

MAKE_DIRECTIVES: Set[str] = {'ifeq', 'ifneq', 'else', 'endif', 'include', '-include', 'define', 'endef'}

def tokenize_makefile_line(line: str) -> List[str]:
    """Tokenizes a Makefile line: comments, variable assignments, targets, directives, and recipe lines."""
    striped = line.strip()
    if not striped:
        return [html.escape(line)]

    # Comments
    if striped.startswith('#'):
        return [highlight_comment_content(line)]

    # Directive (ifeq, else, endif, include)
    first_word = striped.split()[0] if striped.split() else ''
    if first_word in MAKE_DIRECTIVES:
        idx = line.find(first_word)
        prefix = html.escape(line[:idx])
        kw = f'<span class="sv-keyword">{html.escape(first_word)}</span>'
        rest = html.escape(line[idx + len(first_word):])
        return [prefix, kw, rest]

    # Target rule (e.g. `all:`, `clean:`, `run: sim`)
    target_match = re.match(r'^([a-zA-Z0-9_\-\./%]+)\s*:(?!=)(.*)$', line)
    if target_match:
        target, deps = target_match.group(1), target_match.group(2)
        return [
            f'<span class="sv-proto-name" style="font-weight:700">{html.escape(target)}</span>',
            '<span class="sv-op">:</span>',
            html.escape(deps)
        ]

    # Variable assignment (e.g. `CC = gcc`, `CFLAGS ?= -Wall`, `SIM := vcs`)
    var_match = re.match(r'^([a-zA-Z0-9_\-]+)\s*(\??=|\+=|:=|=)\s*(.*)$', line)
    if var_match:
        var_name, op, val = var_match.group(1), var_match.group(2), var_match.group(3)
        return [
            f'<span class="sv-proto-name">{html.escape(var_name)}</span> ',
            f'<span class="sv-op">{html.escape(op)}</span> ',
            f'<span class="sv-string">{html.escape(val)}</span>'
        ]

    # Recipe line (starts with tab or spaces)
    if line.startswith('\t') or line.startswith('    '):
        return [f'<span class="sv-ident">{html.escape(line)}</span>']

    return [html.escape(line)]


# ==============================================================================
# Full Source & Document Block Highlighting APIs
# ==============================================================================

def highlight_source_code_table_rows(
    code: str,
    filename: str,
    clickable_sym_links: bool = False
) -> Tuple[List[str], int]:
    """
    Renders syntax-highlighted HTML table rows with line numbers for a complete source file.
    Supports .sv, .svh, .v, .c, .cc, .h, and Makefile.* files.
    Returns: (list_of_html_rows, line_count)
    """
    is_c = filename.endswith(('.c', '.cc', '.h'))
    is_makefile = ('makefile' in filename.lower() or filename.endswith('.mk'))
    lines = code.splitlines()
    rows: List[str] = []
    in_block_comment = False

    for idx, line in enumerate(lines, 1):
        if is_makefile:
            parts = tokenize_makefile_line(line)
        elif is_c:
            parts, in_block_comment = tokenize_c_line(line, in_block_comment)
        else:
            parts, in_block_comment = tokenize_sv_line(
                line,
                in_block_comment,
                clickable_sym_links=clickable_sym_links
            )

        code_html = "".join(parts) or "&nbsp;"
        rows.append(
            f'<tr id="L{idx}">'
            f'<td class="ln" data-line="{idx}"><a href="#L{idx}">{idx}</a></td>'
            f'<td class="code">{code_html}</td>'
            f'</tr>'
        )

    return rows, len(lines)


def highlight_doc_snippet(raw_code: str) -> str:
    """
    High-fidelity tokenizer for documentation code blocks (<pre><code>...</code></pre>).
    Preserves exact whitespace and handles multi-line blocks cleanly.
    """
    code = html.unescape(raw_code)
    lines = code.splitlines(keepends=True)
    out_parts: List[str] = []
    in_block_comment = False

    for line in lines:
        parts, in_block_comment = tokenize_sv_line(line, in_block_comment, clickable_sym_links=False)
        out_parts.extend(parts)

    return "".join(out_parts)
