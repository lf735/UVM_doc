// -----------------------------------------------------------------------------
// alu_agent.sv - Agent Instantiating Monitor Always + Active Driver/Seqr (Ch.5)
// -----------------------------------------------------------------------------
`ifndef ALU_AGENT_SV
`define ALU_AGENT_SV

class alu_agent extends uvm_agent;
  `uvm_component_utils(alu_agent)

  alu_agent_cfg             cfg;
  uvm_sequencer #(alu_item) seqr;
  alu_driver                drv;
  alu_monitor               mon;

  uvm_analysis_port #(alu_item) req_ap;
  uvm_analysis_port #(alu_item) rsp_ap;

  function new(string name = "alu_agent", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    req_ap = new("req_ap", this);
    rsp_ap = new("rsp_ap", this);

    if (!uvm_config_db#(alu_agent_cfg)::get(this, "", "cfg", cfg)) begin
      `uvm_fatal("AGT", "alu_agent_cfg not found in uvm_config_db")
    end

    uvm_config_db#(alu_agent_cfg)::set(this, "mon", "cfg", cfg);
    mon = alu_monitor::type_id::create("mon", this);

    if (cfg.is_active == UVM_ACTIVE) begin
      uvm_config_db#(alu_agent_cfg)::set(this, "drv", "cfg", cfg);
      seqr = uvm_sequencer#(alu_item)::type_id::create("seqr", this);
      drv  = alu_driver::type_id::create("drv", this);
    end
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    mon.req_ap.connect(req_ap);
    mon.rsp_ap.connect(rsp_ap);
    if (cfg.is_active == UVM_ACTIVE) begin
      drv.seq_item_port.connect(seqr.seq_item_export);
    end
  endfunction
endclass

`endif
