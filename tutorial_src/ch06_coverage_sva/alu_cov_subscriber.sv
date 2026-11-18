// -----------------------------------------------------------------------------
// alu_cov_subscriber.sv - Coverage Subscriber (Metrics Separation) (Ch.6)
// -----------------------------------------------------------------------------
`ifndef ALU_COV_SUBSCRIBER_SV
`define ALU_COV_SUBSCRIBER_SV

class alu_cov_subscriber extends uvm_subscriber #(alu_item);
  `uvm_component_utils(alu_cov_subscriber)

  alu_item cov_tr;

  covergroup cg_alu;
    cp_op: coverpoint cov_tr.op {
      bins arithmetic[] = {ALU_ADD, ALU_SUB, ALU_MUL};
      bins logic_ops[]  = {ALU_XOR, ALU_PASS_A};
      bins invalid_op   = {ALU_INVAL};
    }

    cp_a_corners: coverpoint cov_tr.a {
      bins zero = {16'h0000};
      bins low  = {[16'h0001 : 16'h00FF]};
      bins mid  = {[16'h0100 : 16'hFFFE]};
      bins max  = {16'hFFFF};
    }

    cp_err: coverpoint cov_tr.err_flag {
      bins ok  = {1'b0};
      bins err = {1'b1};
    }

    cx_op_x_err: cross cp_op, cp_err {
      ignore_bins valid_no_err = binsof(cp_op.invalid_op) && binsof(cp_err.ok);
    }
  endgroup

  function new(string name = "alu_cov_subscriber", uvm_component parent = null);
    super.new(name, parent);
    cg_alu = new();
  endfunction

  // Called automatically via analysis_export from monitor's TLM broadcast
  virtual function void write(alu_item t);
    cov_tr = t;
    cg_alu.sample();
  endfunction

  virtual function void report_phase(uvm_phase phase);
    super.report_phase(phase);
    `uvm_info("COV", $sformatf("Functional Coverage achieved: %0.2f%%", cg_alu.get_inst_coverage()), UVM_LOW)
  endfunction
endclass

`endif
