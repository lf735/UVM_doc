---
slug: ral
part: production_uvm
title: 'Register Abstraction Layer (RAL): Block, Adapter & Predictor'
short_title: Register Layer (RAL)
difficulty: Advanced
summary: 'Replace raw hex APB addresses with an object-oriented Register Model: build uvm_reg_block, uvm_reg, uvm_reg_field,
  and uvm_reg_map; translate register ops with apb_reg_adapter; maintain desired/mirrored coherence via uvm_reg_predictor;
  and verify registers via frontdoor, backdoor, and built-in sequences.'
objectives:
- Model `CTRL`, `STATUS` (RO/W1C), `SAT_LIMIT`, and `PKT_COUNT` with exact bitfields, access policies, and reset
  values in `pkt_alu_reg_block`.
- Implement `reg2bus()` and `bus2reg()` inside `apb_reg_adapter` so RAL stays completely bus-agnostic.
- 'Wire `uvm_reg_predictor #(apb_item)` to `apb_agt.ap` (explicit prediction) so even non-RAL APB writes update
  the RAL mirror.'
- Use `reg_model.SAT_LIMIT.get_mirrored_value()` directly inside `alu_scoreboard` and run `uvm_reg_hw_reset_seq`
  + backdoor `peek()`.
apis:
- uvm_reg_block
- uvm_reg
- uvm_reg_field
- uvm_reg_map
- uvm_reg_adapter
- uvm_reg_predictor
- uvm_reg_hw_reset_seq
docs_links:
- label: Registers Overview
  url: docs_view/overviews/registers-txt.html
  desc: Complete UVM Register Layer architecture & concepts.
- label: uvm_reg_block
  url: docs_view/reg/uvm_reg_block-svh.html#uvm_reg_block
  desc: Top-level container for registers, fields, and address maps.
- label: uvm_reg
  url: docs_view/reg/uvm_reg-svh.html#uvm_reg
  desc: Individual register abstraction with desired & mirrored state.
- label: uvm_reg_adapter
  url: docs_view/reg/uvm_reg_adapter-svh.html#uvm_reg_adapter
  desc: Bus-protocol translator (reg2bus / bus2reg).
- label: uvm_reg_predictor
  url: docs_view/reg/uvm_reg_predictor-svh.html#uvm_reg_predictor
  desc: Passively updates RAL mirror from monitored bus transactions.
- label: uvm_reg_hw_reset_seq
  url: docs_view/reg/sequences/uvm_reg_hw_reset_seq-svh.html
  desc: Built-in hardware reset value checker sequence.
example_links:
- label: RAL Primer & Bus Adapter
  url: examples_view/registers/primer.html
  desc: Frontdoor read/write & mirror checking.
- label: Register Sequence Convenience API
  url: examples_view/registers/sequence_api.html
  desc: Clean RAL access APIs inside sequences.
interactive_widget: arch_diff
src_dir: ch10_ral
inherit_from: auto
home_featured:
  badge: Production
  badge_class: home-badge-advanced
  title: RAL & TLM-2 / DPI
  desc: Grow into Scoreboards, SVA, Layered/Virtual Sequences, Callbacks, Heartbeat, RAL, TLM-2 & DPI-C.
sim_log: |
  UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
  UVM_INFO uvm_reg_hw_reset_seq.svh(140) @ 35: reporter [uvm_reg_hw_reset_seq] Verifying reset values of registers in apb_map...
  UVM_INFO alu_test.sv(44) @ 75: uvm_test_top [RAL] Backdoor peek SAT_LIMIT = 0x0800 (mirrored=0x0800)
  UVM_INFO alu_scoreboard.sv(56) @ 140: uvm_test_top.env.scb [SCB] RAL-Aware Scoreboard Summary: PASS=6 FAIL=0
  UVM_INFO alu_test.sv(55) @ 180: uvm_test_top [RAL] Frontdoor PKT_COUNT = 6
  --- UVM Report Summary ---
  UVM_INFO :    14
  UVM_ERROR :   0
stepper:
- step: 1
  title: 1. Bind RAL Map, Adapter & Predictor
  component: alu_env
  file: alu_env.sv
  line: 53
  state: 0 ns · CONNECT
  desc: alu_env maps apb_map to apb_agt.seqr via apb_reg_adapter and wires apb_agt.ap into reg_predictor.
  log_snippet: Running test alu_base_test
- step: 2
  title: 2. Run Built-In Hardware Reset Sequence
  component: alu_base_test
  file: alu_test.sv
  line: 36
  state: 35 ns · RESET SEQ
  desc: uvm_reg_hw_reset_seq verifies default reset values of CTRL, STATUS, SAT_LIMIT, and PKT_COUNT.
  log_snippet: Verifying reset values
- step: 3
  title: 3. Frontdoor Write + Backdoor Peek
  component: pkt_alu_reg_block
  file: alu_test.sv
  line: 44
  state: 75 ns · RAL ACCESS
  desc: Test writes SAT_LIMIT=0x0800 over APB frontdoor and cross-checks via 0-time HDL backdoor peek().
  log_snippet: Backdoor peek SAT_LIMIT = 0x0800
- step: 4
  title: 4. Scoreboard Adapts via RAL Mirror
  component: alu_scoreboard
  file: alu_scoreboard.sv
  line: 47
  state: 140 ns · MIRROR CHECK
  desc: Scoreboard queries reg_model.CTRL.sat_en.get_mirrored_value() to apply saturation clamping automatically.
  log_snippet: Frontdoor PKT_COUNT = 6
quizzes:
- q: Why is explicit prediction (uvm_reg_predictor + set_auto_predict(0)) recommended over auto-predict?
  options:
  - Because auto-predict does not support uvm_reg_block
  - Because explicit prediction updates the RAL mirror from actual monitored bus transactions—even when non-RAL
    sequences or other SoC masters write registers
  - Because auto-predict disables backdoor peek()
  answer: 1
  explanation: Explicit prediction guarantees the mirror stays synchronized with true pin activity on the bus regardless
    of who initiated the transfer.
- q: What is the difference between desired and mirrored values in uvm_reg?
  options:
  - Mirrored holds what we believe is currently in DUT hardware; desired holds the value queued for the next update()
  - Desired is read-only; mirrored is write-only
  - They are aliases for the same variable
  answer: 0
  explanation: You can randomize/set desired values across fields first, then call reg_block.update() to flush only
    registers where desired != mirrored.
---

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
