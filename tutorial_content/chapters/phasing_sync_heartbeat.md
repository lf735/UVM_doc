---
slug: phasing_sync_heartbeat
part: production_uvm
title: Phasing Sub-Phases, Domains, Synchronization & Heartbeat
short_title: Phasing, Sync & Heartbeat
difficulty: Advanced
summary: 'Master complex simulation lifecycle orchestration: structure traffic cleanly across UVM run-time sub-phases
  (reset/configure/main/shutdown), isolate bus clocks with uvm_domain, coordinate parallel sequences via uvm_event_pool
  & uvm_barrier, and prevent silent hangs using uvm_heartbeat.'
objectives:
- Split monolithic `run_phase` code cleanly across `reset_phase`, `configure_phase`, `main_phase`, and `shutdown_phase`.
- Configure an independent `uvm_domain` for the APB agent and keep it synchronized with the common domain via `domain.sync()`.
- Synchronize parallel sequence threads using `uvm_event_pool` and `uvm_barrier`.
- Protect regressions against deadlocked simulations using `uvm_heartbeat` liveness monitoring.
apis:
- uvm_phase
- uvm_domain
- uvm_barrier
- uvm_event
- uvm_event_pool
- uvm_heartbeat
- uvm_runtime_phases
docs_links:
- label: Phasing Overview
  url: docs_view/overviews/phasing-txt.html
  desc: Common phases vs. run-time sub-phases execution schedule.
- label: uvm_runtime_phases
  url: docs_view/base/uvm_runtime_phases-svh.html
  desc: reset, configure, main, shutdown sub-phases.
- label: uvm_domain
  url: docs_view/base/uvm_domain-svh.html#uvm_domain
  desc: Domain isolation and cross-domain phase synchronization.
- label: Synchronization Overview
  url: docs_view/overviews/synchro-txt.html
  desc: uvm_event, uvm_event_pool, and uvm_barrier.
- label: uvm_barrier
  url: docs_view/base/uvm_barrier-svh.html#uvm_barrier
  desc: Multi-process rendezvous threshold synchronization.
- label: uvm_heartbeat
  url: docs_view/base/uvm_heartbeat-svh.html#uvm_heartbeat
  desc: Watchdog detecting stalled or hung UVM components.
example_links:
- label: Phased Execution Lifecycle
  url: examples_view/phasing/basic.html
  desc: Top-down vs. bottom-up phase execution.
- label: Phase Objections & Drain Time
  url: examples_view/phasing/objections.html
  desc: Coordinating shutdown with drain_time.
- label: Event Synchronization (Pool)
  url: examples_view/phasing/event_pool.html
  desc: Global uvm_event_pool rendezvous.
interactive_widget: arch_diff
src_dir: ch09_phasing_sync_heartbeat
inherit_from: auto
sim_log: |
  UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
  UVM_INFO alu_test.sv(34) @ 0: uvm_test_top [PHASE] Executing reset_phase: waiting for DUT reset release
  UVM_INFO alu_test.sv(42) @ 25: uvm_test_top [PHASE] Executing configure_phase: programming SAT_LIMIT=0x1000
  UVM_INFO alu_virtual_seq.sv(28) @ 55: uvm_test_top.env.v_seqr@@vseq [VSEQ] Triggered global 'cfg_done' uvm_event; syncing threads with uvm_barrier
  UVM_INFO alu_seq.sv(72) @ 115: uvm_test_top.env.data_agent.seqr@@seq_b [LAYERED_SEQ] Macro (12 + 34) * 2 = 92
  UVM_INFO alu_test.sv(74) @ 190: uvm_test_top [PHASE] Executing shutdown_phase: draining final pipeline responses
  UVM_INFO alu_scoreboard.sv(59) @ 210: uvm_test_top.env.scb [SCB] Scoreboard Summary: PASS=8 FAIL=0
  --- UVM Report Summary ---
  UVM_INFO :    21
  UVM_ERROR :   0
stepper:
- step: 1
  title: 1. Bind APB Domain & Heartbeat
  component: alu_env
  file: alu_env.sv
  line: 59
  state: 0 ns · CONNECT
  desc: alu_env puts apb_agt into apb_domain synced with common_domain and registers data_agent.drv in uvm_heartbeat.
  log_snippet: Running test alu_base_test
- step: 2
  title: 2. Execute reset_phase & configure_phase
  component: alu_base_test
  file: alu_test.sv
  line: 42
  state: 25 ns · CONFIGURE
  desc: Only after reset_phase finishes does configure_phase program SAT_LIMIT=0x1000 over APB.
  log_snippet: Executing configure_phase
- step: 3
  title: 3. Barrier & Event Sync in main_phase
  component: alu_virtual_seq
  file: alu_virtual_seq.sv
  line: 28
  state: 55 ns · SYNC
  desc: vseq triggers 'cfg_done' uvm_event and aligns parallel sequences at sync_bar.wait_for().
  log_snippet: Triggered global 'cfg_done'
- step: 4
  title: 4. Heartbeat Watch & shutdown_phase
  component: alu_base_test
  file: alu_test.sv
  line: 74
  state: 190 ns · SHUTDOWN
  desc: After main_phase drain_time expires, heartbeat stops and shutdown_phase drains final responses.
  log_snippet: Executing shutdown_phase
quizzes:
- q: What happens if an agent implements run_phase() while tests implement main_phase()?
  options:
  - UVM skips run_phase completely
  - run_phase runs in parallel with the entire reset/configure/main/shutdown sub-phase schedule—ideal for passive
    monitors and forever driver loops
  - It triggers a compile error
  answer: 1
  explanation: Drivers and monitors normally stay in forever loops inside run_phase() while tests orchestrate scenarios
    across reset/configure/main/shutdown.
- q: How does uvm_heartbeat catch a hung simulation?
  options:
  - It monitors that registered components raise/drop activity on a heartbeat objection between trigger pulses of
    an event
  - It counts the total lines in the Makefile
  - It disables all objections
  answer: 0
  explanation: If no monitored component touches the heartbeat objection within a trigger window, uvm_heartbeat
    raises UVM_FATAL to abort hung simulations quickly.
---

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
