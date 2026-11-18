---
slug: coverage_sva
part: checks_advanced
title: 'Verification Metrics & Protocol Checking: Coverage & SVA'
short_title: Coverage & SVA Assertions
difficulty: Intermediate
summary: Complete the three verification pillars by adding Functional Coverage (uvm_subscriber + SystemVerilog covergroups
  + cross coverage) for Metrics and concurrent SystemVerilog Assertions (SVA) inside alu_if for cycle-accurate pin
  protocol checking.
objectives:
- 'Implement a `uvm_subscriber #(alu_item)` sampling `covergroup` bins and `cross` coverage via `write()`.'
- Filter impossible combinations cleanly using `ignore_bins` so 100% coverage closure is meaningful.
- Write concurrent SystemVerilog Assertions (`property` / `assert property` / `cover property`) in `alu_if.sv` for
  pin-level handshake stability.
- Weight sequence distributions (`dist`) to exercise corner cases like `0x0000`, `0xFFFF`, and `ALU_INVAL`.
apis:
- uvm_subscriber
- uvm_analysis_export
- report_phase
- uvm_comparer
docs_links:
- label: uvm_subscriber
  url: docs_view/comps/uvm_subscriber-svh.html#uvm_subscriber
  desc: Built-in analysis listener class with analysis_export.
- label: Transaction Recording
  url: docs_view/overviews/recording-txt.html
  desc: Observing and recording transactions for metrics & debug.
- label: uvm_comparer
  url: docs_view/base/uvm_comparer-svh.html#uvm_comparer
  desc: Policy class for structured object comparison.
example_links:
- label: Register Coverage
  url: examples_view/registers/coverage.html
  desc: Sampling functional covergroups automatically.
interactive_widget: arch_diff
src_dir: ch06_coverage_sva
inherit_from: auto
sim_log: |
  UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
  UVM_INFO alu_seq.sv(15) @ 25: uvm_test_top.env.data_agent.seqr@@seq [SEQ] Starting coverage-driven sequence (20 items)
  UVM_INFO alu_scoreboard.sv(44) @ 40: uvm_test_top.env.scb [SCB] MATCH tag=0 op=ALU_ADD result=0x00000000
  UVM_INFO alu_scoreboard.sv(44) @ 50: uvm_test_top.env.scb [SCB] MATCH tag=1 op=ALU_MUL result=0xfffe0001
  UVM_INFO alu_scoreboard.sv(44) @ 140: uvm_test_top.env.scb [SCB] MATCH tag=10 op=ALU_INVAL result=0xdeadbeef
  UVM_INFO alu_scoreboard.sv(59) @ 270: uvm_test_top.env.scb [SCB] Scoreboard Summary: PASS=20 FAIL=0
  UVM_INFO alu_cov_subscriber.sv(45) @ 270: uvm_test_top.env.cov [COV] Functional Coverage achieved: 94.44%
  --- UVM Report Summary ---
  UVM_INFO :    28
  UVM_ERROR :   0
stepper:
- step: 1
  title: 1. Subscribe Coverage Collector to Monitor
  component: alu_env
  file: alu_env.sv
  line: 39
  state: 0 ns · CONNECT
  desc: alu_env fans out data_agent.req_ap to both scb.req_export and cov.analysis_export.
  log_snippet: Running test alu_base_test
- step: 2
  title: 2. Corner-Weighted Stimulus Generation
  component: alu_smoke_seq
  file: alu_seq.sv
  line: 22
  state: 25 ns · STIMULUS
  desc: Sequence mixes 0x0000, 0xFFFF, and weighted ALU_INVAL opcodes to hit coverage bins.
  log_snippet: MATCH tag=1 op=ALU_MUL
- step: 3
  title: 3. SVA Monitors Cycle-by-Cycle Protocol
  component: alu_if
  file: alu_if.sv
  line: 42
  state: 30 ns · SVA CHECK
  desc: a_in_valid_stable continuously checks that payload remains constant whenever in_ready=0.
  log_snippet: MATCH tag=10 op=ALU_INVAL
- step: 4
  title: 4. Report Functional Coverage Score
  component: alu_cov_subscriber
  file: alu_cov_subscriber.sv
  line: 45
  state: 270 ns · METRICS
  desc: report_phase prints cg_alu.get_inst_coverage() alongside scoreboard PASS=20 FAIL=0.
  log_snippet: Functional Coverage achieved
quizzes:
- q: Why are SVA assertions placed inside alu_if rather than inside alu_scoreboard?
  options:
  - SVA checks cycle-accurate pin-level temporal rules (like $stable while stalled), whereas scoreboards check end-to-end
    transaction data
  - Because scoreboards cannot access $error
  - Because interfaces cannot instantiate UVM classes
  answer: 0
  explanation: SVA excels at cycle-by-cycle signal protocol invariants; UVM scoreboards excel at abstract transaction
    transformations and multi-cycle latency matching.
- q: Why did we connect cov.analysis_export to data_agent.req_ap instead of sampling inside alu_smoke_seq?
  options:
  - Because sequences run inside run_phase and cannot instantiate covergroups
  - So coverage records only transactions that were actually accepted on the hardware bus
  - To slow down simulation for debugging
  answer: 1
  explanation: Observer-based coverage reflects true bus traffic regardless of which sequence or external master
    drove the DUT.
---

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
