// -----------------------------------------------------------------------------
// alu_minimal_test.sv - Bare-Minimum UVM Test (No Agent/Env Yet) (Chapter 3)
// -----------------------------------------------------------------------------
`ifndef ALU_MINIMAL_TEST_SV
`define ALU_MINIMAL_TEST_SV

class alu_minimal_test extends uvm_test;
  `uvm_component_utils(alu_minimal_test)

  uvm_sequencer #(alu_item) seqr;
  alu_driver                drv;

  function new(string name = "alu_minimal_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    seqr = uvm_sequencer#(alu_item)::type_id::create("seqr", this);
    drv  = alu_driver::type_id::create("drv", this);
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    drv.seq_item_port.connect(seqr.seq_item_export);
  endfunction

  virtual task run_phase(uvm_phase phase);
    alu_smoke_seq seq;
    phase.raise_objection(this, "Starting minimal stimulus");
    seq = alu_smoke_seq::type_id::create("seq");
    seq.start(seqr);
    #40ns;
    phase.drop_objection(this, "Finished minimal stimulus");
  endtask
endclass

`endif
