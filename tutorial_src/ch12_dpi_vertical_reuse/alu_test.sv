// -----------------------------------------------------------------------------
// alu_test.sv - Subsystem Test Exercising DPI-C & Vertical Reuse (Ch.12)
// -----------------------------------------------------------------------------
`ifndef ALU_TEST_SV
`define ALU_TEST_SV

class alu_base_test extends uvm_test;
  `uvm_component_utils(alu_base_test)

  soc_subsys_cfg subsys_cfg;
  soc_subsys_env subsys_env;

  function new(string name = "alu_base_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    subsys_cfg = soc_subsys_cfg::type_id::create("subsys_cfg");
    if (!uvm_config_db#(virtual alu_if)::get(this, "", "alu_vif", subsys_cfg.alu_cfg.data_agent_cfg.vif))
      `uvm_fatal("TEST", "Missing alu_vif")
    if (!uvm_config_db#(virtual apb_if)::get(this, "", "apb_vif", subsys_cfg.alu_cfg.apb_cfg.vif))
      `uvm_fatal("TEST", "Missing apb_vif")

    subsys_cfg.passive_reuse_mode = 1'b0;
    uvm_config_db#(soc_subsys_cfg)::set(this, "subsys_env", "subsys_cfg", subsys_cfg);
    subsys_env = soc_subsys_env::type_id::create("subsys_env", this);
  endfunction

  virtual task configure_phase(uvm_phase phase);
    uvm_status_e status;
    phase.raise_objection(this);
    subsys_env.block_alu_env.reg_model.SAT_LIMIT.write(status, 32'h0000_0800, UVM_FRONTDOOR);
    subsys_env.block_alu_env.reg_model.CTRL.write(status, 32'h0000_0003, UVM_FRONTDOOR);
    phase.drop_objection(this);
  endtask

  virtual task main_phase(uvm_phase phase);
    alu_virtual_seq vseq;
    phase.raise_objection(this);
    vseq = alu_virtual_seq::type_id::create("vseq");
    vseq.start(subsys_env.block_alu_env.v_seqr);
    #40ns;
    phase.drop_objection(this);
  endtask
endclass

`endif
