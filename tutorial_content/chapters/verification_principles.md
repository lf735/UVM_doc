---
slug: verification_principles
part: foundations
title: 'Core Verification Principles: Stimuli, Checks & Metrics'
short_title: Stimuli, Checks & Metrics
difficulty: Beginner
summary: 'Master the single most important architectural law of UVM: strictly decoupling Stimuli generation, functional
  Checking, and Coverage Metrics—and moving from pin-wiggling to Transaction-Level Modeling (TLM).'
objectives:
- 'Separate every testbench responsibility into three independent pillars: Stimuli, Checks, and Metrics.'
- Recognize common verification anti-patterns (e.g., drivers checking DUT outputs or sequences inspecting pins).
- Understand why Transaction-Level Modeling (TLM) isolates high-level test intent from pin-level timing.
- 'Preview our running DUT thread: the pkt_alu Packet-ALU IP used across Chapters 3 through 13.'
apis:
- uvm_sequence
- uvm_driver
- uvm_monitor
- uvm_scoreboard
- uvm_subscriber
- uvm_analysis_port
docs_links:
- label: TLM-1 Overview
  url: docs_view/overviews/tlm1-txt.html
  desc: Decoupled component communication using ports, exports, and FIFOs.
- label: Comparators Overview
  url: docs_view/overviews/comparators-txt.html
  desc: Automated expected vs. actual checking patterns.
- label: uvm_analysis_port
  url: docs_view/tlm1/uvm_analysis_port-svh.html#uvm_analysis_port
  desc: One-to-many passive broadcast port from monitors to checkers and coverage.
- label: uvm_subscriber
  url: docs_view/comps/uvm_subscriber-svh.html#uvm_subscriber
  desc: Dedicated base class for metrics and coverage listeners.
example_links:
- label: Hello World & TLM FIFO
  url: examples_view/basics/hello_world.html
  desc: Producer/consumer separation using TLM FIFO.
interactive_widget: scm_matrix
quizzes:
- q: Where should functional coverage (`covergroup`) be sampled in a properly architected UVM testbench?
  options:
  - Inside the sequence right after req.randomize()
  - Inside a passive uvm_subscriber connected to the monitor's analysis_port
  - Inside tb_top's initial block
  answer: 1
  explanation: Sampling from the monitor's analysis_port guarantees you measure transactions that actually occurred
    on the pins, independent of active/passive reuse.
- q: Why must a uvm_driver never verify DUT output correctness?
  options:
  - Because drivers do not have access to uvm_info macros
  - Because when reusing the agent in UVM_PASSIVE mode at SoC level, the driver is not instantiated
  - Because SystemVerilog forbids classes from reading output signals
  answer: 1
  explanation: In passive subsystem/SoC reuse, only the monitor, scoreboard, and coverage collectors remain active—so
    checking must live outside the driver.
---

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
