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
import json
from pathlib import Path
from typing import List, Tuple, Optional, Set, Dict, Any

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

# Bare method names that are unambiguous UVM calls even without parentheses or explicit receiver
UNAMBIGUOUS_BARE_UVM_METHODS: Set[str] = {
    'build_phase', 'connect_phase', 'end_of_elaboration_phase',
    'start_of_simulation_phase', 'run_phase', 'pre_reset_phase', 'reset_phase',
    'post_reset_phase', 'pre_configure_phase', 'configure_phase',
    'post_configure_phase', 'pre_main_phase', 'main_phase', 'post_main_phase',
    'pre_shutdown_phase', 'shutdown_phase', 'post_shutdown_phase',
    'extract_phase', 'check_phase', 'report_phase', 'final_phase',
    'phase_started', 'phase_ready_to_end', 'phase_ended',
    'raise_objection', 'drop_objection', 'set_drain_time',
    'start_item', 'finish_item', 'pre_body', 'post_body',
    'run_test', 'uvm_wait_for_nba_region',
    'set_config_int', 'set_config_string', 'set_config_object',
    'get_config_int', 'get_config_string', 'get_config_object',
    'set_report_verbosity_level', 'set_report_id_verbosity',
    'set_report_severity_action', 'set_report_id_action',
    'do_print', 'do_copy', 'do_compare', 'do_pack', 'do_unpack', 'do_record',
    'convert2string', 'get_full_name', 'get_type_name', 'get_num_children',
    'b_transport', 'nb_transport_fw', 'nb_transport_bw'
}

_UVM_SYMBOL_CATALOG: Optional[Dict[str, Any]] = None


def _get_uvm_symbol_catalog() -> Dict[str, Any]:
    """Lazily loads UVM symbol sets from js/uvm_symbol_quick.js (or uvm_source_database.json)."""
    global _UVM_SYMBOL_CATALOG
    if _UVM_SYMBOL_CATALOG is not None:
        return _UVM_SYMBOL_CATALOG

    root_dir = Path(__file__).resolve().parent.parent
    quick_js = root_dir / "js" / "uvm_symbol_quick.js"
    db_json = root_dir / "data" / "uvm_source_database.json"

    classes: Set[str] = set()
    macros: Set[str] = set()
    methods: Set[str] = set(KNOWN_UVM_METHODS)
    constants: Set[str] = set(SV_CONSTANTS) - {'null', 'this', 'super', '$root', '$unit'}
    types: Set[str] = set()
    var_types: Dict[str, str] = {}

    if quick_js.exists():
        try:
            raw = quick_js.read_text(encoding='utf-8')
            marker = 'window.UVM_SYMBOLS = '
            if marker in raw:
                payload = raw.split(marker, 1)[1].rstrip().rstrip(';')
                data = json.loads(payload)
                classes = set(data.get('classes', {}).keys())
                macros = {k.lstrip('`') for k in data.get('macros', {}).keys()}
                methods.update(data.get('methods', {}).keys())
                constants.update(data.get('constants', {}).keys())
                types = set(data.get('types', {}).keys())
                for vname, vinfo in data.get('vars', {}).items():
                    vtype = vinfo.get('var_type') or vinfo.get('class') or ''
                    if vtype:
                        var_types[vname] = vtype
        except Exception:
            pass
    elif db_json.exists():
        try:
            data = json.loads(db_json.read_text(encoding='utf-8'))
            classes = set(data.get('classes', {}).keys())
            macros = {k.lstrip('`') for k in data.get('macros', {}).keys()}
            methods.update(data.get('methods_index', {}).keys())
            for item in data.get('symbols_index', []):
                stype = item.get('type', '')
                name = item.get('name', '')
                if not name:
                    continue
                if stype == 'constant':
                    constants.add(name)
                elif stype == 'type':
                    types.add(name)
                elif stype in ('function', 'task'):
                    methods.add(name)
        except Exception:
            pass

    _UVM_SYMBOL_CATALOG = {
        'classes': classes,
        'macros': macros,
        'methods': methods,
        'constants': constants,
        'types': types,
        'var_types': var_types,
    }
    return _UVM_SYMBOL_CATALOG

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

