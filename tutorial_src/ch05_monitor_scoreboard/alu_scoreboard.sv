// -----------------------------------------------------------------------------
// alu_scoreboard.sv - TLM FIFO Scoreboard & Comparator (Chapter 5)
// -----------------------------------------------------------------------------
`ifndef ALU_SCOREBOARD_SV
`define ALU_SCOREBOARD_SV

class alu_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(alu_scoreboard)

  uvm_analysis_export #(alu_item)   req_export;
  uvm_analysis_export #(alu_item)   rsp_export;
  uvm_tlm_analysis_fifo #(alu_item) req_fifo;
  uvm_tlm_analysis_fifo #(alu_item) rsp_fifo;

  alu_ref_model ref_model;
  int unsigned  pass_count;
  int unsigned  fail_count;

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
    forever begin
      req_fifo.get(req);
      rsp_fifo.get(act);
      exp = ref_model.predict(req);

      if (act.tag !== exp.tag || act.result !== exp.result || act.err_flag !== exp.err_flag) begin
        fail_count++;
        `uvm_error("SCB", $sformatf(
          "MISMATCH! EXP(tag=%0d res=0x%08h err=%0b) != ACT(tag=%0d res=0x%08h err=%0b)",
          exp.tag, exp.result, exp.err_flag, act.tag, act.result, act.err_flag))
      end else begin
        pass_count++;
        `uvm_info("SCB", $sformatf("MATCH tag=%0d op=%s result=0x%08h",
                  exp.tag, exp.op.name(), act.result), UVM_MEDIUM)
      end
    end
  endtask

  virtual function void check_phase(uvm_phase phase);
    super.check_phase(phase);
    if (!req_fifo.is_empty() || !rsp_fifo.is_empty()) begin
      `uvm_error("SCB", $sformatf("Unmatched items at end of test: req=%0d rsp=%0d",
                 req_fifo.used(), rsp_fifo.used()))
    end
  endfunction

  virtual function void report_phase(uvm_phase phase);
    super.report_phase(phase);
    `uvm_info("SCB", $sformatf("Scoreboard Summary: PASS=%0d FAIL=%0d", pass_count, fail_count), UVM_LOW)
  endfunction
endclass

`endif
