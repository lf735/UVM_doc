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
from collections import OrderedDict
from typing import Dict, List, Any
import page_builder_common as pbc

BASE_DIR = Path(__file__).resolve().parent.parent
EXAMPLES_SRC_DIR = BASE_DIR / "uvm-1.2" / "examples"
OUTPUT_EXAMPLES_VIEW = BASE_DIR / "examples_view"
OUTPUT_JS_DIR = BASE_DIR / "js"

def highlight_code_lines(code, filename):
    """Highlight code lines and return (lines_html, total_lines)."""
    rows, count = pbc.highlight_code_lines(code, filename, clickable_sym_links=True)
    return '\n'.join(rows), count

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
        "apis": ["uvm_component", "uvm_tlm_fifo", "uvm_config_db", "run_test", "uvm_table_printer"],
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
        "apis": ["uvm_component", "uvm_object", "run_test", "uvm_root"],
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
        "apis": ["uvm_component", "uvm_factory", "uvm_coreservice_t", "uvm_printer"],
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
        "apis": ["`uvm_field_int", "uvm_config_db", "apply_config_settings"],
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
        "apis": ["uvm_callback", "`uvm_register_cb", "`uvm_do_callbacks"],
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
        "apis": ["uvm_resource_db", "uvm_config_db", "uvm_component", "uvm_driver"],
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
        "apis": ["run_test", "uvm_cmdline_processor", "uvm_root", "uvm_test"],
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
        "apis": ["set_timeout", "uvm_root", "`uvm_fatal"],
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
        "apis": ["uvm_event", "uvm_pool", "trigger", "wait_trigger"],
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
        "apis": ["uvm_tlm_nb_initiator_socket", "uvm_tlm_nb_target_socket", "nb_transport_fw", "nb_transport_bw", "uvm_tlm_time"],
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
        "apis": ["uvm_tlm_time", "uvm_tlm_b_initiator_socket", "uvm_tlm_b_target_socket", "b_transport"],
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
        "apis": ["uvm_reg_block", "uvm_reg_map", "add_submap"],
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
        "apis": ["set_sequencer", "uvm_reg_map", "uvm_reg_adapter"],
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
        "apis": ["uvm_reg_sequence", "uvm_reg_adapter", "uvm_sequencer", "uvm_sequence"],
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
        "apis": ["uvm_reg", "uvm_reg_field", "uvm_reg_cbs", "predict"],
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
        "apis": ["uvm_reg_block", "uvm_reg", "build_coverage", "sample"],
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
        "apis": ["uvm_reg_block", "uvm_reg", "uvm_reg_field", "uvm_reg_map", "add_reg"],
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
        "apis": ["create_map", "add_submap", "uvm_reg_map"],
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
        "apis": ["uvm_agent", "uvm_driver", "uvm_monitor", "uvm_sequencer", "uvm_sequence", "uvm_sequence_item"],
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

