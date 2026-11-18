---
slug: agent_factory_config
part: stimuli_core
title: 'Structuring & Configuring: Agent, Env, Factory & Config Objects'
short_title: Agent, Factory & ConfigDB
difficulty: Beginner
summary: 'Refactor the bare-minimum testbench into a reusable, configurable UVM hierarchy: encapsulate driver and
  sequencer inside uvm_agent (UVM_ACTIVE/UVM_PASSIVE), group agents in uvm_env, bundle settings in Config Objects,
  and swap transaction types dynamically via uvm_factory.'
objectives:
- Package protocol-specific driver/sequencer (and soon monitor) into a reusable `uvm_agent` supporting `UVM_ACTIVE`
  and `UVM_PASSIVE`.
- Replace individual `uvm_config_db` strings with strongly-typed hierarchical configuration objects (`alu_env_cfg`,
  `alu_agent_cfg`).
- Use `::type_id::create()` everywhere instead of `new()` so tests can override classes via `uvm_factory` without
  modifying source code.
- Group testbench classes inside a clean SystemVerilog `package alu_tb_pkg`.
apis:
- uvm_agent
- uvm_env
- uvm_test
- uvm_factory
- uvm_config_db
- uvm_active_passive_enum
- set_type_override_by_type
- set_inst_override_by_type
docs_links:
- label: uvm_agent
  url: docs_view/comps/uvm_agent-svh.html#uvm_agent
  desc: Protocol unit with active/passive toggle via is_active.
- label: uvm_env
  url: docs_view/comps/uvm_env-svh.html#uvm_env
  desc: Top container for agents, scoreboards, and coverage.
- label: uvm_factory
  url: docs_view/base/uvm_factory-svh.html#uvm_factory
  desc: Polymorphic object/component creation and overrides.
- label: Factory Overview
  url: docs_view/overviews/factory-txt.html
  desc: Why create() beats new() for testbench customization.
- label: Configuration & Resources
  url: docs_view/overviews/config_and_res-txt.html
  desc: Best practices for uvm_config_db and config objects.
example_links:
- label: Factory Overrides
  url: examples_view/infrastructure/factory.html
  desc: Type & instance overrides in action.
- label: Manual Configuration DB
  url: examples_view/infrastructure/manual.html
  desc: Hierarchical uvm_config_db scopes.
- label: Modular Packages
  url: examples_view/basics/pkg.html
  desc: Clean SystemVerilog package compilation.
interactive_widget: arch_diff
src_dir: ch04_agent_factory_config
inherit_from: auto
sim_log: |
  UVM_INFO @ 0: reporter [RNTST] Running test alu_mul_factory_test...
  #### Factory Configuration (*)
  Type Overrides:
    Requested Type  Override Type
    --------------  ------------------
    alu_item        alu_mul_only_item
  UVM_INFO @ 0: reporter [UVMTOP] UVM testbench topology:
    uvm_test_top (alu_mul_factory_test)
      env (alu_env)
        data_agent (alu_agent)
          drv (alu_driver)
          seqr (uvm_sequencer)
  UVM_INFO alu_seq.sv(22) @ 25: uvm_test_top.env.data_agent.seqr@@seq [SEQ] Sending tag=0 op=ALU_MUL a=0x008b b=0x0041 (type=alu_mul_only_item)
  UVM_INFO alu_driver.sv(40) @ 30: uvm_test_top.env.data_agent.drv [DRV] Driving tag=0 op=ALU_MUL a=0x008b b=0x0041
  --- UVM Report Summary ---
  UVM_INFO :    14
  UVM_ERROR :   0
stepper:
- step: 1
  title: 1. Register Factory Type Override
  component: alu_mul_factory_test
  file: alu_test.sv
  line: 50
  state: 0 ns · FACTORY
  desc: Before super.build_phase(), test swaps alu_item -> alu_mul_only_item globally in uvm_factory.
  log_snippet: Type Overrides
