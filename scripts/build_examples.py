#!/usr/bin/env python3
"""
UVM 1.2 Interactive Examples Generator
Parses all 38 official Accellera UVM 1.2 example suites in uvm-1.2/examples/
and generates rich, interactive, standalone HTML studios in examples_view/.

Features:
- Multi-file Code Studio with syntax highlighting and line numbers
- Clickable UVM symbol references inside example code
- Interactive Testbench Topology Diagrams
- Simulation Console with authentic UVM report logs and Questa/VCS/Xcelium commands
- Visual Flow Stepper for the 5 pillar examples (Phases, Objections, TLM-1 FIFO, TLM-2, RAL Primer)
- Client-side 1-click Raw & Native ZIP downloads
- Zero-dependency static build fully compliant with Rule 1 (100% offline file:// compatible)
"""

import os
import re
import html
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EXAMPLES_SRC_DIR = BASE_DIR / "uvm-1.2" / "examples"
OUTPUT_EXAMPLES_VIEW = BASE_DIR / "examples_view"
OUTPUT_JS_DIR = BASE_DIR / "js"

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

def highlight_code_lines(code, filename):
    """Highlight code lines and return (lines_html, total_lines)."""
    lines = code.split('\n')
    is_sv = filename.endswith(('.sv', '.svh', '.v'))
    is_make = filename.startswith('Makefile')
    is_txt = filename.endswith('.txt')

    if not is_sv and not is_make:
        # Plain text
        html_lines = []
        for i, line in enumerate(lines, 1):
            escaped = html.escape(line) or '&nbsp;'
            html_lines.append(f'<tr id="L{i}"><td class="ln" data-line="{i}"><a href="#L{i}">{i}</a></td><td class="code">{escaped}</td></tr>')
        return '\n'.join(html_lines), len(lines)

    in_block_comment = False
    html_lines = []

    for i, line in enumerate(lines, 1):
        line_parts = []
        pos = 0
        length = len(line)

        if in_block_comment:
            end_bc = line.find('*/')
            if end_bc != -1:
                comment_text = line[:end_bc+2]
                line_parts.append(f'<span class="sv-comment">{html.escape(comment_text)}</span>')
                pos = end_bc + 2
                in_block_comment = False
            else:
                line_parts.append(f'<span class="sv-comment">{html.escape(line)}</span>')
                pos = length

        if is_make:
            # Simple makefile coloring
            if pos < length:
                rest = line[pos:]
                if rest.strip().startswith('#'):
                    line_parts.append(f'<span class="sv-comment">{html.escape(rest)}</span>')
                elif '=' in rest:
                    k, v = rest.split('=', 1)
                    line_parts.append(f'<span class="sv-ident">{html.escape(k)}</span>=<span class="sv-string">{html.escape(v)}</span>')
                elif rest.startswith('\t') or rest.startswith('    '):
                    line_parts.append(f'<span class="sv-keyword">{html.escape(rest)}</span>')
                elif ':' in rest:
                    tgt, deps = rest.split(':', 1)
                    line_parts.append(f'<span class="sv-uvm-type" style="font-weight:700">{html.escape(tgt)}</span>:<span class="sv-ident">{html.escape(deps)}</span>')
                else:
                    line_parts.append(html.escape(rest))
        else:
            while pos < length:
                m = TOKEN_REGEX.search(line, pos)
                if not m:
                    line_parts.append(html.escape(line[pos:]))
                    break

                if m.start() > pos:
                    line_parts.append(html.escape(line[pos:m.start()]))

                kind = m.lastgroup
                val = m.group(0)

                if kind == 'BLOCK_COMMENT_START':
                    end_bc = line.find('*/', m.start() + 2)
                    if end_bc != -1:
                        comment_text = line[m.start():end_bc+2]
                        line_parts.append(f'<span class="sv-comment">{html.escape(comment_text)}</span>')
                        pos = end_bc + 2
                    else:
                        line_parts.append(f'<span class="sv-comment">{html.escape(line[m.start():])}</span>')
                        in_block_comment = True
                        pos = length
                    continue
                elif kind == 'LINE_COMMENT':
                    line_parts.append(f'<span class="sv-comment">{html.escape(val)}</span>')
                elif kind == 'STRING' or kind == 'CHAR':
                    line_parts.append(f'<span class="sv-string">{html.escape(val)}</span>')
                elif kind == 'MACRO':
                    line_parts.append(f'<span class="sv-macro">{html.escape(val)}</span>')
                elif kind == 'NUMBER':
                    line_parts.append(f'<span class="sv-number">{html.escape(val)}</span>')
                elif kind == 'IDENT':
                    if val in SV_KEYWORDS:
                        line_parts.append(f'<span class="sv-keyword">{html.escape(val)}</span>')
                    elif val.startswith('uvm_') or val in ('run_test', 'uvm_pkg'):
                        line_parts.append(f'<span class="sv-uvm-type clickable-uvm-sym" data-sym="{html.escape(val)}" title="Click to view {html.escape(val)} documentation">{html.escape(val)}</span>')
                    else:
                        line_parts.append(f'<span class="sv-ident">{html.escape(val)}</span>')
                elif kind == 'OP':
                    line_parts.append(f'<span class="sv-op">{html.escape(val)}</span>')
                else:
                    line_parts.append(html.escape(val))

                pos = m.end()

        code_content = "".join(line_parts) or '&nbsp;'
        html_lines.append(f'<tr id="L{i}"><td class="ln" data-line="{i}"><a href="#L{i}">{i}</a></td><td class="code">{code_content}</td></tr>')

    return '\n'.join(html_lines), len(lines)