# 5 Pillar Stepper Data (Test Scenario Walkthroughs calibrated to test intent)
STEPPER_DATA = {
    "simple/phases/basic": [
        {
            "step": 1,
            "title": "1. Top-Down Construction (build_phase)",
            "state": "Phasing: BUILD_PHASE (Top-Down)",
            "component": "top, a1, a2, b1, d1",
            "highlight_file": "test.sv",
            "highlight_line": 144,
            "log_snippet": "0: top:  build",
            "desc": "Execution begins at top-level. The framework calls build_phase() in strict top-down hierarchical order: top -> a1 -> a -> b1/d1."
        },
        {
            "step": 2,
            "title": "2. Bottom-Up Elaboration Phase",
            "state": "Phasing: ELABORATION (Bottom-Up)",
            "component": "b1, d1, a, top",
            "highlight_file": "test.sv",
            "highlight_line": 105,
            "log_snippet": "0: top.a1.a.d1:  end_of_elaboration",
            "desc": "Once all components exist, end_of_elaboration and start_of_simulation execute bottom-up: leaf components validate bindings before parents display topology."
        },
        {
            "step": 3,
            "title": "3. Run Phase & Objection Arming",
            "state": "Sim Time: 0 ns (Objection Active: 1)",
            "component": "top, b1",
            "highlight_file": "test.sv",
            "highlight_line": 163,
            "log_snippet": "0: top:  start run phase",
            "desc": "top enters run_phase and raises an objection (phase.raise_objection). Subcomponents concurrently launch their timed processes."
        },
        {
            "step": 4,
            "title": "4. Time Progression & Delays (#500)",
            "state": "Sim Time: 500 ns (Objection Released)",
            "component": "top, b1",
            "highlight_file": "test.sv",
            "highlight_line": 167,
            "log_snippet": "500: top:  end run phase",
            "desc": "After #500 time delay elapses, top drops its objection (phase.drop_objection). All concurrent tasks having concluded, run_phase completes cleanly."
        },
        {
            "step": 5,
            "title": "5. Top-Down Cleanup (Extract, Check, Report)",
            "state": "Phasing: CLEANUP (Scoreboard & Report)",
            "component": "top, a1, a2",
            "highlight_file": "test.sv",
            "highlight_line": 159,
            "log_snippet": "500: top:  report",
            "desc": "Post-simulation phases execute sequentially: extract_phase collects state, check_phase validates results, and report_phase prints the final test verdict."
        }
    ],

    "simple/objections": [
        {
            "step": 1,
            "title": "1. Arming Drain Time (10 ns)",
            "state": "Drain Time: 10 ns (Active Objections: 0)",
            "component": "simple_test",
            "highlight_file": "simple.sv",
            "highlight_line": 56,
            "log_snippet": "UVM_INFO simple.sv(55) @ 0 ns: uvm_test_top [drain] Setting drain time of 10",
            "desc": "simple_test configures a 10 ns drain time via set_drain_time(this, 10). When all objections drop to 0, this watchdog delays termination by 10 ns."
        },
        {
            "step": 2,
            "title": "2. Forking 4 Concurrent Threads",
            "state": "Sim Time: 0 ns (Active Objections: 4)",
            "component": "simple_test",
            "highlight_file": "simple.sv",
            "highlight_line": 59,
            "log_snippet": "UVM_INFO simple.sv(74) @ 0 ns: uvm_test_top [doit] Starting doit (0) with delay 35",
            "desc": "The test forks 4 parallel processes with delays of 15, 25, 35, and 50 ns. Each invokes raise_objection(this), bringing global objections to 4."
        },
        {
            "step": 3,
            "title": "3. Threads Dropping (15 ns, 25 ns, 35 ns)",
            "state": "Sim Time: 35 ns (Active Objections: 1)",
            "component": "simple_test",
            "highlight_file": "simple.sv",
            "highlight_line": 80,
            "log_snippet": "UVM_INFO simple.sv(88) @ 35 ns: uvm_test_top [dropped] 1 objection(s) dropped from uvm_test_top, total count is now 1",
            "desc": "Processes finish asynchronously: at 15 ns, 25 ns, and 35 ns, each calls drop_objection. The dropped() callback traces the decrementing counter."
        },
        {
            "step": 4,
            "title": "4. Last Thread (50 ns) & Drain Trigger",
            "state": "Sim Time: 50 ns (Active Objections: 0 -> Drain Armed)",
            "component": "simple_test",
            "highlight_file": "simple.sv",
            "highlight_line": 88,
            "log_snippet": "UVM_INFO simple.sv(88) @ 50 ns: uvm_test_top [dropped] 1 objection(s) dropped from uvm_test_top, total count is now 0",
            "desc": "At t=50 ns, the 50 ns thread finishes. Active objections reach 0, but simulation does NOT terminate: the 10 ns drain watchdog takes over."
        },
        {
            "step": 5,
            "title": "5. Drain Expiration & Termination @ 60 ns",
            "state": "Sim Time: 60 ns (Clean Exit @ 50ns + 10ns)",
            "component": "simple_test, uvm_root",
            "highlight_file": "simple.sv",
            "highlight_line": 64,
            "log_snippet": "UVM_INFO @ 60 ns: reporter [TEST_DONE] 'run' phase is ready to proceed to the 'extract' phase",
            "desc": "At t=60 ns (50 + 10 ns drain), with no new objections raised, drain time expires. The phase controller safely terminates run_phase."
        }
    ],

    "simple/tlm1/fifo": [
        {
            "step": 1,
            "title": "1. TLM Port Setup & 10-Level FIFO",
            "state": "FIFO Occupancy: 0 / 10 (Producer: Ready, Consumer: Waiting)",
            "component": "producer, consumer, fifo",
            "highlight_file": "test.sv",
            "highlight_line": 50,
            "log_snippet": "1: put data 0",
            "desc": "The testbench binds a producer (uvm_put_port) and a consumer (uvm_get_port) to a uvm_tlm_fifo with a buffer capacity of 10 items."
        },
        {
            "step": 2,
            "title": "2. Fast Burst Fill with try_put()",
            "state": "FIFO Occupancy: 10 / 10 [FULL]",
            "component": "producer, fifo",
            "highlight_file": "test.sv",
            "highlight_line": 58,
            "log_snippet": "try_put status return: 10",
            "desc": "The producer pushes 10 items in rapid succession via try_put(p). At t=91 ns, the 10th attempt returns 0 because the FIFO is completely full."
        },
        {
            "step": 3,
            "title": "3. Back-Pressure & Blocking Put",
            "state": "FIFO Occupancy: 10 / 10 [BACK-PRESSURE: Producer Blocked]",
            "component": "producer, fifo",
            "highlight_file": "test.sv",
            "highlight_line": 64,
            "log_snippet": "91: do a blocking put",
            "desc": "Producer invokes blocking put(p). With FIFO full, the put call suspends the producer thread, applying back-pressure without spin-polling."
        },
        {
            "step": 4,
            "title": "4. Consumer Extraction with get()",
            "state": "Sim Time: 100 ns (Consumer Read: data 0)",
            "component": "consumer, fifo",
            "highlight_file": "test.sv",
            "highlight_line": 78,
            "log_snippet": "100: getting one",
            "desc": "At t=100 ns, the consumer wakes up after #100 delay and calls data_in.get(p), extracting the first item (data 0) from the FIFO."
        },
        {
            "step": 5,
            "title": "5. Instant Producer Resume (Delta-Cycle)",
            "state": "FIFO Occupancy: 10 / 10 (Producer Resumed)",
            "component": "producer, consumer, fifo",
            "highlight_file": "test.sv",
            "highlight_line": 65,
            "log_snippet": "100: blocking put succeeded",
            "desc": "In the same delta cycle at t=100 ns, the newly freed FIFO slot unblocks data_out.put(p), resuming producer execution immediately."
        }
    ],

    "simple/tlm2/nonblocking_simple": [
        {
            "step": 1,
            "title": "1. Initiator Sends BEGIN_REQ (Forward)",
            "state": "TLM-2 Phase: BEGIN_REQ (Host -> Device)",
            "component": "host (initiator)",
            "highlight_file": "host.sv",
            "highlight_line": 85,
            "log_snippet": "UVM_INFO host.sv(85) @ 0 ns: host [USB/DEV/FWD] USB_TLM_TOKEN @0: OUT [00000000] addr=7A endp=5",
            "desc": "Host initiator initiates OUT transfer by calling sock.nb_transport_fw(xfer, ph, delay) with ph = USB_TLM_TOKEN, returning UVM_TLM_ACCEPTED without thread blocking."
        },
        {
            "step": 2,
            "title": "2. Payload Transfer & Target Background Task",
            "state": "TLM-2 Phase: DATA Transferred (Device Processing)",
            "component": "host, device",
            "highlight_file": "host.sv",
            "highlight_line": 97,
            "log_snippet": "UVM_INFO host.sv(97) @ 0 ns: host [USB/DEV/FWD] USB_TLM_DATA @0: OUT [00000000] addr=7A endp=5 data='{DE, AD, BE, EF}",
            "desc": "Host sends data payload ('{DE, AD, BE, EF}). Device accepts payload and spawns an asynchronous background thread (fork: out_ack) to model 100 ns hardware latency."
        },
        {
            "step": 3,
            "title": "3. Target Handshake via Backward Path",
            "state": "Sim Time: 100 ns (Phase: USB_TLM_HANDSHAKE / ACK)",
            "component": "device (target)",
            "highlight_file": "device.sv",
            "highlight_line": 68,
            "log_snippet": "UVM_INFO device.sv(68) @ 100 ns: device [USB/HST/BWD] USB_TLM_HANDSHAKE @0: OUT [00000000] addr=7A endp=5 status=ACK",
            "desc": "After 100 ns processing, device targets host via backward path sock.nb_transport_bw(xf, ph, dl) with status ACK, notifying completion."
        },
        {
            "step": 4,
            "title": "4. Device Completes Transfer (UVM_TLM_COMPLETED)",
            "state": "TLM-2 Sync: UVM_TLM_COMPLETED (Zero-Slip Termination)",
            "component": "device, host",
            "highlight_file": "device.sv",
            "highlight_line": 71,
            "log_snippet": "UVM_INFO device.sv(71) @ 100 ns: device [USB/DEV/OUT/DONE] OUT [00000000] addr=7A endp=5 data='{DE, AD, BE, EF} status=ACK",
            "desc": "Transfer finishes with UVM_TLM_COMPLETED. Non-blocking protocol achieves bidirectional cycle-accurate handshaking with zero thread overhead."
        }
    ],

    "simple/registers/primer": [
        {
            "step": 1,
            "title": "1. High-Level Register Write (model.write)",
            "state": "RAL Operation: WRITE (TABLES[12] = 0x3F8A019B)",
            "component": "user_test_seq",
            "highlight_file": "user_test.sv",
            "highlight_line": 46,
            "log_snippet": "UVM_INFO user_test.sv(46) @ 25 ns: user_test [RAL/WRITE] Writing model.TABLES[12] = 0x3F8A019B",
            "desc": "User sequence executes high-level write on the RAL model: model.TABLES[idx].write(status, data). Verification sequences manipulate objects without pin-level knowledge."
        },
        {
            "step": 2,
            "title": "2. Adapter Translation (reg2bus)",
            "state": "Adapter Layer: reg2bus (APB addr=0x0030 data=0x3F8A019B)",
            "component": "reg2apb_adapter, tb_env",
            "highlight_file": "tb_env.sv",
            "highlight_line": 48,
            "log_snippet": "UVM_INFO tb_env.sv(48) @ 25 ns: reg2apb [ADAPT] reg2bus: WRITE addr=0x0030 data=0x3F8A019B",
            "desc": "The register map delegates the operation to reg2apb_adapter::reg2bus(), translating abstract register writes into physical APB bus transactions (apb_rw) with address 0x0030."
        },
        {
            "step": 3,
            "title": "3. Hardware Bus Cycle on DUT",
            "state": "Physical Bus: PSEL=1, PENABLE=1, PWRITE=1",
            "component": "dut (slave)",
            "highlight_file": "dut.sv",
            "highlight_line": 58,
            "log_snippet": "UVM_INFO dut.sv(58) @ 35 ns: apb_slave [BUS] APB Write complete: PADDR=0x0030 PWDATA=0x3F8A019B",
            "desc": "The physical APB driver toggles interface pins. In dut.sv, the hardware slave detects the SETUP+ENABLE cycle and writes the payload into DUT TABLES memory."
        },
        {
            "step": 4,
            "title": "4. High-Level Read & Mirror Check",
            "state": "RAL Readback: TABLES[12] matches 0x3F8A019B",
            "component": "user_test_seq, dut",
            "highlight_file": "user_test.sv",
            "highlight_line": 54,
            "log_snippet": "TABLES[12] is 0x3F8A019B...",
            "desc": "The test issues model.TABLES[i].read(status, data). With set_auto_predict(1), the RAL model automatically updates and verifies its mirrored value, confirming coherence."
        }
    ]
}

