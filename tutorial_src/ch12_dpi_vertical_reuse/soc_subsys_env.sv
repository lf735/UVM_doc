// -----------------------------------------------------------------------------
// soc_subsys_env.sv - Vertical Block-to-Subsystem Reuse Container (Chapter 12)
// Reuses block-level alu_env unchanged inside a SoC environment by switching
// internal agents to UVM_PASSIVE while keeping Scoreboard, RAL & Coverage active.
// -----------------------------------------------------------------------------
`ifndef SOC_SUBSYS_ENV_SV
`define SOC_SUBSYS_ENV_SV

class soc_subsys_cfg extends uvm_object;
  alu_env_cfg alu_cfg;
  bit         passive_reuse_mode = 1'b0;

  `uvm_object_utils_begin(soc_subsys_cfg)
    `uvm_field_object(alu_cfg, UVM_ALL_ON)
    `uvm_field_int(passive_reuse_mode, UVM_ALL_ON)
  `uvm_object_utils_end

  function new(string name = "soc_subsys_cfg");
    super.new(name);
    alu_cfg = alu_env_cfg::type_id::create("alu_cfg");
  endfunction
endclass

class soc_subsys_env extends uvm_env;
  `uvm_component_utils(soc_subsys_env)

  soc_subsys_cfg cfg;
  alu_env        block_alu_env;

  function new(string name = "soc_subsys_env", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(soc_subsys_cfg)::get(this, "", "subsys_cfg", cfg))
      `uvm_fatal("SUBSYS", "soc_subsys_cfg not found")

    if (cfg.passive_reuse_mode) begin
      // Vertical SoC reuse: disable active block drivers, retain passive monitors + checkers
      cfg.alu_cfg.data_agent_cfg.is_active = UVM_PASSIVE;
      cfg.alu_cfg.apb_cfg.is_active        = UVM_PASSIVE;
      `uvm_info("SUBSYS", "Vertical Reuse: block_alu_env configured as UVM_PASSIVE", UVM_LOW)
    end

    uvm_config_db#(alu_env_cfg)::set(this, "block_alu_env", "env_cfg", cfg.alu_cfg);
    block_alu_env = alu_env::type_id::create("block_alu_env", this);
  endfunction
endclass

`endif
