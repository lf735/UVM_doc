// -----------------------------------------------------------------------------
// alu_ref_model.sv - Golden Reference Predictor (Chapter 5)
// -----------------------------------------------------------------------------
`ifndef ALU_REF_MODEL_SV
`define ALU_REF_MODEL_SV

class alu_ref_model extends uvm_component;
  `uvm_component_utils(alu_ref_model)

  function new(string name = "alu_ref_model", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function alu_item predict(alu_item req);
    alu_item exp = alu_item::type_id::create("exp_item");
    exp.copy(req);
    exp.err_flag = 1'b0;

    case (req.op)
      ALU_ADD:    exp.result = {16'd0, req.a} + {16'd0, req.b};
      ALU_SUB:    exp.result = {16'd0, req.a} - {16'd0, req.b};
      ALU_MUL:    exp.result = req.a * req.b;
      ALU_XOR:    exp.result = {16'd0, (req.a ^ req.b)};
      ALU_PASS_A: exp.result = {16'd0, req.a};
      default: begin
        exp.result   = 32'hDEAD_BEEF;
        exp.err_flag = 1'b1;
      end
    endcase
    return exp;
  endfunction
endclass

`endif
