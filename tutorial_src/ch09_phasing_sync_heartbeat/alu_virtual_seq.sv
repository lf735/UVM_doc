// -----------------------------------------------------------------------------
// alu_virtual_seq.sv - Barrier & Event Synchronized Virtual Sequence (Ch.9)
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
    uvm_event_pool ev_pool = uvm_event_pool::get_global_pool();
    uvm_event      cfg_done_ev = ev_pool.get("cfg_done");
    uvm_barrier    sync_bar    = new("sync_bar", 2);

    apb_write_seq         cfg_seq;
    alu_smoke_seq         seq_a;
    alu_layered_frame_seq seq_b;

    cfg_seq = apb_write_seq::type_id::create("cfg_seq");
    cfg_seq.addr = 8'h00;
    cfg_seq.data = 32'h0000_0001;
    cfg_seq.start(p_sequencer.apb_sqr);

    cfg_done_ev.trigger();
    `uvm_info("VSEQ", "Triggered global 'cfg_done' uvm_event; syncing threads with uvm_barrier", UVM_LOW)

    seq_a = alu_smoke_seq::type_id::create("seq_a");
    seq_b = alu_layered_frame_seq::type_id::create("seq_b");

    fork
      begin
        sync_bar.wait_for();
        seq_a.start(p_sequencer.alu_sqr);
      end
      begin
        sync_bar.wait_for();
        seq_b.start(p_sequencer.alu_sqr);
      end
    join
  endtask
endclass

`endif
