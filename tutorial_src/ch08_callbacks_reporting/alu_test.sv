// -----------------------------------------------------------------------------
// alu_test.sv - Cmdline Processor, Callback & Report Catcher Test (Ch.8)
// -----------------------------------------------------------------------------
`ifndef ALU_TEST_SV
`define ALU_TEST_SV

class alu_base_test extends uvm_test;
  `uvm_component_utils(alu_base_test)

  alu_env_cfg        env_cfg;
  alu_env            env;
  alu_err_inject_cb  err_cb;
  alu_report_catcher rpt_catcher;

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

  virtual function void start_of_simulation_phase(uvm_phase phase);
    uvm_cmdline_processor clp = uvm_cmdline_processor::get_inst();
    string inj_arg;
    super.start_of_simulation_phase(phase);

    // Attach fault-injection callback and report catcher when +INJECT_ERR=1
    if (clp.get_arg_value("+INJECT_ERR=", inj_arg) && inj_arg == "1") begin
      err_cb      = alu_err_inject_cb::type_id::create("err_cb");
      rpt_catcher = alu_report_catcher::type_id::create("rpt_catcher");
      uvm_callbacks#(alu_driver, alu_driver_cb)::add(env.data_agent.drv, err_cb);
      uvm_report_cb::add(null, rpt_catcher);
      `uvm_info("TEST", "Registered alu_err_inject_cb + alu_report_catcher via +INJECT_ERR=1", UVM_LOW)
    end
  endfunction

  virtual task run_phase(uvm_phase phase);
    alu_virtual_seq vseq;
    phase.raise_objection(this);
    vseq = alu_virtual_seq::type_id::create("vseq");
    vseq.start(env.v_seqr);
    #40ns;
    phase.drop_objection(this);
  endtask
endclass

`endif
