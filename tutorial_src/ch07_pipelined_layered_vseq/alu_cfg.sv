// -----------------------------------------------------------------------------
// alu_cfg.sv - Dual-Agent Environment Configuration (Chapter 7)
// -----------------------------------------------------------------------------
`ifndef ALU_CFG_SV
`define ALU_CFG_SV

class alu_agent_cfg extends uvm_object;
  uvm_active_passive_enum is_active = UVM_ACTIVE;
  virtual alu_if          vif;
  int unsigned            default_num_items = 12;

  `uvm_object_utils_begin(alu_agent_cfg)
    `uvm_field_enum(uvm_active_passive_enum, is_active, UVM_ALL_ON)
    `uvm_field_int(default_num_items, UVM_ALL_ON | UVM_DEC)
  `uvm_object_utils_end

  function new(string name = "alu_agent_cfg");
    super.new(name);
  endfunction
endclass

class alu_env_cfg extends uvm_object;
  alu_agent_cfg data_agent_cfg;
  apb_agent_cfg apb_cfg;
  bit           enable_scoreboard = 1'b1;
  bit           enable_coverage   = 1'b1;

  `uvm_object_utils_begin(alu_env_cfg)
    `uvm_field_object(data_agent_cfg, UVM_ALL_ON)
    `uvm_field_object(apb_cfg,        UVM_ALL_ON)
    `uvm_field_int(enable_scoreboard, UVM_ALL_ON)
    `uvm_field_int(enable_coverage,   UVM_ALL_ON)
  `uvm_object_utils_end

  function new(string name = "alu_env_cfg");
    super.new(name);
    data_agent_cfg = alu_agent_cfg::type_id::create("data_agent_cfg");
    apb_cfg        = apb_agent_cfg::type_id::create("apb_cfg");
  endfunction
endclass

`endif
