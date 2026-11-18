---
slug: capstone
part: capstone
title: 'Capstone: Ultra-Complete Dynamic Verification Environment'
short_title: Dynamic Complete Env
difficulty: Advanced
summary: 'Explore the complete production UVM 1.2 environment unifying every layer built across Chapters 1-12: click
  any block on the interactive Cytoscape architecture map to inspect its role, jump straight back to the tutorial
  chapter that introduced it, inspect its SystemVerilog/C code, or open its official UVM doc; use the Progressive
  Layer Slider (Ch.03 -> Ch.12) to replay the build-up; and run the live end-to-end execution stepper.'
objectives:
- Trace how every UVM layer interacts in a real multi-agent, RAL-, TLM-2-, and DPI-C-enabled testbench.
- Replay the incremental construction from a 5-component stimuli bench (Ch.03) up to the full SoC-ready testbench
  (Ch.12).
- Navigate fluidly between any architectural block, its teaching chapter, its SystemVerilog/C source, and its UVM
  1.2 reference documentation.
apis:
- uvm_test
- uvm_env
- uvm_agent
- uvm_sequencer
- uvm_driver
- uvm_monitor
- uvm_scoreboard
- uvm_subscriber
- uvm_reg_block
- uvm_tlm_nb_initiator_socket
- uvm_callback
- uvm_report_catcher
- uvm_heartbeat
- uvm_dpi
docs_links:
- label: uvm_test
  url: docs_view/comps/uvm_test-svh.html#uvm_test
  desc: Test control, sub-phases, factory, and objections.
- label: uvm_env
  url: docs_view/comps/uvm_env-svh.html#uvm_env
  desc: Hierarchical verification container.
- label: uvm_reg_block
  url: docs_view/reg/uvm_reg_block-svh.html#uvm_reg_block
  desc: Register Abstraction Layer (RAL) root.
- label: uvm_tlm2_sockets
  url: docs_view/tlm2/uvm_tlm2_sockets-svh.html
  desc: TLM-2.0 bidirectional sockets.
- label: uvm_callback
  url: docs_view/base/uvm_callback-svh.html#uvm_callback
  desc: Non-intrusive fault injection hooks.
- label: uvm_report_catcher
  url: docs_view/base/uvm_report_catcher-svh.html#uvm_report_catcher
  desc: Dynamic report demotion & filtering.
- label: uvm_heartbeat
  url: docs_view/base/uvm_heartbeat-svh.html#uvm_heartbeat
  desc: Deadlock & hang watchdog.
- label: UVM DPI-C Interface
  url: docs_view/dpi/uvm_dpi-svh.html
  desc: SystemVerilog <-> C reference integration.
example_links:
- label: UBUS Verification Component
  url: examples_view/integrated/ubus.html
  desc: Full integrated UVM multi-file VIP suite.
- label: Audio Codec VIP + RAL
  url: examples_view/integrated/codec.html
  desc: Integrated multi-interface VIP with RAL & scoreboard.
interactive_widget: capstone
src_dir: ch13_capstone
inherit_from: auto
home_featured:
  badge: Capstone
  badge_class: home-badge-advanced
  title: Dynamic Complete Env
  desc: Interactive 4-in-1 clickable testbench map with layer replay slider and chapter back-links.
sim_log: |
  UVM_INFO @ 0: reporter [RNTST] Running test alu_capstone_full_test...
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
  UVM_FATAL :   0
stepper:
- step: 1
  title: 1. Build Subsystem & Bind All Infrastructure
  component: soc_subsys_env
  cyNode: grp_subsys
  file: soc_subsys_env.sv
  line: 34
  state: 0 ns · BUILD
  desc: alu_capstone_full_test builds soc_subsys_env -> alu_env with RAL, TLM-2 bridge, scoreboard, coverage, domain,
    and heartbeat.
  log_snippet: UVM testbench topology
- step: 2
  title: 2. Arm Fault Callback & Report Catcher
  component: alu_capstone_full_test
  cyNode: err_cb
  file: alu_test.sv
  line: 40
  state: 0 ns · HOOKS
  desc: With +INJECT_ERR=1, test attaches alu_err_inject_cb to driver and alu_report_catcher globally.
  log_snippet: Enabled non-intrusive fault callback