def generate_simulation_log(suite_key, meta):
    """Generate authentic, realistic simulation log tailored to each example's scenario."""
    title = meta["title"]
    
    if suite_key == "simple/phases/basic":
        return f"""----------------------------------------------------------------
Questa/VCS/Xcelium UVM 1.2 Simulation Log
Example: {title} ({suite_key})
----------------------------------------------------------------
UVM_INFO @ 0 ns: reporter [RNTST] Running test...
0: top:  build
0: top.a1:  build
0: top.a1.a:  build
0: top.a1.a.b1:  build
0: top.a1.a.d1:  build
0: top.a2:  build
0: top.a2.a:  build
0: top.a2.a.b1:  build
0: top.a2.a.d1:  build
0: top.a1.a.d1:  end_of_elaboration
0: top.a1.a.b1:  end_of_elaboration
0: top.a1.a:  end_of_elaboration
0: top.a1:  end_of_elaboration
0: top.a2.a.d1:  end_of_elaboration
0: top.a2.a.b1:  end_of_elaboration
0: top.a2.a:  end_of_elaboration
0: top.a2:  end_of_elaboration
0: top:  end_of_elaboration
0: top.a1.a.d1:  start_of_simulation
0: top.a1.a.b1:  start_of_simulation
0: top.a1.a:  start_of_simulation
0: top.a1:  start_of_simulation
0: top.a2.a.d1:  start_of_simulation
0: top.a2.a.b1:  start_of_simulation
0: top.a2.a:  start_of_simulation
0: top.a2:  start_of_simulation
0: top:  start_of_simulation
0: top:  start run phase
0: top.a1.a:  start run phase
0: top.a1.a.b1:  start run phase
0: top.a2.a:  start run phase
0: top.a2.a.b1:  start run phase
500: top:  end run phase
500: top:  extract
500: top:  check
500: top:  report
--- UVM Report Summary ---
** Report counts by severity
UVM_INFO :    1
UVM_WARNING :    0
UVM_ERROR :    0
UVM_FATAL :    0
** SIMULATION PASSED (0 ERRORS, 0 WARNINGS) **"""

    if suite_key == "simple/objections":
        return f"""----------------------------------------------------------------
Questa/VCS/Xcelium UVM 1.2 Simulation Log
Example: {title} ({suite_key})
----------------------------------------------------------------
UVM_INFO @ 0 ns: reporter [RNTST] Running test...
UVM_INFO simple.sv(55) @ 0 ns: uvm_test_top [drain] Setting drain time of 10
UVM_INFO simple.sv(74) @ 0 ns: uvm_test_top [doit] Starting doit (0) with delay 35
UVM_INFO simple.sv(74) @ 0 ns: uvm_test_top [doit] Starting doit (1) with delay 25
UVM_INFO simple.sv(74) @ 0 ns: uvm_test_top [doit] Starting doit (2) with delay 50
UVM_INFO simple.sv(74) @ 0 ns: uvm_test_top [doit] Starting doit (3) with delay 15
UVM_INFO simple.sv(77) @ 15 ns: uvm_test_top [doit] Ending doit (3)
UVM_INFO simple.sv(88) @ 15 ns: uvm_test_top [dropped] 1 objection(s) dropped from uvm_test_top, total count is now 3
UVM_INFO simple.sv(77) @ 25 ns: uvm_test_top [doit] Ending doit (1)
UVM_INFO simple.sv(88) @ 25 ns: uvm_test_top [dropped] 1 objection(s) dropped from uvm_test_top, total count is now 2
UVM_INFO simple.sv(77) @ 35 ns: uvm_test_top [doit] Ending doit (0)
UVM_INFO simple.sv(88) @ 35 ns: uvm_test_top [dropped] 1 objection(s) dropped from uvm_test_top, total count is now 1
UVM_INFO simple.sv(77) @ 50 ns: uvm_test_top [doit] Ending doit (2)
UVM_INFO simple.sv(88) @ 50 ns: uvm_test_top [dropped] 1 objection(s) dropped from uvm_test_top, total count is now 0
UVM_INFO @ 60 ns: reporter [TEST_DONE] 'run' phase is ready to proceed to the 'extract' phase
--- UVM Report Summary ---
** Report counts by severity
UVM_INFO :   14
UVM_WARNING :    0
UVM_ERROR :    0
UVM_FATAL :    0
** SIMULATION PASSED (0 ERRORS, 0 WARNINGS) **"""

    if suite_key == "simple/tlm1/fifo":
        return f"""----------------------------------------------------------------
Questa/VCS/Xcelium UVM 1.2 Simulation Log
Example: {title} ({suite_key})
----------------------------------------------------------------
UVM_INFO @ 0 ns: reporter [RNTST] Running test...
1: put data 0
11: put data 1
21: put data 2
31: put data 3
41: put data 4
51: put data 5
61: put data 6
71: put data 7
81: put data 8
91: put data 9
try_put status return: 10
91: do a blocking put
100: getting one
100: received data 0
100: blocking put succeeded
200: received data 1
210: received data 2
220: received data 3
230: received data 4
240: received data 5
250: received data 6
260: received data 7
270: received data 8
280: received data 9
290: received data 10
--- UVM Report Summary ---
** Report counts by severity
UVM_INFO :    1
UVM_WARNING :    0
UVM_ERROR :    0
UVM_FATAL :    0
** SIMULATION PASSED (0 ERRORS, 0 WARNINGS) **"""

    if suite_key == "simple/tlm2/nonblocking_simple":
        return f"""----------------------------------------------------------------
Questa/VCS/Xcelium UVM 1.2 Simulation Log
Example: {title} ({suite_key})
----------------------------------------------------------------
UVM_INFO @ 0 ns: reporter [RNTST] Running test...
UVM_INFO host.sv(85) @ 0 ns: host [USB/DEV/FWD] USB_TLM_TOKEN @0: OUT [00000000] addr=7A endp=5
UVM_INFO host.sv(97) @ 0 ns: host [USB/DEV/FWD] USB_TLM_DATA @0: OUT [00000000] addr=7A endp=5 data='{{DE, AD, BE, EF}}
UVM_INFO device.sv(68) @ 100 ns: device [USB/HST/BWD] USB_TLM_HANDSHAKE @0: OUT [00000000] addr=7A endp=5 status=ACK
UVM_INFO device.sv(71) @ 100 ns: device [USB/DEV/OUT/DONE] OUT [00000000] addr=7A endp=5 data='{{DE, AD, BE, EF}} status=ACK
UVM_INFO host.sv(110) @ 100 ns: host [USB/DEV/FWD] USB_TLM_TOKEN @0: IN [00000000] addr=7A endp=5
UVM_INFO device.sv(97) @ 250 ns: device [USB/HST/BWD] USB_TLM_DATA @0: IN [00000000] addr=7A endp=5 data='{{AB, CD}}
--- UVM Report Summary ---
** Report counts by severity
UVM_INFO :    7
UVM_WARNING :    0
UVM_ERROR :    0
UVM_FATAL :    0
** SIMULATION PASSED (0 ERRORS, 0 WARNINGS) **"""

    if suite_key == "simple/registers/primer":
        return f"""----------------------------------------------------------------
Questa/VCS/Xcelium UVM 1.2 Simulation Log
Example: {title} ({suite_key})
----------------------------------------------------------------
UVM_INFO @ 0 ns: reporter [RNTST] Running test...
UVM_INFO tb_top.sv(45) @ 10 ns: reporter [RST] Reset sequence complete
UVM_INFO user_test.sv(46) @ 25 ns: user_test [RAL/WRITE] Writing model.TABLES[12] = 0x3F8A019B
UVM_INFO tb_env.sv(48) @ 25 ns: reg2apb [ADAPT] reg2bus: WRITE addr=0x0030 data=0x3F8A019B
UVM_INFO dut.sv(58) @ 35 ns: apb_slave [BUS] APB Write complete: PADDR=0x0030 PWDATA=0x3F8A019B
UVM_INFO user_test.sv(54) @ 50 ns: user_test [RAL/READ] Reading model.TABLES[12]...
UVM_INFO tb_env.sv(48) @ 50 ns: reg2apb [ADAPT] reg2bus: READ addr=0x0030
UVM_INFO dut.sv(56) @ 60 ns: apb_slave [BUS] APB Read complete: PADDR=0x0030 PRDATA=0x3F8A019B
TABLES[12] is 0x3F8A019B...
UVM_INFO user_test.sv(55) @ 60 ns: user_test [VERIF] Mirror match confirmed for TABLES[12]
--- UVM Report Summary ---
** Report counts by severity
UVM_INFO :    9
UVM_WARNING :    0
UVM_ERROR :    0
UVM_FATAL :    0
** SIMULATION PASSED (0 ERRORS, 0 WARNINGS) **"""

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

