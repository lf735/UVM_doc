// -----------------------------------------------------------------------------
// alu_monitor.sv - Passive Bus Monitor with TLM Analysis Ports (Chapter 5)
// -----------------------------------------------------------------------------
`ifndef ALU_MONITOR_SV
`define ALU_MONITOR_SV

class alu_monitor extends uvm_monitor;
  `uvm_component_utils(alu_monitor)

  alu_agent_cfg  cfg;
  virtual alu_if vif;

  uvm_analysis_port #(alu_item) req_ap;
  uvm_analysis_port #(alu_item) rsp_ap;

  function new(string name = "alu_monitor", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    req_ap = new("req_ap", this);
    rsp_ap = new("rsp_ap", this);
    if (!uvm_config_db#(alu_agent_cfg)::get(this, "", "cfg", cfg)) begin
      `uvm_fatal("MON", "alu_agent_cfg not found in uvm_config_db")
    end
    vif = cfg.vif;
  endfunction

  virtual task run_phase(uvm_phase phase);
    @(posedge vif.rst_n);
    fork
      collect_requests();
      collect_responses();
    join
  endtask

  virtual task collect_requests();
    forever begin
      @(vif.mon_cb);
      if (vif.mon_cb.in_valid && vif.mon_cb.in_ready) begin
        alu_item tr = alu_item::type_id::create("obs_req");
        tr.op  = alu_op_e'(vif.mon_cb.op);
        tr.a   = vif.mon_cb.a;
        tr.b   = vif.mon_cb.b;
        tr.tag = vif.mon_cb.tag;
        `uvm_info("MON_REQ", $sformatf("Observed input: %s", tr.convert2string()), UVM_HIGH)
        req_ap.write(tr);
      end
    end
  endtask

  virtual task collect_responses();
    forever begin
      @(vif.mon_cb);
      if (vif.mon_cb.out_valid && vif.mon_cb.out_ready) begin
        alu_item tr = alu_item::type_id::create("obs_rsp");
        tr.tag      = vif.mon_cb.out_tag;
        tr.result   = vif.mon_cb.result;
        tr.err_flag = vif.mon_cb.err_flag;
        `uvm_info("MON_RSP", $sformatf("Observed output: tag=%0d res=0x%08h err=%0b",
                  tr.tag, tr.result, tr.err_flag), UVM_HIGH)
        rsp_ap.write(tr);
      end
    end
  endtask
endclass

`endif