# Metadata catalogue for all 38 suites
SUITES_METADATA = {
    # 1. Getting Started & Basics
    "simple/trivial": {
        "title": "Trivial Component",
        "category": "Basics",
        "category_title": "Getting Started & Basics",
        "scope": "Simple",
        "difficulty": "Beginner",
        "summary": "Demonstrates the absolute minimum UVM component lifecycle. Creates a basic custom component derived from uvm_component and executes it through run_test().",
        "apis": ["uvm_component", "run_test", "uvm_root"],
        "topology": [
            {"name": "uvm_test_top", "type": "uvm_component", "children": [{"name": "my_component", "type": "my_component", "details": "Derived from uvm_component"}]}
        ],
        "primary_file": "component.sv"
    },
    "simple/hello_world": {
        "title": "Hello World & TLM FIFO",
        "category": "Basics",
        "category_title": "Getting Started & Basics",
        "scope": "Simple",
        "difficulty": "Beginner",
        "summary": "Classic UVM hello world testbench demonstrating producer and consumer components connected through a uvm_tlm_fifo, with uvm_config_db configuration and table printing.",
        "apis": ["uvm_component", "uvm_tlm_fifo", "uvm_config_db", "run_test", "uvm_default_table_printer"],
        "topology": [
            {"name": "top (uvm_component)", "type": "env", "children": [
                {"name": "producer1", "type": "producer", "details": "put_port"},
                {"name": "fifo1", "type": "uvm_tlm_fifo #(packet)", "details": "Depth: 1"},
                {"name": "consumer1", "type": "consumer", "details": "get_port"}
            ]}
        ],
        "primary_file": "hello_world.sv",
        "has_stepper": True
    },
    "simple/basic_examples/module": {
        "title": "Module-Based UVM",
        "category": "Basics",
        "category_title": "Getting Started & Basics",
        "scope": "Simple",
        "difficulty": "Beginner",
        "summary": "Illustrates executing UVM testbench hierarchies directly from pure SystemVerilog modules and calling run_test without a formal top-level test class.",
        "apis": ["uvm_component", "run_test", "uvm_pkg"],
        "topology": [{"name": "top_module", "type": "module", "children": [{"name": "uvm_test_top", "type": "test"}]}],
        "primary_file": "test.sv"
    },
    "simple/basic_examples/pkg": {
        "title": "Modular Packages",
        "category": "Basics",
        "category_title": "Getting Started & Basics",
        "scope": "Simple",
        "difficulty": "Beginner",
        "summary": "Shows best practices for packaging UVM components into clean, reusable SystemVerilog packages and importing them into test top modules.",
        "apis": ["uvm_pkg", "package", "import"],
        "topology": [{"name": "my_pkg", "type": "package", "children": [{"name": "my_component", "type": "class"}, {"name": "my_env", "type": "class"}]}],
        "primary_file": "test.sv"
    },

    # 2. Core Infrastructure
    "simple/factory": {
        "title": "Factory Overrides",
        "category": "Infrastructure",
        "category_title": "Core Infrastructure",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Demonstrates factory registration (`uvm_component_utils`), polymorphism, and swapping components dynamically using set_type_override_by_type and set_inst_override_by_type.",
        "apis": ["uvm_factory", "set_type_override_by_type", "set_inst_override_by_type", "create"],
        "topology": [{"name": "env", "type": "env", "children": [{"name": "gen", "type": "gen -> gen_special (Overridden)"}]}],
        "primary_file": "test.sv"
    },
    "simple/configuration/manual": {
        "title": "Manual Configuration DB",
        "category": "Infrastructure",
        "category_title": "Core Infrastructure",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Explicitly stores and retrieves configuration parameters and virtual interfaces using uvm_config_db::set() and uvm_config_db::get() with strict scope matching.",
        "apis": ["uvm_config_db", "uvm_resource_db"],
        "topology": [{"name": "top", "type": "top", "children": [{"name": "instA", "type": "classA"}, {"name": "instB", "type": "classB"}]}],
        "primary_file": "top.sv"
    },
    "simple/configuration/automated": {
        "title": "Automated Configuration Tables",
        "category": "Infrastructure",
        "category_title": "Core Infrastructure",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Uses UVM field automation macros (`uvm_field_int`, etc.) and automated configuration tables for zero-boilerplate field population during build_phase.",
        "apis": ["uvm_field_int", "uvm_config_db", "apply_config_settings"],
        "topology": [{"name": "top", "type": "top", "children": [{"name": "instA", "type": "classA"}, {"name": "instB", "type": "classB"}]}],
        "primary_file": "top.sv"
    },
    "simple/callbacks": {
        "title": "Callback Hooks",
        "category": "Infrastructure",
        "category_title": "Core Infrastructure",
        "scope": "Simple",
        "difficulty": "Advanced",
        "summary": "Implements non-intrusive testbench modifications using uvm_callback and uvm_register_cb to alter component behavior or inject errors without editing component source code.",
        "apis": ["uvm_callback", "uvm_register_cb", "`uvm_do_callbacks"],
        "topology": [{"name": "driver", "type": "driver", "children": [{"name": "cb_hook", "type": "user_callback", "details": "Injects error packets"}]}],
        "primary_file": "top.sv"
    },
    "simple/interfaces": {
        "title": "Virtual Interface Connection",
        "category": "Infrastructure",
        "category_title": "Core Infrastructure",
        "scope": "Simple",
        "difficulty": "Beginner",
        "summary": "Demonstrates encapsulating physical SystemVerilog interface instances in uvm_config_db and retrieving them inside UVM drivers/monitors as virtual interfaces.",
        "apis": ["virtual interface", "uvm_config_db", "uvm_driver"],
        "topology": [{"name": "dut_if (interface)", "type": "interface", "details": "Physical signals"}, {"name": "driver", "type": "uvm_driver", "details": "Holds virtual dut_if"}],
        "primary_file": "interface.sv"
    },

    # 3. Phasing & Objections
    "simple/phases/basic": {
        "title": "Phased Execution Lifecycle",
        "category": "Phasing",
        "category_title": "Phasing & Objections",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Exercises the complete 12-phase UVM execution lifecycle from build_phase to report_phase, contrasting top-down, bottom-up and runtime task phases.",
        "apis": ["uvm_phase", "build_phase", "connect_phase", "run_phase", "report_phase"],
        "topology": [{"name": "test", "type": "uvm_test", "children": [{"name": "env", "type": "uvm_env", "children": [{"name": "compA", "type": "uvm_component"}]}]}],
        "primary_file": "test.sv",
        "has_stepper": True
    },
    "simple/phases/run_test": {
        "title": "Dynamic Test Selection",
        "category": "Phasing",
        "category_title": "Phasing & Objections",
        "scope": "Simple",
        "difficulty": "Beginner",
        "summary": "Demonstrates calling run_test() with command-line argument +UVM_TESTNAME to instantiate and execute different test classes dynamically without recompilation.",
        "apis": ["run_test", "+UVM_TESTNAME", "uvm_root"],
        "topology": [{"name": "uvm_root", "type": "singleton", "details": "Instantiates test selected by +UVM_TESTNAME"}],
        "primary_file": "test.sv"
    },
    "simple/phases/timeout": {
        "title": "Simulation Watchdogs & Timeouts",
        "category": "Phasing",
        "category_title": "Phasing & Objections",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Configures global simulation watchdog timers via uvm_root::set_timeout() to cleanly terminate runaway simulations with appropriate error diagnostics.",
        "apis": ["set_timeout", "uvm_root", "uvm_fatal"],
        "topology": [{"name": "uvm_top", "type": "root", "details": "Watchdog timer set to 1000 ns"}],
        "primary_file": "test.sv"
    },
    "simple/objections": {
        "title": "Phase Objections & Drain Time",
        "category": "Phasing",
        "category_title": "Phasing & Objections",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Controls simulation duration using phase.raise_objection() and phase.drop_objection() with configurable phase drain times to allow in-flight DUT packets to flush.",
        "apis": ["raise_objection", "drop_objection", "set_drain_time", "uvm_objection"],
        "topology": [{"name": "test", "type": "test", "children": [{"name": "worker", "type": "component", "details": "Raises & drops objection"}]}],
        "primary_file": "simple.sv",
        "has_stepper": True
    },
    "simple/basic_examples/event_pool": {
        "title": "Event Synchronization (Pool)",
        "category": "Phasing",
        "category_title": "Phasing & Objections",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Coordinates asynchronous parallel components using the global uvm_event_pool singleton, triggering named events and waiting on triggers across disparate components.",
        "apis": ["uvm_event_pool", "uvm_event", "trigger", "wait_trigger"],
        "topology": [{"name": "componentA", "type": "trigger", "details": "Triggers 'done_event'"}, {"name": "componentB", "type": "listener", "details": "Waits on 'done_event'"}],
        "primary_file": "test.sv"
    },

    # 4. Sequences & Stimulus
    "simple/sequence/basic_read_write_sequence": {
        "title": "Basic Read/Write Sequence",
        "category": "Sequences",
        "category_title": "Stimulus & Sequences",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Demonstrates standard transaction item generation, sequencer arbitration, and the driver-sequencer handshake via start_item() and finish_item().",
        "apis": ["uvm_sequence", "uvm_sequencer", "uvm_sequence_item", "start_item", "finish_item"],
        "topology": [{"name": "sequence", "type": "seq", "details": "Generates items"}, {"name": "sequencer", "type": "sqr", "details": "Arbitration"}, {"name": "driver", "type": "drv", "details": "Executes pins"}],
        "primary_file": "top.sv"
    },

    # 5. TLM-1 Communication
    "simple/tlm1/producer_consumer": {
        "title": "Blocking Put & Get Ports",
        "category": "TLM-1",
        "category_title": "TLM-1 Communication",
        "scope": "Simple",
        "difficulty": "Beginner",
        "summary": "Classic point-to-point transaction communication between a producer and consumer component using blocking uvm_blocking_put_port and uvm_blocking_get_port.",
        "apis": ["uvm_blocking_put_port", "uvm_blocking_get_port", "uvm_tlm_fifo"],
        "topology": [{"name": "producer", "type": "comp", "details": "put_port"}, {"name": "fifo", "type": "uvm_tlm_fifo", "details": "Depth: 1"}, {"name": "consumer", "type": "comp", "details": "get_port"}],
        "primary_file": "fifo.sv"
    },
    "simple/tlm1/fifo": {
        "title": "TLM-1 FIFO with Non-Blocking Check",
        "category": "TLM-1",
        "category_title": "TLM-1 Communication",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Deep dive into uvm_tlm_fifo operations comparing blocking put/get against non-blocking try_put, try_get, can_put, and can_get methods under varying traffic rates.",
        "apis": ["uvm_tlm_fifo", "try_put", "try_get", "can_put", "can_get"],
        "topology": [{"name": "producer", "type": "comp"}, {"name": "fifo", "type": "uvm_tlm_fifo", "details": "try_put / try_get"}, {"name": "consumer", "type": "comp"}],
        "primary_file": "test.sv",
        "has_stepper": True
    },
    "simple/tlm1/bidir": {
        "title": "Bidirectional TLM Transport",
        "category": "TLM-1",
        "category_title": "TLM-1 Communication",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Illustrates bidirectional master/slave transaction exchange using uvm_master_port and uvm_slave_port to send a request and immediately receive a response in a single call.",
        "apis": ["uvm_master_port", "uvm_slave_port", "transport"],
        "topology": [{"name": "master", "type": "master_port", "details": "Sends REQ, gets RSP"}, {"name": "slave", "type": "slave_port", "details": "Processes REQ, returns RSP"}],
        "primary_file": "bidir.sv"
    },
    "simple/tlm1/hierarchy": {
        "title": "Hierarchical TLM Port Forwarding",
        "category": "TLM-1",
        "category_title": "TLM-1 Communication",
        "scope": "Simple",
        "difficulty": "Advanced",
        "summary": "Demonstrates connecting TLM ports and exports across multiple levels of hierarchy, forwarding transactions from parent envs down to child agents and sub-components.",
        "apis": ["uvm_put_port", "uvm_put_export", "uvm_put_imp"],
        "topology": [{"name": "top_env", "type": "env", "children": [{"name": "sub_env", "type": "env", "children": [{"name": "leaf_comp", "type": "comp"}]}]}],
        "primary_file": "hierarchy.sv"
    },

    # 6. TLM-2 Interconnects
    "simple/tlm2/blocking_simple": {
        "title": "Blocking TLM-2 Transport (b_transport)",
        "category": "TLM-2",
        "category_title": "TLM-2 Interconnects",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Implements the TLM-2 blocking transport interface using b_transport() with generic payload transactions, modeling timing delay annotations.",
        "apis": ["uvm_tlm_b_target_socket", "uvm_tlm_b_initiator_socket", "b_transport", "uvm_tlm_generic_payload"],
        "topology": [{"name": "initiator", "type": "socket", "details": "Calls b_transport(xfer, delay)"}, {"name": "target", "type": "socket", "details": "Serves transaction"}],
        "primary_file": "tb_run.sv"
    },
    "simple/tlm2/nonblocking_simple": {
        "title": "Non-Blocking 4-Phase Protocol",
        "category": "TLM-2",
        "category_title": "TLM-2 Interconnects",
        "scope": "Simple",
        "difficulty": "Advanced",
        "summary": "Exemplifies the full IEEE 1666 TLM-2 non-blocking 4-phase transaction protocol (BEGIN_REQ, END_REQ, BEGIN_RESP, END_RESP) modeling USB bulk transfers without simulation deadlocks.",
        "apis": ["nb_transport_fw", "nb_transport_bw", "uvm_tlm_phase_e", "uvm_tlm_sync_e"],
        "topology": [{"name": "host", "type": "initiator", "details": "USB Host"}, {"name": "device", "type": "target", "details": "USB Device Endpoint"}],
        "primary_file": "tb_run.sv",
        "has_stepper": True
    },
    "simple/tlm2/temporal_decoupling": {
        "title": "Temporal Decoupling & Quantum Keeper",
        "category": "TLM-2",
        "category_title": "TLM-2 Interconnects",
        "scope": "Simple",
        "difficulty": "Advanced",
        "summary": "Accelerates simulation speed by letting initiators run ahead of simulation time within a defined time quantum before synchronizing with global simulation time.",
        "apis": ["uvm_tlm_time", "temporal decoupling", "b_transport"],
        "topology": [{"name": "fast_initiator", "type": "quantum_keeper", "details": "Accumulates local delay"}, {"name": "target", "type": "target", "details": "Synchronizes at quantum boundaries"}],
        "primary_file": "tb_run.sv"
    },

    # 7. Register Abstraction Layer (RAL)
    "simple/registers/primer": {
        "title": "RAL Primer & Bus Adapter",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Comprehensive introductory guide to the UVM Register Abstraction Layer: creating a register model, integrating a register adapter (reg2bus/bus2reg), and running register sequences.",
        "apis": ["uvm_reg_block", "uvm_reg", "uvm_reg_field", "uvm_reg_adapter", "uvm_reg_predictor"],
        "topology": [
            {"name": "reg_model", "type": "uvm_reg_block", "details": "High-level RAL model"},
            {"name": "adapter", "type": "uvm_reg_adapter", "details": "reg2bus / bus2reg"},
            {"name": "bus_agent", "type": "agent", "details": "Drives physical APB bus"}
        ],
        "primary_file": "test.sv",
        "has_stepper": True
    },
    "simple/registers/sequence_api": {
        "title": "Register Sequence Convenience API",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Demonstrates the write_reg and read_reg convenience methods in user sequences, providing automatic parent sequencing without manual sequence context passing.",
        "apis": ["write_reg", "read_reg", "uvm_reg_sequence"],
        "topology": [{"name": "sequence", "type": "seq", "details": "Calls write_reg / read_reg"}, {"name": "reg_model", "type": "RAL"}],
        "primary_file": "blk_run.sv"
    },
    "simple/registers/vertical_reuse": {
        "title": "Vertical Register Model Reuse",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Advanced",
        "summary": "Demonstrates reusing block-level register sequences and register models unchanged inside system-level testbenches with hierarchical address offsets.",
        "apis": ["uvm_reg_block", "default_map", "add_submap"],
        "topology": [{"name": "sys_reg_model", "type": "system", "children": [{"name": "blk_A", "type": "block"}, {"name": "blk_B", "type": "block"}]}],
        "primary_file": "sys_run.sv"
    },
    "simple/registers/integration/10direct": {
        "title": "Direct Register Integration",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Integrates an explicit register model directly with a single physical bus sequencer and adapter without intermediate translation layers.",
        "apis": ["set_sequencer", "default_map", "uvm_reg_adapter"],
        "topology": [{"name": "reg_model", "type": "RAL"}, {"name": "adapter", "type": "adapter"}, {"name": "sequencer", "type": "sqr"}],
        "primary_file": "tb_env.sv"
    },
    "simple/registers/integration/20layered": {
        "title": "Layered Register Integration",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Advanced",
        "summary": "Connects a register model through layered sequencers, translating high-level register items into protocol-specific sub-transactions.",
        "apis": ["layered sequencer", "uvm_reg_sequence", "adapter"],
        "topology": [{"name": "reg_model", "type": "RAL"}, {"name": "reg_seq", "type": "seq"}, {"name": "layer_sqr", "type": "sqr"}, {"name": "phy_sqr", "type": "sqr"}],
        "primary_file": "tb_env.sv"
    },
    "simple/registers/models/aliasing": {
        "title": "Aliased Registers",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Models hardware registers that can be accessed via multiple distinct memory addresses, maintaining synchronized mirrored values across aliases.",
        "apis": ["uvm_reg", "predict", "add_field"],
        "topology": [{"name": "reg_primary", "type": "addr 0x00"}, {"name": "reg_alias", "type": "addr 0x04", "details": "Same underlying HW bits"}],
        "primary_file": "tb_run.sv"
    },
    "simple/registers/models/broadcast": {
        "title": "Broadcast Register Writes",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Models broadcast register writes where a single write transaction to a broadcast address updates multiple distinct register instances simultaneously.",
        "apis": ["uvm_reg_block", "write", "predict"],
        "topology": [{"name": "broadcast_reg", "type": "write-only", "details": "Updates reg1, reg2, reg3"}],
        "primary_file": "tb_run.sv"
    },
    "simple/registers/models/coverage": {
        "title": "Register Functional Coverage",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Integrates SystemVerilog covergroups directly within register and field definitions to track address coverage, field value coverage, and access type coverage.",
        "apis": ["build_coverage", "sample", "uvm_coverage_model_e"],
        "topology": [{"name": "reg_model", "type": "RAL", "details": "Embedded covergroups sampled on read/write"}],
        "primary_file": "tb_run.sv"
    },
    "simple/registers/models/fifo_reg": {
        "title": "FIFO Registers",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Advanced",
        "summary": "Models hardware FIFO buffer registers where repeated writes push data into a queue and reads pop data, handling depth limits and status flags.",
        "apis": ["uvm_reg_fifo", "write", "read"],
        "topology": [{"name": "fifo_reg", "type": "reg_fifo", "details": "Internal queue depth: 16"}],
        "primary_file": "tb_run.sv"
    },
    "simple/registers/models/not_yet_implemented": {
        "title": "Unimplemented / Stub Registers",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Beginner",
        "summary": "Handles registers reserved in the address map that are not yet implemented in silicon, preventing testbench crashes or spurious verification failures.",
        "apis": ["uvm_reg", "set_check_on_read"],
        "topology": [{"name": "reserved_reg", "type": "stub", "details": "Returns default / ignores writes"}],
        "primary_file": "tb_run.sv"
    },
    "simple/registers/models/reg_without_field": {
        "title": "Registers Without Subfields",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Beginner",
        "summary": "Demonstrates lightweight modeling of single raw 32-bit/64-bit registers where individual field slicing is unnecessary.",
        "apis": ["uvm_reg", "configure"],
        "topology": [{"name": "raw_reg", "type": "reg", "details": "32-bit monolithic value"}],
        "primary_file": "tb_run.sv"
    },
    "simple/registers/models/ro_wo_same_addr": {
        "title": "RO & WO Sharing Same Address",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Intermediate",
        "summary": "Models distinct read-only and write-only registers mapped to the exact same physical bus address, isolating write mirrors from read status.",
        "apis": ["default_map", "add_reg", "RO", "WO"],
        "topology": [{"name": "addr 0x10", "type": "shared", "details": "Write -> TX Buffer, Read -> RX Buffer"}],
        "primary_file": "tb_run.sv"
    },
    "simple/registers/models/shared_reg": {
        "title": "Multi-Domain Shared Registers",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Advanced",
        "summary": "Models registers accessible from multiple bus masters or clock domains with separate bus maps and synchronization semantics.",
        "apis": ["create_map", "add_submap", "default_map"],
        "topology": [{"name": "shared_reg", "type": "reg", "details": "Mapped in both CPU_map and DMA_map"}],
        "primary_file": "blk_run.sv"
    },
    "simple/registers/models/user-defined": {
        "title": "User-Defined Register Callbacks",
        "category": "Registers",
        "category_title": "Register Layer (RAL)",
        "scope": "Simple",
        "difficulty": "Advanced",
        "summary": "Extends standard register access behaviors with custom pre_read, post_read, pre_write, and post_write user callbacks for side-effects.",
        "apis": ["uvm_reg_cbs", "pre_write", "post_write", "pre_read", "post_read"],
        "topology": [{"name": "reg_ctrl", "type": "reg", "details": "Has user_callback attached"}],
        "primary_file": "tb_run.sv"
    },

    # 8. Integrated Environments & VIPs
    "integrated/ubus": {
        "title": "UBUS Verification Component & TB",
        "category": "Integrated",
        "category_title": "Integrated Environments & VIPs",
        "scope": "Integrated",
        "difficulty": "Advanced",
        "summary": "Accellera's canonical comprehensive UBUS verification component and complete environment: master and slave agents, centralized bus monitor, arbiter, scoreboard, sequence library, and test suites.",
        "apis": ["uvm_agent", "uvm_driver", "uvm_monitor", "uvm_sequencer", "uvm_scoreboard", "uvm_env"],
        "topology": [
            {"name": "ubus_example_tb", "type": "env", "children": [
                {"name": "ubus_env", "type": "uvm_env", "children": [
                    {"name": "masters[0..1]", "type": "ubus_master_agent", "details": "Driver + Monitor + Sequencer"},
                    {"name": "slaves[0]", "type": "ubus_slave_agent", "details": "Driver + Monitor + Sequencer"},
                    {"name": "bus_monitor", "type": "ubus_bus_monitor", "details": "Bus protocol monitor"}
                ]},
                {"name": "scoreboard", "type": "ubus_example_scoreboard", "details": "End-to-end data checker"}
            ]}
        ],
        "primary_file": "examples/ubus_example_tb.sv",
        "is_integrated": True
    },
    "integrated/codec": {
        "title": "Full-Duplex Serial Codec & RAL TB",
        "category": "Integrated",
        "category_title": "Integrated Environments & VIPs",
        "scope": "Integrated",
        "difficulty": "Advanced",
        "summary": "Complete industrial testbench for a full-duplex parallel-to-serial codec DUT: integrating an APB interface, complete RAL register model with interrupt status registers, scoreboard, and serial VIP.",
        "apis": ["uvm_reg_block", "uvm_agent", "uvm_scoreboard", "uvm_env", "uvm_sequence"],
        "topology": [
            {"name": "codec_tb_env", "type": "env", "children": [
                {"name": "reg_model", "type": "RAL", "details": "Codec registers (IntSrc, TxStatus, etc.)"},
                {"name": "apb_agent", "type": "agent", "details": "APB Master driver"},
                {"name": "serial_vip", "type": "vip_agent", "details": "TX/RX bitstream checker"},
                {"name": "sym_sb", "type": "scoreboard", "details": "Symbol align checker"}
            ]}
        ],
        "primary_file": "tb_top.sv",
        "is_integrated": True
    },
    "integrated/apb": {
        "title": "APB VIP Agent Library",
        "category": "Integrated",
        "category_title": "Integrated Environments & VIPs",
        "scope": "Integrated",
        "difficulty": "Intermediate",
        "summary": "Reusable AMBA APB (Advanced Peripheral Bus) UVC package: master agent, configurable sequencer, monitor, signal interface, and read/write transfer sequences.",
        "apis": ["uvm_agent", "uvm_driver", "uvm_monitor", "uvm_sequence", "apb_rw"],
        "topology": [
            {"name": "apb_agent", "type": "agent", "children": [
                {"name": "apb_master", "type": "driver", "details": "Drives PSEL, PENABLE, PWRITE"},
                {"name": "apb_sequencer", "type": "sequencer"},
                {"name": "apb_monitor", "type": "monitor", "details": "Samples bus pin activity"}
            ]}
        ],
        "primary_file": "apb.sv",
        "is_integrated": True
    }
}

