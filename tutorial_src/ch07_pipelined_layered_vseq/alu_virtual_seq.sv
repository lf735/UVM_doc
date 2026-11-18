// -----------------------------------------------------------------------------
// alu_virtual_seq.sv - Virtual Sequence Orchestrating APB + Data Streams (Ch.7)
// -----------------------------------------------------------------------------
`ifndef ALU_VIRTUAL_SEQ_SV
`define ALU_VIRTUAL_SEQ_SV

class alu_virtual_seq extends uvm_sequence;
  `uvm_object_utils(alu_virtual_seq)
  `uvm_declare_p_sequencer(alu_virtual_sequencer)

  function new(string name = "alu_virtual_seq");
    super.new(name);
  endfunction

  virtual task body();
    apb_write_seq         cfg_seq;
    alu_smoke_seq         smoke_seq;
    alu_layered_frame_seq layered_seq;

    `uvm_info("VSEQ", "Phase 1: Configuring CTRL register via APB agent (EN=1, SAT_EN=0)", UVM_LOW)
    cfg_seq = apb_write_seq::type_id::create("cfg_seq");
    cfg_seq.addr = 8'h00;
    cfg_seq.data = 32'h0000_0001;
    cfg_seq.start(p_sequencer.apb_sqr);

    `uvm_info("VSEQ", "Phase 2: Launching parallel smoke + layered arithmetic flows", UVM_LOW)
    smoke_seq   = alu_smoke_seq::type_id::create("smoke_seq");
    layered_seq = alu_layered_frame_seq::type_id::create("layered_seq");

    // Sequencer arbitration coordinates concurrent sequences cleanly
    p_sequencer.alu_sqr.set_arbitration(SEQ_ARB_STRICT_FIFO);
    fork
      smoke_seq.start(p_sequencer.alu_sqr);
      layered_seq.start(p_sequencer.alu_sqr);
    join
  endtask
endclass

`endif