def _format_clickable_sym(
    css_class: str,
    val: str,
    esc: str,
    sym_kind: str,
    sym_label: str,
    owner: Optional[str] = None,
    base: Optional[str] = None,
) -> str:
    """Formats a clickable UVM symbol token span with optional static context metadata."""
    attrs = [
        f'class="{css_class} clickable-uvm-sym"',
        f'data-sym="{esc}"',
        f'data-sym-kind="{sym_kind}"',
    ]
    if owner:
        attrs.append(f'data-sym-owner="{html.escape(owner)}"')
    if base:
        attrs.append(f'data-sym-base="{html.escape(base)}"')
    attrs.append(f'title="Click to view {esc} {sym_label}documentation"')
    return f'<span {" ".join(attrs)}>{esc}</span>'


def _infer_method_context(
    prev_text: str,
    line_ctx: Optional[Dict[str, Any]],
    catalog: Dict[str, Any],
) -> Tuple[Optional[str], Optional[str]]:
    """Infers static owner class or UVM base class for a method call or declaration."""
    owner: Optional[str] = None
    base: Optional[str] = line_ctx.get('current_uvm_base') if line_ctx else None

    m_scope = re.search(r'([A-Za-z_][A-Za-z0-9_]*)\s*(?:#\s*\([^)]*\)\s*)?::$', prev_text)
    if m_scope:
        qual = m_scope.group(1)
        if qual == 'type_id':
            m_outer = re.search(
                r'([A-Za-z_][A-Za-z0-9_]*)\s*(?:#\s*\([^)]*\)\s*)?::\s*type_id\s*::$',
                prev_text
            )
            if m_outer and line_ctx:
                outer_cls = m_outer.group(1)
                outer_base = line_ctx.get('class_base_map', {}).get(outer_cls) or outer_cls
                if outer_base in ('uvm_component', 'uvm_test', 'uvm_env', 'uvm_agent', 'uvm_driver', 'uvm_monitor', 'uvm_scoreboard', 'uvm_sequencer'):
                    return 'uvm_component_registry', None
            return 'uvm_object_registry', None
        if qual in catalog['classes']:
            return qual, None
        if line_ctx and qual in line_ctx.get('class_base_map', {}):
            return None, line_ctx['class_base_map'][qual]
        return None, None

    if re.search(r'[A-Za-z0-9_\)\]]\s*\.$', prev_text):
        m_dot = re.search(r'([A-Za-z_][A-Za-z0-9_]*)\s*\.$', prev_text)
        if m_dot:
            recv = m_dot.group(1)
            if recv in ('this', 'super'):
                return None, base
            if line_ctx:
                vtype = line_ctx.get('var_types', {}).get(recv)
                if vtype:
                    if vtype in catalog['classes']:
                        return vtype, None
                    mapped = line_ctx.get('class_base_map', {}).get(vtype)
                    if mapped:
                        return None, mapped
            if recv in catalog['var_types']:
                return catalog['var_types'][recv], None
        return None, None

    return owner, base