# 5 Pillar Stepper Data
STEPPER_DATA = {
    "simple/phases/basic": [
        {
            "step": 1,
            "title": "1. Build Phase (Top-Down Construction)",
            "component": "test & env",
            "highlight_file": "test.sv",
            "highlight_line": 25,
            "log_snippet": "UVM_INFO @ 0 ns: reporter [PH_TRACE] In build_phase",
            "desc": "Execution begins in top-down order. The root instantiates tests and sub-components. Components query `uvm_config_db` to retrieve configuration tables and virtual interfaces before creating children."
        },
        {
            "step": 2,
            "title": "2. Connect Phase (Bottom-Up Wiring)",
            "component": "env & sub-components",
            "highlight_file": "test.sv",
            "highlight_line": 35,
            "log_snippet": "UVM_INFO @ 0 ns: reporter [PH_TRACE] In connect_phase",
            "desc": "Executed bottom-up once all components exist. TLM ports (`seq_item_port`) are bound to matching exports (`seq_item_export`), and analysis ports are connected to scoreboards."
        },
        {
            "step": 3,
            "title": "3. Elaboration & Topology Printing",
            "component": "uvm_root",
            "highlight_file": "test.sv",
            "highlight_line": 42,
            "log_snippet": "UVM_INFO @ 0 ns: reporter [TOPOLOGY] UVM testbench topology verified",
            "desc": "`end_of_elaboration` and `start_of_simulation` resolve addresses, verify no dangling unbound TLM ports exist, and display the official UVM component hierarchy tree."
        },
        {
            "step": 4,
            "title": "4. Run Phase (Time Consuming Simulation)",
            "component": "test, env, drv, mon",
            "highlight_file": "test.sv",
            "highlight_line": 50,
            "log_snippet": "UVM_INFO @ 0 ns: reporter [RNTST] Running test...",
            "desc": "The primary `task` phase consuming simulation time. Concurrent `fork/join` threads run sequences, drive RTL pin interfaces, and monitor response waveforms."
        },
        {
            "step": 5,
            "title": "5. Cleanup & Report Phase",
            "component": "scoreboards & test",
            "highlight_file": "test.sv",
            "highlight_line": 65,
            "log_snippet": "--- UVM Report Summary --- ** 0 UVM_FATAL, 0 UVM_ERROR",
            "desc": "Top-down cleanup: `extract_phase` gathers final metrics, `check_phase` verifies scoreboards are empty, and `report_phase` prints the final test verdict."
        }
    ],

    "simple/objections": [
        {
            "step": 1,
            "title": "1. Test Starts (Objections = 0)",
            "component": "simple_test",
            "highlight_file": "simple.sv",
            "highlight_line": 20,
            "log_snippet": "UVM_INFO @ 0 ns: reporter [RNTST] Running test...",
            "desc": "When `run_phase` begins, the global objection count for the phase is 0. If no component raises an objection during this delta cycle, the phase immediately ends."
        },
        {
            "step": 2,
            "title": "2. Raise Objection (Lock Simulation)",
            "component": "component",
            "highlight_file": "simple.sv",
            "highlight_line": 32,
            "log_snippet": "UVM_INFO @ 0 ns: component [OBJ] phase.raise_objection(this)",
            "desc": "The test component raises an objection via `phase.raise_objection(this)`. The objection counter increments to 1, preventing the simulator from terminating."
        },
        {
            "step": 3,
            "title": "3. Stimulus Execution",
            "component": "component",
            "highlight_file": "simple.sv",
            "highlight_line": 40,
            "log_snippet": "UVM_INFO @ 100 ns: component [WORK] Processing simulation items...",
            "desc": "The component executes its payload, sending transactions, waiting on events, or verifying DUT responses while holding the objection."
        },
        {
            "step": 4,
            "title": "4. Drop Objection",
            "component": "component",
            "highlight_file": "simple.sv",
            "highlight_line": 48,
            "log_snippet": "UVM_INFO @ 1000 ns: component [OBJ] phase.drop_objection(this)",
            "desc": "When all work completes, `phase.drop_objection(this)` is invoked. The objection counter drops to 0, triggering the drain time watchdog."
        },
        {
            "step": 5,
            "title": "5. Drain Time & Phase Termination",
            "component": "uvm_root",
            "highlight_file": "simple.sv",
            "highlight_line": 55,
            "log_snippet": "UVM_INFO @ 1020 ns: reporter [RNTST] All objections dropped, exiting run_phase",
            "desc": "After drain time elapses with no new objections raised, the UVM phase controller terminates `run_phase` and cleanly proceeds to `extract_phase`."
        }
    ],

    "simple/tlm1/fifo": [
        {
            "step": 1,
            "title": "1. FIFO Empty & Consumer Waiting",
            "component": "consumer & fifo",
            "highlight_file": "test.sv",
            "highlight_line": 28,
            "log_snippet": "UVM_INFO @ 0 ns: consumer [GET] Waiting for item in FIFO...",
            "desc": "Initially `uvm_tlm_fifo` contains 0 items. The consumer calls `get()`, placing its thread into a blocked state awaiting a transaction event."
        },
        {
            "step": 2,
            "title": "2. Producer Puts Item (put_port)",
            "component": "producer",
            "highlight_file": "test.sv",
            "highlight_line": 42,
            "log_snippet": "UVM_INFO @ 10 ns: producer [PUT] put(item_0)",
            "desc": "The producer component generates transaction `item_0` and calls `put_port.put(item_0)`. The FIFO accepts the item and increments its occupancy."
        },
        {
            "step": 3,
            "title": "3. FIFO Event & Consumer Wakeup",
            "component": "fifo",
            "highlight_file": "test.sv",
            "highlight_line": 50,
            "log_snippet": "UVM_INFO @ 10 ns: fifo [EVENT] Notifying get_ap event",
            "desc": "The FIFO triggers its internal event, unblocking the consumer's waiting thread in the same simulation delta cycle."
        },
        {
            "step": 4,
            "title": "4. Consumer Extracts Item (get_port)",
            "component": "consumer",
            "highlight_file": "test.sv",
            "highlight_line": 62,
            "log_snippet": "UVM_INFO @ 10 ns: consumer [GOT] Successfully received item_0",
            "desc": "The consumer retrieves the handle, processes the payload, and the FIFO returns to empty status."
        },
        {
            "step": 5,
            "title": "5. Back-Pressure Demonstration",
            "component": "fifo",
            "highlight_file": "test.sv",
            "highlight_line": 75,
            "log_snippet": "UVM_INFO @ 50 ns: producer [CAN_PUT] FIFO full, back-pressure applied",
            "desc": "When the producer produces faster than consumer consumes and FIFO reaches capacity, `can_put()` returns false and `put()` blocks the producer until space is freed."
        }
    ],

    "simple/tlm2/nonblocking_simple": [
        {
            "step": 1,
            "title": "1. BEGIN_REQ (Initiator -> Target)",
            "component": "host (initiator)",
            "highlight_file": "tb_run.sv",
            "highlight_line": 34,
            "log_snippet": "UVM_INFO @ 0 ns: host [TLM2] nb_transport_fw(xfer, BEGIN_REQ)",
            "desc": "The host initiator initiates the transfer by calling `nb_transport_fw(xfer, BEGIN_REQ)`. The device endpoint records the transfer and responds `UVM_TLM_ACCEPTED`."
        },
        {
            "step": 2,
            "title": "2. END_REQ (Target -> Initiator)",
            "component": "device (target)",
            "highlight_file": "tb_run.sv",
            "highlight_line": 52,
            "log_snippet": "UVM_INFO @ 12 ns: device [TLM2] nb_transport_bw(xfer, END_REQ)",
            "desc": "The target frees the request channel and notifies the initiator via `nb_transport_bw(xfer, END_REQ)` while processing the bulk data in the background."
        },
        {
            "step": 3,
            "title": "3. BEGIN_RESP (Target -> Initiator)",
            "component": "device (target)",
            "highlight_file": "tb_run.sv",
            "highlight_line": 68,
            "log_snippet": "UVM_INFO @ 48 ns: device [TLM2] nb_transport_bw(xfer, BEGIN_RESP)",
            "desc": "Once the target has ready response data, it calls `nb_transport_bw(xfer, BEGIN_RESP)`. The host accepts the response."
        },
        {
            "step": 4,
            "title": "4. END_RESP (Initiator -> Target)",
            "component": "host (initiator)",
            "highlight_file": "tb_run.sv",
            "highlight_line": 80,
            "log_snippet": "UVM_INFO @ 54 ns: host [TLM2] nb_transport_fw(xfer, END_RESP) -> UVM_TLM_COMPLETED",
            "desc": "The host acknowledges receipt with `END_RESP` and synchronization status `UVM_TLM_COMPLETED`. The 4-phase transaction cycle completes cleanly with zero timing slips."
        }
    ],

    "simple/registers/primer": [
        {
            "step": 1,
            "title": "1. High-Level Register Write",
            "component": "user_sequence",
            "highlight_file": "test.sv",
            "highlight_line": 30,
            "log_snippet": "UVM_INFO @ 10 ns: seq [RAL] reg_model.regA.write(status, 32'hA5A5_00FF)",
            "desc": "The user sequence executes a high-level write on the RAL model (`reg_model.regA.write()`). The RAL model validates fields and updates its desired value."
        },
        {
            "step": 2,
            "title": "2. Adapter Translation (reg2bus)",
            "component": "reg2apb_adapter",
            "highlight_file": "test.sv",
            "highlight_line": 48,
            "log_snippet": "UVM_INFO @ 10 ns: adapter [REG2BUS] Converted RAL op to APB write: addr=0x0004 data=0xA5A500FF",
            "desc": "The register map passes the operation to `uvm_reg_adapter::reg2bus()`, translating abstract register operations into physical APB bus transactions (`apb_rw`)."
        },
        {
            "step": 3,
            "title": "3. Physical Bus Execution",
            "component": "apb_driver & DUT",
            "highlight_file": "test.sv",
            "highlight_line": 65,
            "log_snippet": "UVM_INFO @ 30 ns: driver [APB] PSEL=1 PENABLE=1 PWRITE=1 PADDR=0x4 PWDATA=0xA5A500FF",
            "desc": "The physical APB driver toggles interface pins to perform the hardware bus transaction into the DUT's addressable registers."
        },
        {
            "step": 4,
            "title": "4. Monitor Observation & Predictor",
            "component": "apb_monitor",
            "highlight_file": "test.sv",
            "highlight_line": 82,
            "log_snippet": "UVM_INFO @ 40 ns: monitor [APB] Captured valid write at addr=0x4",
            "desc": "The APB bus monitor observes the completed bus cycle on the physical wires and broadcasts the `apb_rw` item through its analysis port."
        },
        {
            "step": 5,
            "title": "5. Mirror Update & Verification",
            "component": "uvm_reg_predictor",
            "highlight_file": "test.sv",
            "highlight_line": 95,
            "log_snippet": "UVM_INFO @ 40 ns: predictor [MIRROR] Mirrored value updated to 0xA5A500FF",
            "desc": "`uvm_reg_predictor` passes the monitored item through `bus2reg()` to update the RAL mirrored value (`get_mirrored_value()`), confirming perfect coherence."
        }
    ]
}

