// -----------------------------------------------------------------------------
// alu_env.sv - Verification Environment Container (Chapter 4)
// -----------------------------------------------------------------------------
`ifndef ALU_ENV_SV
`define ALU_ENV_SV

class alu_env extends uvm_env;
  `uvm_component_utils(alu_env)

  alu_env_cfg cfg;
  alu_agent   data_agent;

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
  endfunction
endclass

`endif