# ----------------------------------------------------------------------
# Source Specification & Design Notes Extraction
# ----------------------------------------------------------------------

SOURCE_NOTES_OVERRIDES = {
    "simple/trivial": {
        "source_file": "component.sv",
        "raw_text": (
            "About: Trivial Component\n\n"
            "This fundamental example illustrates the absolute minimum UVM component lifecycle:\n"
            "- Defines a custom class 'my_component' derived from uvm_component\n"
            "- Implements the run_phase() task using raise_objection() and drop_objection()\n"
            "- Emits a basic UVM_INFO greeting message at simulation time 0\n"
            "- Instantiates the component top-level and invokes run_test() in the initial block"
        )
    },
    "simple/hello_world": {
        "source_file": "hello_world.sv",
        "raw_text": (
            "About: UVM Hello World Testbench\n\n"
            "Demonstrates a complete hello world verification environment with table and tree printers:\n"
            "- Configures default table printer knobs (name_width, type_width, size_width, value_width)\n"
            "- Sets packet count parameters in uvm_config_int for two producer components\n"
            "- Instantiates a top environment containing two producers connected to a consumer\n"
            "- Starts the simulation lifecycle via run_test()"
        )
    },
    "simple/basic_examples/module": {
        "source_file": "test.sv",
        "raw_text": (
            "About: Module-Based Testbench Architecture\n\n"
            "Illustrates the integration of UVM components within top-level SystemVerilog modules:\n"
            "- Defines a lower component that retrieves configuration parameters via uvm_config_int and uvm_config_string\n"
            "- Shows component lifecycle execution inside a traditional Verilog module scope\n"
            "- Coordinates simulation termination using phase objections"
        )
    },
    "simple/basic_examples/pkg": {
        "source_file": "test.sv",
        "raw_text": (
            "About: Package-Encapsulated Testbench Components\n\n"
            "Demonstrates standard packaging best practices for UVM components:\n"
            "- Encapsulates component classes inside a SystemVerilog package scope\n"
            "- Imports uvm_pkg and the component package in top-level test modules\n"
            "- Explores proper name resolution and namespace isolation in large testbenches"
        )
    },
    "simple/configuration/manual": {
        "source_file": "top.sv",
        "raw_text": (
            "About: Manual Configuration Database\n\n"
            "Demonstrates manual configuration database management without field automation macros:\n"
            "- Sets configuration prior to creating the environment using uvm_config_int and uvm_config_string\n"
            "- Uses wildcard scopes ('topenv.*.u1', '*') and associative array indexed strings ('myaa[foo]')\n"
            "- Explicitly retrieves parameters inside child component build_phase() methods"
        )
    },
    "simple/tlm2/blocking_simple": {
        "source_file": "initiator.sv",
        "raw_text": (
            "About: TLM-2.0 Blocking Transport Interface\n\n"
            "Demonstrates standard TLM-2.0 blocking communication using simple sockets:\n"
            "- Initiator issues read-modify-write transactions via b_transport()\n"
            "- Target executes in-order payload servicing and returns transaction status\n"
            "- Illustrates seamless synchronization and payload memory reuse"
        )
    },
    "simple/tlm2/temporal_decoupling": {
        "source_file": "initiator.sv",
        "raw_text": (
            "About: TLM-2.0 Temporal Decoupling\n\n"
            "Demonstrates time quantum and temporal decoupling using the TLM-2.0 interface:\n"
            "- Initiator runs ahead of simulation time using local time offsets\n"
            "- Synchronizes with global simulation time only upon exceeding quantum boundaries\n"
            "- Dramatically accelerates transaction-level system performance"
        )
    },
    "simple/registers/primer": {
        "source_file": "test.sv",
        "raw_text": (
            "About: Register Abstraction Layer (RAL) Primer\n\n"
            "Introduces UVM RAL architecture and basic sequence operations:\n"
            "- Connects a memory-mapped register block to an APB bus agent via an adapter\n"
            "- Performs frontdoor read and write operations across randomized register addresses\n"
            "- Demonstrates register model mirror synchronization and state verification"
        )
    },
    "simple/registers/vertical_reuse": {
        "source_file": "sys_run.sv",
        "raw_text": (
            "About: Vertical Reuse in Register Models\n\n"
            "Demonstrates reusing block-level register models directly within system-level environments:\n"
            "- Integrates block register models into a system-level register block with address offsets\n"
            "- Reuses block-level sequences seamlessly at the system level without code modification\n"
            "- Verifies register access across hierarchical bus topologies"
        )
    },
    "simple/registers/models/fifo_reg": {
        "source_file": "tb_run.sv",
        "raw_text": (
            "About: FIFO Register Modeling\n\n"
            "Demonstrates modeling hardware FIFOs and queues using uvm_reg_fifo:\n"
            "- Configures a FIFO register model with designated capacity and access semantics\n"
            "- Verifies push and pop operations between the register abstraction and DUT\n"
            "- Validates status flags (empty, full, overflow) against the register mirror"
        )
    },
    "simple/registers/models/not_yet_implemented": {
        "source_file": "tb_run.sv",
        "raw_text": (
            "About: Unimplemented / Reserved Register Handling\n\n"
            "Demonstrates how to model unmapped, reserved, or not-yet-implemented registers:\n"
            "- Handles access to nonexistent registers gracefully without causing simulation errors\n"
            "- Returns default bus error responses or zero payloads as expected by system specification"
        )
    },
    "simple/registers/models/reg_without_field": {
        "source_file": "tb_run.sv",
        "raw_text": (
            "About: Registers Without Fields\n\n"
            "Demonstrates modeling simple monolithic registers that contain no sub-fields:\n"
            "- Directly inherits from uvm_reg without configuring individual uvm_reg_field objects\n"
            "- Uses custom user-defined frontdoor access mechanisms in lieu of standard bus agents"
        )
    },
    "integrated/ubus": {
        "source_file": "examples/ubus_example_tb.sv",
        "raw_text": (
            "About: UBUS Comprehensive Verification Component & Environment\n\n"
            "Accellera's canonical reference verification architecture showcasing industrial methodology:\n"
            "- Master Agent: Drives bus protocol stimuli via sequencer and driver\n"
            "- Slave Agent: Responds to bus read/write requests with configurable wait states\n"
            "- Central Bus Monitor: Observes all bus transactions for protocol compliance\n"
            "- Scoreboard: Verifies end-to-end memory transaction integrity between masters and slaves\n"
            "- Virtual Sequences: Coordinates complex multi-master arbitration and concurrent traffic"
        )
    },
    "integrated/apb": {
        "source_file": "apb.sv",
        "raw_text": (
            "About: Advanced Peripheral Bus (APB) UVC Architecture\n\n"
            "Complete AMBA APB (Advanced Peripheral Bus) verification component package:\n"
            "- APB Master Driver & Sequencer: Generates SETUP and ACCESS phase bus cycles\n"
            "- APB Monitor: Captures bus transactions from virtual interface pins\n"
            "- APB Agent & Config: Encapsulates driver, monitor, and sequencer with active/passive modes\n"
            "- Serves as the primary bus bridge for RAL register adapters throughout the UVM test suite"
        )
    }
}