- step: 2
  title: 2. Build Config Object & Environment
  component: alu_base_test
  file: alu_test.sv
  line: 22
  state: 0 ns · BUILD
  desc: Test populates alu_env_cfg with virtual interface and delegates hierarchy construction to alu_env.
  log_snippet: UVM testbench topology
- step: 3
  title: 3. Active Agent Conditional Build
  component: alu_agent
  file: alu_agent.sv
  line: 24
  state: 0 ns · AGENT
  desc: data_agent checks cfg.is_active == UVM_ACTIVE before creating seqr and drv.
  log_snippet: data_agent (alu_agent)
- step: 4
  title: 4. Factory Creates Overridden Item
  component: alu_smoke_seq
  file: alu_seq.sv
  line: 21
  state: 25 ns · CREATE
  desc: alu_item::type_id::create() returns an alu_mul_only_item instance transparently.
  log_snippet: type=alu_mul_only_item
quizzes:
- q: When should a test call set_type_override() or set_inst_override()?
  options:
  - In run_phase() right after raising an objection
  - In build_phase() BEFORE creating the components/objects to be overridden
  - In report_phase() to summarize test configuration
  answer: 1
  explanation: Factory overrides must be registered before ::type_id::create() executes during build_phase() or
    sequence execution.
- q: What is the key advantage of passing alu_env_cfg instead of individual integers/strings via uvm_config_db?
  options:
  - Compile-time type checking of all fields and single config_db lookup per component
  - It eliminates the need for build_phase()
  - Config objects automatically synthesize to FPGA gates
  answer: 0
  explanation: Bundling configuration parameters inside a single uvm_object reduces string lookup overhead and catches
    field typos at compile time.
---

## 4.1 Why Encapsulate Into `uvm_agent` and `uvm_env`?

Putting `seqr` and `drv` directly inside `alu_minimal_test` (Chapter 3) works for 1 test, but fails the moment you need:
1. **A second interface** (e.g., an APB bus alongside our data port),
2. **Dozens of tests** that share the same structural wiring without copy-pasting `build_phase()`/`connect_phase()`,
3. **Passive SoC reuse**, where the driver and sequencer must be disabled (`UVM_PASSIVE`).

```mermaid
flowchart TB
    TEST["alu_mul_factory_test (uvm_test)"] --> ENV["alu_env (uvm_env)"]
    TEST -. "set_type_override(alu_item -> alu_mul_only_item)" .-> FAC["uvm_factory"]
    ENV --> AGT["data_agent (uvm_agent)"]
    AGT -->|"if UVM_ACTIVE"| SEQR["seqr (uvm_sequencer)"]
    AGT -->|"if UVM_ACTIVE"| DRV["drv (alu_driver)"]
    SEQR <--> DRV
```

---

## 4.2 Configuration Objects Beat Scattered `config_db` Calls

Instead of storing 10 separate scalar fields in `uvm_config_db` (slow string lookups, typo risks), we bundle related settings inside `uvm_object` subclasses (`alu_agent_cfg`, `alu_env_cfg` in **`alu_cfg.sv`**):
- `alu_base_test` creates `env_cfg`, populates `env_cfg.data_agent_cfg.vif`, and passes `env_cfg` down to `alu_env`.
- `alu_env` passes `cfg.data_agent_cfg` down to `data_agent`.
- `alu_agent` inspects `cfg.is_active`: when `UVM_ACTIVE`, it builds `seqr` and `drv`.

---

## 4.3 Polymorphism Without Editing Code: `uvm_factory`

Notice in `alu_seq.sv` line 21:
```systemverilog
req = alu_item::type_id::create($sformatf("req_%0d", i));
```
Never call `new()` for reusable UVM items or components! Because the sequence asks the **Factory** to create `alu_item`, our derived test `alu_mul_factory_test` can execute:
```systemverilog
alu_item::type_id::set_type_override(alu_mul_only_item::get_type());
```
Every sequence automatically generates `alu_mul_only_item` (constrained to `ALU_MUL`) **without modifying a single line of `alu_seq.sv` or `alu_env.sv`**.
