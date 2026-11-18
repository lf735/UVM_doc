// -----------------------------------------------------------------------------
// alu_env.sv - Dual-Agent Env with Virtual Sequencer Wiring (Chapter 7)
// -----------------------------------------------------------------------------
`ifndef ALU_ENV_SV
`define ALU_ENV_SV

class alu_env extends uvm_env;
  `uvm_component_utils(alu_env)

  alu_env_cfg           cfg;
  alu_agent             data_agent;
  apb_agent             apb_agt;
  alu_virtual_sequencer v_seqr;
  alu_scoreboard        scb;
  alu_cov_subscriber    cov;

  function new(string name = "alu_env", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(alu_env_cfg)::get(this, "", "env_cfg", cfg)) begin
      `uvm_fatal("ENV", "alu_env_cfg not found in uvm_config_db")
    end

    uvm_config_db#(alu_agent_cfg)::set(this, "data_agent", "cfg", cfg.data_agent_cfg);
    uvm_config_db#(apb_agent_cfg)::set(this, "apb_agt",    "cfg", cfg.apb_cfg);

    data_agent = alu_agent::type_id::create("data_agent", this);
    apb_agt    = apb_agent::type_id::create("apb_agt", this);
    v_seqr     = alu_virtual_sequencer::type_id::create("v_seqr", this);

    if (cfg.enable_scoreboard) scb = alu_scoreboard::type_id::create("scb", this);
    if (cfg.enable_coverage)   cov = alu_cov_subscriber::type_id::create("cov", this);
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    // Bind sub-sequencer handles onto the virtual sequencer
    if (data_agent.seqr != null) v_seqr.alu_sqr = data_agent.seqr;
    if (apb_agt.seqr    != null) v_seqr.apb_sqr = apb_agt.seqr;

    if (cfg.enable_scoreboard) begin
      data_agent.req_ap.connect(scb.req_export);
      data_agent.rsp_ap.connect(scb.rsp_export);
    end
    if (cfg.enable_coverage) begin
      data_agent.req_ap.connect(cov.analysis_export);
    end
  endfunction
endclass

`endif
