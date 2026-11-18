// -----------------------------------------------------------------------------
// apb_agent_pkg.sv - Reusable APB3 Master Agent Components (Chapter 7)
// -----------------------------------------------------------------------------
`ifndef APB_AGENT_PKG_SV
`define APB_AGENT_PKG_SV

class apb_item extends uvm_sequence_item;
  rand bit          pwrite;
  rand logic [7:0]  paddr;
  rand logic [31:0] pwdata;
  logic [31:0]      prdata;

  `uvm_object_utils_begin(apb_item)
    `uvm_field_int(pwrite, UVM_ALL_ON)
    `uvm_field_int(paddr,  UVM_ALL_ON | UVM_HEX)
    `uvm_field_int(pwdata, UVM_ALL_ON | UVM_HEX)
    `uvm_field_int(prdata, UVM_ALL_ON | UVM_HEX)
  `uvm_object_utils_end

  function new(string name = "apb_item");
    super.new(name);
  endfunction

  virtual function string convert2string();
    return $sformatf("%s addr=0x%02h wdata=0x%08h rdata=0x%08h",
                     pwrite ? "WR" : "RD", paddr, pwdata, prdata);
  endfunction
endclass

class apb_agent_cfg extends uvm_object;
  uvm_active_passive_enum is_active = UVM_ACTIVE;
  virtual apb_if          vif;
  `uvm_object_utils(apb_agent_cfg)
  function new(string name = "apb_agent_cfg");
    super.new(name);
  endfunction
endclass

class apb_driver extends uvm_driver #(apb_item);
  `uvm_component_utils(apb_driver)
  apb_agent_cfg  cfg;
  virtual apb_if vif;

  function new(string name = "apb_driver", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(apb_agent_cfg)::get(this, "", "cfg", cfg))
      `uvm_fatal("APB_DRV", "Missing apb_agent_cfg")
    vif = cfg.vif;
  endfunction

  virtual task run_phase(uvm_phase phase);
    apb_item req;
    vif.reset_signals();
    @(posedge vif.rst_n);
    @(vif.drv_cb);
    forever begin
      seq_item_port.get_next_item(req);
      // SETUP phase
      vif.drv_cb.psel    <= 1'b1;
      vif.drv_cb.penable <= 1'b0;
      vif.drv_cb.pwrite  <= req.pwrite;
      vif.drv_cb.paddr   <= req.paddr;
      vif.drv_cb.pwdata  <= req.pwdata;
      @(vif.drv_cb);
      // ACCESS phase
      vif.drv_cb.penable <= 1'b1;
      do @(vif.drv_cb); while (!vif.drv_cb.pready);
      if (!req.pwrite) req.prdata = vif.drv_cb.prdata;
      vif.drv_cb.psel    <= 1'b0;
      vif.drv_cb.penable <= 1'b0;
      seq_item_port.item_done();
    end
  endtask
endclass

class apb_monitor extends uvm_monitor;
  `uvm_component_utils(apb_monitor)
  apb_agent_cfg              cfg;
  virtual apb_if             vif;
  uvm_analysis_port #(apb_item) ap;

  function new(string name = "apb_monitor", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    ap = new("ap", this);
    if (!uvm_config_db#(apb_agent_cfg)::get(this, "", "cfg", cfg))
      `uvm_fatal("APB_MON", "Missing apb_agent_cfg")
    vif = cfg.vif;
  endfunction

  virtual task run_phase(uvm_phase phase);
    @(posedge vif.rst_n);
    forever begin
      @(vif.mon_cb);
      if (vif.mon_cb.psel && vif.mon_cb.penable && vif.mon_cb.pready) begin
        apb_item tr = apb_item::type_id::create("apb_tr");
        tr.pwrite = vif.mon_cb.pwrite;
        tr.paddr  = vif.mon_cb.paddr;
        tr.pwdata = vif.mon_cb.pwdata;
        tr.prdata = vif.mon_cb.prdata;
        ap.write(tr);
      end
    end
  endtask
endclass

class apb_agent extends uvm_agent;
  `uvm_component_utils(apb_agent)
  apb_agent_cfg             cfg;
  uvm_sequencer #(apb_item) seqr;
  apb_driver                drv;
  apb_monitor               mon;
  uvm_analysis_port #(apb_item) ap;

  function new(string name = "apb_agent", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    ap = new("ap", this);
    if (!uvm_config_db#(apb_agent_cfg)::get(this, "", "cfg", cfg))
      `uvm_fatal("APB_AGT", "Missing apb_agent_cfg")
    uvm_config_db#(apb_agent_cfg)::set(this, "mon", "cfg", cfg);
    mon = apb_monitor::type_id::create("mon", this);
    if (cfg.is_active == UVM_ACTIVE) begin
      uvm_config_db#(apb_agent_cfg)::set(this, "drv", "cfg", cfg);
      seqr = uvm_sequencer#(apb_item)::type_id::create("seqr", this);
      drv  = apb_driver::type_id::create("drv", this);
    end
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    mon.ap.connect(ap);
    if (cfg.is_active == UVM_ACTIVE) drv.seq_item_port.connect(seqr.seq_item_export);
  endfunction
endclass

class apb_write_seq extends uvm_sequence #(apb_item);
  `uvm_object_utils(apb_write_seq)
  rand logic [7:0]  addr;
  rand logic [31:0] data;
  function new(string name = "apb_write_seq");
    super.new(name);
  endfunction
  virtual task body();
    apb_item req = apb_item::type_id::create("apb_req");
    start_item(req);
    req.pwrite = 1'b1;
    req.paddr  = addr;
    req.pwdata = data;
    finish_item(req);
  endtask
endclass

`endif
