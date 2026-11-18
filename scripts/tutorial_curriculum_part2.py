#!/usr/bin/env python3
"""
UVM 1.2 Progressive Tutorial Curriculum — Part II (Chapters 7 to 13).
"""

from typing import Dict, List, Any
from tutorial_curriculum import _doc, _ex


CHAPTERS_PART_2: List[Dict[str, Any]] = [
    # =========================================================================
    # CHAPTER 7: Pipelining, Arbitration, Layered Sequences & Virtual Sequencer
    # =========================================================================
    {
        "num": 7,
        "slug": "ch07_pipelined_layered_vseq",
        "part": "Checks & Advanced",
        "part_title": "III. Checking, Metrics & Advanced Stimulus",
        "title": "07. Pipelined Responses, Arbitration, Layered Sequences & Virtual Sequencer",
        "short_title": "07. Layered & Virtual Seq",
        "difficulty": "Intermediate",
        "src_dir": "ch07_pipelined_layered_vseq",
        "dut_files": ["dut/pkt_alu.sv"],
        "inherit_from": "ch06_coverage_sva",
        "exclude_inherited": ["dut/pkt_alu_basic.sv"],
        "primary_file": "alu_virtual_seq.sv",
        "summary": (
            "Upgrade to the full dual-interface pkt_alu DUT (Valid/Ready + APB3): implement tagged driver "
            "responses (put/get_response), sequencer arbitration (lock/SEQ_ARB_STRICT_FIFO), multi-layer "
            "protocol translation sequences, and a Virtual Sequencer orchestrating both interfaces."
        ),
        "apis": [
            "uvm_sequence_base", "uvm_sequencer_base", "`uvm_declare_p_sequencer",
            "uvm_sequencer", "uvm_driver"
        ],
        "objectives": [
            "Return tagged responses (`rsp.set_id_info(req)` + `put(rsp)`) from a pipelined driver back to its originating sequence (`get_response(rsp)`).",
            "Translate high-level macro frames `(x + y) * scale` into chained low-level bus items via **Layered Sequences**.",
            "Arbitrate concurrent stimulus streams safely using `set_arbitration(SEQ_ARB_STRICT_FIFO)` and `lock()/unlock()`.",
            "Coordinate APB register setup and data traffic cleanly using a **Virtual Sequencer** (`alu_virtual_sequencer`) and `uvm_declare_p_sequencer`."
        ],
        "interactive_widget": "arch_diff",
        "new_components": ["apb_agent", "v_seqr", "layered_seq", "pkt_alu"],
        "docs_links": [
            _doc("uvm_sequence_base", "seq/uvm_sequence_base-svh.html#uvm_sequence_base", "start(), wait_for_grant(), send_request(), get_response()."),
            _doc("uvm_sequencer_base", "seq/uvm_sequencer_base-svh.html#uvm_sequencer_base", "Arbitration modes, grab(), and lock()."),
            _doc("Sequences Overview", "overviews/sequences-txt.html", "Sequence layering and hierarchical reuse."),
            _doc("Sequencers Overview", "overviews/sequencers-txt.html", "Sequencer arbitration and virtual sequencer architecture."),
            _doc("Sequence Macros", "macros/uvm_sequence_defines-svh.html", "`uvm_declare_p_sequencer and sequence helpers."),
        ],
        "example_links": [
            _ex("Basic Read/Write Sequence", "sequences/basic_read_write_sequence.html", "Sequence item transport & responses."),
            _ex("APB Verification IP", "integrated/apb.html", "Official UVM APB agent reference."),
        ],
        "markdown_body": """
## 7.1 Upgrading to a Multi-Interface DUT (`pkt_alu.sv`)

Real hardware almost always has **at least two buses**: a **Control/Register interface** (here APB3) and a **Datapath interface** (`Valid/Ready`). Driving them independently without coordination causes race conditions (e.g., sending packets before configuring saturation registers).

```mermaid
sequenceDiagram
    participant VSeq as alu_virtual_seq
    participant APBSqr as apb_agt.seqr
    participant ALUSqr as data_agent.seqr
    participant Drv as alu_driver

    VSeq->>APBSqr: cfg_seq.start(p_sequencer.apb_sqr)
    APBSqr-->>VSeq: APB CTRL.EN=1 done
    par Concurrent Streams
        VSeq->>ALUSqr: smoke_seq.start(p_sequencer.alu_sqr)
    and Layered Frame
        VSeq->>ALUSqr: layered_seq.start(p_sequencer.alu_sqr)
        ALUSqr->>Drv: step1: ADD(x, y)
        Drv-->>ALUSqr: put(rsp1) -> sum
        ALUSqr->>Drv: step2: MUL(sum, scale)
        Drv-->>ALUSqr: put(rsp2) -> final
    end
```

---

## 7.2 Tagged Driver Responses & Layered Sequences

Look at **`alu_driver.sv`**: instead of `get_next_item()`/`item_done()`, we use `seq_item_port.get(req)` and return a response via:
```systemverilog
rsp.set_id_info(req); // Copies transaction_id & sequence_id so sequencer routes rsp to the right thread!
seq_item_port.put(rsp);
```
Because **`alu_layered_frame_seq`** (`alu_seq.sv`) receives `rsp1` via `get_response(rsp1)`, it can feed the hardware result of `(x + y)` directly into the second transaction `MUL(sum, scale)`!

---

## 7.3 Virtual Sequencer & Virtual Sequences

A **Virtual Sequencer** (`alu_virtual_sequencer`) drives **zero pins of its own**. It simply holds typed handles to sub-sequencers (`alu_sqr`, `apb_sqr`) connected in `alu_env::connect_phase()`.
Inside **`alu_virtual_seq`**, `` `uvm_declare_p_sequencer(alu_virtual_sequencer) `` creates a strongly-typed `p_sequencer` handle so one test scenario orchestrates APB configuration followed by parallel data streams.
""",
        "sim_log": """UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
UVM_INFO alu_virtual_seq.sv(18) @ 25: uvm_test_top.env.v_seqr@@vseq [VSEQ] Phase 1: Configuring CTRL register via APB agent (EN=1, SAT_EN=0)
UVM_INFO alu_virtual_seq.sv(24) @ 55: uvm_test_top.env.v_seqr@@vseq [VSEQ] Phase 2: Launching parallel smoke + layered arithmetic flows
UVM_INFO alu_seq.sv(72) @ 105: uvm_test_top.env.data_agent.seqr@@layered_seq [LAYERED_SEQ] Macro (18 + 27) * 3 = 135
UVM_INFO alu_scoreboard.sv(59) @ 190: uvm_test_top.env.scb [SCB] Scoreboard Summary: PASS=8 FAIL=0
UVM_INFO alu_cov_subscriber.sv(45) @ 190: uvm_test_top.env.cov [COV] Functional Coverage achieved: 72.50%
--- UVM Report Summary ---
UVM_INFO :    16
UVM_ERROR :   0""",
        "stepper": [
            {"step": 1, "title": "1. Connect Sub-Sequencers to Virtual Sequencer", "component": "alu_env", "file": "alu_env.sv", "line": 36, "state": "0 ns · CONNECT", "desc": "alu_env binds data_agent.seqr -> v_seqr.alu_sqr and apb_agt.seqr -> v_seqr.apb_sqr.", "log_snippet": "Running test alu_base_test"},
            {"step": 2, "title": "2. Virtual Sequence Configures APB CTRL", "component": "alu_virtual_seq", "file": "alu_virtual_seq.sv", "line": 21, "state": "25 ns · APB CFG", "desc": "vseq executes apb_write_seq on p_sequencer.apb_sqr before launching datapath traffic.", "log_snippet": "Configuring CTRL register via APB"},
            {"step": 3, "title": "3. Layered Step 1 + Driver Response", "component": "alu_driver", "file": "alu_driver.sv", "line": 46, "state": "65 ns · PIPELINED RSP", "desc": "Driver completes ADD(x,y), copies id info via rsp.set_id_info(req), and returns rsp1.", "log_snippet": "Launching parallel smoke + layered"},
            {"step": 4, "title": "4. Layered Step 2 Consumes Response", "component": "alu_layered_frame_seq", "file": "alu_seq.sv", "line": 66, "state": "105 ns · LAYERED", "desc": "Layered sequence passes rsp1.result[15:0] as operand 'a' for step2 MUL -> (x+y)*scale.", "log_snippet": "Macro (18 + 27) * 3 = 135"}
        ],
        "quizzes": [
            {
                "q": "Why must a pipelined driver call rsp.set_id_info(req) before seq_item_port.put(rsp)?",
                "options": [
                    "To allocate memory in uvm_factory",
                    "To copy sequence_id and transaction_id so the sequencer routes the response to the exact waiting sequence thread",
                    "To reset the virtual interface signals"
                ],
                "answer": 1,
                "explanation": "When multiple sequences run concurrently, sequence_id and transaction_id uniquely identify which sequence's get_response(rsp) should wake up."
            },
            {
                "q": "Does a Virtual Sequencer connect directly to any uvm_driver?",
                "options": [
                    "Yes, it has its own seq_item_port driving RTL pins",
                    "No, it only holds references to underlying protocol sequencers so a virtual sequence can coordinate them",
                    "Only when operating in UVM_PASSIVE mode"
                ],
                "answer": 1,
                "explanation": "A virtual sequencer coordinates sub-sequencers; actual pin driving still belongs strictly to each agent's driver."
            }
        ],
    },

    # =========================================================================
    # CHAPTER 8: Non-Intrusive Extension — Callbacks, Report Catcher & Cmdline
    # =========================================================================
    {
        "num": 8,
        "slug": "ch08_callbacks_reporting",
        "part": "Production UVM",
        "part_title": "IV. Production UVM, RAL, TLM-2, DPI-C & Capstone",
        "title": "08. Non-Intrusive Extension: Callbacks, Report Catcher & Cmdline",
        "short_title": "08. Callbacks & Reporting",
        "difficulty": "Advanced",
        "src_dir": "ch08_callbacks_reporting",
        "dut_files": ["dut/pkt_alu.sv"],
        "inherit_from": "ch07_pipelined_layered_vseq",
        "primary_file": "alu_driver_cb.sv",
        "summary": (
            "Customize VIP behavior without modifying source code: inject faults via uvm_callback hooks, "
            "intercept and demote expected negative-test errors with uvm_report_catcher, and control simulation "
            "behavior dynamically from the command line using uvm_cmdline_processor."
        ),
        "apis": [
            "uvm_callback", "`uvm_register_cb", "`uvm_do_callbacks",
            "uvm_report_catcher", "uvm_report_handler", "uvm_cmdline_processor"
        ],
        "objectives": [
            "Instrument a VIP driver cleanly with `` `uvm_register_cb `` and `` `uvm_do_callbacks ``.",
            "Inject targeted error transactions from a test using `uvm_callbacks#(alu_driver, alu_driver_cb)::add()` without altering sequence or driver code.",
            "Use `uvm_report_catcher` to intercept expected `UVM_ERROR` IDs (`ALU_ERR_INJ`) during fault-injection tests and demote them safely.",
            "Parse custom `+PLUSARGS` at runtime with `uvm_cmdline_processor::get_inst()`."
        ],
        "interactive_widget": "arch_diff",
        "new_components": ["err_cb", "report_catcher"],
        "docs_links": [
            _doc("uvm_callback", "base/uvm_callback-svh.html#uvm_callback", "Base callback class and registration pool."),
            _doc("Callback Macros", "macros/uvm_callback_defines-svh.html", "`uvm_register_cb and `uvm_do_callbacks macros."),
            _doc("uvm_report_catcher", "base/uvm_report_catcher-svh.html#uvm_report_catcher", "Intercept, modify, promote, or demote UVM reports."),
            _doc("Reporting Overview", "overviews/reporting-txt.html", "UVM reporting severity, verbosity, and actions."),
            _doc("uvm_cmdline_processor", "base/uvm_cmdline_processor-svh.html#uvm_cmdline_processor", "Read simulation +plusargs dynamically."),
            _doc("Cmdline Overview", "overviews/cmdlineproc-txt.html", "Standard UVM CLI arguments and custom flags."),
        ],
        "example_links": [
            _ex("Callback Hooks", "infrastructure/callbacks.html", "Injecting error packets via uvm_callback."),
        ],
        "markdown_body": """
## 8.1 Extending Locked VIPs with `uvm_callback`

When verifying with third-party or shared company VIPs, **you must not edit the VIP driver** just to inject one protocol glitch or corrupt a specific packet tag.

```mermaid
flowchart LR
    TEST["alu_base_test (+INJECT_ERR=1)"] -->|"callbacks::add(drv, err_cb)"| CB["alu_err_inject_cb"]
    TEST -->|"report_cb::add(null, catcher)"| RC["alu_report_catcher"]
    DRV["alu_driver"] -->|"uvm_do_callbacks(pre_drive)"| CB
    CB -->|"mutates tag=2 to ALU_INVAL + UVM_ERROR"| RC
    RC -->|"demotes UVM_ERROR to UVM_INFO"| LOG["Clean Passing Negative Test"]
```

In **`alu_driver.sv`**, two macro lines expose an extensible hook:
1. `` `uvm_register_cb(alu_driver, alu_driver_cb) `` inside the class declaration.
2. `` `uvm_do_callbacks(alu_driver, alu_driver_cb, pre_drive(this, req)) `` right before driving pins.

If zero callbacks are registered, `` `uvm_do_callbacks `` is a zero-cost no-op. When `+INJECT_ERR=1` is passed on the simulator command line, `alu_base_test` attaches **`alu_err_inject_cb`** to mutate `tag == 2` into `ALU_INVAL`!

---

## 8.2 Negative Testing & `uvm_report_catcher`

Error-injection tests intentionally trigger error messages (`ALU_ERR_INJ`). If left at `UVM_ERROR`, regression scripts mark the simulation as **FAILED**.
**`alu_report_catcher`** intercepts every report before it reaches the console:
- Matches `get_severity() == UVM_ERROR && get_id() == "ALU_ERR_INJ"`,
- Calls `set_severity(UVM_INFO)` and prepends `"[CAUGHT & DEMOTED] "`,
- Returns `THROW` (so any chained catchers still run) while letting real unexpected bugs fail loudly!
""",
        "sim_log": """UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
UVM_INFO alu_test.sv(38) @ 0: uvm_test_top [TEST] Registered alu_err_inject_cb + alu_report_catcher via +INJECT_ERR=1
UVM_INFO alu_virtual_seq.sv(18) @ 25: uvm_test_top.env.v_seqr@@vseq [VSEQ] Phase 1: Configuring CTRL register via APB agent (EN=1, SAT_EN=0)
UVM_INFO alu_driver_cb.sv(25) @ 75: reporter [ALU_ERR_INJ] [CAUGHT & DEMOTED] Callback injecting invalid opcode on tag=2
UVM_INFO alu_scoreboard.sv(44) @ 85: uvm_test_top.env.scb [SCB] MATCH tag=2 op=ALU_INVAL result=0xdeadbeef err=1
UVM_INFO alu_scoreboard.sv(59) @ 190: uvm_test_top.env.scb [SCB] Scoreboard Summary: PASS=8 FAIL=0
--- UVM Report Summary ---
UVM_INFO :    18
UVM_ERROR :   0""",
        "stepper": [
            {"step": 1, "title": "1. Parse +INJECT_ERR=1 via Cmdline Processor", "component": "alu_base_test", "file": "alu_test.sv", "line": 31, "state": "0 ns · START_OF_SIM", "desc": "uvm_cmdline_processor inspects +INJECT_ERR=1 and registers callback + report catcher.", "log_snippet": "Registered alu_err_inject_cb"},
            {"step": 2, "title": "2. Driver Invokes Pre-Drive Callback", "component": "alu_driver", "file": "alu_driver.sv", "line": 34, "state": "75 ns · CALLBACK", "desc": "`uvm_do_callbacks calls err_cb.pre_drive(this, req), mutating tag=2 to ALU_INVAL.", "log_snippet": "Callback injecting invalid opcode"},
            {"step": 3, "title": "3. Report Catcher Intercepts & Demotes", "component": "alu_report_catcher", "file": "alu_report_catcher.sv", "line": 17, "state": "75 ns · CATCH", "desc": "alu_report_catcher catches UVM_ERROR [ALU_ERR_INJ] and demotes it to UVM_INFO.", "log_snippet": "[CAUGHT & DEMOTED]"},
            {"step": 4, "title": "4. Monitor & Scoreboard Observe Injected Fault", "component": "alu_scoreboard", "file": "alu_scoreboard.sv", "line": 44, "state": "85 ns · CHECK", "desc": "Because monitor observes real pins, scoreboard sees ALU_INVAL and verifies DUT outputs 0xdeadbeef & err=1!", "log_snippet": "MATCH tag=2 op=ALU_INVAL"}
        ],
        "quizzes": [
            {
                "q": "When should you choose a uvm_callback instead of a uvm_factory override?",
                "options": [
                    "When you want to inject a lightweight behavioral hook (e.g. error injection on specific cycles) into an existing component instance without subclassing and replacing the whole component",
                    "Whenever creating a sequence item",
                    "When replacing the RTL DUT module"
                ],
                "answer": 0,
                "explanation": "Callbacks attach multiple orthogonal hooks dynamically per instance without duplicating or subclassing the entire driver."
            },
            {
                "q": "What is the difference between returning CAUGHT vs. THROW inside uvm_report_catcher::catch()?",
                "options": [
                    "CAUGHT suppresses the report completely from being printed or passing to further catchers; THROW lets the (possibly modified) report continue down the catcher chain and print",
                    "THROW aborts the simulation with $fatal",
                    "They behave identically"
                ],
                "answer": 0,
                "explanation": "Returning THROW after calling set_severity(UVM_INFO) prints the demoted report cleanly; returning CAUGHT drops the message silently."
            }
        ],
    },

    # =========================================================================
    # CHAPTER 9: Sub-Phases, Domains, Barriers, Events & Heartbeat
    # =========================================================================
    {
        "num": 9,
        "slug": "ch09_phasing_sync_heartbeat",
        "part": "Production UVM",
        "part_title": "IV. Production UVM, RAL, TLM-2, DPI-C & Capstone",
        "title": "09. Phasing Sub-Phases, Domains, Synchronization & Heartbeat",
        "short_title": "09. Phasing, Sync & Heartbeat",
        "difficulty": "Advanced",
        "src_dir": "ch09_phasing_sync_heartbeat",
        "dut_files": ["dut/pkt_alu.sv"],
        "inherit_from": "ch08_callbacks_reporting",
        "primary_file": "alu_test.sv",
        "summary": (
            "Master complex simulation lifecycle orchestration: structure traffic cleanly across UVM run-time "
            "sub-phases (reset/configure/main/shutdown), isolate bus clocks with uvm_domain, coordinate parallel "
            "sequences via uvm_event_pool & uvm_barrier, and prevent silent hangs using uvm_heartbeat."
        ),
        "apis": [
            "uvm_phase", "uvm_domain", "uvm_barrier", "uvm_event",
            "uvm_event_pool", "uvm_heartbeat", "uvm_runtime_phases"
        ],
        "objectives": [
            "Split monolithic `run_phase` code cleanly across `reset_phase`, `configure_phase`, `main_phase`, and `shutdown_phase`.",
            "Configure an independent `uvm_domain` for the APB agent and keep it synchronized with the common domain via `domain.sync()`.",
            "Synchronize parallel sequence threads using `uvm_event_pool` and `uvm_barrier`.",
            "Protect regressions against deadlocked simulations using `uvm_heartbeat` liveness monitoring."
        ],
        "interactive_widget": "arch_diff",
        "new_components": ["apb_domain", "heartbeat_watchdog"],
        "docs_links": [
            _doc("Phasing Overview", "overviews/phasing-txt.html", "Common phases vs. run-time sub-phases execution schedule."),
            _doc("uvm_runtime_phases", "base/uvm_runtime_phases-svh.html", "reset, configure, main, shutdown sub-phases."),
            _doc("uvm_domain", "base/uvm_domain-svh.html#uvm_domain", "Domain isolation and cross-domain phase synchronization."),
            _doc("Synchronization Overview", "overviews/synchro-txt.html", "uvm_event, uvm_event_pool, and uvm_barrier."),
            _doc("uvm_barrier", "base/uvm_barrier-svh.html#uvm_barrier", "Multi-process rendezvous threshold synchronization."),
            _doc("uvm_heartbeat", "base/uvm_heartbeat-svh.html#uvm_heartbeat", "Watchdog detecting stalled or hung UVM components."),
        ],
        "example_links": [
            _ex("Phased Execution Lifecycle", "phasing/basic.html", "Top-down vs. bottom-up phase execution."),
            _ex("Phase Objections & Drain Time", "phasing/objections.html", "Coordinating shutdown with drain_time."),
            _ex("Event Synchronization (Pool)", "phasing/event_pool.html", "Global uvm_event_pool rendezvous."),
        ],
        "markdown_body": """
## 9.1 Structuring Execution Across Run-Time Sub-Phases

In complex SoC testbenches, placing reset waiting, register configuration, main traffic, and end-of-test drain all inside a single `run_phase()` turns tests into tangled spaghetti. UVM splits `run_phase` in parallel with **12 fine-grained run-time sub-phases**—most importantly:

```mermaid
flowchart LR
    R["reset_phase"] --> C["configure_phase"] --> M["main_phase (+ drain_time)"] --> S["shutdown_phase"]
```

In **`alu_test.sv`**:
- **`reset_phase`**: waits for `rst_n == 1` before any configuration runs.
- **`configure_phase`**: programs `SAT_LIMIT` over APB *before* datapath sequences start.
- **`main_phase`**: executes `alu_virtual_seq`, activates **`uvm_heartbeat`**, and sets `phase.phase_done.set_drain_time(this, 20ns)`.
- **`shutdown_phase`**: cleanly drains final pipelined packets and performs end-of-test register checks.

---

## 9.2 Synchronization Primitives & `uvm_heartbeat`

1. **`uvm_event_pool` & `uvm_barrier` (`alu_virtual_seq.sv`):**
   - `uvm_event_pool::get_global_pool().get("cfg_done")` lets any monitor, sequence, or scoreboard wait on named milestones without global variable spaghetti.
   - `uvm_barrier("sync_bar", 2)` guarantees `seq_a` and `seq_b` hit the starting gate together before competing on `alu_sqr`.
2. **`uvm_domain` (`alu_env.sv`):**
   - Isolates `apb_agt` inside `apb_domain`, synchronized in lockstep with `uvm_domain::get_common_domain()` via `apb_domain.sync(...)`—ready for multi-reset SoCs!
3. **`uvm_heartbeat`:**
   - Watches registered components (`data_agent.drv`). If a bus deadlock prevents `hb_obj` activity between two `hb_trig` triggers, UVM immediately terminates with `UVM_FATAL [HBFAIL]` instead of burning hours of compute!
""",
        "sim_log": """UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
UVM_INFO alu_test.sv(34) @ 0: uvm_test_top [PHASE] Executing reset_phase: waiting for DUT reset release
UVM_INFO alu_test.sv(42) @ 25: uvm_test_top [PHASE] Executing configure_phase: programming SAT_LIMIT=0x1000
UVM_INFO alu_virtual_seq.sv(28) @ 55: uvm_test_top.env.v_seqr@@vseq [VSEQ] Triggered global 'cfg_done' uvm_event; syncing threads with uvm_barrier
UVM_INFO alu_seq.sv(72) @ 115: uvm_test_top.env.data_agent.seqr@@seq_b [LAYERED_SEQ] Macro (12 + 34) * 2 = 92
UVM_INFO alu_test.sv(74) @ 190: uvm_test_top [PHASE] Executing shutdown_phase: draining final pipeline responses
UVM_INFO alu_scoreboard.sv(59) @ 210: uvm_test_top.env.scb [SCB] Scoreboard Summary: PASS=8 FAIL=0
--- UVM Report Summary ---
UVM_INFO :    21
UVM_ERROR :   0""",
        "stepper": [
            {"step": 1, "title": "1. Bind APB Domain & Heartbeat", "component": "alu_env", "file": "alu_env.sv", "line": 59, "state": "0 ns · CONNECT", "desc": "alu_env puts apb_agt into apb_domain synced with common_domain and registers data_agent.drv in uvm_heartbeat.", "log_snippet": "Running test alu_base_test"},
            {"step": 2, "title": "2. Execute reset_phase & configure_phase", "component": "alu_base_test", "file": "alu_test.sv", "line": 42, "state": "25 ns · CONFIGURE", "desc": "Only after reset_phase finishes does configure_phase program SAT_LIMIT=0x1000 over APB.", "log_snippet": "Executing configure_phase"},
            {"step": 3, "title": "3. Barrier & Event Sync in main_phase", "component": "alu_virtual_seq", "file": "alu_virtual_seq.sv", "line": 28, "state": "55 ns · SYNC", "desc": "vseq triggers 'cfg_done' uvm_event and aligns parallel sequences at sync_bar.wait_for().", "log_snippet": "Triggered global 'cfg_done'"},
            {"step": 4, "title": "4. Heartbeat Watch & shutdown_phase", "component": "alu_base_test", "file": "alu_test.sv", "line": 74, "state": "190 ns · SHUTDOWN", "desc": "After main_phase drain_time expires, heartbeat stops and shutdown_phase drains final responses.", "log_snippet": "Executing shutdown_phase"}
        ],
        "quizzes": [
            {
                "q": "What happens if an agent implements run_phase() while tests implement main_phase()?",
                "options": [
                    "UVM skips run_phase completely",
                    "run_phase runs in parallel with the entire reset/configure/main/shutdown sub-phase schedule—ideal for passive monitors and forever driver loops",
                    "It triggers a compile error"
                ],
                "answer": 1,
                "explanation": "Drivers and monitors normally stay in forever loops inside run_phase() while tests orchestrate scenarios across reset/configure/main/shutdown."
            },
            {
                "q": "How does uvm_heartbeat catch a hung simulation?",
                "options": [
                    "It monitors that registered components raise/drop activity on a heartbeat objection between trigger pulses of an event",
                    "It counts the total lines in the Makefile",
                    "It disables all objections"
                ],
                "answer": 0,
                "explanation": "If no monitored component touches the heartbeat objection within a trigger window, uvm_heartbeat raises UVM_FATAL to abort hung simulations quickly."
            }
        ],
    },

    # =========================================================================
    # CHAPTER 10: Register Abstraction Layer (RAL)
    # =========================================================================
    {
        "num": 10,
        "slug": "ch10_ral",
        "part": "Production UVM",
        "part_title": "IV. Production UVM, RAL, TLM-2, DPI-C & Capstone",
        "title": "10. Register Abstraction Layer (RAL): Block, Adapter & Predictor",
        "short_title": "10. Register Layer (RAL)",
        "difficulty": "Advanced",
        "src_dir": "ch10_ral",
        "dut_files": ["dut/pkt_alu.sv"],
        "inherit_from": "ch09_phasing_sync_heartbeat",
        "primary_file": "pkt_alu_reg_block.sv",
        "summary": (
            "Replace raw hex APB addresses with an object-oriented Register Model: build uvm_reg_block, "
            "uvm_reg, uvm_reg_field, and uvm_reg_map; translate register ops with apb_reg_adapter; maintain "
            "desired/mirrored coherence via uvm_reg_predictor; and verify registers via frontdoor, backdoor, "
            "and built-in sequences."
        ),
        "apis": [
            "uvm_reg_block", "uvm_reg", "uvm_reg_field", "uvm_reg_map",
            "uvm_reg_adapter", "uvm_reg_predictor", "uvm_reg_hw_reset_seq"
        ],
        "objectives": [
            "Model `CTRL`, `STATUS` (RO/W1C), `SAT_LIMIT`, and `PKT_COUNT` with exact bitfields, access policies, and reset values in `pkt_alu_reg_block`.",
            "Implement `reg2bus()` and `bus2reg()` inside `apb_reg_adapter` so RAL stays completely bus-agnostic.",
            "Wire `uvm_reg_predictor #(apb_item)` to `apb_agt.ap` (explicit prediction) so even non-RAL APB writes update the RAL mirror.",
            "Use `reg_model.SAT_LIMIT.get_mirrored_value()` directly inside `alu_scoreboard` and run `uvm_reg_hw_reset_seq` + backdoor `peek()`."
        ],
        "interactive_widget": "arch_diff",
        "new_components": ["ral_block", "reg_adapter", "reg_predictor"],
        "docs_links": [
            _doc("Registers Overview", "overviews/registers-txt.html", "Complete UVM Register Layer architecture & concepts."),
            _doc("uvm_reg_block", "reg/uvm_reg_block-svh.html#uvm_reg_block", "Top-level container for registers, fields, and address maps."),
            _doc("uvm_reg", "reg/uvm_reg-svh.html#uvm_reg", "Individual register abstraction with desired & mirrored state."),
            _doc("uvm_reg_adapter", "reg/uvm_reg_adapter-svh.html#uvm_reg_adapter", "Bus-protocol translator (reg2bus / bus2reg)."),
            _doc("uvm_reg_predictor", "reg/uvm_reg_predictor-svh.html#uvm_reg_predictor", "Passively updates RAL mirror from monitored bus transactions."),
            _doc("uvm_reg_hw_reset_seq", "reg/sequences/uvm_reg_hw_reset_seq-svh.html", "Built-in hardware reset value checker sequence."),
        ],
        "example_links": [
            _ex("RAL Primer & Bus Adapter", "registers/primer.html", "Frontdoor read/write & mirror checking."),
            _ex("Register Sequence Convenience API", "registers/sequence_api.html", "Clean RAL access APIs inside sequences."),
        ],
        "markdown_body": """
## 10.1 Why RAL Eliminates Raw Address Hardcoding

Writing `addr = 8'h08; data = 32'h800;` across 200 tests breaks immediately if a register moves from `0x08` to `0x14`.
With **UVM RAL (`pkt_alu_reg_block.sv`)**, tests write intent symbolically:
```systemverilog
env.reg_model.SAT_LIMIT.write(status, 32'h0000_0800, UVM_FRONTDOOR);
```

```mermaid
flowchart LR
    SEQ["Test / Sequence: CTRL.write(3)"] --> MAP["uvm_reg_map (apb_map)"]
    MAP -->|"reg2bus()"| ADP["apb_reg_adapter"]
    ADP -->|"apb_item"| APB["apb_agt.drv -> DUT"]
    APB -->|"apb_agt.mon (ap)"| PRED["uvm_reg_predictor"]
    PRED -->|"bus2reg()"| MAP
    MAP -->|"updates mirror"| SCB["alu_scoreboard.get_mirrored_value()"]
```

---

## 10.2 Explicit Prediction & Backdoor Access

1. **Explicit Prediction (`set_auto_predict(0)`):** Every bus access observed by `apb_monitor` enters `reg_predictor.bus_in`, converts back via `apb_reg_adapter::bus2reg()`, and updates the RAL **mirrored value**—even if another bus master (not RAL!) wrote the register.
2. **Frontdoor vs. Backdoor:** `UVM_FRONTDOOR` cycles real APB pins (`psel`/`penable`); `UVM_BACKDOOR` (`peek()`/`poke()` via `add_hdl_path("tb_top.u_dut")`) reads RTL signals directly in **0 simulation time**.
3. **Built-in Register Tests:** `uvm_reg_hw_reset_seq` automatically sweeps every register in `apb_map` and checks its hardware reset value!
""",
        "sim_log": """UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
UVM_INFO uvm_reg_hw_reset_seq.svh(140) @ 35: reporter [uvm_reg_hw_reset_seq] Verifying reset values of registers in apb_map...
UVM_INFO alu_test.sv(44) @ 75: uvm_test_top [RAL] Backdoor peek SAT_LIMIT = 0x0800 (mirrored=0x0800)
UVM_INFO alu_scoreboard.sv(56) @ 140: uvm_test_top.env.scb [SCB] RAL-Aware Scoreboard Summary: PASS=6 FAIL=0
UVM_INFO alu_test.sv(55) @ 180: uvm_test_top [RAL] Frontdoor PKT_COUNT = 6
--- UVM Report Summary ---
UVM_INFO :    14
UVM_ERROR :   0""",
        "stepper": [
            {"step": 1, "title": "1. Bind RAL Map, Adapter & Predictor", "component": "alu_env", "file": "alu_env.sv", "line": 53, "state": "0 ns · CONNECT", "desc": "alu_env maps apb_map to apb_agt.seqr via apb_reg_adapter and wires apb_agt.ap into reg_predictor.", "log_snippet": "Running test alu_base_test"},
            {"step": 2, "title": "2. Run Built-In Hardware Reset Sequence", "component": "alu_base_test", "file": "alu_test.sv", "line": 36, "state": "35 ns · RESET SEQ", "desc": "uvm_reg_hw_reset_seq verifies default reset values of CTRL, STATUS, SAT_LIMIT, and PKT_COUNT.", "log_snippet": "Verifying reset values"},
            {"step": 3, "title": "3. Frontdoor Write + Backdoor Peek", "component": "pkt_alu_reg_block", "file": "alu_test.sv", "line": 44, "state": "75 ns · RAL ACCESS", "desc": "Test writes SAT_LIMIT=0x0800 over APB frontdoor and cross-checks via 0-time HDL backdoor peek().", "log_snippet": "Backdoor peek SAT_LIMIT = 0x0800"},
            {"step": 4, "title": "4. Scoreboard Adapts via RAL Mirror", "component": "alu_scoreboard", "file": "alu_scoreboard.sv", "line": 47, "state": "140 ns · MIRROR CHECK", "desc": "Scoreboard queries reg_model.CTRL.sat_en.get_mirrored_value() to apply saturation clamping automatically.", "log_snippet": "Frontdoor PKT_COUNT = 6"}
        ],
        "quizzes": [
            {
                "q": "Why is explicit prediction (uvm_reg_predictor + set_auto_predict(0)) recommended over auto-predict?",
                "options": [
                    "Because auto-predict does not support uvm_reg_block",
                    "Because explicit prediction updates the RAL mirror from actual monitored bus transactions—even when non-RAL sequences or other SoC masters write registers",
                    "Because auto-predict disables backdoor peek()"
                ],
                "answer": 1,
                "explanation": "Explicit prediction guarantees the mirror stays synchronized with true pin activity on the bus regardless of who initiated the transfer."
            },
            {
                "q": "What is the difference between desired and mirrored values in uvm_reg?",
                "options": [
                    "Mirrored holds what we believe is currently in DUT hardware; desired holds the value queued for the next update()",
                    "Desired is read-only; mirrored is write-only",
                    "They are aliases for the same variable"
                ],
                "answer": 0,
                "explanation": "You can randomize/set desired values across fields first, then call reg_block.update() to flush only registers where desired != mirrored."
            }
        ],
    },

    # =========================================================================
    # CHAPTER 11: TLM-2.0 Sockets, Generic Payload & Temporal Decoupling
    # =========================================================================
    {
        "num": 11,
        "slug": "ch11_tlm2_sockets",
        "part": "Production UVM",
        "part_title": "IV. Production UVM, RAL, TLM-2, DPI-C & Capstone",
        "title": "11. TLM-2.0 Sockets, Generic Payload & Temporal Decoupling",
        "short_title": "11. TLM-2.0 & Sockets",
        "difficulty": "Advanced",
        "src_dir": "ch11_tlm2_sockets",
        "dut_files": ["dut/pkt_alu.sv"],
        "inherit_from": "ch10_ral",
        "primary_file": "alu_tlm2_bridge.sv",
        "summary": (
            "Bridge SystemVerilog testbenches with architectural SystemC/ESL models using UVM TLM-2.0: "
            "pack transactions into uvm_tlm_generic_payload, connect bidirectional initiator/target sockets, "
            "execute 4-phase nb_transport_fw/bw handshakes, and track local time quanta with uvm_tlm_time."
        ),
        "apis": [
            "uvm_tlm_nb_initiator_socket", "uvm_tlm_nb_target_socket", "uvm_tlm_generic_payload",
            "uvm_tlm_time", "uvm_tlm_ifs"
        ],
        "objectives": [
            "Differentiate TLM-1 unidirectional ports/exports from TLM-2.0 bidirectional sockets (`nb_initiator_socket` ↔ `nb_target_socket`).",
            "Serialize protocol items into standardized `uvm_tlm_generic_payload` byte arrays (`set_address`, `set_data`, `set_write`).",
            "Implement the 4-phase non-blocking handshake (`BEGIN_REQ`, `END_REQ`, `BEGIN_RESP`, `END_RESP`) across `nb_transport_fw` and `nb_transport_bw`.",
            "Apply temporal decoupling via `uvm_tlm_time` quantum accumulation for high-speed virtual platform modeling."
        ],
        "interactive_widget": "arch_diff",
        "new_components": ["tlm2_bridge"],
        "docs_links": [
            _doc("TLM-2 Overview", "overviews/tlm2-txt.html", "TLM-2.0 standard concepts, blocking vs. non-blocking & sockets."),
            _doc("uvm_tlm2_sockets", "tlm2/uvm_tlm2_sockets-svh.html", "Initiator, target, and passthrough TLM-2 sockets."),
            _doc("uvm_tlm_generic_payload", "tlm2/uvm_tlm2_generic_payload-svh.html#uvm_tlm_generic_payload", "Interoperable memory-mapped bus payload class."),
            _doc("uvm_tlm_time", "tlm2/uvm_tlm2_time-svh.html#uvm_tlm_time", "Resolution-independent delay and quantum time tracker."),
        ],
        "example_links": [
            _ex("Blocking TLM-2 Transport", "tlm-2/blocking_simple.html", "Simple b_transport initiator/target socket pair."),
            _ex("Non-Blocking 4-Phase Protocol", "tlm-2/nonblocking_simple.html", "Interactive 4-phase nb_transport_fw/bw walkthrough."),
            _ex("Temporal Decoupling & Quantum", "tlm-2/temporal_decoupling.html", "uvm_tlm_time quantum synchronization."),
        ],
        "markdown_body": """
## 11.1 TLM-1 vs. TLM-2.0: When Do You Need Sockets?

TLM-1 (`uvm_analysis_port`, `uvm_tlm_fifo`) excels inside UVM testbenches, whereas **TLM-2.0** mirrors the IEEE 1666 SystemC standard so SystemVerilog models interoperate seamlessly with fast C++/SystemC architectural simulators:

| Feature | TLM-1 | TLM-2.0 |
| :--- | :--- | :--- |
| **Connection** | Separate `port` + `export` + `imp` | Single **Bidirectional Socket** (`connect()` wires both FW & BW paths!) |
| **Payload** | Custom `uvm_sequence_item` | Standard **`uvm_tlm_generic_payload`** (addr, command, byte array, response status) |
| **Timing** | Untimed / blocking tasks | **Temporal Decoupling** (`uvm_tlm_time` quantum) & 4-phase AT protocol |

---

## 11.2 4-Phase Non-Blocking Handshake & Temporal Decoupling

```mermaid
sequenceDiagram
    participant Init as alu_tlm2_bridge (Initiator)
    participant Tgt as alu_ref_model (Target)

    Init->>Tgt: nb_transport_fw(gp, BEGIN_REQ, local_quantum)
    Note over Tgt: Decodes gp byte array -> predict(tr)
    Tgt->>Init: nb_transport_bw(gp, BEGIN_RESP, delay)
    Init-->>Tgt: phase = END_RESP, return UVM_TLM_COMPLETED
```

In **`alu_tlm2_bridge.sv`**, each monitored `alu_item` is serialized into `uvm_tlm_generic_payload`, increments `local_quantum` by `5ns`, and dispatches `nb_init_socket.nb_transport_fw(...)` directly to `alu_ref_model.nb_target_socket`.
""",
        "sim_log": """UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
UVM_INFO alu_tlm2_bridge.sv(54) @ 35: uvm_test_top.env.tlm2_bridge [TLM2] FW BEGIN_REQ addr=0x1000 sync=UVM_TLM_UPDATED
UVM_INFO alu_tlm2_bridge.sv(66) @ 35: uvm_test_top.env.tlm2_bridge [TLM2] BW BEGIN_RESP -> END_RESP status=UVM_TLM_OK_RESPONSE
UVM_INFO alu_tlm2_bridge.sv(49) @ 65: uvm_test_top.env.tlm2_bridge [TLM2] Quantum limit reached (20 ns), syncing local time
UVM_INFO alu_scoreboard.sv(56) @ 180: uvm_test_top.env.scb [SCB] RAL-Aware Scoreboard Summary: PASS=6 FAIL=0
--- UVM Report Summary ---
UVM_INFO :    17
UVM_ERROR :   0""",
        "stepper": [
            {"step": 1, "title": "1. Connect TLM-2 Initiator & Target Sockets", "component": "alu_env", "file": "alu_env.sv", "line": 69, "state": "0 ns · CONNECT", "desc": "A single socket connect() binds forward and backward paths between tlm2_bridge and ref_model.", "log_snippet": "Running test alu_base_test"},
            {"step": 2, "title": "2. Marshal alu_item -> uvm_tlm_generic_payload", "component": "alu_tlm2_bridge", "file": "alu_tlm2_bridge.sv", "line": 31, "state": "35 ns · PACK GP", "desc": "write() packs op, tag, a, b into an 8-byte generic payload and increments uvm_tlm_time quantum.", "log_snippet": "FW BEGIN_REQ"},
            {"step": 3, "title": "3. Target Processes Forward & Replies Backward", "component": "alu_ref_model", "file": "alu_ref_model.sv", "line": 44, "state": "35 ns · NB_TRANSPORT", "desc": "nb_transport_fw extracts bytes, predicts result, sets OK status, and fires nb_transport_bw.", "log_snippet": "BW BEGIN_RESP"},
            {"step": 4, "title": "4. Quantum Sync Boundary", "component": "alu_tlm2_bridge", "file": "alu_tlm2_bridge.sv", "line": 49, "state": "65 ns · QUANTUM", "desc": "When accumulated local_quantum hits 20 ns, bridge resets quantum and synchronizes with global simulation time.", "log_snippet": "Quantum limit reached"}
        ],
        "quizzes": [
            {
                "q": "Why does TLM-2 require only ONE connect() call between initiator and target sockets?",
                "options": [
                    "Because TLM-2 sockets bundle both the forward port/imp and backward export/imp into a single bidirectional endpoint",
                    "Because TLM-2 does not allow responses",
                    "Because sockets bypass connect_phase()"
                ],
                "answer": 0,
                "explanation": "Each socket simultaneously acts as initiator/port for forward calls and target/export for backward calls, halving connection boilerplate."
            },
            {
                "q": "What is the purpose of uvm_tlm_time in temporal decoupling?",
                "options": [
                    "To print wall-clock CPU hours",
                    "To let fast virtual-platform transactions advance locally inside a time quantum before yielding to the global simulator scheduler",
                    "To slow down RTL clock edges"
                ],
                "answer": 1,
                "explanation": "Batching multiple transactions inside a local time quantum drastically reduces expensive context switches in high-level architectural simulation."
            }
        ],
    },

    # =========================================================================
    # CHAPTER 12: DPI-C Integration & Vertical Block-to-SoC Reuse
    # =========================================================================
    {
        "num": 12,
        "slug": "ch12_dpi_vertical_reuse",
        "part": "Production UVM",
        "part_title": "IV. Production UVM, RAL, TLM-2, DPI-C & Capstone",
        "title": "12. DPI-C C/C++ Reference Integration & Vertical SoC Reuse",
        "short_title": "12. DPI-C & Vertical Reuse",
        "difficulty": "Advanced",
        "src_dir": "ch12_dpi_vertical_reuse",
        "dut_files": ["dut/pkt_alu.sv", "c_model/pkt_alu_ref.c"],
        "inherit_from": "ch11_tlm2_sockets",
        "primary_file": "soc_subsys_env.sv",
        "summary": (
            "Connect SystemVerilog verification directly to production C/C++ golden models via SystemVerilog DPI-C "
            "(import \"DPI-C\"), and wrap our entire block environment inside soc_subsys_env to demonstrate vertical "
            "block-to-SoC reuse using UVM_PASSIVE mode."
        ),
        "apis": [
            "uvm_agent", "uvm_env", "uvm_active_passive_enum", "uvm_dpi"
        ],
        "objectives": [
            "Declare C ABI functions cleanly in SystemVerilog using `import \"DPI-C\" function` (`pkt_alu_dpi_pkg.sv`).",
            "Delegate golden reference prediction from `alu_ref_model` into compiled C (`c_model/pkt_alu_ref.c`) without writing bit-twiddling models twice.",
            "Compile C and SystemVerilog together in simulator Makefiles (`vlog ... ../c_model/pkt_alu_ref.c`).",
            "Reuse an entire block-level `alu_env` unchanged inside a subsystem/SoC wrapper (`soc_subsys_env`) by switching internal agents to `UVM_PASSIVE`."
        ],
        "interactive_widget": "arch_diff",
        "new_components": ["pkt_alu_dpi_pkg", "c_model", "soc_subsys_env"],
        "docs_links": [
            _doc("UVM DPI-C Interface", "dpi/uvm_dpi-svh.html", "How UVM 1.2 itself bridges SystemVerilog and C via DPI."),
            _doc("UVM HDL Backdoor DPI", "dpi/uvm_hdl-svh.html", "DPI-based RTL hierarchical path access used by RAL backdoor."),
            _doc("uvm_agent (Passive Mode)", "comps/uvm_agent-svh.html#uvm_agent", "Reusing monitors & checkers when external SoC masters drive pins."),
        ],
        "example_links": [
            _ex("Vertical Register Reuse", "registers/vertical_reuse.html", "Official UVM example scaling block env into subsystem env."),
        ],
        "markdown_body": """
## 12.1 Zero-Copy Golden Modeling with SystemVerilog DPI-C

Complex DSP, crypto, or AI accelerators already have **gold-standard C/C++ models** written by the Architecture team. Re-coding those algorithms in SystemVerilog invites transcription bugs.
Using **Direct Programming Interface (DPI-C)** (`pkt_alu_dpi_pkg.sv` + `c_model/pkt_alu_ref.c`), `alu_ref_model` invokes compiled C functions directly at native speed:

```mermaid
flowchart LR
    SCB["alu_scoreboard (SV)"] -->|"predict_with_cfg()"| REF["alu_ref_model (SV)"]
    REF -->|"import DPI-C pkt_alu_dpi_calc()"| CMOD["pkt_alu_ref.c (Compiled C)"]
    CMOD -->|"out_result, out_err"| REF
```

Notice in `Makefile.questa`, simulators compile `.c` files directly alongside `.sv` without manual PLI/VPI wrappers!

---

## 12.2 Vertical Reuse: From IP Block to Full SoC (`soc_subsys_env.sv`)

Remember **Chapter 1's V-Cycle** and **Chapter 2's Separation of Concerns**? Because we never put checks in the driver or metrics in the sequence, **`soc_subsys_env`** instantiates `block_alu_env` inside a chip-level testbench:
- When a CPU or DMA master on the SoC now drives `pkt_alu`, setting `passive_reuse_mode = 1` switches `data_agent` and `apb_agt` to **`UVM_PASSIVE`**.
- The drivers and sequencers disappear automatically—while **`alu_monitor`**, **`uvm_reg_predictor`**, **`alu_scoreboard` (with DPI-C C model)**, **`alu_cov_subscriber`**, and **SVA assertions** continue checking 100% of chip traffic unchanged!
""",
        "sim_log": """UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
UVM_INFO alu_test.sv(31) @ 0: uvm_test_top [TEST] Built soc_subsys_env -> block_alu_env (active/passive configurable)
UVM_INFO alu_scoreboard.sv(54) @ 60: uvm_test_top.subsys_env.block_alu_env.scb [SCB] DPI-C MATCH tag=0 result=0x000004d3
UVM_INFO alu_scoreboard.sv(54) @ 70: uvm_test_top.subsys_env.block_alu_env.scb [SCB] DPI-C MATCH tag=1 result=0x00000800
UVM_INFO alu_scoreboard.sv(63) @ 180: uvm_test_top.subsys_env.block_alu_env.scb [SCB] DPI-C + RAL Scoreboard: PASS=6 FAIL=0
--- UVM Report Summary ---
UVM_INFO :    15
UVM_ERROR :   0""",
        "stepper": [
            {"step": 1, "title": "1. Subsystem Wraps Block Environment", "component": "soc_subsys_env", "file": "soc_subsys_env.sv", "line": 34, "state": "0 ns · SUBSYS BUILD", "desc": "soc_subsys_env instantiates block_alu_env and toggles UVM_PASSIVE automatically in SoC reuse mode.", "log_snippet": "Built soc_subsys_env"},
            {"step": 2, "title": "2. DPI-C Import Bridge", "component": "pkt_alu_dpi_pkg", "file": "pkt_alu_dpi_pkg.sv", "line": 7, "state": "0 ns · DPI BIND", "desc": "import \"DPI-C\" binds SystemVerilog predict_with_cfg() to C function pkt_alu_dpi_calc().", "log_snippet": "DPI-C MATCH"},
            {"step": 3, "title": "3. Scoreboard Combines RAL Mirror + C Model", "component": "alu_scoreboard", "file": "alu_scoreboard.sv", "line": 46, "state": "60 ns · DPI-C CHECK", "desc": "Scoreboard pulls live SAT_LIMIT from RAL mirror, calls C model via DPI-C, and verifies saturation clamping.", "log_snippet": "DPI-C MATCH tag=1 result=0x00000800"}
        ],
        "quizzes": [
            {
                "q": "When reusing block_alu_env in a SoC where an embedded RISC-V core drives pkt_alu, what changes inside alu_env?",
                "options": [
                    "You must rewrite the scoreboard and coverage collector from scratch",
                    "You set cfg.data_agent_cfg.is_active = UVM_PASSIVE and cfg.apb_cfg.is_active = UVM_PASSIVE while keeping monitors, RAL predictor, scoreboard, and coverage intact",
                    "You delete alu_monitor.sv"
                ],
                "answer": 1,
                "explanation": "Passive agents disable drivers/sequencers while preserving monitors, predictors, scoreboards, and functional coverage unchanged."
            },
            {
                "q": "What is the main benefit of calling pkt_alu_ref.c through SystemVerilog DPI-C?",
                "options": [
                    "Single golden reference source shared with Architecture/Software without re-implementing algorithms in SystemVerilog",
                    "DPI-C synthesizes C into ASIC silicon gates",
                    "It eliminates the need for clocking blocks"
                ],
                "answer": 0,
                "explanation": "DPI-C lets SystemVerilog testbenches execute the architect's exact C/C++ reference model directly at native speed."
            }
        ],
    },

    # =========================================================================
    # CHAPTER 13: Capstone — Ultra-Complete Dynamic Verification Environment
    # =========================================================================
    {
        "num": 13,
        "slug": "ch13_capstone",
        "part": "Capstone",
        "part_title": "V. Capstone — Ultra-Complete Dynamic Environment",
        "title": "13. Capstone: Ultra-Complete Dynamic Verification Environment",
        "short_title": "13. Dynamic Complete Env",
        "difficulty": "Advanced",
        "src_dir": "ch13_capstone",
        "dut_files": ["dut/pkt_alu.sv", "c_model/pkt_alu_ref.c"],
        "inherit_from": "ch12_dpi_vertical_reuse",
        "primary_file": "alu_test.sv",
        "summary": (
            "Explore the complete production UVM 1.2 environment unifying every layer built across Chapters 1-12: "
            "click any block on the interactive Cytoscape architecture map to inspect its role, jump straight back "
            "to the tutorial chapter that introduced it, inspect its SystemVerilog/C code, or open its official UVM doc; "
            "use the Progressive Layer Slider (Ch.03 -> Ch.12) to replay the build-up; and run the live end-to-end "
            "execution stepper."
        ),
        "apis": [
            "uvm_test", "uvm_env", "uvm_agent", "uvm_sequencer", "uvm_driver", "uvm_monitor",
            "uvm_scoreboard", "uvm_subscriber", "uvm_reg_block", "uvm_tlm_nb_initiator_socket",
            "uvm_callback", "uvm_report_catcher", "uvm_heartbeat", "uvm_dpi"
        ],
        "objectives": [
            "Trace how every UVM layer interacts in a real multi-agent, RAL-, TLM-2-, and DPI-C-enabled testbench.",
            "Replay the incremental construction from a 5-component stimuli bench (Ch.03) up to the full SoC-ready testbench (Ch.12).",
            "Navigate fluidly between any architectural block, its teaching chapter, its SystemVerilog/C source, and its UVM 1.2 reference documentation."
        ],
        "interactive_widget": "capstone",
        "new_components": [],
        "docs_links": [
            _doc("uvm_test", "comps/uvm_test-svh.html#uvm_test", "Test control, sub-phases, factory, and objections."),
            _doc("uvm_env", "comps/uvm_env-svh.html#uvm_env", "Hierarchical verification container."),
            _doc("uvm_reg_block", "reg/uvm_reg_block-svh.html#uvm_reg_block", "Register Abstraction Layer (RAL) root."),
            _doc("uvm_tlm2_sockets", "tlm2/uvm_tlm2_sockets-svh.html", "TLM-2.0 bidirectional sockets."),
            _doc("uvm_callback", "base/uvm_callback-svh.html#uvm_callback", "Non-intrusive fault injection hooks."),
            _doc("uvm_report_catcher", "base/uvm_report_catcher-svh.html#uvm_report_catcher", "Dynamic report demotion & filtering."),
            _doc("uvm_heartbeat", "base/uvm_heartbeat-svh.html#uvm_heartbeat", "Deadlock & hang watchdog."),
            _doc("UVM DPI-C Interface", "dpi/uvm_dpi-svh.html", "SystemVerilog <-> C reference integration."),
        ],
        "example_links": [
            _ex("UBUS Verification Component", "integrated/ubus.html", "Full integrated UVM multi-file VIP suite."),
            _ex("Audio Codec VIP + RAL", "integrated/codec.html", "Integrated multi-interface VIP with RAL & scoreboard."),
        ],
        "markdown_body": """
## 13.1 The Complete Architecture at a Glance

Congratulations—every single block below was earned step by step across Chapters 1 through 12!

Use the **4-in-1 Dynamic Environment Explorer** below to:
1. **Click any component node** on the interactive diagram to highlight its TLM/signal wires, inspect its exact ports and responsibilities, **jump back to the chapter that built it (`← Review Chapter XX`)**, focus its source tab, or open its official **UVM 1.2 Reference Doc**.
2. **Slide the Progressive Build-Up control (`Ch.03 → Ch.13`)** to watch the environment expand incrementally from minimal stimuli to full SoC readiness.
3. **Run the End-to-End Flow Stepper** below to trace a full transaction lifecycle (`RAL Config → Virtual/Layered Seq → Callback Fault Injection → Report Catcher → Monitor → TLM-2 Bridge → C/DPI-C Golden Model → RAL-Aware Scoreboard + Coverage`) synchronized across the diagram, Code Studio, and simulation log.
""",
        "sim_log": """UVM_INFO @ 0: reporter [RNTST] Running test alu_capstone_full_test...
UVM_INFO @ 0: reporter [UVMTOP] UVM testbench topology: uvm_test_top.subsys_env.block_alu_env (14 components)
UVM_INFO alu_test.sv(44) @ 0: uvm_test_top [CAPSTONE] Enabled non-intrusive fault callback & report catcher
UVM_INFO alu_test.sv(66) @ 75: uvm_test_top [CAPSTONE] RAL configured & peeked SAT_LIMIT=0x0800
UVM_INFO alu_virtual_seq.sv(28) @ 80: uvm_test_top.subsys_env.block_alu_env.v_seqr@@vseq [VSEQ] Triggered global 'cfg_done' uvm_event; syncing threads with uvm_barrier
UVM_INFO alu_driver_cb.sv(25) @ 100: reporter [ALU_ERR_INJ] [CAUGHT & DEMOTED] Callback injecting invalid opcode on tag=2
UVM_INFO alu_tlm2_bridge.sv(54) @ 100: uvm_test_top.subsys_env.block_alu_env.tlm2_bridge [TLM2] FW BEGIN_REQ addr=0x1002 sync=UVM_TLM_UPDATED
UVM_INFO alu_scoreboard.sv(54) @ 110: uvm_test_top.subsys_env.block_alu_env.scb [SCB] DPI-C MATCH tag=2 result=0xdeadbeef
UVM_INFO alu_seq.sv(72) @ 145: uvm_test_top.subsys_env.block_alu_env.data_agent.seqr@@seq_b [LAYERED_SEQ] Macro (12 + 34) * 2 = 92
UVM_INFO alu_test.sv(101) @ 215: uvm_test_top [CAPSTONE] Final PKT_COUNT readback = 8
UVM_INFO alu_scoreboard.sv(63) @ 215: uvm_test_top.subsys_env.block_alu_env.scb [SCB] DPI-C + RAL Scoreboard: PASS=8 FAIL=0
UVM_INFO alu_cov_subscriber.sv(45) @ 215: uvm_test_top.subsys_env.block_alu_env.cov [COV] Functional Coverage achieved: 96.88%
--- UVM Report Summary ---
UVM_INFO :    24
UVM_WARNING : 0
UVM_ERROR :   0
UVM_FATAL :   0""",
        "stepper": [
            {"step": 1, "title": "1. Build Subsystem & Bind All Infrastructure", "component": "soc_subsys_env", "cyNode": "grp_subsys", "file": "soc_subsys_env.sv", "line": 34, "state": "0 ns · BUILD", "desc": "alu_capstone_full_test builds soc_subsys_env -> alu_env with RAL, TLM-2 bridge, scoreboard, coverage, domain, and heartbeat.", "log_snippet": "UVM testbench topology"},
            {"step": 2, "title": "2. Arm Fault Callback & Report Catcher", "component": "alu_capstone_full_test", "cyNode": "err_cb", "file": "alu_test.sv", "line": 40, "state": "0 ns · HOOKS", "desc": "With +INJECT_ERR=1, test attaches alu_err_inject_cb to driver and alu_report_catcher globally.", "log_snippet": "Enabled non-intrusive fault callback"},
            {"step": 3, "title": "3. RAL Reset Check, Frontdoor & Backdoor", "component": "pkt_alu_reg_block", "cyNode": "ral_block", "file": "alu_test.sv", "line": 63, "state": "75 ns · RAL CFG", "desc": "configure_phase runs uvm_reg_hw_reset_seq, writes SAT_LIMIT=0x0800 via APB, and verifies via backdoor peek().", "log_snippet": "RAL configured & peeked"},
            {"step": 4, "title": "4. Virtual Sequence Barrier & Layered Burst", "component": "alu_virtual_seq", "cyNode": "layered_seq", "file": "alu_virtual_seq.sv", "line": 28, "state": "80 ns · VSEQ SYNC", "desc": "Virtual sequence fires 'cfg_done' uvm_event and aligns parallel smoke + layered frame sequences at sync_bar.", "log_snippet": "Triggered global 'cfg_done'"},
            {"step": 5, "title": "5. Callback Fault + Catcher Demotion + SVA", "component": "alu_driver", "cyNode": "data_drv", "file": "alu_driver.sv", "line": 34, "state": "100 ns · CB + SVA", "desc": "Driver triggers pre_drive callback on tag=2; alu_report_catcher demotes [ALU_ERR_INJ] while SVA verifies stable pins.", "log_snippet": "[CAUGHT & DEMOTED]"},
            {"step": 6, "title": "6. Monitor -> TLM-2 Bridge -> DPI-C -> Scoreboard & Cov", "component": "alu_scoreboard", "cyNode": "scoreboard", "file": "alu_scoreboard.sv", "line": 46, "state": "110 ns · DPI-C + COV", "desc": "Monitor fans req_ap to TLM-2 bridge, DPI-C golden model, RAL-aware scoreboard, and coverage subscriber.", "log_snippet": "DPI-C MATCH tag=2"},
            {"step": 7, "title": "7. Shutdown Phase, PKT_COUNT Readback & Sign-Off", "component": "alu_capstone_full_test", "cyNode": "uvm_test", "file": "alu_test.sv", "line": 100, "state": "215 ns · SIGN-OFF", "desc": "shutdown_phase stops heartbeat, reads PKT_COUNT=8 via RAL, and reports PASS=8 FAIL=0 with 96.88% coverage.", "log_snippet": "DPI-C + RAL Scoreboard: PASS=8 FAIL=0"}
        ],
        "quizzes": [
            {
                "q": "In the complete Capstone testbench, how does the Scoreboard know what saturation threshold the DUT is currently using?",
                "options": [
                    "It reads the mirrored SAT_LIMIT value from pkt_alu_reg_block, which is kept automatically updated by apb_monitor + uvm_reg_predictor",
                    "It parses the RTL file pkt_alu.sv directly",
                    "The driver passes register values via `uvm_info"
                ],
                "answer": 0,
                "explanation": "Explicit RAL prediction updates the mirror from APB bus traffic so the scoreboard always knows the live DUT configuration."
            },
            {
                "q": "Which combination ensures that negative fault-injection tests pass cleanly without hiding unexpected real bugs?",
                "options": [
                    "Disabling all UVM_ERRORs globally with +UVM_MAX_QUIT_COUNT=999",
                    "Pairing targeted uvm_callback error injection with an ID-filtered uvm_report_catcher + scoreboard verification",
                    "Deleting the scoreboard"
                ],
                "answer": 1,
                "explanation": "Filtering strictly on ID == 'ALU_ERR_INJ' lets legitimate unexpected DUT mismatches fail immediately as UVM_ERRORs."
            }
        ],
    },
]
