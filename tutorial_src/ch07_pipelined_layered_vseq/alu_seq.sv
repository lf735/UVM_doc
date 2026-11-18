// -----------------------------------------------------------------------------
// alu_seq.sv - Pipelined Response Sequence, Lock & Layered Sequences (Chapter 7)
// -----------------------------------------------------------------------------
`ifndef ALU_SEQ_SV
`define ALU_SEQ_SV

// High-level macro transaction (upper protocol layer)
class alu_macro_frame_item extends uvm_sequence_item;
  rand logic [15:0] x;
  rand logic [15:0] y;
  rand logic [15:0] scale;
  `uvm_object_utils(alu_macro_frame_item)

  function new(string name = "alu_macro_frame_item");
    super.new(name);
  endfunction
endclass

// Pipelined response-aware leaf sequence using grab()/lock() arbitration
class alu_smoke_seq extends uvm_sequence #(alu_item);
  `uvm_object_utils(alu_smoke_seq)

  rand int unsigned num_items = 6;
  rand bit          use_lock  = 1'b0;

  function new(string name = "alu_smoke_seq");
    super.new(name);
  endfunction

  virtual task body();
    alu_item req, rsp;
    if (use_lock) m_sequencer.lock(this);

    for (int i = 0; i < num_items; i++) begin
      req = alu_item::type_id::create($sformatf("req_%0d", i));
      start_item(req);
      if (!req.randomize() with { tag == local::i[3:0]; }) begin
        `uvm_fatal("SEQ", "Randomization failed")
      end
      finish_item(req);
      get_response(rsp);
      `uvm_info("SEQ", $sformatf("Received rsp: %s", rsp.convert2string()), UVM_HIGH)
    end

    if (use_lock) m_sequencer.unlock(this);
  endtask
endclass

// Layered Translator Sequence: converts high-level frame "(x + y) * scale"
// into two consecutive low-level alu_item operations on the data sequencer.
class alu_layered_frame_seq extends uvm_sequence #(alu_item);
  `uvm_object_utils(alu_layered_frame_seq)

  alu_macro_frame_item frame;

  function new(string name = "alu_layered_frame_seq");
    super.new(name);
  endfunction

  virtual task body();
    alu_item step1, step2, rsp1, rsp2;
    if (frame == null) begin
      frame = alu_macro_frame_item::type_id::create("frame");
      void'(frame.randomize() with { x inside {[1:50]}; y inside {[1:50]}; scale inside {[2:4]}; });
    end

    // Layer Step 1: sum = x + y
    step1 = alu_item::type_id::create("step1_add");
    start_item(step1);
    step1.op  = ALU_ADD;
    step1.a   = frame.x;
    step1.b   = frame.y;
    step1.tag = 4'hA;
    finish_item(step1);
    get_response(rsp1);

    // Layer Step 2: result = sum * scale (feeds output of Step 1 into Step 2!)
    step2 = alu_item::type_id::create("step2_mul");
    start_item(step2);
    step2.op  = ALU_MUL;
    step2.a   = rsp1.result[15:0];
    step2.b   = frame.scale;
    step2.tag = 4'hB;
    finish_item(step2);
    get_response(rsp2);

    `uvm_info("LAYERED_SEQ", $sformatf("Macro (%0d + %0d) * %0d = %0d",
              frame.x, frame.y, frame.scale, rsp2.result), UVM_LOW)
  endtask
endclass

`endif