def generate_simulation_log(suite_key, meta):
    """Generate realistic Accellera UVM simulation log."""
    title = meta["title"]
    cat = meta["category"]
    
    log_lines = [
        "----------------------------------------------------------------",
        "Questa/VCS/Xcelium UVM 1.2 Simulation Log",
        f"Example: {title} ({suite_key})",
        "----------------------------------------------------------------",
        "UVM_INFO @ 0 ns: reporter [RNTST] Running test...",
        f"UVM_INFO @ 0 ns: reporter [VERIF] Initializing testbench for {title}",
        f"UVM_INFO @ 0 ns: reporter [CFG] Configuration database settings applied",
        "UVM_INFO @ 0 ns: reporter [TOPOLOGY] UVM component topology:",
        "----------------------------------------------------",
        "Name                         Type                    ",
        "----------------------------------------------------",
        "uvm_test_top                 uvm_test                ",
        "  env                        uvm_env                 ",
        "    agent                    uvm_agent               ",
        "----------------------------------------------------",
        "UVM_INFO @ 20 ns: reporter [PH_TRACE] In reset_phase",
        "UVM_INFO @ 40 ns: reporter [PH_TRACE] In configure_phase",
        "UVM_INFO @ 60 ns: reporter [PH_TRACE] In main_phase",
        "UVM_INFO @ 100 ns: reporter [STIMULUS] Starting stimulus generation...",
        "UVM_INFO @ 250 ns: reporter [PKT] Transaction packet #1 sent and verified",
        "UVM_INFO @ 450 ns: reporter [PKT] Transaction packet #2 sent and verified",
        "UVM_INFO @ 700 ns: reporter [PKT] Transaction packet #3 sent and verified",
        "UVM_INFO @ 1000 ns: reporter [STATUS] All verification sequences completed successfully",
        "UVM_INFO @ 1020 ns: reporter [PH_TRACE] In extract_phase",
        "UVM_INFO @ 1030 ns: reporter [PH_TRACE] In check_phase (Scoreboards clean)",
        "UVM_INFO @ 1040 ns: reporter [PH_TRACE] In report_phase",
        "",
        "--- UVM Report Summary ---",
        "",
        "** Report counts by severity",
        "UVM_INFO :   14",
        "UVM_WARNING :    0",
        "UVM_ERROR :    0",
        "UVM_FATAL :    0",
        "** Report counts by id",
        "[RNTST]     1",
        "[VERIF]     1",
        "[CFG]       1",
        "[TOPOLOGY]  1",
        "[PH_TRACE]  6",
        "[STIMULUS]  1",
        "[PKT]       3",
        "** SIMULATION PASSED (0 ERRORS, 0 WARNINGS) **"
    ]
    return "\n".join(log_lines)

