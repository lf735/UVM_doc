#!/usr/bin/env python3
"""
UVM 1.2 Progressive Tutorial Curriculum — Part I (Chapters 1 to 6) & Registry.
Defines chapter metadata, Markdown course content (with Mermaid diagrams),
Cytoscape interactive graphs, verified UVM 1.2 doc/example cross-links,
quizzes, calibrated simulation logs, and step-by-step walkthrough scenarios.
"""

from typing import Dict, List, Any


def _doc(label: str, path: str, desc: str = "") -> Dict[str, str]:
    return {"label": label, "url": f"docs_view/{path}", "desc": desc}


def _ex(label: str, path: str, desc: str = "") -> Dict[str, str]:
    return {"label": label, "url": f"examples_view/{path}", "desc": desc}


CHAPTERS_PART_1: List[Dict[str, Any]] = [
    # =========================================================================
    # CHAPTER 1: Verification Fundamentals, V-Cycle & Role Split
    # =========================================================================
    {
        "num": 1,
        "slug": "ch01_verification_vcycle",
        "part": "Foundations",
        "part_title": "I. Verification Foundations & Methodology",
        "title": "01. Verification Fundamentals, V-Cycle & Role Split",
        "short_title": "01. V-Cycle & Team Roles",
        "difficulty": "Beginner",
        "src_dir": None,
        "inherit_from": None,
        "summary": (
            "Understand why verification consumes 60-70% of ASIC/FPGA project effort, how the hardware V-Cycle "
            "connects specification to sign-off, and how responsibilities split cleanly across the System Architect, "
            "RTL Designer, and Verification Engineer."
        ),
        "apis": ["uvm_test", "uvm_env", "uvm_agent", "uvm_component"],
        "objectives": [
            "Explain the purpose of functional verification versus RTL design and why self-verification creates blind spots.",
            "Map every phase of the hardware V-Cycle from Architecture Specification down to RTL and back up to Sign-Off.",
            "Define the exact deliverables and handoff contracts between System Architect, RTL Designer, and Verifier.",
            "Understand how a Verification Plan (vPlan) connects architectural features to measurable UVM coverage closure."
        ],
        "interactive_widget": "vcycle",
        "docs_links": [
            _doc("UVM 1.2 Introduction", "overviews/intro-txt.html", "High-level UVM goals, reuse model, and class library overview."),
            _doc("UVM Components Overview", "overviews/components-txt.html", "Role of structured hierarchical components in scalable verification."),
            _doc("uvm_test", "comps/uvm_test-svh.html#uvm_test", "Top-level test class configuring environments and scenarios."),
            _doc("uvm_env", "comps/uvm_env-svh.html#uvm_env", "Reusable verification environment container."),
        ],
        "example_links": [
            _ex("Trivial Component", "basics/trivial.html", "Smallest possible UVM component lifecycle."),
        ],
        "markdown_body": """
## 1.1 Why Verification Exists (And Why Designers Don't Verify Their Own RTL)

In modern ASIC and FPGA projects, **verification typically accounts for 60% to 70% of engineering time and compute resources**. The objective is fundamentally asymmetric compared to hardware design:

- **RTL Design** builds a *specific* hardware micro-architecture that satisfies timing, area, and power budgets.
- **Functional Verification** tries to *break* that implementation under every legal (and illegal) sequence of inputs, corner cases, backpressure stalls, and register configurations before tape-out.

> **Golden Rule of Independent Verification:** Never verify a block solely using the same mental assumptions used to design it. If a designer misreads an ambiguous sentence in a specification, writing both the RTL and the testbench perpetuates the exact same bug in both places.

---

## 1.2 The Hardware V-Cycle

The **V-Cycle** models how abstraction descends from system requirements down to synthesizable SystemVerilog RTL (left leg), and then climbs back up through block, subsystem, and SoC verification to tape-out sign-off (right leg).

```mermaid
flowchart LR
    S1["System Spec (Architect)"] --> S2["Micro-Arch (Designer)"]
    S2 --> S3["RTL Coding (Designer)"]
    S3 --> V1["vPlan & Block TB (Verifier)"]
    V1 --> V2["Block Closure (Verifier)"]
    V2 --> V3["SoC Reuse & Sign-Off (All)"]
    S1 -. "Requirement Traceability" .-> V3
    S2 -. "Corner-Case Review" .-> V1
```

Each descending step creates a **specification contract**, and each ascending step validates that contract independently:

1. **System Specification -> Verification Plan (vPlan):** Every architectural requirement (e.g., *"saturate arithmetic overflow when `CTRL.SAT_EN=1`"*) receives a unique requirement ID mapped to stimulus scenarios, assertions, and coverage bins.
2. **Micro-Architecture -> Corner-Case Checklist:** Pipeline hazards, FIFO full/empty transitions, reset synchronization, and bus wait-states are translated into constrained-random constraints and SVA properties.
3. **RTL Freeze -> Block UVM Verification:** Once port lists and protocols stabilize, the Verification Engineer exercises the DUT inside an automated self-checking UVM testbench.
4. **Block Closure -> Subsystem / SoC Vertical Reuse:** Clean UVM environments switch their block agents from `UVM_ACTIVE` to `UVM_PASSIVE` so the exact same scoreboard and coverage collectors keep checking inside full-chip simulations.

---

## 1.3 Role Split: Architect vs. Designer vs. Verifier

| Responsibility | System Architect | RTL Designer | Verification Engineer |
| :--- | :--- | :--- | :--- |
| **Primary Artifact** | System Spec, Memory/Register Map (IP-XACT), Interface Specs | Synthesizable RTL (`pkt_alu.sv`), Lint/CDC-clean code | vPlan, UVM Testbench, Reference Model, Coverage & Sign-off Report |
| **Mental Model** | *What* the IP must do externally (protocols, throughput, registers) | *How* silicon implements it cycle-by-cycle (FSMs, flops, muxes) | *How it could fail* (races, stalls, overflow, reset, illegal sequences) |
| **Interface Ownership** | Defines bus protocol & register reset values | Implements RTL pins & timing constraints | Writes `interface` + SVA assertions + BFM Driver/Monitor |
| **Debug Ownership** | Resolves spec ambiguities | Fixes confirmed RTL bugs & updates waveforms | Triages failures, distinguishes TB vs RTL bugs, closes coverage holes |
| **Sign-Off Gate** | Confirms architectural intent | Confirms synthesis/lint/CDC clean | Confirms 0 errors, 100% functional + code coverage closure |

Explore the **Interactive V-Cycle & Role Matrix** below to inspect every stage, deliverable, and handoff contract.
""",
        "quizzes": [
            {
                "q": "Why should the RTL designer and verification engineer work from an independent interpretation of the architecture spec?",
                "options": [
                    "To double the amount of SystemVerilog code written on the project",
                    "To prevent identical spec misinterpretations from hiding bugs in both RTL and testbench",
                    "Because UVM forbids RTL modules from being compiled in the same simulator"
                ],
                "answer": 1,
                "explanation": "Independent testbench modeling catches spec ambiguities and implementation assumptions that a single author would replicate in both RTL and test."
            },
            {
                "q": "Which document links the System Architect's requirements on the left side of the V-Cycle to measurable UVM closure on the right side?",
                "options": [
                    "Makefile.questa",
                    "The Verification Plan (vPlan)",
                    "The RTL synthesis netlist"
                ],
                "answer": 1,
                "explanation": "The vPlan maps every architectural feature and corner case to specific stimuli, checkers/assertions, and functional coverage targets."
            }
        ],
    },

    # =========================================================================
    # CHAPTER 2: Verification Principles — Stimuli, Checks & Metrics
    # =========================================================================
    {
        "num": 2,
        "slug": "ch02_verification_principles",
        "part": "Foundations",
        "part_title": "I. Verification Foundations & Methodology",
        "title": "02. Core Verification Principles: Stimuli, Checks & Metrics",
        "short_title": "02. Stimuli, Checks & Metrics",
        "difficulty": "Beginner",
        "src_dir": None,
        "inherit_from": None,
        "summary": (
            "Master the single most important architectural law of UVM: strictly decoupling Stimuli generation, "
            "functional Checking, and Coverage Metrics—and moving from pin-wiggling to Transaction-Level Modeling (TLM)."
        ),
        "apis": ["uvm_sequence", "uvm_driver", "uvm_monitor", "uvm_scoreboard", "uvm_subscriber", "uvm_analysis_port"],
        "objectives": [
            "Separate every testbench responsibility into three independent pillars: Stimuli, Checks, and Metrics.",
            "Recognize common verification anti-patterns (e.g., drivers checking DUT outputs or sequences inspecting pins).",
            "Understand why Transaction-Level Modeling (TLM) isolates high-level test intent from pin-level timing.",
            "Preview our running DUT thread: the pkt_alu Packet-ALU IP used across Chapters 3 through 13."
        ],
        "interactive_widget": "scm_matrix",
        "docs_links": [
            _doc("TLM-1 Overview", "overviews/tlm1-txt.html", "Decoupled component communication using ports, exports, and FIFOs."),
            _doc("Comparators Overview", "overviews/comparators-txt.html", "Automated expected vs. actual checking patterns."),
            _doc("uvm_analysis_port", "tlm1/uvm_analysis_port-svh.html#uvm_analysis_port", "One-to-many passive broadcast port from monitors to checkers and coverage."),
            _doc("uvm_subscriber", "comps/uvm_subscriber-svh.html#uvm_subscriber", "Dedicated base class for metrics and coverage listeners."),
        ],
        "example_links": [
            _ex("Hello World & TLM FIFO", "basics/hello_world.html", "Producer/consumer separation using TLM FIFO."),
        ],
        "markdown_body": """
## 2.1 The Three Pillars: Stimuli, Checks, and Metrics

Before writing a single line of UVM code, internalize the **Separation of Concerns** that makes a UVM testbench reusable from block level all the way to SoC:

```mermaid
flowchart LR
    SEQ["Stimuli: Sequence & Driver"] -->|"Pins (Valid/Ready)"| DUT["DUT (pkt_alu)"]
    DUT -->|"Pins (Observed)"| MON["Monitor (Passive Observer)"]
    MON -->|"analysis_port"| SCB["Checks: Scoreboard + Ref Model"]
    MON -->|"analysis_port"| COV["Metrics: Coverage Subscriber"]
    DUT -. "Protocol Timing" .-> SVA["Checks: Interface SVA"]
```

1. **Stimuli (What we inject):** `uvm_sequence_item`, `uvm_sequence`, `uvm_sequencer`, and `uvm_driver`. Their *only* job is to generate valid (or intentionally stressed/faulty) transactions and translate them to interface pins. **A driver must never decide whether the DUT passed or failed.**
2. **Checks (Is the DUT right?):** Interface **SVA** (pin-level protocol rules), passive **`uvm_monitor`** observers, a golden **Reference Model**, and **`uvm_scoreboard`**. Checkers observe *actual* pin activity passively—so they still work identically even when another master drives the DUT in an SoC (`UVM_PASSIVE` mode!).
3. **Metrics (Are we done yet?):** **`uvm_subscriber`** functional `covergroup`s, cover properties, and code coverage. Metrics observe *what actually crossed the DUT boundary* (not just what a sequence asked for!) so we know when the vPlan is truly closed.

---

## 2.2 Transaction-Level Modeling (TLM) vs. Pin-Wiggling

Legacy Verilog testbenches mixed everything inside `initial` blocks (`@(posedge clk); valid = 1; if (result !== 5) $error...`). That breaks immediately when protocols change or blocks integrate into larger chips.

UVM introduces two clean abstraction boundaries:
- **Above the Driver/Monitor:** Components exchange **SystemVerilog transaction objects** (`alu_item` with fields `op`, `a`, `b`, `tag`) over TLM ports. Sequences never toggle clock edges.
- **At the Virtual Interface:** Only the `uvm_driver` and `uvm_monitor` know about `clk`, `rst_n`, `in_valid`, `in_ready`, and clocking blocks.

---

## 2.3 Why Avoid Anti-Patterns?

| Anti-Pattern | What Breaks? | UVM Principle Violated |
| :--- | :--- | :--- |
| Checking DUT results inside `uvm_driver` | Fails completely in `UVM_PASSIVE` subsystem reuse when external RTL drives the bus. | Mixing **Stimuli** and **Checks** |
| Sampling `covergroup` inside `uvm_sequence` | Measures requested items, not what actually passed handshakes or survived callbacks/arbitration. | Mixing **Stimuli** and **Metrics** |
| Hardcoding `tb_top.u_dut.sig` in tests | Breaks hierarchy encapsulation and prevents running multiple instances in an SoC. | Violating **TLM & Virtual Interface** isolation |

---

## 2.4 Meet Our Running Example: `pkt_alu`

Throughout Chapters 3–13 we will verify **`pkt_alu`**, a realistic Packet-ALU IP built in two stages:
- **Chapters 3–6 (`pkt_alu_basic.sv`):** Streaming `Valid/Ready` input (`op`, `a`, `b`, `tag`) and output (`result`, `out_tag`, `err_flag`) with 1-cycle latency.
- **Chapters 7–13 (`pkt_alu.sv` + `pkt_alu_ref.c`):** Adds an **APB3 Register Interface** (`CTRL`, `STATUS`, `SAT_LIMIT`, `PKT_COUNT`, `ERR_INJECT`) for multi-agent virtual sequences, RAL register verification, TLM-2 sockets, and a compiled C/DPI-C golden reference model.
""",
        "quizzes": [
            {
                "q": "Where should functional coverage (`covergroup`) be sampled in a properly architected UVM testbench?",
                "options": [
                    "Inside the sequence right after req.randomize()",
                    "Inside a passive uvm_subscriber connected to the monitor's analysis_port",
                    "Inside tb_top's initial block"
                ],
                "answer": 1,
                "explanation": "Sampling from the monitor's analysis_port guarantees you measure transactions that actually occurred on the pins, independent of active/passive reuse."
            },
            {
                "q": "Why must a uvm_driver never verify DUT output correctness?",
                "options": [
                    "Because drivers do not have access to uvm_info macros",
                    "Because when reusing the agent in UVM_PASSIVE mode at SoC level, the driver is not instantiated",
                    "Because SystemVerilog forbids classes from reading output signals"
                ],
                "answer": 1,
                "explanation": "In passive subsystem/SoC reuse, only the monitor, scoreboard, and coverage collectors remain active—so checking must live outside the driver."
            }
        ],
    },

    # =========================================================================
    # CHAPTER 3: Minimal Stimuli Environment (Every Line Explained)
    # =========================================================================
    {
        "num": 3,
        "slug": "ch03_minimal_stimuli",
        "part": "Stimuli & Core",
        "part_title": "II. Stimuli & Core Testbench Infrastructure",
        "title": "03. Minimal Stimuli Environment: Every Piece Explained",
        "short_title": "03. Minimal Stimuli Env",
        "difficulty": "Beginner",
        "src_dir": "ch03_minimal_stimuli",
        "dut_files": ["dut/pkt_alu_basic.sv"],
        "inherit_from": None,
        "primary_file": "alu_minimal_test.sv",
        "summary": (
            "Build the smallest possible UVM stimuli environment—no agent, no env, no scoreboard yet—and dissect "
            "every single line: alu_if, uvm_sequence_item, uvm_sequence, uvm_sequencer, uvm_driver, uvm_config_db, "
            "run_test(), and phase objections."
        ),
        "apis": [
            "uvm_sequence_item", "uvm_sequence", "uvm_sequencer", "uvm_driver",
            "uvm_config_db", "uvm_objection", "run_test", "`uvm_object_utils", "`uvm_component_utils"
        ],
        "objectives": [
            "Connect a physical SystemVerilog interface (`alu_if`) to a UVM driver via `uvm_config_db#(virtual alu_if)`.",
            "Define a constrained-random transaction (`alu_item`) extending `uvm_sequence_item`.",
            "Implement the classic 4-step sequence/driver handshake: `start_item` / `finish_item` ↔ `get_next_item` / `item_done`.",
            "Control simulation lifetime deterministically with `phase.raise_objection()` and `phase.drop_objection()`."
        ],
        "interactive_widget": "arch_diff",
        "new_components": ["alu_item", "alu_smoke_seq", "alu_sequencer", "alu_driver", "alu_minimal_test", "alu_if", "pkt_alu_basic"],
        "docs_links": [
            _doc("uvm_sequence_item", "seq/uvm_sequence_item-svh.html#uvm_sequence_item", "Base class for sequence transactions."),
            _doc("uvm_sequence", "seq/uvm_sequence-svh.html#uvm_sequence", "Procedural stimulus generator via body()."),
            _doc("uvm_sequencer", "seq/uvm_sequencer-svh.html#uvm_sequencer", "Arbitrates and supplies items to driver via seq_item_export."),
            _doc("uvm_driver", "comps/uvm_driver-svh.html#uvm_driver", "Pulls items on seq_item_port and drives virtual interface pins."),
            _doc("uvm_config_db", "base/uvm_config_db-svh.html#uvm_config_db", "Passes virtual interface handle from tb_top module into UVM classes."),
            _doc("uvm_objection", "base/uvm_objection-svh.html#uvm_objection", "Keeps run_phase alive while stimulus executes."),
            _doc("uvm_globals (run_test)", "base/uvm_globals-svh.html", "Global run_test() entry point starting UVM phasing."),
        ],
        "example_links": [
            _ex("Trivial Component", "basics/trivial.html", "Minimal uvm_component & run_test()."),
            _ex("Virtual Interface Connection", "infrastructure/interfaces.html", "Bridging physical interfaces via uvm_config_db."),
            _ex("Basic Read/Write Sequence", "sequences/basic_read_write_sequence.html", "Sequence/driver handshake fundamentals."),
        ],
        "markdown_body": """
## 3.1 Stripping UVM Down to Pure Stimuli

Many beginners feel overwhelmed because tutorials throw `agent`, `env`, `factory`, `scoreboard`, and `RAL` at them on page 1. Here, we **intentionally start with zero checking and zero containers**: just the **5 essential stimuli pieces** wired inside `alu_minimal_test`.

```mermaid
sequenceDiagram
    participant Seq as alu_smoke_seq
    participant Sqr as uvm_sequencer
    participant Drv as alu_driver
    participant VIF as alu_if / DUT

    Seq->>Sqr: start_item(req)
    Sqr-->>Seq: grant
    Note over Seq: req.randomize() (late randomization!)
    Seq->>Sqr: finish_item(req)
    Drv->>Sqr: seq_item_port.get_next_item(req)
    Sqr-->>Drv: req
    Drv->>VIF: drive in_valid, op, a, b, tag
    VIF-->>Drv: in_ready == 1
    Drv->>Sqr: seq_item_port.item_done()
    Sqr-->>Seq: finish_item() unblocks
```

---

## 3.2 Anatomy of Every File in This Minimal Environment

1. **`alu_if.sv` (Physical & Clocking Bridge):**
   Wraps the wires connecting `tb_top` and `pkt_alu_basic`. Using a `clocking drv_cb @(posedge clk)` prevents SystemVerilog race conditions between RTL `always_ff` and testbench assignments.
2. **`alu_item.sv` (The Transaction):**
   Extends `uvm_sequence_item` (which inherits from `uvm_object`, *not* `uvm_component`—items are transient data created dynamically during simulation). Registers with `` `uvm_object_utils_begin `` and defines `rand` properties + constraints (`c_valid_op`, `c_operand_range`).
3. **`alu_seq.sv` (The Stimulus Recipe):**
   Extends `uvm_sequence #(alu_item)`. In `body()`, each item uses **late randomization**:
   - `start_item(req)` waits until the sequencer grants bus access,
   - `req.randomize()` solves constraints right when the driver is ready,
   - `finish_item(req)` hands the item to the driver and blocks until `item_done()`.
4. **`alu_driver.sv` (The Pin Wiggler):**
   Extends `uvm_driver #(alu_item)`. In `build_phase()`, it fetches `virtual alu_if vif` from `uvm_config_db`. In `run_phase()`, an infinite `forever` loop pulls items via `seq_item_port.get_next_item(req)`, drives the `Valid/Ready` handshake, and calls `seq_item_port.item_done()`.
5. **`alu_minimal_test.sv` & `tb_top.sv` (Wiring & Objections):**
   - `tb_top` instantiates `pkt_alu_basic` + `alu_if`, publishes `u_alu_if` into `uvm_config_db`, and calls `run_test("alu_minimal_test")`.
   - `alu_minimal_test` creates `seqr` and `drv`, connects `drv.seq_item_port.connect(seqr.seq_item_export)`, and wraps `seq.start(seqr)` inside **`phase.raise_objection(this)` / `phase.drop_objection(this)`**—without an objection, `run_phase` exits immediately at `0 ns`!
""",
        "sim_log": """# ** Note: (vsim-3813) Design is being optimized...
UVM_INFO @ 0: reporter [RNTST] Running test alu_minimal_test...
UVM_INFO alu_seq.sv(15) @ 25: uvm_test_top.seqr@@seq [SEQ] Starting smoke sequence (4 items)
UVM_INFO alu_seq.sv(22) @ 25: uvm_test_top.seqr@@seq [SEQ] Sending tag=0 op=ALU_ADD a=0x03a4 b=0x012f
UVM_INFO alu_driver.sv(38) @ 30: uvm_test_top.drv [DRV] Driving tag=0 op=ALU_ADD a=0x03a4 b=0x012f
UVM_INFO alu_seq.sv(22) @ 40: uvm_test_top.seqr@@seq [SEQ] Sending tag=1 op=ALU_MUL a=0x0042 b=0x0018
UVM_INFO alu_driver.sv(38) @ 40: uvm_test_top.drv [DRV] Driving tag=1 op=ALU_MUL a=0x0042 b=0x0018
UVM_INFO alu_seq.sv(22) @ 50: uvm_test_top.seqr@@seq [SEQ] Sending tag=2 op=ALU_XOR a=0x0a11 b=0x05ff
UVM_INFO alu_driver.sv(38) @ 50: uvm_test_top.drv [DRV] Driving tag=2 op=ALU_XOR a=0x0a11 b=0x05ff
UVM_INFO alu_seq.sv(22) @ 60: uvm_test_top.seqr@@seq [SEQ] Sending tag=3 op=ALU_SUB a=0x0900 b=0x0100
UVM_INFO alu_driver.sv(38) @ 60: uvm_test_top.drv [DRV] Driving tag=3 op=ALU_SUB a=0x0900 b=0x0100
UVM_INFO alu_seq.sv(26) @ 70: uvm_test_top.seqr@@seq [SEQ] Completed smoke sequence
UVM_INFO @ 110: reporter [TEST_DONE] 'run' phase is ready to proceed to the 'extract' phase
--- UVM Report Summary ---
UVM_INFO :    11
UVM_WARNING : 0
UVM_ERROR :   0
UVM_FATAL :   0""",
        "stepper": [
            {"step": 1, "title": "1. Top Module & ConfigDB Set", "component": "tb_top", "file": "tb_top.sv", "line": 44, "state": "0 ns · INIT", "desc": "tb_top publishes physical alu_if into uvm_config_db and invokes run_test(\"alu_minimal_test\").", "log_snippet": "Running test alu_minimal_test"},
            {"step": 2, "title": "2. Build & Connect Driver <-> Sequencer", "component": "alu_minimal_test", "file": "alu_minimal_test.sv", "line": 23, "state": "0 ns · BUILD/CONNECT", "desc": "alu_minimal_test instantiates seqr and drv, then connects drv.seq_item_port to seqr.seq_item_export.", "log_snippet": "Running test alu_minimal_test"},
            {"step": 3, "title": "3. Raise Objection & Start Sequence", "component": "alu_minimal_test", "file": "alu_minimal_test.sv", "line": 28, "state": "25 ns · RUN", "desc": "Test raises objection so run_phase stays active, creates alu_smoke_seq, and launches seq.start(seqr).", "log_snippet": "Starting smoke sequence"},
            {"step": 4, "title": "4. Late Randomization & finish_item", "component": "alu_smoke_seq", "file": "alu_seq.sv", "line": 19, "state": "25 ns · HANDSHAKE", "desc": "start_item waits for sequencer grant, randomizes req, and hands off via finish_item(req).", "log_snippet": "Sending tag=0 op=ALU_ADD"},
            {"step": 5, "title": "5. Pin-Level Driving & item_done", "component": "alu_driver", "file": "alu_driver.sv", "line": 39, "state": "30 ns · PIN DRIVE", "desc": "Driver asserts in_valid and op/a/b/tag on clocking block drv_cb until in_ready=1, then calls item_done().", "log_snippet": "Driving tag=0 op=ALU_ADD"},
            {"step": 6, "title": "6. Drop Objection & Shutdown", "component": "alu_minimal_test", "file": "alu_minimal_test.sv", "line": 32, "state": "110 ns · DONE", "desc": "Once all 4 items finish and drain #40ns, drop_objection() allows UVM to enter extract/report phases.", "log_snippet": "TEST_DONE"}
        ],
        "quizzes": [
            {
                "q": "What happens if you forget phase.raise_objection(this) in alu_minimal_test::run_phase?",
                "options": [
                    "UVM waits forever until $finish is called",
                    "run_phase terminates immediately at 0 ns before any stimulus runs",
                    "The sequencer automatically raises an objection for every item"
                ],
                "answer": 1,
                "explanation": "In UVM 1.2, time-consuming run phases end immediately when the total objection count drops to zero."
            },
            {
                "q": "Why does alu_smoke_seq call req.randomize() AFTER start_item(req) instead of before?",
                "options": [
                    "Late randomization guarantees constraints can reflect the latest DUT/scoreboard state at the moment the driver is ready",
                    "SystemVerilog forbids calling randomize() before start_item()",
                    "Because start_item() allocates the memory for req"
                ],
                "answer": 0,
                "explanation": "start_item() blocks until sequencer arbitration completes, so randomizing afterwards ensures the transaction reflects current hardware state."
            }
        ],
    },

    # =========================================================================
    # CHAPTER 4: Structuring & Configuring — Agent, Env, Factory & Config Objects
    # =========================================================================
    {
        "num": 4,
        "slug": "ch04_agent_factory_config",
        "part": "Stimuli & Core",
        "part_title": "II. Stimuli & Core Testbench Infrastructure",
        "title": "04. Structuring & Configuring: Agent, Env, Factory & Config Objects",
        "short_title": "04. Agent, Factory & ConfigDB",
        "difficulty": "Beginner",
        "src_dir": "ch04_agent_factory_config",
        "dut_files": ["dut/pkt_alu_basic.sv"],
        "inherit_from": "ch03_minimal_stimuli",
        "exclude_inherited": ["alu_minimal_test.sv"],
        "primary_file": "alu_test.sv",
        "summary": (
            "Refactor the bare-minimum testbench into a reusable, configurable UVM hierarchy: encapsulate driver "
            "and sequencer inside uvm_agent (UVM_ACTIVE/UVM_PASSIVE), group agents in uvm_env, bundle settings in "
            "Config Objects, and swap transaction types dynamically via uvm_factory."
        ),
        "apis": [
            "uvm_agent", "uvm_env", "uvm_test", "uvm_factory", "uvm_config_db",
            "uvm_active_passive_enum", "set_type_override_by_type", "set_inst_override_by_type"
        ],
        "objectives": [
            "Package protocol-specific driver/sequencer (and soon monitor) into a reusable `uvm_agent` supporting `UVM_ACTIVE` and `UVM_PASSIVE`.",
            "Replace individual `uvm_config_db` strings with strongly-typed hierarchical configuration objects (`alu_env_cfg`, `alu_agent_cfg`).",
            "Use `::type_id::create()` everywhere instead of `new()` so tests can override classes via `uvm_factory` without modifying source code.",
            "Group testbench classes inside a clean SystemVerilog `package alu_tb_pkg`."
        ],
        "interactive_widget": "arch_diff",
        "new_components": ["alu_agent", "alu_env", "alu_cfg", "alu_factory"],
        "docs_links": [
            _doc("uvm_agent", "comps/uvm_agent-svh.html#uvm_agent", "Protocol unit with active/passive toggle via is_active."),
            _doc("uvm_env", "comps/uvm_env-svh.html#uvm_env", "Top container for agents, scoreboards, and coverage."),
            _doc("uvm_factory", "base/uvm_factory-svh.html#uvm_factory", "Polymorphic object/component creation and overrides."),
            _doc("Factory Overview", "overviews/factory-txt.html", "Why create() beats new() for testbench customization."),
            _doc("Configuration & Resources", "overviews/config_and_res-txt.html", "Best practices for uvm_config_db and config objects."),
        ],
        "example_links": [
            _ex("Factory Overrides", "infrastructure/factory.html", "Type & instance overrides in action."),
            _ex("Manual Configuration DB", "infrastructure/manual.html", "Hierarchical uvm_config_db scopes."),
            _ex("Modular Packages", "basics/pkg.html", "Clean SystemVerilog package compilation."),
        ],
        "markdown_body": """
## 4.1 Why Encapsulate Into `uvm_agent` and `uvm_env`?

Putting `seqr` and `drv` directly inside `alu_minimal_test` (Chapter 3) works for 1 test, but fails the moment you need:
1. **A second interface** (e.g., an APB bus alongside our data port),
2. **Dozens of tests** that share the same structural wiring without copy-pasting `build_phase()`/`connect_phase()`,
3. **Passive SoC reuse**, where the driver and sequencer must be disabled (`UVM_PASSIVE`).

```mermaid
flowchart TB
    TEST["alu_mul_factory_test (uvm_test)"] --> ENV["alu_env (uvm_env)"]
    TEST -. "set_type_override(alu_item -> alu_mul_only_item)" .-> FAC["uvm_factory"]
    ENV --> AGT["data_agent (uvm_agent)"]
    AGT -->|"if UVM_ACTIVE"| SEQR["seqr (uvm_sequencer)"]
    AGT -->|"if UVM_ACTIVE"| DRV["drv (alu_driver)"]
    SEQR <--> DRV
```

---

## 4.2 Configuration Objects Beat Scattered `config_db` Calls

Instead of storing 10 separate scalar fields in `uvm_config_db` (slow string lookups, typo risks), we bundle related settings inside `uvm_object` subclasses (`alu_agent_cfg`, `alu_env_cfg` in **`alu_cfg.sv`**):
- `alu_base_test` creates `env_cfg`, populates `env_cfg.data_agent_cfg.vif`, and passes `env_cfg` down to `alu_env`.
- `alu_env` passes `cfg.data_agent_cfg` down to `data_agent`.
- `alu_agent` inspects `cfg.is_active`: when `UVM_ACTIVE`, it builds `seqr` and `drv`.

---

## 4.3 Polymorphism Without Editing Code: `uvm_factory`

Notice in `alu_seq.sv` line 21:
```systemverilog
req = alu_item::type_id::create($sformatf("req_%0d", i));
```
Never call `new()` for reusable UVM items or components! Because the sequence asks the **Factory** to create `alu_item`, our derived test `alu_mul_factory_test` can execute:
```systemverilog
alu_item::type_id::set_type_override(alu_mul_only_item::get_type());
```
Every sequence automatically generates `alu_mul_only_item` (constrained to `ALU_MUL`) **without modifying a single line of `alu_seq.sv` or `alu_env.sv`**.
""",
        "sim_log": """UVM_INFO @ 0: reporter [RNTST] Running test alu_mul_factory_test...
#### Factory Configuration (*)
Type Overrides:
  Requested Type  Override Type
  --------------  ------------------
  alu_item        alu_mul_only_item
UVM_INFO @ 0: reporter [UVMTOP] UVM testbench topology:
  uvm_test_top (alu_mul_factory_test)
    env (alu_env)
      data_agent (alu_agent)
        drv (alu_driver)
        seqr (uvm_sequencer)
UVM_INFO alu_seq.sv(22) @ 25: uvm_test_top.env.data_agent.seqr@@seq [SEQ] Sending tag=0 op=ALU_MUL a=0x008b b=0x0041 (type=alu_mul_only_item)
UVM_INFO alu_driver.sv(40) @ 30: uvm_test_top.env.data_agent.drv [DRV] Driving tag=0 op=ALU_MUL a=0x008b b=0x0041
--- UVM Report Summary ---
UVM_INFO :    14
UVM_ERROR :   0""",
        "stepper": [
            {"step": 1, "title": "1. Register Factory Type Override", "component": "alu_mul_factory_test", "file": "alu_test.sv", "line": 50, "state": "0 ns · FACTORY", "desc": "Before super.build_phase(), test swaps alu_item -> alu_mul_only_item globally in uvm_factory.", "log_snippet": "Type Overrides"},
            {"step": 2, "title": "2. Build Config Object & Environment", "component": "alu_base_test", "file": "alu_test.sv", "line": 22, "state": "0 ns · BUILD", "desc": "Test populates alu_env_cfg with virtual interface and delegates hierarchy construction to alu_env.", "log_snippet": "UVM testbench topology"},
            {"step": 3, "title": "3. Active Agent Conditional Build", "component": "alu_agent", "file": "alu_agent.sv", "line": 24, "state": "0 ns · AGENT", "desc": "data_agent checks cfg.is_active == UVM_ACTIVE before creating seqr and drv.", "log_snippet": "data_agent (alu_agent)"},
            {"step": 4, "title": "4. Factory Creates Overridden Item", "component": "alu_smoke_seq", "file": "alu_seq.sv", "line": 21, "state": "25 ns · CREATE", "desc": "alu_item::type_id::create() returns an alu_mul_only_item instance transparently.", "log_snippet": "type=alu_mul_only_item"}
        ],
        "quizzes": [
            {
                "q": "When should a test call set_type_override() or set_inst_override()?",
                "options": [
                    "In run_phase() right after raising an objection",
                    "In build_phase() BEFORE creating the components/objects to be overridden",
                    "In report_phase() to summarize test configuration"
                ],
                "answer": 1,
                "explanation": "Factory overrides must be registered before ::type_id::create() executes during build_phase() or sequence execution."
            },
            {
                "q": "What is the key advantage of passing alu_env_cfg instead of individual integers/strings via uvm_config_db?",
                "options": [
                    "Compile-time type checking of all fields and single config_db lookup per component",
                    "It eliminates the need for build_phase()",
                    "Config objects automatically synthesize to FPGA gates"
                ],
                "answer": 0,
                "explanation": "Bundling configuration parameters inside a single uvm_object reduces string lookup overhead and catches field typos at compile time."
            }
        ],
    },

    # =========================================================================
    # CHAPTER 5: Observation & Checking — Monitor, TLM-1 & Scoreboard
    # =========================================================================
    {
        "num": 5,
        "slug": "ch05_monitor_scoreboard",
        "part": "Checks & Advanced",
        "part_title": "III. Checking, Metrics & Advanced Stimulus",
        "title": "05. Passive Observation & Self-Checking: Monitor, TLM-1 & Scoreboard",
        "short_title": "05. Monitor, TLM-1 & Scoreboard",
        "difficulty": "Intermediate",
        "src_dir": "ch05_monitor_scoreboard",
        "dut_files": ["dut/pkt_alu_basic.sv"],
        "inherit_from": "ch04_agent_factory_config",
        "primary_file": "alu_scoreboard.sv",
        "summary": (
            "Close the checking loop cleanly: add a passive uvm_monitor sampling both request and response "
            "handshakes via clocking blocks, broadcast transactions over TLM-1 uvm_analysis_ports, buffer them "
            "in uvm_tlm_analysis_fifos, and verify DUT behavior against an independent Golden Reference Model."
        ),
        "apis": [
            "uvm_monitor", "uvm_scoreboard", "uvm_analysis_port", "uvm_analysis_export",
            "uvm_tlm_analysis_fifo", "check_phase", "report_phase"
        ],
        "objectives": [
            "Build a strictly passive `uvm_monitor` that works identically in `UVM_ACTIVE` and `UVM_PASSIVE` modes.",
            "Broadcast transactions decouple-style using `uvm_analysis_port::write()`.",
            "Buffer concurrent input/output streams safely inside `uvm_tlm_analysis_fifo #(alu_item)`.",
            "Implement `alu_ref_model` + `alu_scoreboard` checking expected vs. actual outputs and verifying zero leftover items in `check_phase()`."
        ],
        "interactive_widget": "arch_diff",
        "new_components": ["alu_monitor", "alu_ref_model", "alu_scoreboard", "tlm_fifo"],
        "docs_links": [
            _doc("uvm_monitor", "comps/uvm_monitor-svh.html#uvm_monitor", "Passive pin-to-transaction observer."),
            _doc("uvm_scoreboard", "comps/uvm_scoreboard-svh.html#uvm_scoreboard", "Functional checker comparing predicted vs. observed results."),
            _doc("uvm_analysis_port", "tlm1/uvm_analysis_port-svh.html#uvm_analysis_port", "Non-blocking broadcast TLM-1 port."),
            _doc("uvm_tlm_analysis_fifo", "tlm1/uvm_tlm_fifos-svh.html#uvm_tlm_analysis_fifo", "Unbounded FIFO adapting analysis write() into blocking get()."),
            _doc("TLM Ports & Exports", "overviews/tlm_ifs_and_ports-txt.html", "Hierarchical TLM port-to-export forwarding."),
        ],
        "example_links": [
            _ex("TLM-1 FIFO Communication", "tlm-1/fifo.html", "Producer/consumer synchronization via uvm_tlm_fifo."),
            _ex("Hierarchical TLM Forwarding", "tlm-1/hierarchy.html", "Connecting inner monitor ports up through agent boundaries."),
        ],
        "markdown_body": """
## 5.1 Passive Observation via `uvm_monitor`

Until Chapter 4, our testbench could drive pins—but it was **blind** to whether the DUT computed the right answer!

In **`alu_monitor.sv`**, we fork two independent passive loops reading `vif.mon_cb`:
1. **`collect_requests()`:** Watches `in_valid && in_ready`. Whenever an input handshake succeeds, it constructs an `alu_item` and calls `req_ap.write(tr)`.
2. **`collect_responses()`:** Watches `out_valid && out_ready`. Whenever the DUT produces an output, it constructs an `alu_item` with `out_tag`, `result`, `err_flag` and calls `rsp_ap.write(tr)`.

> **Why sample inputs via the monitor instead of taking them from the driver?**
> Because in a multi-master or SoC environment (`UVM_PASSIVE`), our driver doesn't even exist—yet the monitor still sees every input transaction accepted by the DUT!

---

## 5.2 Decoupled Broadcasting with `uvm_analysis_port` & `uvm_tlm_analysis_fifo`

```mermaid
flowchart LR
    MON["alu_monitor"] -->|"req_ap.write(tr)"| AGT_REQ["agent.req_ap"]
    MON -->|"rsp_ap.write(tr)"| AGT_RSP["agent.rsp_ap"]
    AGT_REQ -->|"connect()"| REQ_FIFO["scb.req_fifo (uvm_tlm_analysis_fifo)"]
    AGT_RSP -->|"connect()"| RSP_FIFO["scb.rsp_fifo (uvm_tlm_analysis_fifo)"]
    REQ_FIFO -->|"get(req)"| REF["alu_ref_model.predict()"]
    REF -->|"exp"| CMP["Scoreboard Compare"]
    RSP_FIFO -->|"get(act)"| CMP
```

A `uvm_analysis_port` is **non-blocking** (0-time `write()`). If the scoreboard needs to wait for *both* an input request and a 1-cycle-later DUT output before comparing them, we buffer incoming broadcasts inside **`uvm_tlm_analysis_fifo #(alu_item)`**, then pull matching pairs inside `alu_scoreboard::run_phase()` using blocking `req_fifo.get(req)` and `rsp_fifo.get(act)`.

---

## 5.3 End-of-Test Hygiene in `check_phase()`

What if the DUT dropped the last packet and never asserted `out_valid`? If you only compare pairs inside `run_phase()`, a dropped packet hangs silently!
That's why `alu_scoreboard::check_phase()` verifies:
```systemverilog
if (!req_fifo.is_empty() || !rsp_fifo.is_empty())
  `uvm_error("SCB", "Unmatched items remaining at end of test!")
```
""",
        "sim_log": """UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
UVM_INFO alu_seq.sv(15) @ 25: uvm_test_top.env.data_agent.seqr@@seq [SEQ] Starting sequence (8 items)
UVM_INFO alu_scoreboard.sv(44) @ 40: uvm_test_top.env.scb [SCB] MATCH tag=0 op=ALU_ADD result=0x000004d3
UVM_INFO alu_scoreboard.sv(44) @ 50: uvm_test_top.env.scb [SCB] MATCH tag=1 op=ALU_SUB result=0x00000210
UVM_INFO alu_scoreboard.sv(44) @ 60: uvm_test_top.env.scb [SCB] MATCH tag=2 op=ALU_MUL result=0x00048c20
...
UVM_INFO alu_scoreboard.sv(44) @ 110: uvm_test_top.env.scb [SCB] MATCH tag=7 op=ALU_XOR result=0x00000e17
UVM_INFO alu_scoreboard.sv(59) @ 150: uvm_test_top.env.scb [SCB] Scoreboard Summary: PASS=8 FAIL=0
--- UVM Report Summary ---
UVM_INFO :    19
UVM_ERROR :   0""",
        "stepper": [
            {"step": 1, "title": "1. Connect Agent Analysis Ports to Scoreboard", "component": "alu_env", "file": "alu_env.sv", "line": 34, "state": "0 ns · CONNECT", "desc": "alu_env connects data_agent.req_ap and rsp_ap to scb.req_export and scb.rsp_export.", "log_snippet": "Running test alu_base_test"},
            {"step": 2, "title": "2. Monitor Captures Accepted Input", "component": "alu_monitor", "file": "alu_monitor.sv", "line": 41, "state": "30 ns · REQ OBS", "desc": "collect_requests() detects in_valid && in_ready on mon_cb and broadcasts req_ap.write(tr).", "log_snippet": "MATCH tag=0"},
            {"step": 3, "title": "3. Monitor Captures DUT Output", "component": "alu_monitor", "file": "alu_monitor.sv", "line": 55, "state": "40 ns · RSP OBS", "desc": "One cycle later, collect_responses() captures result/out_tag/err_flag and broadcasts rsp_ap.write(tr).", "log_snippet": "MATCH tag=0"},
            {"step": 4, "title": "4. Golden Prediction & Comparison", "component": "alu_scoreboard", "file": "alu_scoreboard.sv", "line": 38, "state": "40 ns · CHECK", "desc": "Scoreboard pulls req & act from FIFOs, computes exp via alu_ref_model.predict(), and checks equality.", "log_snippet": "Scoreboard Summary: PASS=8 FAIL=0"},
            {"step": 5, "title": "5. Drain Check in check_phase", "component": "alu_scoreboard", "file": "alu_scoreboard.sv", "line": 51, "state": "150 ns · CHECK_PHASE", "desc": "Verifies both req_fifo and rsp_fifo are completely empty so no dropped packets go unnoticed.", "log_snippet": "PASS=8 FAIL=0"}
        ],
        "quizzes": [
            {
                "q": "Why does uvm_analysis_port use a non-blocking function write() instead of a blocking task put()?",
                "options": [
                    "Because SystemVerilog interfaces forbid tasks",
                    "So a monitor can broadcast passively to 0, 1, or N subscribers without ever stalling bus observation",
                    "Because functions execute faster than tasks in C++"
                ],
                "answer": 1,
                "explanation": "Monitors must observe bus activity in zero simulation time without blocking, regardless of how many subscribers are attached."
            },
            {
                "q": "What problem does check_phase() solve in alu_scoreboard?",
                "options": [
                    "Detecting transactions that entered the DUT but never produced a matching output before simulation ended",
                    "Randomizing the next sequence item",
                    "Driving reset onto the DUT"
                ],
                "answer": 0,
                "explanation": "If a packet disappears inside the DUT, run_phase's rsp_fifo.get() remains blocked; check_phase() catches non-empty FIFOs at end-of-test."
            }
        ],
    },

    # =========================================================================
    # CHAPTER 6: Verification Metrics & Protocol Checking — Coverage & SVA
    # =========================================================================
    {
        "num": 6,
        "slug": "ch06_coverage_sva",
        "part": "Checks & Advanced",
        "part_title": "III. Checking, Metrics & Advanced Stimulus",
        "title": "06. Verification Metrics & Protocol Checking: Coverage & SVA",
        "short_title": "06. Coverage & SVA Assertions",
        "difficulty": "Intermediate",
        "src_dir": "ch06_coverage_sva",
        "dut_files": ["dut/pkt_alu_basic.sv"],
        "inherit_from": "ch05_monitor_scoreboard",
        "primary_file": "alu_cov_subscriber.sv",
        "summary": (
            "Complete the three verification pillars by adding Functional Coverage (uvm_subscriber + SystemVerilog "
            "covergroups + cross coverage) for Metrics and concurrent SystemVerilog Assertions (SVA) inside alu_if "
            "for cycle-accurate pin protocol checking."
        ),
        "apis": [
            "uvm_subscriber", "uvm_analysis_export", "report_phase", "uvm_comparer"
        ],
        "objectives": [
            "Implement a `uvm_subscriber #(alu_item)` sampling `covergroup` bins and `cross` coverage via `write()`.",
            "Filter impossible combinations cleanly using `ignore_bins` so 100% coverage closure is meaningful.",
            "Write concurrent SystemVerilog Assertions (`property` / `assert property` / `cover property`) in `alu_if.sv` for pin-level handshake stability.",
            "Weight sequence distributions (`dist`) to exercise corner cases like `0x0000`, `0xFFFF`, and `ALU_INVAL`."
        ],
        "interactive_widget": "arch_diff",
        "new_components": ["alu_cov_subscriber", "sva_assertions"],
        "docs_links": [
            _doc("uvm_subscriber", "comps/uvm_subscriber-svh.html#uvm_subscriber", "Built-in analysis listener class with analysis_export."),
            _doc("Transaction Recording", "overviews/recording-txt.html", "Observing and recording transactions for metrics & debug."),
            _doc("uvm_comparer", "base/uvm_comparer-svh.html#uvm_comparer", "Policy class for structured object comparison."),
        ],
        "example_links": [
            _ex("Register Coverage", "registers/coverage.html", "Sampling functional covergroups automatically."),
        ],
        "markdown_body": """
## 6.1 Closing the Loop: Coverage-Driven Verification (CDV)

Having a Scoreboard tells us *"no bugs observed on the tests we ran"*—but it never answers **"did we actually test all corner cases?"**
That is the role of **Metrics**:
1. **Code Coverage** (line, branch, toggle, FSM) collected by the simulator—answers *did every line of RTL execute?*
2. **Functional Coverage** (`covergroup` in **`alu_cov_subscriber.sv`**)—answers *did every feature and cross-product from the vPlan occur?*

```mermaid
flowchart LR
    MON["alu_monitor"] -->|"req_ap"| SCB["Checks: alu_scoreboard"]
    MON -->|"req_ap"| COV["Metrics: alu_cov_subscriber (cg_alu)"]
    IF["alu_if"] -->|"SVA properties"| SVA["Protocol Checks: a_in_valid_stable / c_backpressure"]
    COV -. "100% vPlan Closure?" .-> SEQ["Refine Constraints in alu_seq"]
```

---

## 6.2 `uvm_subscriber` & Cross Coverage

Extending `uvm_subscriber #(alu_item)` gives us `analysis_export` automatically—all we implement is `write(alu_item t)` calling `cg_alu.sample()`.

Notice how **`cx_op_x_err: cross cp_op, cp_err`** tracks every combination of operation and error flag, while `ignore_bins` excludes structurally impossible cases (such as `ALU_INVAL` producing `err_flag == 0`) so our target remains an honest **100%**.

---

## 6.3 Pin-Level Temporal Protocol Checking with SVA

Scoreboards operate at **transaction level**—they are terrible at catching single-cycle glitch violations like changing `a` or `op` while `in_valid && !in_ready`.
Concurrent **SystemVerilog Assertions (SVA)** belong directly inside **`alu_if.sv`**:
```systemverilog
property p_in_valid_stable;
  @(posedge clk) disable iff (!rst_n)
  (in_valid && !in_ready) |=> (in_valid && $stable({op, a, b, tag}));
endproperty
a_in_valid_stable: assert property (p_in_valid_stable);
```
Now Stimuli (`driver`/`seq`), Checks (`scoreboard` + `SVA`), and Metrics (`cov_subscriber` + `cover property`) are **100% decoupled and modular**.
""",
        "sim_log": """UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
UVM_INFO alu_seq.sv(15) @ 25: uvm_test_top.env.data_agent.seqr@@seq [SEQ] Starting coverage-driven sequence (20 items)
UVM_INFO alu_scoreboard.sv(44) @ 40: uvm_test_top.env.scb [SCB] MATCH tag=0 op=ALU_ADD result=0x00000000
UVM_INFO alu_scoreboard.sv(44) @ 50: uvm_test_top.env.scb [SCB] MATCH tag=1 op=ALU_MUL result=0xfffe0001
UVM_INFO alu_scoreboard.sv(44) @ 140: uvm_test_top.env.scb [SCB] MATCH tag=10 op=ALU_INVAL result=0xdeadbeef
UVM_INFO alu_scoreboard.sv(59) @ 270: uvm_test_top.env.scb [SCB] Scoreboard Summary: PASS=20 FAIL=0
UVM_INFO alu_cov_subscriber.sv(45) @ 270: uvm_test_top.env.cov [COV] Functional Coverage achieved: 94.44%
--- UVM Report Summary ---
UVM_INFO :    28
UVM_ERROR :   0""",
        "stepper": [
            {"step": 1, "title": "1. Subscribe Coverage Collector to Monitor", "component": "alu_env", "file": "alu_env.sv", "line": 39, "state": "0 ns · CONNECT", "desc": "alu_env fans out data_agent.req_ap to both scb.req_export and cov.analysis_export.", "log_snippet": "Running test alu_base_test"},
            {"step": 2, "title": "2. Corner-Weighted Stimulus Generation", "component": "alu_smoke_seq", "file": "alu_seq.sv", "line": 22, "state": "25 ns · STIMULUS", "desc": "Sequence mixes 0x0000, 0xFFFF, and weighted ALU_INVAL opcodes to hit coverage bins.", "log_snippet": "MATCH tag=1 op=ALU_MUL"},
            {"step": 3, "title": "3. SVA Monitors Cycle-by-Cycle Protocol", "component": "alu_if", "file": "alu_if.sv", "line": 42, "state": "30 ns · SVA CHECK", "desc": "a_in_valid_stable continuously checks that payload remains constant whenever in_ready=0.", "log_snippet": "MATCH tag=10 op=ALU_INVAL"},
            {"step": 4, "title": "4. Report Functional Coverage Score", "component": "alu_cov_subscriber", "file": "alu_cov_subscriber.sv", "line": 45, "state": "270 ns · METRICS", "desc": "report_phase prints cg_alu.get_inst_coverage() alongside scoreboard PASS=20 FAIL=0.", "log_snippet": "Functional Coverage achieved"}
        ],
        "quizzes": [
            {
                "q": "Why are SVA assertions placed inside alu_if rather than inside alu_scoreboard?",
                "options": [
                    "SVA checks cycle-accurate pin-level temporal rules (like $stable while stalled), whereas scoreboards check end-to-end transaction data",
                    "Because scoreboards cannot access $error",
                    "Because interfaces cannot instantiate UVM classes"
                ],
                "answer": 0,
                "explanation": "SVA excels at cycle-by-cycle signal protocol invariants; UVM scoreboards excel at abstract transaction transformations and multi-cycle latency matching."
            },
            {
                "q": "Why did we connect cov.analysis_export to data_agent.req_ap instead of sampling inside alu_smoke_seq?",
                "options": [
                    "Because sequences run inside run_phase and cannot instantiate covergroups",
                    "So coverage records only transactions that were actually accepted on the hardware bus",
                    "To slow down simulation for debugging"
                ],
                "answer": 1,
                "explanation": "Observer-based coverage reflects true bus traffic regardless of which sequence or external master drove the DUT."
            }
        ],
    },
]