def _update_sv_line_context(line: str, line_ctx: Dict[str, Any], catalog: Dict[str, Any]) -> None:
    """Updates lightweight per-file SystemVerilog class and variable type tracking."""
    code_part = re.sub(r'//.*$', '', line)
    code_part = re.sub(r'"[^"]*"', '""', code_part)

    m_cls = re.search(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s+extends\s+([A-Za-z_][A-Za-z0-9_]*)', code_part)
    if m_cls:
        cls_name, base_name = m_cls.group(1), m_cls.group(2)
        uvm_base = base_name if base_name in catalog['classes'] else line_ctx['class_base_map'].get(base_name)
        if uvm_base:
            line_ctx['class_base_map'][cls_name] = uvm_base
            line_ctx['current_uvm_base'] = uvm_base
        else:
            line_ctx['current_uvm_base'] = None
    elif re.search(r'\bendclass\b', code_part):
        line_ctx['current_uvm_base'] = None

    known_types = catalog['classes'] | catalog['types']
    for m_var in re.finditer(
        r'\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:#\s*\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\b',
        code_part
    ):
        tname, vname = m_var.group(1), m_var.group(2)
        if tname in known_types and vname not in ALL_SV_KEYWORDS:
            line_ctx['var_types'][vname] = tname


def tokenize_sv_line(
    line: str,
    in_block_comment: bool,
    clickable_sym_links: bool = False,
    line_ctx: Optional[Dict[str, Any]] = None
) -> Tuple[List[str], bool]:
    """
    Tokenizes a single line of SystemVerilog code into HTML syntax spans.
    Returns: (list_of_html_spans, new_in_block_comment_state)
    """
    catalog = _get_uvm_symbol_catalog() if clickable_sym_links else None
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
                    elif clickable_sym_links and catalog and val.lstrip('`') in catalog['macros']:
                        line_parts.append(
                            _format_clickable_sym('sv-macro', val, esc, 'macro', 'macro ')
                        )
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
                    elif val in SV_CONSTANTS or (clickable_sym_links and catalog and val in catalog['constants']):
                        if (
                            clickable_sym_links
                            and val not in {'null', 'this', 'super', '$root', '$unit'}
                        ):
                            line_parts.append(
                                _format_clickable_sym('sv-constant', val, esc, 'constant', 'constant ')
                            )
                        else:
                            line_parts.append(f'<span class="sv-constant">{esc}</span>')
                    elif val.startswith(('uvm_', 'ovm_')) or val == 'uvm_pkg':
                        if clickable_sym_links and catalog:
                            if val in catalog['classes'] or val == 'uvm_pkg':
                                line_parts.append(
                                    _format_clickable_sym('sv-uvm-type', val, esc, 'class', '')
                                )
                            elif val in catalog['types']:
                                line_parts.append(
                                    _format_clickable_sym('sv-uvm-type', val, esc, 'type', 'type ')
                                )
                            elif val in catalog['var_types']:
                                line_parts.append(
                                    _format_clickable_sym('sv-uvm-type', val, esc, 'var', '')
                                )
                            elif val in catalog['methods']:
                                prev_text = line[:start].rstrip()
                                owner, base = _infer_method_context(prev_text, line_ctx, catalog)
                                if not owner and not base and not prev_text.endswith(('.', '::')):
                                    owner = 'Global'
                                line_parts.append(
                                    _format_clickable_sym('sv-method', val, esc, 'method', 'method ', owner, base)
                                )
                            else:
                                line_parts.append(f'<span class="sv-uvm-type">{esc}</span>')
                        elif clickable_sym_links:
                            line_parts.append(
                                f'<span class="sv-uvm-type clickable-uvm-sym" data-sym="{esc}" '
                                f'title="Click to view {esc} documentation">{esc}</span>'
                            )
                        else:
                            line_parts.append(f'<span class="sv-uvm-type">{esc}</span>')
                    elif val in KNOWN_UVM_METHODS or (clickable_sym_links and catalog and val in catalog['methods']):
                        if clickable_sym_links and catalog:
                            rest = line[end:].lstrip()
                            prev_text = line[:start].rstrip()
                            is_dot_member = bool(re.search(r'[A-Za-z0-9_\)\]]\s*\.$', prev_text))
                            is_scope_member = prev_text.endswith('::')
                            is_named_arg = prev_text.endswith('.') and not is_dot_member
                            is_call = rest.startswith('(') and not is_named_arg
                            is_func_hdr = bool(re.search(r'\b(function|task)\b[^();]*$', prev_text))
                            is_unambiguous_bare = (
                                val in UNAMBIGUOUS_BARE_UVM_METHODS
                                and not is_named_arg
                                and not re.search(
                                    r'\b(input|output|inout|wire|logic|bit|reg|int|integer|string|real)\b\s*$',
                                    prev_text
                                )
                            )
                            if is_call or is_dot_member or is_scope_member or is_func_hdr or is_unambiguous_bare:
                                owner, base = _infer_method_context(prev_text, line_ctx, catalog)
                                line_parts.append(
                                    _format_clickable_sym('sv-method', val, esc, 'method', 'method ', owner, base)
                                )
                            else:
                                line_parts.append(
                                    f'<span class="sv-method">{esc}</span>'
                                    if val in KNOWN_UVM_METHODS
                                    else f'<span class="sv-ident">{esc}</span>'
                                )
                        else:
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
    catalog = _get_uvm_symbol_catalog() if (clickable_sym_links and not is_makefile and not is_c) else None
    line_ctx: Optional[Dict[str, Any]] = (
        {
            'current_uvm_base': None,
            'class_base_map': {},
            'var_types': dict(catalog['var_types']),
        }
        if catalog
        else None
    )

    for idx, line in enumerate(lines, 1):
        if is_makefile:
            parts = tokenize_makefile_line(line)
        elif is_c:
            parts, in_block_comment = tokenize_c_line(line, in_block_comment)
        else:
            if line_ctx is not None and not in_block_comment:
                _update_sv_line_context(line, line_ctx, catalog)
            parts, in_block_comment = tokenize_sv_line(
                line,
                in_block_comment,
                clickable_sym_links=clickable_sym_links,
                line_ctx=line_ctx
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
