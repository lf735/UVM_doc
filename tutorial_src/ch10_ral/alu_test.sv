// -----------------------------------------------------------------------------
// alu_test.sv - RAL Built-In Sequences, Frontdoor & Backdoor Test (Ch.10)
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
    if (!uvm_config_db#(virtual alu_if)::get(this, "", "alu_vif", env_cfg.data_agent_cfg.vif))
      `uvm_fatal("TEST", "Missing alu_vif")
    if (!uvm_config_db#(virtual apb_if)::get(this, "", "apb_vif", env_cfg.apb_cfg.vif))
      `uvm_fatal("TEST", "Missing apb_vif")

    uvm_config_db#(alu_env_cfg)::set(this, "env", "env_cfg", env_cfg);
    env = alu_env::type_id::create("env", this);
  endfunction

  virtual task configure_phase(uvm_phase phase);
    uvm_status_e           status;
    uvm_reg_data_t         rdata;
    uvm_reg_hw_reset_seq   hw_rst_seq;
    phase.raise_objection(this);

    // 1. Run built-in reset check sequence across all registers
    hw_rst_seq = uvm_reg_hw_reset_seq::type_id::create("hw_rst_seq");
    hw_rst_seq.model = env.reg_model;
    hw_rst_seq.start(null);

    // 2. Frontdoor write enabling saturation clamp
    env.reg_model.SAT_LIMIT.write(status, 32'h0000_0800, UVM_FRONTDOOR);
    env.reg_model.CTRL.write(status, 32'h0000_0003, UVM_FRONTDOOR); // EN=1, SAT_EN=1

    // 3. Backdoor zero-time peek verification
    env.reg_model.SAT_LIMIT.peek(status, rdata);
    `uvm_info("RAL", $sformatf("Backdoor peek SAT_LIMIT = 0x%04h (mirrored=0x%04h)",
              rdata, env.reg_model.SAT_LIMIT.get_mirrored_value()), UVM_LOW)
    phase.drop_objection(this);
  endtask

  virtual task main_phase(uvm_phase phase);
    alu_smoke_seq seq;
    uvm_status_e  status;
    uvm_reg_data_t pkt_cnt;
    phase.raise_objection(this);
    seq = alu_smoke_seq::type_id::create("seq");
    seq.start(env.data_agent.seqr);
    #30ns;
    env.reg_model.PKT_COUNT.read(status, pkt_cnt, UVM_FRONTDOOR);
    `uvm_info("RAL", $sformatf("Frontdoor PKT_COUNT = %0d", pkt_cnt), UVM_LOW)
    phase.drop_objection(this);
  endtask
endclass

`endif