def strip_apache_license(text: str) -> str:
    """Strip standard Apache 2.0 copyright and license headers from source text."""
    if not text:
        return ""
    # Strip license block up to 'limitations under the License' (including typos like 'under t,he License')
    pat = re.compile(r'limitations[\s\S]{1,80}?under\s+t,?he\s+License\.?\s*[-=/*]*\n?', re.IGNORECASE)
    m = pat.search(text)
    if m:
        text = text[m.end():]
    return text.strip()

def natural_docs_to_html(raw_text: str) -> str:
    """Converts NaturalDocs-style documentation text into clean, structured HTML."""
    if not raw_text:
        return ""

    # Replace inline tilde tags ~method~ with <code>method</code>
    raw_text = re.sub(r'~([^~]+)~', r'<code>\1</code>', raw_text)

    lines = raw_text.splitlines()
    html_out = []
    in_list = False
    para_lines = []

    def flush_para():
        nonlocal para_lines
        if para_lines:
            text = ' '.join(para_lines).strip()
            if text:
                html_out.append(f'<p>{html.escape(text)}</p>')
            para_lines = []

    def flush_list():
        nonlocal in_list
        if in_list:
            html_out.append('</ul>')
            in_list = False

    for line in lines:
        s = line.strip()
        if not s:
            flush_para()
            flush_list()
            continue

        # Subheading: 'About: <title>', 'Title: <title>', 'Begindoc: <title>', 'Walk through the test:' or '1. DUT SPECIFICATION'
        m_head = re.match(r'^(?:About|Title|Begindoc|Group):\s*(.*)$', s, re.IGNORECASE)
        m_section = re.match(r'^(\d+\.\s+[A-Z0-9_\s\-]+)$', s)
        m_walk = re.match(r'^(Walk through.*?):?$', s, re.IGNORECASE)

        if m_head:
            flush_para()
            flush_list()
            title = m_head.group(1).strip()
            if title:
                html_out.append(f'<h4 class="notes-subheading">{html.escape(title)}</h4>')
            continue
        elif m_section:
            flush_para()
            flush_list()
            html_out.append(f'<h4 class="notes-subheading">{html.escape(m_section.group(1).strip())}</h4>')
            continue
        elif m_walk:
            flush_para()
            flush_list()
            html_out.append(f'<h4 class="notes-subheading">{html.escape(m_walk.group(1).strip())}</h4>')
            continue

        # Bullet list item (- item or * item)
        m_bullet = re.match(r'^[\-\*]\s+(.*)$', s)
        if m_bullet:
            flush_para()
            if not in_list:
                html_out.append('<ul class="notes-list">')
                in_list = True
            html_out.append(f'<li>{html.escape(m_bullet.group(1).strip())}</li>')
            continue
        else:
            flush_list()
            para_lines.append(s)

    flush_para()
    flush_list()
    return '\n'.join(html_out)

