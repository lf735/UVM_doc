// -----------------------------------------------------------------------------
// alu_scoreboard.sv - DPI-C + RAL Mirrored Scoreboard (Chapter 12)
// -----------------------------------------------------------------------------
`ifndef ALU_SCOREBOARD_SV
`define ALU_SCOREBOARD_SV

class alu_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(alu_scoreboard)

  uvm_analysis_export #(alu_item)   req_export;
  uvm_analysis_export #(alu_item)   rsp_export;
  uvm_tlm_analysis_fifo #(alu_item) req_fifo;
  uvm_tlm_analysis_fifo #(alu_item) rsp_fifo;

  alu_ref_model      ref_model;
  pkt_alu_reg_block  reg_model;
  int unsigned       pass_count;
  int unsigned       fail_count;

  function new(string name = "alu_scoreboard", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    req_export = new("req_export", this);
    rsp_export = new("rsp_export", this);
    req_fifo   = new("req_fifo", this);
    rsp_fifo   = new("rsp_fifo", this);
    ref_model  = alu_ref_model::type_id::create("ref_model", this);
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    req_export.connect(req_fifo.analysis_export);
    rsp_export.connect(rsp_fifo.analysis_export);
  endfunction

  virtual task run_phase(uvm_phase phase);
    alu_item req, exp, act;
    bit sat_en, err_mask;
    logic [15:0] sat_lim;

    forever begin
      req_fifo.get(req);
      rsp_fifo.get(act);

      sat_en   = (reg_model != null) ? reg_model.CTRL.sat_en.get_mirrored_value() : 1'b0;
      err_mask = (reg_model != null) ? reg_model.CTRL.err_mask.get_mirrored_value() : 1'b0;
      sat_lim  = (reg_model != null) ? reg_model.SAT_LIMIT.limit.get_mirrored_value() : 16'hFFFF;

      exp = ref_model.predict_with_cfg(req, sat_en, sat_lim, err_mask);

      if (act.tag !== exp.tag || act.result !== exp.result || act.err_flag !== exp.err_flag) begin
        fail_count++;
        `uvm_error("SCB", $sformatf("MISMATCH EXP=0x%08h ACT=0x%08h", exp.result, act.result))
      end else begin
        pass_count++;
        `uvm_info("SCB", $sformatf("DPI-C MATCH tag=%0d result=0x%08h", act.tag, act.result), UVM_MEDIUM)
      end
    end
  endtask

  virtual function void report_phase(uvm_phase phase);
    super.report_phase(phase);
    `uvm_info("SCB", $sformatf("DPI-C + RAL Scoreboard: PASS=%0d FAIL=%0d", pass_count, fail_count), UVM_LOW)
  endfunction
endclass

`endif
