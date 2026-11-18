---
slug: minimal_stimuli
part: stimuli_core
title: 'Minimal Stimuli Environment: Every Piece Explained'
short_title: Minimal Stimuli Env
difficulty: Beginner
summary: 'Build the smallest possible UVM stimuli environment—no agent, no env, no scoreboard yet—and dissect every
  single line: alu_if, uvm_sequence_item, uvm_sequence, uvm_sequencer, uvm_driver, uvm_config_db, run_test(), and
  phase objections.'
objectives:
- Connect a physical SystemVerilog interface (`alu_if`) to a UVM driver via `uvm_config_db#(virtual alu_if)`.
- Define a constrained-random transaction (`alu_item`) extending `uvm_sequence_item`.
- 'Implement the classic 4-step sequence/driver handshake: `start_item` / `finish_item` ↔ `get_next_item` / `item_done`.'
- Control simulation lifetime deterministically with `phase.raise_objection()` and `phase.drop_objection()`.
apis:
- uvm_sequence_item
- uvm_sequence
- uvm_sequencer
- uvm_driver
- uvm_config_db
- uvm_objection
- run_test
- '`uvm_object_utils'
- '`uvm_component_utils'
docs_links:
- label: uvm_sequence_item
  url: docs_view/seq/uvm_sequence_item-svh.html#uvm_sequence_item
  desc: Base class for sequence transactions.
- label: uvm_sequence
  url: docs_view/seq/uvm_sequence-svh.html#uvm_sequence
  desc: Procedural stimulus generator via body().
- label: uvm_sequencer
  url: docs_view/seq/uvm_sequencer-svh.html#uvm_sequencer
  desc: Arbitrates and supplies items to driver via seq_item_export.
- label: uvm_driver
  url: docs_view/comps/uvm_driver-svh.html#uvm_driver
  desc: Pulls items on seq_item_port and drives virtual interface pins.
- label: uvm_config_db
  url: docs_view/base/uvm_config_db-svh.html#uvm_config_db
  desc: Passes virtual interface handle from tb_top module into UVM classes.
- label: uvm_objection
  url: docs_view/base/uvm_objection-svh.html#uvm_objection
  desc: Keeps run_phase alive while stimulus executes.
- label: uvm_globals (run_test)
  url: docs_view/base/uvm_globals-svh.html
  desc: Global run_test() entry point starting UVM phasing.
example_links:
- label: Trivial Component
  url: examples_view/basics/trivial.html
  desc: Minimal uvm_component & run_test().
- label: Virtual Interface Connection
  url: examples_view/infrastructure/interfaces.html
  desc: Bridging physical interfaces via uvm_config_db.
- label: Basic Read/Write Sequence
  url: examples_view/sequences/basic_read_write_sequence.html
  desc: Sequence/driver handshake fundamentals.
interactive_widget: arch_diff
src_dir: ch03_minimal_stimuli
home_featured:
  badge: Stimuli
  badge_class: home-badge-beginner
  title: Minimal Stimuli
  desc: 'Start with the simplest possible UVM bench: sequence, sequencer, driver, config_db & objections.'
sim_log: |
  # ** Note: (vsim-3813) Design is being optimized...
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
  UVM_FATAL :   0
stepper:
- step: 1
  title: 1. Top Module & ConfigDB Set
  component: tb_top
  file: tb_top.sv
  line: 44
  state: 0 ns · INIT
  desc: tb_top publishes physical alu_if into uvm_config_db and invokes run_test("alu_minimal_test").
  log_snippet: Running test alu_minimal_test
- step: 2
  title: 2. Build & Connect Driver <-> Sequencer
  component: alu_minimal_test
  file: alu_minimal_test.sv
  line: 23
  state: 0 ns · BUILD/CONNECT
  desc: alu_minimal_test instantiates seqr and drv, then connects drv.seq_item_port to seqr.seq_item_export.
  log_snippet: Running test alu_minimal_test
- step: 3
  title: 3. Raise Objection & Start Sequence
  component: alu_minimal_test
  file: alu_minimal_test.sv
  line: 28
  state: 25 ns · RUN
  desc: Test raises objection so run_phase stays active, creates alu_smoke_seq, and launches seq.start(seqr).
  log_snippet: Starting smoke sequence
- step: 4
  title: 4. Late Randomization & finish_item
  component: alu_smoke_seq
  file: alu_seq.sv
  line: 19
  state: 25 ns · HANDSHAKE
  desc: start_item waits for sequencer grant, randomizes req, and hands off via finish_item(req).
  log_snippet: Sending tag=0 op=ALU_ADD
- step: 5
  title: 5. Pin-Level Driving & item_done
  component: alu_driver
  file: alu_driver.sv
  line: 39
  state: 30 ns · PIN DRIVE
  desc: Driver asserts in_valid and op/a/b/tag on clocking block drv_cb until in_ready=1, then calls item_done().
  log_snippet: Driving tag=0 op=ALU_ADD
- step: 6
  title: 6. Drop Objection & Shutdown
  component: alu_minimal_test
  file: alu_minimal_test.sv
  line: 32
  state: 110 ns · DONE
  desc: 'Once all 4 items finish and drain #40ns, drop_objection() allows UVM to enter extract/report phases.'
  log_snippet: TEST_DONE
quizzes:
- q: What happens if you forget phase.raise_objection(this) in alu_minimal_test::run_phase?
  options:
  - UVM waits forever until $finish is called
  - run_phase terminates immediately at 0 ns before any stimulus runs
  - The sequencer automatically raises an objection for every item
  answer: 1
  explanation: In UVM 1.2, time-consuming run phases end immediately when the total objection count drops to zero.
- q: Why does alu_smoke_seq call req.randomize() AFTER start_item(req) instead of before?
  options:
  - Late randomization guarantees constraints can reflect the latest DUT/scoreboard state at the moment the driver
    is ready
  - SystemVerilog forbids calling randomize() before start_item()
  - Because start_item() allocates the memory for req
  answer: 0
  explanation: start_item() blocks until sequencer arbitration completes, so randomizing afterwards ensures the
    transaction reflects current hardware state.
---

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
