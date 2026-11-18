// -----------------------------------------------------------------------------
// alu_driver_cb.sv - Non-Intrusive Driver Callback Hooks (Chapter 8)
// -----------------------------------------------------------------------------
`ifndef ALU_DRIVER_CB_SV
`define ALU_DRIVER_CB_SV

virtual class alu_driver_cb extends uvm_callback;
  function new(string name = "alu_driver_cb");
    super.new(name);
  endfunction

  // Hook invoked before driving pins onto alu_if
  virtual task pre_drive(alu_driver drv, alu_item req);
  endtask
endclass

// Concrete fault-injection callback mutating one item into ALU_INVAL
class alu_err_inject_cb extends alu_driver_cb;
  `uvm_object_utils(alu_err_inject_cb)

  int unsigned target_tag = 2;

  function new(string name = "alu_err_inject_cb");
    super.new(name);
  endfunction

  virtual task pre_drive(alu_driver drv, alu_item req);
    if (req.tag == target_tag[3:0]) begin
      `uvm_error("ALU_ERR_INJ", $sformatf("Callback injecting invalid opcode on tag=%0d", req.tag))
      req.op = ALU_INVAL;
    end
  endtask
endclass

`endif