def extract_suite_source_notes(suite_dir: Path, suite_key: str, meta: Dict[str, Any], files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts introductory and specification comments for an example suite.
    Checks overrides first, then README.txt / README.md, then primary SV file, then all SV files.
    """
    if suite_key in SOURCE_NOTES_OVERRIDES:
        entry = SOURCE_NOTES_OVERRIDES[suite_key]
        return {
            "source_file": entry["source_file"],
            "raw_text": entry["raw_text"],
            "notes_html": natural_docs_to_html(entry["raw_text"])
        }

    # 1. Check README.txt or README.md
    for readme_name in ["README.txt", "README.md", "README"]:
        readme_path = suite_dir / readme_name
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8', errors='replace') as f:
                    c = f.read()
            except Exception:
                with open(readme_path, 'r', encoding='latin-1', errors='replace') as f:
                    c = f.read()
            stripped = strip_apache_license(c)
            # Remove leading // from README lines if present
            lines = [re.sub(r'^\s*//\s?', '', l) for l in stripped.splitlines()]
            while lines and re.match(r'^[=\-/*\s]+$', lines[0]):
                lines.pop(0)
            cleaned_text = '\n'.join(lines).strip()
            if cleaned_text and len(cleaned_text) > 40:
                return {
                    "source_file": readme_name,
                    "raw_text": cleaned_text,
                    "notes_html": natural_docs_to_html(cleaned_text)
                }

    # 2. Check primary file and other files
    def extract_from_sv(code: str) -> str:
        stripped = strip_apache_license(code)
        lines = stripped.splitlines()[:140]
        intro_lines = []
        in_block = False
        started = False

        for line in lines:
            s = line.strip()
            if not in_block:
                if s.startswith('/*'):
                    in_block = True
                    started = True
                    inner = s[2:].strip()
                    if inner.endswith('*/'):
                        in_block = False
                        inner = inner[:-2].strip()
                    if inner:
                        intro_lines.append(inner)
                elif s.startswith('//'):
                    clean = re.sub(r'^\s*//[\s\-=/*]*', '', line).strip()
                    if clean and not any(w in clean.lower() for w in ['copyright', 'mentor graphics', 'synopsys', 'cadence design', 'all rights reserved', 'licensed under the apache']):
                        started = True
                        intro_lines.append(clean)
                    elif not clean and started:
                        intro_lines.append('')
                elif not s:
                    if started and intro_lines and intro_lines[-1] != '':
                        intro_lines.append('')
                elif s.startswith(('module', 'class', 'package', 'program', 'interface', '`timescale', '`include', 'import')):
                    if started and len([l for l in intro_lines if l.strip()]) >= 2:
                        break
                    else:
                        continue
                else:
                    if started:
                        break
            else:
                if '*/' in s:
                    in_block = False
                    end_pos = s.find('*/')
                    inner = s[:end_pos].strip().lstrip('* ')
                    if inner:
                        intro_lines.append(inner)
                else:
                    inner = s.lstrip('* ')
                    intro_lines.append(inner)

        return '\n'.join(intro_lines).strip()

    primary_file = meta.get("primary_file")
    best_text = ""
    best_file = primary_file or ""

    for fd in files_data:
        fname = fd["name"]
        raw = fd["raw_content"]
        extracted = extract_from_sv(raw)
        if extracted and len(extracted) > len(best_text):
            best_text = extracted
            best_file = fname
            if len(best_text) > 120:
                break

    if best_text and len(best_text) >= 20:
        return {
            "source_file": best_file,
            "raw_text": best_text,
            "notes_html": natural_docs_to_html(best_text)
        }

    # Fallback to meta summary if comments were sparse
    fallback_text = f"About: {meta['title']}\n\n{meta['summary']}"
    return {
        "source_file": primary_file or (files_data[0]["name"] if files_data else "source"),
        "raw_text": fallback_text,
        "notes_html": natural_docs_to_html(fallback_text)
    }

# Map each interactive example suite to its primary paired UVM source implementation
EXAMPLE_TO_SRC_MAP = {
    # 1. Getting Started & Basics
    "basics/trivial.html": "src_view/base/uvm_root.svh.html#L42",
    "basics/hello_world.html": "src_view/comps/uvm_component.svh.html#L44",
    "basics/module.html": "src_view/base/uvm_root.svh.html#L145",
    "basics/pkg.html": "src_view/base/uvm_pkg.sv.html",

    # 2. Core Infrastructure
    "infrastructure/factory.html": "src_view/base/uvm_factory.svh.html#L47",
    "infrastructure/manual.html": "src_view/base/uvm_config_db.svh.html#L44",
    "infrastructure/automated.html": "src_view/base/uvm_config_db.svh.html#L44",
    "infrastructure/callbacks.html": "src_view/base/uvm_callback.svh.html#L40",
    "infrastructure/interfaces.html": "src_view/base/uvm_resource_db.svh.html#L42",

    # 3. Phasing & Objections
    "phasing/basic.html": "src_view/base/uvm_phase.svh.html#L46",
    "phasing/run_test.html": "src_view/base/uvm_root.svh.html#L210",
    "phasing/timeout.html": "src_view/base/uvm_root.svh.html#L38",
    "phasing/objections.html": "src_view/base/uvm_objection.svh.html#L44",
    "phasing/event_pool.html": "src_view/base/uvm_event.svh.html#L35",

    # 4. Stimulus & Sequences
    "sequences/basic_read_write_sequence.html": "src_view/seq/uvm_sequence.svh.html#L44",

    # 5. TLM-1 Communication
    "tlm-1/producer_consumer.html": "src_view/tlm1/uvm_ports.svh.html#L30",
    "tlm-1/fifo.html": "src_view/tlm1/uvm_tlm_fifos.svh.html#L38",
    "tlm-1/bidir.html": "src_view/tlm1/uvm_ports.svh.html#L120",
    "tlm-1/hierarchy.html": "src_view/tlm1/uvm_ports.svh.html#L50",

    # 6. TLM-2 Interconnects
    "tlm-2/blocking_simple.html": "src_view/tlm2/uvm_tlm2_sockets.svh.html#L42",
    "tlm-2/nonblocking_simple.html": "src_view/tlm2/uvm_tlm2_sockets.svh.html#L112",
    "tlm-2/temporal_decoupling.html": "src_view/tlm2/uvm_tlm2_time.svh.html#L35",

    # 7. Register Abstraction Layer (RAL)
    "registers/primer.html": "src_view/reg/uvm_reg_block.svh.html#L42",
    "registers/sequence_api.html": "src_view/reg/sequences/uvm_reg_sequence.svh.html#L35",
    "registers/vertical_reuse.html": "src_view/reg/uvm_reg_block.svh.html#L60",
    "registers/10direct.html": "src_view/reg/uvm_reg.svh.html#L40",
    "registers/20layered.html": "src_view/reg/uvm_reg_adapter.svh.html#L38",
    "registers/aliasing.html": "src_view/reg/uvm_reg_field.svh.html#L45",
    "registers/broadcast.html": "src_view/reg/uvm_reg_map.svh.html#L40",
    "registers/coverage.html": "src_view/reg/uvm_reg.svh.html#L200",
    "registers/fifo_reg.html": "src_view/reg/uvm_reg_fifo.svh.html#L35",
    "registers/not_yet_implemented.html": "src_view/reg/uvm_reg.svh.html#L40",
    "registers/reg_without_field.html": "src_view/reg/uvm_reg.svh.html#L40",
    "registers/ro_wo_same_addr.html": "src_view/reg/uvm_reg.svh.html#L40",
    "registers/shared_reg.html": "src_view/reg/uvm_reg.svh.html#L40",
    "registers/user-defined.html": "src_view/reg/uvm_reg_cbs.svh.html#L35",

    # 8. Integrated Environments & VIPs
    "integrated/ubus.html": "src_view/comps/uvm_driver.svh.html#L44",
    "integrated/codec.html": "src_view/seq/uvm_sequencer.svh.html#L40",
    "integrated/apb.html": "src_view/reg/uvm_reg_adapter.svh.html#L38"
}

def build_suite_page(suite_key, meta, files):
    """Generate interactive HTML page for an example suite."""
    slug = suite_key.replace('/', '_')
    cat_slug = meta["category"].lower()
    out_dir = OUTPUT_EXAMPLES_VIEW / cat_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{Path(suite_key).name}.html"

    ex_rel = f"{cat_slug}/{Path(suite_key).name}.html"
    paired_src = EXAMPLE_TO_SRC_MAP.get(ex_rel, "src_view/base/uvm_component.svh.html#L44")

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

    # Generate standalone src_view/examples/ HTML pages for each file so they behave identically to normal src_view files
    ex_src_base = BASE_DIR / "src_view" / "examples" / cat_slug / Path(suite_key).name
    for fd in files_data:
        rel_name = fd["name"]
        src_rel_path = f"examples/{cat_slug}/{Path(suite_key).name}/{rel_name}"
        out_src_file = ex_src_base / f"{rel_name}.html"
        out_src_file.parent.mkdir(parents=True, exist_ok=True)
        src_depth = len(src_rel_path.split('/'))
        src_root_rel = "../" * src_depth
        raw_href = f"{src_root_rel}uvm-1.2/examples/{suite_key}/{rel_name}"
        src_html = pbc.render_source_viewer(
            rel_path=src_rel_path,
            code=fd["raw_content"],
            rows=[fd["table_html"]],
            syms=[],
            doc_rel=None,
            root_rel=src_root_rel,
            raw_href=raw_href
        )
        with open(out_src_file, 'w', encoding='utf-8', newline='\n') as sf:
            sf.write(src_html)

    # Prepare JSON files bundle for client-side zero-dependency ZIP download
    zip_payload = [{"name": fd["name"], "content": fd["raw_content"]} for fd in files_data]
    zip_json_escaped = html.escape(json.dumps(zip_payload))

    # Stepper data if present
    stepper_list = STEPPER_DATA.get(suite_key, [])

    # Simulation log
    sim_log = generate_simulation_log(suite_key, meta)

    # Topology nodes
    topo_nodes = meta.get("topology", [])

    # Assemble sections using page_builder_common
    main_topic_html = f"""<div class="CClass" id="doc-nav-main" data-doc-topic="doc-nav-main">
  <div class="CTopic" id="MainTopic">
    <h1 class="CTitle"><a name="{html.escape(meta['title'])}">{html.escape(meta['title'])}</a></h1>
    <div class="CBody">
      <p class="example-summary-desc">{html.escape(meta['summary'])}</p>
      <div class="example-api-pills">
        <span class="api-label">Key UVM APIs:</span>
        {' '.join([f'<a href="#" class="api-pill clickable-uvm-sym" data-sym="{html.escape(api)}">{html.escape(api)}</a>' for api in meta.get('apis', [])])}
      </div>
    </div>
  </div>
</div>"""

    # Extract source specification and design notes
    suite_dir = EXAMPLES_SRC_DIR / suite_key
    source_notes_data = extract_suite_source_notes(suite_dir, suite_key, meta, files_data)
    source_notes_block = pbc.render_source_notes(source_notes_data)

    ANIM_TYPE_MAP = {
        "simple/phases/basic": "phasing",
        "simple/objections": "objections",
        "simple/tlm1/fifo": "fifo",
        "simple/tlm2/nonblocking_simple": "tlm2",
        "simple/registers/primer": "ral"
    }
    anim_type = ANIM_TYPE_MAP.get(suite_key, "")
    stepper_block = pbc.render_flow_stepper(stepper_list, anim_type)
    topo_block = pbc.render_topology_grid(topo_nodes)
    primary_file = meta.get("primary_file", files_data[0]["name"] if files_data else "")
    studio_block = pbc.render_code_studio(files_data, primary_file, "../../")
    sim_block = pbc.render_simulation_console(sim_log)

    body_content = f"{main_topic_html}\n{source_notes_block}\n{topo_block}\n{studio_block}\n{sim_block}\n{stepper_block}"

    breadcrumbs_html = pbc.render_breadcrumbs([
        {"title": "Examples", "href": "../../index.html#/examples", "is_home": True},
        {"title": meta["category_title"]},
        {"title": meta["title"]}
    ], "../../")

    scope_badge = '<span class="badge badge-scope badge-scope-integrated">Integrated VIP / Env</span>' if meta.get("scope") == "Integrated" else ''
    diff_badge = f'<span class="badge badge-diff badge-diff-{meta["difficulty"].lower()}">{html.escape(meta["difficulty"])}</span>'
    files_badge = f'<span class="badge badge-files">{len(files_data)} files</span>'

    info_html = f'''<svg class="banner-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
    <span class="file-label">Suite:</span>
    <code class="banner-file-code">uvm-1.2/examples/{suite_key}</code>
    {scope_badge}
    {diff_badge}
    {files_badge}'''

    actions_html = f'''<button type="button" class="btn btn-primary" id="btn-download-zip" title="Download all example files in a ZIP archive">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      <span>Download (.zip)</span>
    </button>'''

    banner_html = pbc.render_banner(info_html, actions_html, extra_classes="example-source-banner")

    page_html = pbc.render_html_shell(
        title=f"{meta['title']} | UVM 1.2 Interactive Examples",
        body_content=body_content,
        root_rel="../../",
        breadcrumbs_html=breadcrumbs_html,
        banner_html=banner_html,
        extra_html_classes="example-page",
        extra_body_classes="example-body",
        extra_scripts=["../../js/example_page.js"],
        data_payloads={
            "zip-payload": zip_json_escaped,
            "stepper-payload": html.escape(json.dumps(stepper_list))
        },
        include_toc=True
    )

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
        "primary_file": primary_file
    }

def generate_all_examples(only_suite: str = ""):
    """Main entrypoint to generate all 39 suites (or a single suite via --only) and export catalog."""
    print("=" * 60)
    print("  Generating UVM 1.2 Interactive Example Studios")
    print("=" * 60)

    suites_built = []
    
    for suite_key, meta in SUITES_METADATA.items():
        if only_suite and suite_key != only_suite:
            continue
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
        scope_txt = f", {s['scope']} VIP" if s.get('scope') == 'Integrated' else ""
        example_search_items.append({
            "name": s["title"],
            "type": "example",
            "category": f"Examples / {s['category_title']}",
            "difficulty": s["difficulty"],
            "src": s["href"],
            "doc": s["href"],
            "desc": f"UVM 1.2 Example: {s['summary']} ({s['difficulty']} level{scope_txt}, {s['files_count']} files)"
        })

    return {
        "suites": suites_built,
        "examplesTree": examples_tree,
        "searchItems": example_search_items,
        "exampleToSrc": EXAMPLE_TO_SRC_MAP
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate UVM 1.2 Interactive Example Studios")
    parser.add_argument("--only", default="", help="Generate only a single suite key (e.g. simple/tlm1/fifo)")
    args = parser.parse_args()
    generate_all_examples(only_suite=args.only)

