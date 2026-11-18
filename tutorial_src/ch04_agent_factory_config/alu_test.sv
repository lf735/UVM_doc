// -----------------------------------------------------------------------------
// alu_test.sv - Base Test & Factory Override Test (Chapter 4)
// -----------------------------------------------------------------------------
`ifndef ALU_TEST_SV
`define ALU_TEST_SV

class alu_base_test extends uvm_test;
  `uvm_component_utils(alu_base_test)

  alu_env_cfg env_cfg;
  alu_env     env;

  function new(string name = "alu_base_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env_cfg = alu_env_cfg::type_id::create("env_cfg");
    if (!uvm_config_db#(virtual alu_if)::get(this, "", "alu_vif", env_cfg.data_agent_cfg.vif)) begin
      `uvm_fatal("TEST", "Missing alu_vif in uvm_config_db")
    end
    env_cfg.data_agent_cfg.is_active = UVM_ACTIVE;
    uvm_config_db#(alu_env_cfg)::set(this, "env", "env_cfg", env_cfg);
    env = alu_env::type_id::create("env", this);
  endfunction

  virtual function void end_of_elaboration_phase(uvm_phase phase);
    super.end_of_elaboration_phase(phase);
    uvm_top.print_topology();
  endfunction

  virtual task run_phase(uvm_phase phase);
    alu_smoke_seq seq;
    phase.raise_objection(this);
    seq = alu_smoke_seq::type_id::create("seq");
    seq.num_items = env_cfg.data_agent_cfg.default_num_items;
    seq.start(env.data_agent.seqr);
    #40ns;
    phase.drop_objection(this);
  endtask
endclass

class alu_mul_factory_test extends alu_base_test;
  `uvm_component_utils(alu_mul_factory_test)

  function new(string name = "alu_mul_factory_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    // Apply global factory type override BEFORE building child hierarchy
    alu_item::type_id::set_type_override(alu_mul_only_item::get_type());
    super.build_phase(phase);
    uvm_factory::get().print();
  endfunction
endclass

`endif
