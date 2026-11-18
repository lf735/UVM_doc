---
slug: pipelined_layered_vseq
part: checks_advanced
title: Pipelined Responses, Arbitration, Layered Sequences & Virtual Sequencer
short_title: Layered & Virtual Seq
difficulty: Intermediate
summary: 'Upgrade to the full dual-interface pkt_alu DUT (Valid/Ready + APB3): implement tagged driver responses
  (put/get_response), sequencer arbitration (lock/SEQ_ARB_STRICT_FIFO), multi-layer protocol translation sequences,
  and a Virtual Sequencer orchestrating both interfaces.'
objectives:
- Return tagged responses (`rsp.set_id_info(req)` + `put(rsp)`) from a pipelined driver back to its originating
  sequence (`get_response(rsp)`).
- Translate high-level macro frames `(x + y) * scale` into chained low-level bus items via **Layered Sequences**.
- Arbitrate concurrent stimulus streams safely using `set_arbitration(SEQ_ARB_STRICT_FIFO)` and `lock()/unlock()`.
- Coordinate APB register setup and data traffic cleanly using a **Virtual Sequencer** (`alu_virtual_sequencer`)
  and `uvm_declare_p_sequencer`.
apis:
- uvm_sequence_base
- uvm_sequencer_base
- '`uvm_declare_p_sequencer'
- uvm_sequencer
- uvm_driver
docs_links:
- label: uvm_sequence_base
  url: docs_view/seq/uvm_sequence_base-svh.html#uvm_sequence_base
  desc: start(), wait_for_grant(), send_request(), get_response().
- label: uvm_sequencer_base
  url: docs_view/seq/uvm_sequencer_base-svh.html#uvm_sequencer_base
  desc: Arbitration modes, grab(), and lock().
- label: Sequences Overview
  url: docs_view/overviews/sequences-txt.html
  desc: Sequence layering and hierarchical reuse.
- label: Sequencers Overview
  url: docs_view/overviews/sequencers-txt.html
  desc: Sequencer arbitration and virtual sequencer architecture.
- label: Sequence Macros
  url: docs_view/macros/uvm_sequence_defines-svh.html
  desc: '`uvm_declare_p_sequencer and sequence helpers.'
example_links:
- label: Basic Read/Write Sequence
  url: examples_view/sequences/basic_read_write_sequence.html
  desc: Sequence item transport & responses.
- label: APB Verification IP
  url: examples_view/integrated/apb.html
  desc: Official UVM APB agent reference.
interactive_widget: arch_diff
src_dir: ch07_pipelined_layered_vseq
inherit_from: auto
sim_log: |
  UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
  UVM_INFO alu_virtual_seq.sv(18) @ 25: uvm_test_top.env.v_seqr@@vseq [VSEQ] Phase 1: Configuring CTRL register via APB agent (EN=1, SAT_EN=0)
  UVM_INFO alu_virtual_seq.sv(24) @ 55: uvm_test_top.env.v_seqr@@vseq [VSEQ] Phase 2: Launching parallel smoke + layered arithmetic flows
  UVM_INFO alu_seq.sv(72) @ 105: uvm_test_top.env.data_agent.seqr@@layered_seq [LAYERED_SEQ] Macro (18 + 27) * 3 = 135
  UVM_INFO alu_scoreboard.sv(59) @ 190: uvm_test_top.env.scb [SCB] Scoreboard Summary: PASS=8 FAIL=0
  UVM_INFO alu_cov_subscriber.sv(45) @ 190: uvm_test_top.env.cov [COV] Functional Coverage achieved: 72.50%
  --- UVM Report Summary ---
  UVM_INFO :    16
  UVM_ERROR :   0
stepper:
- step: 1
  title: 1. Connect Sub-Sequencers to Virtual Sequencer
  component: alu_env
  file: alu_env.sv
  line: 36
  state: 0 ns · CONNECT
  desc: alu_env binds data_agent.seqr -> v_seqr.alu_sqr and apb_agt.seqr -> v_seqr.apb_sqr.
  log_snippet: Running test alu_base_test
- step: 2
  title: 2. Virtual Sequence Configures APB CTRL
  component: alu_virtual_seq
  file: alu_virtual_seq.sv
  line: 21
  state: 25 ns · APB CFG
  desc: vseq executes apb_write_seq on p_sequencer.apb_sqr before launching datapath traffic.
  log_snippet: Configuring CTRL register via APB
- step: 3
  title: 3. Layered Step 1 + Driver Response
  component: alu_driver
  file: alu_driver.sv
  line: 46
  state: 65 ns · PIPELINED RSP
  desc: Driver completes ADD(x,y), copies id info via rsp.set_id_info(req), and returns rsp1.
  log_snippet: Launching parallel smoke + layered
- step: 4
  title: 4. Layered Step 2 Consumes Response
  component: alu_layered_frame_seq
  file: alu_seq.sv
  line: 66
  state: 105 ns · LAYERED
  desc: Layered sequence passes rsp1.result[15:0] as operand 'a' for step2 MUL -> (x+y)*scale.
  log_snippet: Macro (18 + 27) * 3 = 135
quizzes:
- q: Why must a pipelined driver call rsp.set_id_info(req) before seq_item_port.put(rsp)?
  options:
  - To allocate memory in uvm_factory
  - To copy sequence_id and transaction_id so the sequencer routes the response to the exact waiting sequence thread
  - To reset the virtual interface signals
  answer: 1
  explanation: When multiple sequences run concurrently, sequence_id and transaction_id uniquely identify which
    sequence's get_response(rsp) should wake up.
- q: Does a Virtual Sequencer connect directly to any uvm_driver?
  options:
  - Yes, it has its own seq_item_port driving RTL pins
  - No, it only holds references to underlying protocol sequencers so a virtual sequence can coordinate them
  - Only when operating in UVM_PASSIVE mode
  answer: 1
  explanation: A virtual sequencer coordinates sub-sequencers; actual pin driving still belongs strictly to each
    agent's driver.
---

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
