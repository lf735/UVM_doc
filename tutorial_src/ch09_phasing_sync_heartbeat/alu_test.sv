// -----------------------------------------------------------------------------
// alu_test.sv - Sub-Phases (Reset/Configure/Main/Shutdown) & Heartbeat (Ch.9)
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

  virtual task reset_phase(uvm_phase phase);
    phase.raise_objection(this);
    `uvm_info("PHASE", "Executing reset_phase: waiting for DUT reset release", UVM_LOW)
    @(posedge env_cfg.data_agent_cfg.vif.rst_n);
    phase.drop_objection(this);
  endtask

  virtual task configure_phase(uvm_phase phase);
    apb_write_seq sat_seq;
    phase.raise_objection(this);
    `uvm_info("PHASE", "Executing configure_phase: programming SAT_LIMIT=0x1000", UVM_LOW)
    sat_seq = apb_write_seq::type_id::create("sat_seq");
    sat_seq.addr = 8'h08;
    sat_seq.data = 32'h0000_1000;
    sat_seq.start(env.apb_agt.seqr);
    phase.drop_objection(this);
  endtask

  virtual task main_phase(uvm_phase phase);
    alu_virtual_seq vseq;
    phase.raise_objection(this);
    phase.phase_done.set_drain_time(this, 20ns);

    // Start heartbeat watchdog during main traffic window
    env.hb.start(env.hb_trig);
    fork
      begin : hb_kick
        forever begin
          #25ns;
          env.hb_obj.raise_objection(env.data_agent.drv);
          env.hb_trig.trigger();
          env.hb_obj.drop_objection(env.data_agent.drv);
        end
      end
    join_none

    vseq = alu_virtual_seq::type_id::create("vseq");
    vseq.start(env.v_seqr);
    env.hb.stop();
    disable hb_kick;
    phase.drop_objection(this);
  endtask

  virtual task shutdown_phase(uvm_phase phase);
    phase.raise_objection(this);
    `uvm_info("PHASE", "Executing shutdown_phase: draining final pipeline responses", UVM_LOW)
    #20ns;
    phase.drop_objection(this);
  endtask
endclass

`endif
