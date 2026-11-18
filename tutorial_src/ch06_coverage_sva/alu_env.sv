// -----------------------------------------------------------------------------
// alu_env.sv - Environment Connecting Monitor to Scoreboard & Coverage (Ch.6)
// -----------------------------------------------------------------------------
`ifndef ALU_ENV_SV
`define ALU_ENV_SV

class alu_env extends uvm_env;
  `uvm_component_utils(alu_env)

  alu_env_cfg        cfg;
  alu_agent          data_agent;
  alu_scoreboard     scb;
  alu_cov_subscriber cov;

  function new(string name = "alu_env", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(alu_env_cfg)::get(this, "", "env_cfg", cfg)) begin
      `uvm_fatal("ENV", "alu_env_cfg not found in uvm_config_db")
    end

    uvm_config_db#(alu_agent_cfg)::set(this, "data_agent", "cfg", cfg.data_agent_cfg);
    data_agent = alu_agent::type_id::create("data_agent", this);

    if (cfg.enable_scoreboard) begin
      scb = alu_scoreboard::type_id::create("scb", this);
    end
    if (cfg.enable_coverage) begin
      cov = alu_cov_subscriber::type_id::create("cov", this);
    end
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
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