- step: 3
  title: 3. RAL Reset Check, Frontdoor & Backdoor
  component: pkt_alu_reg_block
  cyNode: ral_block
  file: alu_test.sv
  line: 63
  state: 75 ns · RAL CFG
  desc: configure_phase runs uvm_reg_hw_reset_seq, writes SAT_LIMIT=0x0800 via APB, and verifies via backdoor peek().
  log_snippet: RAL configured & peeked
- step: 4
  title: 4. Virtual Sequence Barrier & Layered Burst
  component: alu_virtual_seq
  cyNode: layered_seq
  file: alu_virtual_seq.sv
  line: 28
  state: 80 ns · VSEQ SYNC
  desc: Virtual sequence fires 'cfg_done' uvm_event and aligns parallel smoke + layered frame sequences at sync_bar.
  log_snippet: Triggered global 'cfg_done'
- step: 5
  title: 5. Callback Fault + Catcher Demotion + SVA
  component: alu_driver
  cyNode: data_drv
  file: alu_driver.sv
  line: 34
  state: 100 ns · CB + SVA
  desc: Driver triggers pre_drive callback on tag=2; alu_report_catcher demotes [ALU_ERR_INJ] while SVA verifies
    stable pins.
  log_snippet: '[CAUGHT & DEMOTED]'
- step: 6
  title: 6. Monitor -> TLM-2 Bridge -> DPI-C -> Scoreboard & Cov
  component: alu_scoreboard
  cyNode: scoreboard
  file: alu_scoreboard.sv
  line: 46
  state: 110 ns · DPI-C + COV
  desc: Monitor fans req_ap to TLM-2 bridge, DPI-C golden model, RAL-aware scoreboard, and coverage subscriber.
  log_snippet: DPI-C MATCH tag=2
- step: 7
  title: 7. Shutdown Phase, PKT_COUNT Readback & Sign-Off
  component: alu_capstone_full_test
  cyNode: uvm_test
  file: alu_test.sv
  line: 100
  state: 215 ns · SIGN-OFF
  desc: shutdown_phase stops heartbeat, reads PKT_COUNT=8 via RAL, and reports PASS=8 FAIL=0 with 96.88% coverage.
  log_snippet: 'DPI-C + RAL Scoreboard: PASS=8 FAIL=0'
quizzes:
- q: In the complete Capstone testbench, how does the Scoreboard know what saturation threshold the DUT is currently
    using?
  options:
  - It reads the mirrored SAT_LIMIT value from pkt_alu_reg_block, which is kept automatically updated by apb_monitor
    + uvm_reg_predictor
  - It parses the RTL file pkt_alu.sv directly
  - The driver passes register values via `uvm_info
  answer: 0
  explanation: Explicit RAL prediction updates the mirror from APB bus traffic so the scoreboard always knows the
    live DUT configuration.
- q: Which combination ensures that negative fault-injection tests pass cleanly without hiding unexpected real bugs?
  options:
  - Disabling all UVM_ERRORs globally with +UVM_MAX_QUIT_COUNT=999
  - Pairing targeted uvm_callback error injection with an ID-filtered uvm_report_catcher + scoreboard verification
  - Deleting the scoreboard
  answer: 1
  explanation: Filtering strictly on ID == 'ALU_ERR_INJ' lets legitimate unexpected DUT mismatches fail immediately
    as UVM_ERRORs.
---

## 13.1 The Complete Architecture at a Glance

Congratulations—every single block below was earned step by step across Chapters 1 through 12!

Use the **4-in-1 Dynamic Environment Explorer** below to:
1. **Click any component node** on the interactive diagram to highlight its TLM/signal wires, inspect its exact ports and responsibilities, **jump back to the chapter that built it (`← Review Chapter XX`)**, focus its source tab, or open its official **UVM 1.2 Reference Doc**.
2. **Slide the Progressive Build-Up control (`Ch.03 → Ch.13`)** to watch the environment expand incrementally from minimal stimuli to full SoC readiness.
3. **Run the End-to-End Flow Stepper** below to trace a full transaction lifecycle (`RAL Config → Virtual/Layered Seq → Callback Fault Injection → Report Catcher → Monitor → TLM-2 Bridge → C/DPI-C Golden Model → RAL-Aware Scoreboard + Coverage`) synchronized across the diagram, Code Studio, and simulation log.