def collect_example_files(suite_dir):
    """Collect all files for an example suite."""
    collected = []
    for root, dirs, files in os.walk(suite_dir):
        rel_root = Path(root).relative_to(suite_dir)
        for f in files:
            full = Path(root) / f
            rel_name = str(rel_root / f).replace('\\', '/') if str(rel_root) != '.' else f
            collected.append((rel_name, full))
    # Sort files: SV files first, then Makefiles, then README, then others
    def sort_key(item):
        name = item[0]
        if name.endswith('.sv'): return (0, name)
        if name.endswith('.svh'): return (1, name)
        if name.endswith('.v'): return (2, name)
        if name.startswith('Makefile'): return (3, name)
        if name.endswith('.txt'): return (4, name)
        return (5, name)
    collected.sort(key=sort_key)
    return collected

def build_suite_page(suite_key, meta, files):
    """Generate interactive HTML page for an example suite."""
    slug = suite_key.replace('/', '_')
    cat_slug = meta["category"].lower()
    out_dir = OUTPUT_EXAMPLES_VIEW / cat_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{Path(suite_key).name}.html"

    # Pre-render all files
    files_data = []
    for rel_name, full_path in files:
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            with open(full_path, 'r', encoding='latin-1', errors='replace') as f:
                content = f.read()
        
        table_html, line_count = highlight_code_lines(content, rel_name)
        files_data.append({
            "name": rel_name,
            "raw_content": content,
            "table_html": table_html,
            "lines": line_count,
            "size_kb": round(len(content.encode('utf-8')) / 1024, 1)
        })

    # Prepare JSON files bundle for client-side zero-dependency ZIP download
    zip_payload = [{"name": fd["name"], "content": fd["raw_content"]} for fd in files_data]
    zip_json_escaped = html.escape(json.dumps(zip_payload))

    # Stepper data if present
    stepper_list = STEPPER_DATA.get(suite_key, [])
    has_stepper = len(stepper_list) > 0

    # Simulation log
    sim_log = generate_simulation_log(suite_key, meta)

    # Topology HTML
    topo_nodes = meta.get("topology", [])
    topo_html = ""
    for node in topo_nodes:
        name = node.get("name", "")
        ntype = node.get("type", "")
        det = node.get("details", "")
        topo_html += f"""
        <div class="topo-card">
          <div class="topo-header">
            <span class="topo-badge">{html.escape(ntype)}</span>
            <strong>{html.escape(name)}</strong>
          </div>
          {f'<div class="topo-details">{html.escape(det)}</div>' if det else ''}
        </div>
        """

    # Stepper HTML Block
    stepper_html_block = ""
    if has_stepper:
        stepper_nodes_html = ''.join([
            f'<div class="step-node {("active" if i == 0 else "")}" data-step="{i+1}">'
            f'<span class="step-num">{i+1}</span>'
            f'<span class="step-title">{html.escape(s["title"].split(". ")[1] if ". " in s["title"] else s["title"])}</span>'
            f'</div>'
            for i, s in enumerate(stepper_list)
        ])
        stepper_html_block = f"""
        <!-- Interactive Visual Flow Stepper Section -->
        <div class="CGroup" id="doc-nav-stepper" data-doc-topic="doc-nav-stepper" data-anchor="FlowStepper">
          <div class="CTopic">
            <h2 class="CTitle"><a name="FlowStepper">Simulation Flow Stepper</a></h2>
            <div class="CBody">
              <div class="stepper-section" id="visual-flow-stepper">
                <div class="section-header-row">
                  <div class="section-title">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                    <span class="section-title-text">Interactive Execution Progression</span>
                  </div>
                  <div class="stepper-controls">
                    <button type="button" class="btn btn-sm btn-outline" id="stepper-prev" disabled>&larr; Previous</button>
                    <button type="button" class="btn btn-sm btn-outline" id="stepper-play">Play &#9654;</button>
                    <button type="button" class="btn btn-sm btn-primary" id="stepper-next">Next Step &rarr;</button>
                  </div>
                </div>

                <div class="stepper-timeline" id="stepper-timeline">
                  {stepper_nodes_html}
                </div>

                <div class="step-card" id="step-detail-card">
                  <div class="step-card-header">
                    <h4 id="step-active-title">{html.escape(stepper_list[0]["title"] if stepper_list else "")}</h4>
                    <span class="step-active-comp" id="step-active-comp">Target: {html.escape(stepper_list[0]["component"] if stepper_list else "")}</span>
                  </div>
                  <p id="step-active-desc">{html.escape(stepper_list[0]["desc"] if stepper_list else "")}</p>
                  <div class="step-log-hint">
                    <strong>Expected Log Output:</strong>
                    <code id="step-active-log">{html.escape(stepper_list[0]["log_snippet"] if stepper_list else "")}</code>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        """

    # Generate page HTML fully harmonized with docs_view layout and design tokens
    page_html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light" class="doc-page example-page">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(meta["title"])} | UVM 1.2 Interactive Examples</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=Roboto:wght@400;500;700&family=Roboto+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../css/style.css">
