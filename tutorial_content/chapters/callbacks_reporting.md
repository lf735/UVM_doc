---
slug: callbacks_reporting
part: production_uvm
title: 'Non-Intrusive Extension: Callbacks, Report Catcher & Cmdline'
short_title: Callbacks & Reporting
difficulty: Advanced
summary: 'Customize VIP behavior without modifying source code: inject faults via uvm_callback hooks, intercept
  and demote expected negative-test errors with uvm_report_catcher, and control simulation behavior dynamically
  from the command line using uvm_cmdline_processor.'
objectives:
- Instrument a VIP driver cleanly with `` `uvm_register_cb `` and `` `uvm_do_callbacks ``.
- Inject targeted error transactions from a test using `uvm_callbacks#(alu_driver, alu_driver_cb)::add()` without
  altering sequence or driver code.
- Use `uvm_report_catcher` to intercept expected `UVM_ERROR` IDs (`ALU_ERR_INJ`) during fault-injection tests and
  demote them safely.
- Parse custom `+PLUSARGS` at runtime with `uvm_cmdline_processor::get_inst()`.
apis:
- uvm_callback
- '`uvm_register_cb'
- '`uvm_do_callbacks'
- uvm_report_catcher
- uvm_report_handler
- uvm_cmdline_processor
docs_links:
- label: uvm_callback
  url: docs_view/base/uvm_callback-svh.html#uvm_callback
  desc: Base callback class and registration pool.
- label: Callback Macros
  url: docs_view/macros/uvm_callback_defines-svh.html
  desc: '`uvm_register_cb and `uvm_do_callbacks macros.'
- label: uvm_report_catcher
  url: docs_view/base/uvm_report_catcher-svh.html#uvm_report_catcher
  desc: Intercept, modify, promote, or demote UVM reports.
- label: Reporting Overview
  url: docs_view/overviews/reporting-txt.html
  desc: UVM reporting severity, verbosity, and actions.
- label: uvm_cmdline_processor
  url: docs_view/base/uvm_cmdline_processor-svh.html#uvm_cmdline_processor
  desc: Read simulation +plusargs dynamically.
- label: Cmdline Overview
  url: docs_view/overviews/cmdlineproc-txt.html
  desc: Standard UVM CLI arguments and custom flags.
example_links:
- label: Callback Hooks
  url: examples_view/infrastructure/callbacks.html
  desc: Injecting error packets via uvm_callback.
interactive_widget: arch_diff
src_dir: ch08_callbacks_reporting
inherit_from: auto
sim_log: |
  UVM_INFO @ 0: reporter [RNTST] Running test alu_base_test...
  UVM_INFO alu_test.sv(38) @ 0: uvm_test_top [TEST] Registered alu_err_inject_cb + alu_report_catcher via +INJECT_ERR=1
  UVM_INFO alu_virtual_seq.sv(18) @ 25: uvm_test_top.env.v_seqr@@vseq [VSEQ] Phase 1: Configuring CTRL register via APB agent (EN=1, SAT_EN=0)
  UVM_INFO alu_driver_cb.sv(25) @ 75: reporter [ALU_ERR_INJ] [CAUGHT & DEMOTED] Callback injecting invalid opcode on tag=2
  UVM_INFO alu_scoreboard.sv(44) @ 85: uvm_test_top.env.scb [SCB] MATCH tag=2 op=ALU_INVAL result=0xdeadbeef err=1
  UVM_INFO alu_scoreboard.sv(59) @ 190: uvm_test_top.env.scb [SCB] Scoreboard Summary: PASS=8 FAIL=0
  --- UVM Report Summary ---
  UVM_INFO :    18
  UVM_ERROR :   0
stepper:
- step: 1
  title: 1. Parse +INJECT_ERR=1 via Cmdline Processor
  component: alu_base_test
  file: alu_test.sv
  line: 31
  state: 0 ns · START_OF_SIM
  desc: uvm_cmdline_processor inspects +INJECT_ERR=1 and registers callback + report catcher.
  log_snippet: Registered alu_err_inject_cb
