---
slug: verification_vcycle
part: foundations
title: Verification Fundamentals, V-Cycle & Role Split
short_title: V-Cycle & Team Roles
difficulty: Beginner
summary: Understand why verification consumes 60-70% of ASIC/FPGA project effort, how the hardware V-Cycle connects
  specification to sign-off, and how responsibilities split cleanly across the System Architect, RTL Designer, and
  Verification Engineer.
objectives:
- Explain the purpose of functional verification versus RTL design and why self-verification creates blind spots.
- Map every phase of the hardware V-Cycle from Architecture Specification down to RTL and back up to Sign-Off.
- Define the exact deliverables and handoff contracts between System Architect, RTL Designer, and Verifier.
- Understand how a Verification Plan (vPlan) connects architectural features to measurable UVM coverage closure.
apis:
- uvm_test
- uvm_env
- uvm_agent
- uvm_component
docs_links:
- label: UVM 1.2 Introduction
  url: docs_view/overviews/intro-txt.html
  desc: High-level UVM goals, reuse model, and class library overview.
- label: UVM Components Overview
  url: docs_view/overviews/components-txt.html
  desc: Role of structured hierarchical components in scalable verification.
- label: uvm_test
  url: docs_view/comps/uvm_test-svh.html#uvm_test
  desc: Top-level test class configuring environments and scenarios.
- label: uvm_env
  url: docs_view/comps/uvm_env-svh.html#uvm_env
  desc: Reusable verification environment container.
example_links:
- label: Trivial Component
  url: examples_view/basics/trivial.html
  desc: Smallest possible UVM component lifecycle.
interactive_widget: vcycle
home_featured:
  badge: Foundations
  badge_class: home-badge-beginner
  title: V-Cycle & Roles
  desc: Interactive V-Cycle, Architect / Designer / Verifier task split, and Stimuli / Checks / Metrics.
quizzes:
- q: Why should the RTL designer and verification engineer work from an independent interpretation of the architecture
    spec?
  options:
  - To double the amount of SystemVerilog code written on the project
  - To prevent identical spec misinterpretations from hiding bugs in both RTL and testbench
  - Because UVM forbids RTL modules from being compiled in the same simulator
  answer: 1
  explanation: Independent testbench modeling catches spec ambiguities and implementation assumptions that a single
    author would replicate in both RTL and test.
- q: Which document links the System Architect's requirements on the left side of the V-Cycle to measurable UVM
    closure on the right side?
  options:
  - Makefile.questa
  - The Verification Plan (vPlan)
  - The RTL synthesis netlist
  answer: 1
  explanation: The vPlan maps every architectural feature and corner case to specific stimuli, checkers/assertions,
    and functional coverage targets.
---

## 1.1 Why Verification Exists (And Why Designers Don't Verify Their Own RTL)

In modern ASIC and FPGA projects, **verification typically accounts for 60% to 70% of engineering time and compute resources**. The objective is fundamentally asymmetric compared to hardware design:

- **RTL Design** builds a *specific* hardware micro-architecture that satisfies timing, area, and power budgets.
- **Functional Verification** tries to *break* that implementation under every legal (and illegal) sequence of inputs, corner cases, backpressure stalls, and register configurations before tape-out.

> **Golden Rule of Independent Verification:** Never verify a block solely using the same mental assumptions used to design it. If a designer misreads an ambiguous sentence in a specification, writing both the RTL and the testbench perpetuates the exact same bug in both places.

---

## 1.2 The Hardware V-Cycle

The **V-Cycle** models how abstraction descends from system requirements down to synthesizable SystemVerilog RTL (left leg), and then climbs back up through block, subsystem, and SoC verification to tape-out sign-off (right leg).

```mermaid
flowchart LR
    S1["System Spec (Architect)"] --> S2["Micro-Arch (Designer)"]
    S2 --> S3["RTL Coding (Designer)"]
    S3 --> V1["vPlan & Block TB (Verifier)"]
    V1 --> V2["Block Closure (Verifier)"]
    V2 --> V3["SoC Reuse & Sign-Off (All)"]
    S1 -. "Requirement Traceability" .-> V3
    S2 -. "Corner-Case Review" .-> V1
```

Each descending step creates a **specification contract**, and each ascending step validates that contract independently:

1. **System Specification -> Verification Plan (vPlan):** Every architectural requirement (e.g., *"saturate arithmetic overflow when `CTRL.SAT_EN=1`"*) receives a unique requirement ID mapped to stimulus scenarios, assertions, and coverage bins.
2. **Micro-Architecture -> Corner-Case Checklist:** Pipeline hazards, FIFO full/empty transitions, reset synchronization, and bus wait-states are translated into constrained-random constraints and SVA properties.
3. **RTL Freeze -> Block UVM Verification:** Once port lists and protocols stabilize, the Verification Engineer exercises the DUT inside an automated self-checking UVM testbench.
4. **Block Closure -> Subsystem / SoC Vertical Reuse:** Clean UVM environments switch their block agents from `UVM_ACTIVE` to `UVM_PASSIVE` so the exact same scoreboard and coverage collectors keep checking inside full-chip simulations.

---

## 1.3 Role Split: Architect vs. Designer vs. Verifier

| Responsibility | System Architect | RTL Designer | Verification Engineer |
| :--- | :--- | :--- | :--- |
| **Primary Artifact** | System Spec, Memory/Register Map (IP-XACT), Interface Specs | Synthesizable RTL (`pkt_alu.sv`), Lint/CDC-clean code | vPlan, UVM Testbench, Reference Model, Coverage & Sign-off Report |
| **Mental Model** | *What* the IP must do externally (protocols, throughput, registers) | *How* silicon implements it cycle-by-cycle (FSMs, flops, muxes) | *How it could fail* (races, stalls, overflow, reset, illegal sequences) |
| **Interface Ownership** | Defines bus protocol & register reset values | Implements RTL pins & timing constraints | Writes `interface` + SVA assertions + BFM Driver/Monitor |
| **Debug Ownership** | Resolves spec ambiguities | Fixes confirmed RTL bugs & updates waveforms | Triages failures, distinguishes TB vs RTL bugs, closes coverage holes |
| **Sign-Off Gate** | Confirms architectural intent | Confirms synthesis/lint/CDC clean | Confirms 0 errors, 100% functional + code coverage closure |

Explore the **Interactive V-Cycle & Role Matrix** below to inspect every stage, deliverable, and handoff contract.