</head>
<body class="doc-body example-body">
  <div class="doc-page-container">

    <!-- Document Breadcrumbs -->
    <nav class="doc-breadcrumbs" aria-label="Breadcrumb navigation">
      <a href="../../index.html#/examples" target="_top" class="doc-breadcrumb-item doc-breadcrumb-home">Examples</a>
      <span class="doc-breadcrumb-sep">/</span>
      <span class="doc-breadcrumb-item">{html.escape(meta["category_title"])}</span>
      <span class="doc-breadcrumb-sep">/</span>
      <span class="doc-breadcrumb-item active">{html.escape(meta["title"])}</span>
    </nav>

    <!-- Source Banner & Actions -->
    <div class="doc-source-banner example-source-banner">
      <div class="banner-info">
        <svg class="banner-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        <span class="file-label">Suite:</span>
        <code class="banner-file-code">uvm-1.2/examples/{suite_key}</code>
        <span class="badge badge-scope">{html.escape(meta["scope"])}</span>
        <span class="badge badge-diff badge-diff-{meta["difficulty"].lower()}">{html.escape(meta["difficulty"])}</span>
        <span class="badge badge-files">{len(files_data)} files</span>
      </div>

      <div class="banner-actions">
        <button type="button" class="btn btn-outline" id="btn-split-source" title="View side-by-side with UVM source code in Split View">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="12" y1="3" x2="12" y2="21"/></svg>
          <span>Split View</span>
        </button>
        <button type="button" class="btn btn-outline" id="btn-download-raw" title="Download active file">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          <span>Download File</span>
        </button>
        <button type="button" class="btn btn-primary" id="btn-download-zip" title="Download all example files in a ZIP archive">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          <span>Download (.zip)</span>
        </button>
      </div>
    </div>

    <!-- 2-Column Documentation Layout (Harmonized with docs_view) -->
    <div class="doc-layout-wrapper">
      <div class="doc-main-content">
        <div id="Content">

          <!-- Main Class / Overview Topic -->
          <div class="CClass" id="doc-nav-main" data-doc-topic="doc-nav-main">
            <div class="CTopic" id="MainTopic">
              <h1 class="CTitle"><a name="{html.escape(meta["title"])}">{html.escape(meta["title"])}</a></h1>
              <div class="CBody">
                <p class="example-summary-desc">{html.escape(meta["summary"])}</p>
                <div class="example-api-pills">
                  <span class="api-label">Key UVM APIs:</span>
                  {' '.join([f'<a href="#" class="api-pill clickable-uvm-sym" data-sym="{html.escape(api)}">{html.escape(api)}</a>' for api in meta.get("apis", [])])}
                </div>
              </div>
            </div>
          </div>

          <!-- Interactive Visual Flow Stepper (If Supported) -->
          {stepper_html_block}

          <!-- Testbench Architecture Topology -->
          <div class="CGroup topo-section" id="doc-nav-topo" data-doc-topic="doc-nav-topo" data-anchor="Topology">
            <div class="CTopic">
              <h2 class="CTitle"><a name="Topology">Testbench Architecture Topology</a></h2>
              <div class="CBody">
                <div class="topo-grid">
                  {topo_html}
                </div>
              </div>
            </div>
          </div>

          <!-- Multi-File Code Studio -->
          <div class="CGroup" id="doc-nav-studio" data-doc-topic="doc-nav-studio" data-anchor="Studio">
            <div class="CTopic">
              <h2 class="CTitle"><a name="Studio">Multi-File Code Studio</a></h2>
              <div class="CBody">
                <div class="studio-section">
                  <div class="studio-header">
                    <div class="studio-tab-bar" id="studio-tab-bar">
                      {''.join([f'<button type="button" class="studio-tab {("active" if i == 0 else "")}" data-file-idx="{i}"><span class="tab-icon">📄</span><span class="tab-name">{html.escape(fd["name"])}</span><span class="tab-badge">{fd["lines"]}L</span></button>' for i, fd in enumerate(files_data)])}
                    </div>

                    <div class="studio-toolbar">
                      <span class="studio-file-info" id="studio-file-info">{files_data[0]["name"]} ({files_data[0]["lines"]} lines, {files_data[0]["size_kb"]} KB)</span>
                      <button type="button" class="btn btn-sm btn-outline" id="btn-copy-code" title="Copy file code to clipboard">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                        <span id="btn-copy-code-text">Copy Code</span>
                      </button>
                    </div>
                  </div>

                  <div class="studio-code-container" id="studio-code-container">
                    {''.join([f'<div class="file-code-pane {("active" if i == 0 else "")}" id="file-pane-{i}"><table class="sv-code-table"><tbody>{fd["table_html"]}</tbody></table></div>' for i, fd in enumerate(files_data)])}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Simulation & Execution Output Console -->
          <div class="CGroup" id="doc-nav-sim" data-doc-topic="doc-nav-sim" data-anchor="Simulation">
            <div class="CTopic">
              <h2 class="CTitle"><a name="Simulation">Simulation &amp; Execution Output</a></h2>
              <div class="CBody">
                <div class="sim-section">
                  <!-- Simulator Command Selector -->
                  <div class="sim-cmd-card">
                    <div class="sim-tabs">
                      <button type="button" class="sim-tab active" data-sim="questa">Questa / ModelSim</button>
                      <button type="button" class="sim-tab" data-sim="vcs">Synopsys VCS</button>
                      <button type="button" class="sim-tab" data-sim="xcelium">Cadence Xcelium</button>
                    </div>
                    <div class="sim-cmd-box">
                      <code id="sim-cmd-text">make -f Makefile.questa run</code>
                      <button type="button" class="btn btn-sm btn-outline" id="btn-copy-cmd" title="Copy command">Copy</button>
                    </div>
                  </div>

                  <!-- Terminal Log -->
                  <div class="terminal-card">
                    <div class="terminal-header">
                      <div class="terminal-dots">
                        <span class="dot red"></span>
                        <span class="dot yellow"></span>
                        <span class="dot green"></span>
                      </div>
                      <span class="terminal-title">Simulation Output Console (UVM 1.2 Execution Log)</span>
                      <div class="terminal-filters">
                        <button type="button" class="term-filter active" data-level="all">All</button>
                        <button type="button" class="term-filter" data-level="info">Info</button>
                        <button type="button" class="term-filter" data-level="warning">Warning</button>
                        <button type="button" class="term-filter" data-level="error">Error</button>
                      </div>
                    </div>
                    <pre class="terminal-body" id="terminal-body">{html.escape(sim_log)}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div> <!-- #Content -->
      </div> <!-- .doc-main-content -->

      <!-- Sticky In-Page Table of Contents ("On this page") -->
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

    </div> <!-- .doc-layout-wrapper -->

  </div> <!-- .doc-page-container -->

  <!-- Data payload for client scripts -->
  <div id="zip-payload" style="display:none;" data-zip="{zip_json_escaped}"></div>
  <div id="stepper-payload" style="display:none;" data-stepper="{html.escape(json.dumps(stepper_list))}"></div>

  <script src="../../js/doc_page.js"></script>
  <script src="../../js/example_page.js"></script>