- step: 2
  title: 2. Driver Invokes Pre-Drive Callback
  component: alu_driver
  file: alu_driver.sv
  line: 34
  state: 75 ns · CALLBACK
  desc: '`uvm_do_callbacks calls err_cb.pre_drive(this, req), mutating tag=2 to ALU_INVAL.'
  log_snippet: Callback injecting invalid opcode
- step: 3
  title: 3. Report Catcher Intercepts & Demotes
  component: alu_report_catcher
  file: alu_report_catcher.sv
  line: 17
  state: 75 ns · CATCH
  desc: alu_report_catcher catches UVM_ERROR [ALU_ERR_INJ] and demotes it to UVM_INFO.
  log_snippet: '[CAUGHT & DEMOTED]'
- step: 4
  title: 4. Monitor & Scoreboard Observe Injected Fault
  component: alu_scoreboard
  file: alu_scoreboard.sv
  line: 44
  state: 85 ns · CHECK
  desc: Because monitor observes real pins, scoreboard sees ALU_INVAL and verifies DUT outputs 0xdeadbeef & err=1!
  log_snippet: MATCH tag=2 op=ALU_INVAL
quizzes:
- q: When should you choose a uvm_callback instead of a uvm_factory override?
  options:
  - When you want to inject a lightweight behavioral hook (e.g. error injection on specific cycles) into an existing
    component instance without subclassing and replacing the whole component
  - Whenever creating a sequence item
  - When replacing the RTL DUT module
  answer: 0
  explanation: Callbacks attach multiple orthogonal hooks dynamically per instance without duplicating or subclassing
    the entire driver.
- q: What is the difference between returning CAUGHT vs. THROW inside uvm_report_catcher::catch()?
  options:
  - CAUGHT suppresses the report completely from being printed or passing to further catchers; THROW lets the (possibly
    modified) report continue down the catcher chain and print
  - THROW aborts the simulation with $fatal
  - They behave identically
  answer: 0
  explanation: Returning THROW after calling set_severity(UVM_INFO) prints the demoted report cleanly; returning
    CAUGHT drops the message silently.
---

## 8.1 Extending Locked VIPs with `uvm_callback`

When verifying with third-party or shared company VIPs, **you must not edit the VIP driver** just to inject one protocol glitch or corrupt a specific packet tag.

```mermaid
flowchart LR
    TEST["alu_base_test (+INJECT_ERR=1)"] -->|"callbacks::add(drv, err_cb)"| CB["alu_err_inject_cb"]
    TEST -->|"report_cb::add(null, catcher)"| RC["alu_report_catcher"]
    DRV["alu_driver"] -->|"uvm_do_callbacks(pre_drive)"| CB
    CB -->|"mutates tag=2 to ALU_INVAL + UVM_ERROR"| RC
    RC -->|"demotes UVM_ERROR to UVM_INFO"| LOG["Clean Passing Negative Test"]
```

In **`alu_driver.sv`**, two macro lines expose an extensible hook:
1. `` `uvm_register_cb(alu_driver, alu_driver_cb) `` inside the class declaration.
2. `` `uvm_do_callbacks(alu_driver, alu_driver_cb, pre_drive(this, req)) `` right before driving pins.

If zero callbacks are registered, `` `uvm_do_callbacks `` is a zero-cost no-op. When `+INJECT_ERR=1` is passed on the simulator command line, `alu_base_test` attaches **`alu_err_inject_cb`** to mutate `tag == 2` into `ALU_INVAL`!

---

## 8.2 Negative Testing & `uvm_report_catcher`

Error-injection tests intentionally trigger error messages (`ALU_ERR_INJ`). If left at `UVM_ERROR`, regression scripts mark the simulation as **FAILED**.
**`alu_report_catcher`** intercepts every report before it reaches the console:
- Matches `get_severity() == UVM_ERROR && get_id() == "ALU_ERR_INJ"`,
- Calls `set_severity(UVM_INFO)` and prepends `"[CAUGHT & DEMOTED] "`,
- Returns `THROW` (so any chained catchers still run) while letting real unexpected bugs fail loudly!
