---
slug: tlm2_sockets
part: production_uvm
title: TLM-2.0 Sockets, Generic Payload & Temporal Decoupling
short_title: TLM-2.0 & Sockets
difficulty: Advanced
summary: 'Bridge SystemVerilog testbenches with architectural SystemC/ESL models using UVM TLM-2.0: pack transactions
  into uvm_tlm_generic_payload, connect bidirectional initiator/target sockets, execute 4-phase nb_transport_fw/bw
  handshakes, and track local time quanta with uvm_tlm_time.'
objectives:
- Differentiate TLM-1 unidirectional ports/exports from TLM-2.0 bidirectional sockets (`nb_initiator_socket` ↔ `nb_target_socket`).
- Serialize protocol items into standardized `uvm_tlm_generic_payload` byte arrays (`set_address`, `set_data`, `set_write`).
- Implement the 4-phase non-blocking handshake (`BEGIN_REQ`, `END_REQ`, `BEGIN_RESP`, `END_RESP`) across `nb_transport_fw`
  and `nb_transport_bw`.
- Apply temporal decoupling via `uvm_tlm_time` quantum accumulation for high-speed virtual platform modeling.
apis:
- uvm_tlm_nb_initiator_socket
- uvm_tlm_nb_target_socket
- uvm_tlm_generic_payload
- uvm_tlm_time
- uvm_tlm_ifs
docs_links:
- label: TLM-2 Overview
  url: docs_view/overviews/tlm2-txt.html
  desc: TLM-2.0 standard concepts, blocking vs. non-blocking & sockets.
- label: uvm_tlm2_sockets
  url: docs_view/tlm2/uvm_tlm2_sockets-svh.html
  desc: Initiator, target, and passthrough TLM-2 sockets.
- label: uvm_tlm_generic_payload
  url: docs_view/tlm2/uvm_tlm2_generic_payload-svh.html#uvm_tlm_generic_payload
  desc: Interoperable memory-mapped bus payload class.
- label: uvm_tlm_time
  url: docs_view/tlm2/uvm_tlm2_time-svh.html#uvm_tlm_time
  desc: Resolution-independent delay and quantum time tracker.
example_links:
- label: Blocking TLM-2 Transport
  url: examples_view/tlm-2/blocking_simple.html
  desc: Simple b_transport initiator/target socket pair.
- label: Non-Blocking 4-Phase Protocol
  url: examples_view/tlm-2/nonblocking_simple.html
  desc: Interactive 4-phase nb_transport_fw/bw walkthrough.
- label: Temporal Decoupling & Quantum
  url: examples_view/tlm-2/temporal_decoupling.html
  desc: uvm_tlm_time quantum synchronization.
interactive_widget: arch_diff
src_dir: ch11_tlm2_sockets
inherit_from: auto
sim_log: |
  UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
  UVM_INFO alu_tlm2_bridge.sv(54) @ 35: uvm_test_top.env.tlm2_bridge [TLM2] FW BEGIN_REQ addr=0x1000 sync=UVM_TLM_UPDATED
  UVM_INFO alu_tlm2_bridge.sv(66) @ 35: uvm_test_top.env.tlm2_bridge [TLM2] BW BEGIN_RESP -> END_RESP status=UVM_TLM_OK_RESPONSE
  UVM_INFO alu_tlm2_bridge.sv(49) @ 65: uvm_test_top.env.tlm2_bridge [TLM2] Quantum limit reached (20 ns), syncing local time
  UVM_INFO alu_scoreboard.sv(56) @ 180: uvm_test_top.env.scb [SCB] RAL-Aware Scoreboard Summary: PASS=6 FAIL=0
  --- UVM Report Summary ---
  UVM_INFO :    17
  UVM_ERROR :   0
stepper:
- step: 1
  title: 1. Connect TLM-2 Initiator & Target Sockets
  component: alu_env
  file: alu_env.sv
  line: 69
  state: 0 ns · CONNECT
  desc: A single socket connect() binds forward and backward paths between tlm2_bridge and ref_model.
  log_snippet: Running test alu_base_test
- step: 2
  title: 2. Marshal alu_item -> uvm_tlm_generic_payload
  component: alu_tlm2_bridge
  file: alu_tlm2_bridge.sv
  line: 31
  state: 35 ns · PACK GP
  desc: write() packs op, tag, a, b into an 8-byte generic payload and increments uvm_tlm_time quantum.
  log_snippet: FW BEGIN_REQ
- step: 3
  title: 3. Target Processes Forward & Replies Backward
  component: alu_ref_model
  file: alu_ref_model.sv
  line: 44
  state: 35 ns · NB_TRANSPORT
  desc: nb_transport_fw extracts bytes, predicts result, sets OK status, and fires nb_transport_bw.
  log_snippet: BW BEGIN_RESP
- step: 4
  title: 4. Quantum Sync Boundary
  component: alu_tlm2_bridge
  file: alu_tlm2_bridge.sv
  line: 49
  state: 65 ns · QUANTUM
  desc: When accumulated local_quantum hits 20 ns, bridge resets quantum and synchronizes with global simulation
    time.
  log_snippet: Quantum limit reached
quizzes:
- q: Why does TLM-2 require only ONE connect() call between initiator and target sockets?
  options:
  - Because TLM-2 sockets bundle both the forward port/imp and backward export/imp into a single bidirectional endpoint
  - Because TLM-2 does not allow responses
  - Because sockets bypass connect_phase()
  answer: 0
  explanation: Each socket simultaneously acts as initiator/port for forward calls and target/export for backward
    calls, halving connection boilerplate.
- q: What is the purpose of uvm_tlm_time in temporal decoupling?
  options:
  - To print wall-clock CPU hours
  - To let fast virtual-platform transactions advance locally inside a time quantum before yielding to the global
    simulator scheduler
  - To slow down RTL clock edges
  answer: 1
  explanation: Batching multiple transactions inside a local time quantum drastically reduces expensive context
    switches in high-level architectural simulation.
---

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
