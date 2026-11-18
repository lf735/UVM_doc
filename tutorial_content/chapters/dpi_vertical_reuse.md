---
slug: dpi_vertical_reuse
part: production_uvm
title: DPI-C C/C++ Reference Integration & Vertical SoC Reuse
short_title: DPI-C & Vertical Reuse
difficulty: Advanced
summary: Connect SystemVerilog verification directly to production C/C++ golden models via SystemVerilog DPI-C (import
  "DPI-C"), and wrap our entire block environment inside soc_subsys_env to demonstrate vertical block-to-SoC reuse
  using UVM_PASSIVE mode.
objectives:
- Declare C ABI functions cleanly in SystemVerilog using `import "DPI-C" function` (`pkt_alu_dpi_pkg.sv`).
- Delegate golden reference prediction from `alu_ref_model` into compiled C (`c_model/pkt_alu_ref.c`) without writing
  bit-twiddling models twice.
- Compile C and SystemVerilog together in simulator Makefiles (`vlog ... ../c_model/pkt_alu_ref.c`).
- Reuse an entire block-level `alu_env` unchanged inside a subsystem/SoC wrapper (`soc_subsys_env`) by switching
  internal agents to `UVM_PASSIVE`.
apis:
- uvm_agent
- uvm_env
- uvm_active_passive_enum
- uvm_dpi
docs_links:
- label: UVM DPI-C Interface
  url: docs_view/dpi/uvm_dpi-svh.html
  desc: How UVM 1.2 itself bridges SystemVerilog and C via DPI.
- label: UVM HDL Backdoor DPI
  url: docs_view/dpi/uvm_hdl-svh.html
  desc: DPI-based RTL hierarchical path access used by RAL backdoor.
- label: uvm_agent (Passive Mode)
  url: docs_view/comps/uvm_agent-svh.html#uvm_agent
  desc: Reusing monitors & checkers when external SoC masters drive pins.
example_links:
- label: Vertical Register Reuse
  url: examples_view/registers/vertical_reuse.html
  desc: Official UVM example scaling block env into subsystem env.
interactive_widget: arch_diff
src_dir: ch12_dpi_vertical_reuse
inherit_from: auto
sim_log: |
  UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
  UVM_INFO alu_test.sv(31) @ 0: uvm_test_top [TEST] Built soc_subsys_env -> block_alu_env (active/passive configurable)
  UVM_INFO alu_scoreboard.sv(54) @ 60: uvm_test_top.subsys_env.block_alu_env.scb [SCB] DPI-C MATCH tag=0 result=0x000004d3
  UVM_INFO alu_scoreboard.sv(54) @ 70: uvm_test_top.subsys_env.block_alu_env.scb [SCB] DPI-C MATCH tag=1 result=0x00000800
  UVM_INFO alu_scoreboard.sv(63) @ 180: uvm_test_top.subsys_env.block_alu_env.scb [SCB] DPI-C + RAL Scoreboard: PASS=6 FAIL=0
  --- UVM Report Summary ---
  UVM_INFO :    15
  UVM_ERROR :   0
stepper:
- step: 1
  title: 1. Subsystem Wraps Block Environment
  component: soc_subsys_env
  file: soc_subsys_env.sv
  line: 34
  state: 0 ns · SUBSYS BUILD
  desc: soc_subsys_env instantiates block_alu_env and toggles UVM_PASSIVE automatically in SoC reuse mode.
  log_snippet: Built soc_subsys_env
- step: 2
  title: 2. DPI-C Import Bridge
  component: pkt_alu_dpi_pkg
  file: pkt_alu_dpi_pkg.sv
  line: 7
  state: 0 ns · DPI BIND
  desc: import "DPI-C" binds SystemVerilog predict_with_cfg() to C function pkt_alu_dpi_calc().
  log_snippet: DPI-C MATCH
- step: 3
  title: 3. Scoreboard Combines RAL Mirror + C Model
  component: alu_scoreboard
  file: alu_scoreboard.sv
  line: 46
  state: 60 ns · DPI-C CHECK
  desc: Scoreboard pulls live SAT_LIMIT from RAL mirror, calls C model via DPI-C, and verifies saturation clamping.
  log_snippet: DPI-C MATCH tag=1 result=0x00000800
quizzes:
- q: When reusing block_alu_env in a SoC where an embedded RISC-V core drives pkt_alu, what changes inside alu_env?
  options:
  - You must rewrite the scoreboard and coverage collector from scratch
  - You set cfg.data_agent_cfg.is_active = UVM_PASSIVE and cfg.apb_cfg.is_active = UVM_PASSIVE while keeping monitors,
    RAL predictor, scoreboard, and coverage intact
  - You delete alu_monitor.sv
  answer: 1
  explanation: Passive agents disable drivers/sequencers while preserving monitors, predictors, scoreboards, and
    functional coverage unchanged.
- q: What is the main benefit of calling pkt_alu_ref.c through SystemVerilog DPI-C?
  options:
  - Single golden reference source shared with Architecture/Software without re-implementing algorithms in SystemVerilog
  - DPI-C synthesizes C into ASIC silicon gates
  - It eliminates the need for clocking blocks
  answer: 0
  explanation: DPI-C lets SystemVerilog testbenches execute the architect's exact C/C++ reference model directly
    at native speed.
---

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
