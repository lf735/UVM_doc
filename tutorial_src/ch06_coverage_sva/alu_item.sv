// -----------------------------------------------------------------------------
// alu_item.sv - Sequence Item Allowing Weighted Invalid Opcode (Chapter 6)
// -----------------------------------------------------------------------------
`ifndef ALU_ITEM_SV
`define ALU_ITEM_SV

typedef enum logic [2:0] {
  ALU_ADD    = 3'd0,
  ALU_SUB    = 3'd1,
  ALU_MUL    = 3'd2,
  ALU_XOR    = 3'd3,
  ALU_PASS_A = 3'd4,
  ALU_INVAL  = 3'd5
} alu_op_e;

class alu_item extends uvm_sequence_item;
  rand alu_op_e     op;
  rand logic [15:0] a;
  rand logic [15:0] b;
  rand logic [3:0]  tag;

  logic [31:0] result;
  logic        err_flag;

  constraint c_valid_op {
    op dist { [ALU_ADD:ALU_PASS_A] := 9, ALU_INVAL := 1 };
  }

  constraint c_operand_range {
    a dist { 16'h0000 := 1, [16'h0001:16'hFFFE] := 8, 16'hFFFF := 1 };
    b inside {[16'h0000 : 16'hFFFF]};
  }

  `uvm_object_utils_begin(alu_item)
    `uvm_field_enum(alu_op_e, op, UVM_ALL_ON)
    `uvm_field_int(a,        UVM_ALL_ON | UVM_HEX)
    `uvm_field_int(b,        UVM_ALL_ON | UVM_HEX)
    `uvm_field_int(tag,      UVM_ALL_ON | UVM_DEC)
    `uvm_field_int(result,   UVM_ALL_ON | UVM_HEX)
    `uvm_field_int(err_flag, UVM_ALL_ON)
  `uvm_object_utils_end

  function new(string name = "alu_item");
    super.new(name);
  endfunction

  virtual function string convert2string();
    return $sformatf("tag=%0d op=%s a=0x%04h b=0x%04h res=0x%08h err=%0b",
                     tag, op.name(), a, b, result, err_flag);
  endfunction
endclass

`endif
