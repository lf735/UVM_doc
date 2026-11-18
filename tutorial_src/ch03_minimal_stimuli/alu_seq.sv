// -----------------------------------------------------------------------------
// alu_seq.sv - Minimal Stimulus Sequence (Chapter 3)
// -----------------------------------------------------------------------------
`ifndef ALU_SEQ_SV
`define ALU_SEQ_SV

class alu_smoke_seq extends uvm_sequence #(alu_item);
  `uvm_object_utils(alu_smoke_seq)

  rand int unsigned num_items = 4;

  function new(string name = "alu_smoke_seq");
    super.new(name);
  endfunction

  virtual task body();
    alu_item req;
    `uvm_info("SEQ", $sformatf("Starting smoke sequence (%0d items)", num_items), UVM_LOW)

    for (int i = 0; i < num_items; i++) begin
      req = alu_item::type_id::create($sformatf("req_%0d", i));
      start_item(req);
      if (!req.randomize() with { tag == local::i[3:0]; }) begin
        `uvm_fatal("SEQ", "Randomization failed for alu_item")
      end
      `uvm_info("SEQ", $sformatf("Sending %s", req.convert2string()), UVM_MEDIUM)
      finish_item(req);
    end

    `uvm_info("SEQ", "Completed smoke sequence", UVM_LOW)
  endtask
endclass

`endif
