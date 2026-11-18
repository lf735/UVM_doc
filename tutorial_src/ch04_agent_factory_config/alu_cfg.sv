// -----------------------------------------------------------------------------
// alu_cfg.sv - Hierarchical Configuration Objects (Chapter 4)
// -----------------------------------------------------------------------------
`ifndef ALU_CFG_SV
`define ALU_CFG_SV

class alu_agent_cfg extends uvm_object;
  uvm_active_passive_enum is_active = UVM_ACTIVE;
  virtual alu_if          vif;
  int unsigned            default_num_items = 6;

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
  bit           enable_factory_override_demo = 1'b0;

  `uvm_object_utils_begin(alu_env_cfg)
    `uvm_field_object(data_agent_cfg, UVM_ALL_ON)
    `uvm_field_int(enable_factory_override_demo, UVM_ALL_ON)
  `uvm_object_utils_end

  function new(string name = "alu_env_cfg");
    super.new(name);
    data_agent_cfg = alu_agent_cfg::type_id::create("data_agent_cfg");
  endfunction
endclass

`endif