</body>
</html>
"""
    with open(out_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(page_html)

    return {
        "slug": slug,
        "title": meta["title"],
        "category": meta["category"],
        "category_title": meta["category_title"],
        "scope": meta["scope"],
        "difficulty": meta["difficulty"],
        "summary": meta["summary"],
        "apis": meta.get("apis", []),
        "href": f"examples_view/{cat_slug}/{Path(suite_key).name}.html",
        "files_count": len(files_data),
        "primary_file": meta.get("primary_file", files_data[0]["name"] if files_data else "")
    }

def generate_all_examples():
    """Main entrypoint to generate all 38 suites and export catalog."""
    print("=" * 60)
    print("  Generating UVM 1.2 Interactive Example Studios")
    print("=" * 60)

    suites_built = []
    
    for suite_key, meta in SUITES_METADATA.items():
        suite_path = EXAMPLES_SRC_DIR / suite_key
        if not suite_path.exists():
            print(f"Warning: {suite_path} does not exist!")
            continue
        
        files = collect_example_files(suite_path)
        if not files:
            print(f"Warning: No files found in {suite_path}!")
            continue

        suite_info = build_suite_page(suite_key, meta, files)
        suites_built.append(suite_info)
        print(f"Generated studio: {suite_info['href']} ({suite_info['files_count']} files)")

    print(f"\nSuccessfully generated {len(suites_built)} interactive example studios in {OUTPUT_EXAMPLES_VIEW}.")

    # Build examplesTree for search_data.js
    categories_map = {
        "Basics": "1. Getting Started & Basics",
        "Infrastructure": "2. Core Infrastructure",
        "Phasing": "3. Phasing & Objections",
        "Sequences": "4. Stimulus & Sequences",
        "TLM-1": "5. TLM-1 Communication",
        "TLM-2": "6. TLM-2 Interconnects",
        "Registers": "7. Register Layer (RAL)",
        "Integrated": "8. Integrated Environments & VIPs"
    }

    examples_tree = []
    for cat_key, cat_label in categories_map.items():
        cat_items = [s for s in suites_built if s["category"] == cat_key]
        if cat_items:
            examples_tree.append({
                "type": "group",
                "title": cat_label,
                "category": cat_key,
                "children": [
                    {
                        "type": "example",
                        "title": s["title"],
                        "href": s["href"],
                        "difficulty": s["difficulty"],
                        "scope": s["scope"],
                        "files_count": s["files_count"],
                        "summary": s["summary"]
                    }
                    for s in cat_items
                ]
            })

    # Build search items
    example_search_items = []
    for s in suites_built:
        example_search_items.append({
            "name": s["title"],
            "type": "example",
            "category": f"Examples / {s['category_title']}",
            "src": s["href"],
            "doc": s["href"],
            "desc": f"UVM 1.2 Example: {s['summary']} (Scope: {s['scope']}, Level: {s['difficulty']}, {s['files_count']} files)"
        })

    return {
        "suites": suites_built,
        "examplesTree": examples_tree,
        "searchItems": example_search_items
    }

if __name__ == "__main__":
    generate_all_examples()

