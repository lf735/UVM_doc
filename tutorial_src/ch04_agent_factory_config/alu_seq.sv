// -----------------------------------------------------------------------------
// alu_seq.sv - Configurable Sequence Using Factory Creation (Chapter 4)
// -----------------------------------------------------------------------------
`ifndef ALU_SEQ_SV
`define ALU_SEQ_SV

class alu_smoke_seq extends uvm_sequence #(alu_item);
  `uvm_object_utils(alu_smoke_seq)

  rand int unsigned num_items = 6;

  function new(string name = "alu_smoke_seq");
    super.new(name);
  endfunction

  virtual task body();
    alu_item req;
    `uvm_info("SEQ", $sformatf("Starting sequence (%0d items)", num_items), UVM_LOW)

    for (int i = 0; i < num_items; i++) begin
      // Factory creation allows test-level type overrides without editing sequence code
      req = alu_item::type_id::create($sformatf("req_%0d", i));
      start_item(req);
      if (!req.randomize() with { tag == local::i[3:0]; }) begin
        `uvm_fatal("SEQ", "Randomization failed for alu_item")
      end
      `uvm_info("SEQ", $sformatf("Sending %s (type=%s)", req.convert2string(), req.get_type_name()), UVM_MEDIUM)
      finish_item(req);
    end
  endtask
endclass

`endif
