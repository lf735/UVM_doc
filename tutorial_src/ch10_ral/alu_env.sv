// -----------------------------------------------------------------------------
// alu_env.sv - Environment Integrating RAL Block, Adapter & Predictor (Ch.10)
// -----------------------------------------------------------------------------
`ifndef ALU_ENV_SV
`define ALU_ENV_SV

class alu_env extends uvm_env;
  `uvm_component_utils(alu_env)

  alu_env_cfg                   cfg;
  alu_agent                     data_agent;
  apb_agent                     apb_agt;
  alu_virtual_sequencer         v_seqr;
  alu_scoreboard                scb;
  alu_cov_subscriber            cov;

  pkt_alu_reg_block             reg_model;
  apb_reg_adapter               reg_adapter;
  uvm_reg_predictor #(apb_item) reg_predictor;

  uvm_domain                    apb_domain;
  uvm_heartbeat                 hb;
  uvm_objection                 hb_obj;
  uvm_event                     hb_trig;

  function new(string name = "alu_env", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(alu_env_cfg)::get(this, "", "env_cfg", cfg))
      `uvm_fatal("ENV", "alu_env_cfg not found")

    uvm_config_db#(alu_agent_cfg)::set(this, "data_agent", "cfg", cfg.data_agent_cfg);
    uvm_config_db#(apb_agent_cfg)::set(this, "apb_agt",    "cfg", cfg.apb_cfg);

    data_agent    = alu_agent::type_id::create("data_agent", this);
    apb_agt       = apb_agent::type_id::create("apb_agt", this);
    v_seqr        = alu_virtual_sequencer::type_id::create("v_seqr", this);
    reg_model     = pkt_alu_reg_block::type_id::create("reg_model");
    reg_model.build();
    reg_adapter   = apb_reg_adapter::type_id::create("reg_adapter");
    reg_predictor = uvm_reg_predictor#(apb_item)::type_id::create("reg_predictor", this);

    if (cfg.enable_scoreboard) scb = alu_scoreboard::type_id::create("scb", this);
    if (cfg.enable_coverage)   cov = alu_cov_subscriber::type_id::create("cov", this);

    apb_domain = new("apb_domain");
    hb_obj     = new("hb_obj");
    hb         = new("hb", this, hb_obj);
    hb_trig    = new("hb_trig");
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    if (data_agent.seqr != null) v_seqr.alu_sqr = data_agent.seqr;
    if (apb_agt.seqr    != null) v_seqr.apb_sqr = apb_agt.seqr;

    // Bind RAL map to APB sequencer + explicit predictor
    if (apb_agt.seqr != null) begin
      reg_model.apb_map.set_sequencer(apb_agt.seqr, reg_adapter);
    end
    reg_model.apb_map.set_auto_predict(0);
    reg_predictor.map     = reg_model.apb_map;
    reg_predictor.adapter = reg_adapter;
    apb_agt.ap.connect(reg_predictor.bus_in);

    if (cfg.enable_scoreboard) begin
      scb.reg_model = reg_model;
      data_agent.req_ap.connect(scb.req_export);
      data_agent.rsp_ap.connect(scb.rsp_export);
    end
    if (cfg.enable_coverage) begin
      data_agent.req_ap.connect(cov.analysis_export);
    end
  endfunction
endclass

`endif
