---
slug: monitor_scoreboard
part: checks_advanced
title: 'Passive Observation & Self-Checking: Monitor, TLM-1 & Scoreboard'
short_title: Monitor, TLM-1 & Scoreboard
difficulty: Intermediate
summary: 'Close the checking loop cleanly: add a passive uvm_monitor sampling both request and response handshakes
  via clocking blocks, broadcast transactions over TLM-1 uvm_analysis_ports, buffer them in uvm_tlm_analysis_fifos,
  and verify DUT behavior against an independent Golden Reference Model.'
objectives:
- Build a strictly passive `uvm_monitor` that works identically in `UVM_ACTIVE` and `UVM_PASSIVE` modes.
- Broadcast transactions decouple-style using `uvm_analysis_port::write()`.
- 'Buffer concurrent input/output streams safely inside `uvm_tlm_analysis_fifo #(alu_item)`.'
- Implement `alu_ref_model` + `alu_scoreboard` checking expected vs. actual outputs and verifying zero leftover
  items in `check_phase()`.
apis:
- uvm_monitor
- uvm_scoreboard
- uvm_analysis_port
- uvm_analysis_export
- uvm_tlm_analysis_fifo
- check_phase
- report_phase
docs_links:
- label: uvm_monitor
  url: docs_view/comps/uvm_monitor-svh.html#uvm_monitor
  desc: Passive pin-to-transaction observer.
- label: uvm_scoreboard
  url: docs_view/comps/uvm_scoreboard-svh.html#uvm_scoreboard
  desc: Functional checker comparing predicted vs. observed results.
- label: uvm_analysis_port
  url: docs_view/tlm1/uvm_analysis_port-svh.html#uvm_analysis_port
  desc: Non-blocking broadcast TLM-1 port.
- label: uvm_tlm_analysis_fifo
  url: docs_view/tlm1/uvm_tlm_fifos-svh.html#uvm_tlm_analysis_fifo
  desc: Unbounded FIFO adapting analysis write() into blocking get().
- label: TLM Ports & Exports
  url: docs_view/overviews/tlm_ifs_and_ports-txt.html
  desc: Hierarchical TLM port-to-export forwarding.
example_links:
- label: TLM-1 FIFO Communication
  url: examples_view/tlm-1/fifo.html
  desc: Producer/consumer synchronization via uvm_tlm_fifo.
- label: Hierarchical TLM Forwarding
  url: examples_view/tlm-1/hierarchy.html
  desc: Connecting inner monitor ports up through agent boundaries.
interactive_widget: arch_diff
src_dir: ch05_monitor_scoreboard
inherit_from: auto
sim_log: |
  UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
  UVM_INFO alu_seq.sv(15) @ 25: uvm_test_top.env.data_agent.seqr@@seq [SEQ] Starting sequence (8 items)
  UVM_INFO alu_scoreboard.sv(44) @ 40: uvm_test_top.env.scb [SCB] MATCH tag=0 op=ALU_ADD result=0x000004d3
  UVM_INFO alu_scoreboard.sv(44) @ 50: uvm_test_top.env.scb [SCB] MATCH tag=1 op=ALU_SUB result=0x00000210
  UVM_INFO alu_scoreboard.sv(44) @ 60: uvm_test_top.env.scb [SCB] MATCH tag=2 op=ALU_MUL result=0x00048c20
  ...
  UVM_INFO alu_scoreboard.sv(44) @ 110: uvm_test_top.env.scb [SCB] MATCH tag=7 op=ALU_XOR result=0x00000e17
  UVM_INFO alu_scoreboard.sv(59) @ 150: uvm_test_top.env.scb [SCB] Scoreboard Summary: PASS=8 FAIL=0
  --- UVM Report Summary ---
  UVM_INFO :    19
  UVM_ERROR :   0
stepper:
- step: 1
  title: 1. Connect Agent Analysis Ports to Scoreboard
  component: alu_env
  file: alu_env.sv
  line: 34
  state: 0 ns · CONNECT
  desc: alu_env connects data_agent.req_ap and rsp_ap to scb.req_export and scb.rsp_export.
  log_snippet: Running test alu_base_test
- step: 2
  title: 2. Monitor Captures Accepted Input
  component: alu_monitor
  file: alu_monitor.sv
  line: 41
  state: 30 ns · REQ OBS
  desc: collect_requests() detects in_valid && in_ready on mon_cb and broadcasts req_ap.write(tr).
  log_snippet: MATCH tag=0
- step: 3
  title: 3. Monitor Captures DUT Output
  component: alu_monitor
  file: alu_monitor.sv
  line: 55
  state: 40 ns · RSP OBS
  desc: One cycle later, collect_responses() captures result/out_tag/err_flag and broadcasts rsp_ap.write(tr).
  log_snippet: MATCH tag=0
- step: 4
  title: 4. Golden Prediction & Comparison
  component: alu_scoreboard
  file: alu_scoreboard.sv
  line: 38
  state: 40 ns · CHECK
  desc: Scoreboard pulls req & act from FIFOs, computes exp via alu_ref_model.predict(), and checks equality.
  log_snippet: 'Scoreboard Summary: PASS=8 FAIL=0'
- step: 5
  title: 5. Drain Check in check_phase
  component: alu_scoreboard
  file: alu_scoreboard.sv
  line: 51
  state: 150 ns · CHECK_PHASE
  desc: Verifies both req_fifo and rsp_fifo are completely empty so no dropped packets go unnoticed.
  log_snippet: PASS=8 FAIL=0
quizzes:
- q: Why does uvm_analysis_port use a non-blocking function write() instead of a blocking task put()?
  options:
  - Because SystemVerilog interfaces forbid tasks
  - So a monitor can broadcast passively to 0, 1, or N subscribers without ever stalling bus observation
  - Because functions execute faster than tasks in C++
  answer: 1
  explanation: Monitors must observe bus activity in zero simulation time without blocking, regardless of how many
    subscribers are attached.
- q: What problem does check_phase() solve in alu_scoreboard?
  options:
  - Detecting transactions that entered the DUT but never produced a matching output before simulation ended
  - Randomizing the next sequence item
  - Driving reset onto the DUT
  answer: 0
  explanation: If a packet disappears inside the DUT, run_phase's rsp_fifo.get() remains blocked; check_phase()
    catches non-empty FIFOs at end-of-test.
---

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
