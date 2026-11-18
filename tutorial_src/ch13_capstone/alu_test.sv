// -----------------------------------------------------------------------------
// alu_test.sv - Capstone Full Production UVM 1.2 Test (Chapter 13)
// Integrates: Subsystem Env + Factory + Cmdline + Callbacks + Report Catcher
//             + Sub-Phases + Heartbeat + RAL + Virtual Seq + TLM-2 + DPI-C
// -----------------------------------------------------------------------------
`ifndef ALU_TEST_SV
`define ALU_TEST_SV

class alu_capstone_full_test extends uvm_test;
  `uvm_component_utils(alu_capstone_full_test)

  soc_subsys_cfg     subsys_cfg;
  soc_subsys_env     subsys_env;
  alu_err_inject_cb  err_cb;
  alu_report_catcher rpt_catcher;

  function new(string name = "alu_capstone_full_test", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    subsys_cfg = soc_subsys_cfg::type_id::create("subsys_cfg");
    if (!uvm_config_db#(virtual alu_if)::get(this, "", "alu_vif", subsys_cfg.alu_cfg.data_agent_cfg.vif))
      `uvm_fatal("TEST", "Missing alu_vif")
    if (!uvm_config_db#(virtual apb_if)::get(this, "", "apb_vif", subsys_cfg.alu_cfg.apb_cfg.vif))
      `uvm_fatal("TEST", "Missing apb_vif")

    subsys_cfg.alu_cfg.enable_scoreboard = 1'b1;
    subsys_cfg.alu_cfg.enable_coverage   = 1'b1;
    uvm_config_db#(soc_subsys_cfg)::set(this, "subsys_env", "subsys_cfg", subsys_cfg);
    subsys_env = soc_subsys_env::type_id::create("subsys_env", this);
  endfunction

  virtual function void start_of_simulation_phase(uvm_phase phase);
    uvm_cmdline_processor clp = uvm_cmdline_processor::get_inst();
    string inj_arg;
    super.start_of_simulation_phase(phase);
    uvm_top.print_topology();

    if (clp.get_arg_value("+INJECT_ERR=", inj_arg) && inj_arg == "1") begin
      err_cb      = alu_err_inject_cb::type_id::create("err_cb");
      rpt_catcher = alu_report_catcher::type_id::create("rpt_catcher");
      uvm_callbacks#(alu_driver, alu_driver_cb)::add(subsys_env.block_alu_env.data_agent.drv, err_cb);
      uvm_report_cb::add(null, rpt_catcher);
      `uvm_info("CAPSTONE", "Enabled non-intrusive fault callback & report catcher", UVM_LOW)
    end
  endfunction

  virtual task reset_phase(uvm_phase phase);
    phase.raise_objection(this);
    @(posedge subsys_cfg.alu_cfg.data_agent_cfg.vif.rst_n);
    phase.drop_objection(this);
  endtask

  virtual task configure_phase(uvm_phase phase);
    uvm_status_e         status;
    uvm_reg_data_t       rdata;
    uvm_reg_hw_reset_seq hw_rst_seq;
    phase.raise_objection(this);

    hw_rst_seq = uvm_reg_hw_reset_seq::type_id::create("hw_rst_seq");
    hw_rst_seq.model = subsys_env.block_alu_env.reg_model;
    hw_rst_seq.start(null);

    subsys_env.block_alu_env.reg_model.SAT_LIMIT.write(status, 32'h0000_0800, UVM_FRONTDOOR);
    subsys_env.block_alu_env.reg_model.CTRL.write(status, 32'h0000_0003, UVM_FRONTDOOR);
    subsys_env.block_alu_env.reg_model.SAT_LIMIT.peek(status, rdata);
    `uvm_info("CAPSTONE", $sformatf("RAL configured & peeked SAT_LIMIT=0x%04h", rdata), UVM_LOW)
    phase.drop_objection(this);
  endtask

  virtual task main_phase(uvm_phase phase);
    alu_virtual_seq vseq;
    alu_env         b_env = subsys_env.block_alu_env;
    phase.raise_objection(this);
    phase.phase_done.set_drain_time(this, 25ns);

    b_env.hb.start(b_env.hb_trig);
    fork
      begin : hb_watch
        forever begin
          #25ns;
          b_env.hb_obj.raise_objection(b_env.data_agent.drv);
          b_env.hb_trig.trigger();
          b_env.hb_obj.drop_objection(b_env.data_agent.drv);
        end
      end
    join_none

    vseq = alu_virtual_seq::type_id::create("vseq");
    vseq.start(b_env.v_seqr);
    b_env.hb.stop();
    disable hb_watch;
    phase.drop_objection(this);
  endtask

  virtual task shutdown_phase(uvm_phase phase);
    uvm_status_e   status;
    uvm_reg_data_t pkt_cnt;
    phase.raise_objection(this);
    #25ns;
    subsys_env.block_alu_env.reg_model.PKT_COUNT.read(status, pkt_cnt, UVM_FRONTDOOR);
    `uvm_info("CAPSTONE", $sformatf("Final PKT_COUNT readback = %0d", pkt_cnt), UVM_LOW)
    phase.drop_objection(this);
  endtask
endclass

`endif
