// -----------------------------------------------------------------------------
// alu_driver.sv - Driver Instrumented with `uvm_do_callbacks (Chapter 8)
// -----------------------------------------------------------------------------
`ifndef ALU_DRIVER_SV
`define ALU_DRIVER_SV

class alu_driver extends uvm_driver #(alu_item);
  `uvm_component_utils(alu_driver)
  `uvm_register_cb(alu_driver, alu_driver_cb)

  alu_agent_cfg  cfg;
  virtual alu_if vif;

  function new(string name = "alu_driver", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(alu_agent_cfg)::get(this, "", "cfg", cfg)) begin
      `uvm_fatal("DRV", "Configuration object 'cfg' not found in uvm_config_db")
    end
    vif = cfg.vif;
  endfunction

  virtual task run_phase(uvm_phase phase);
    vif.reset_signals();
    @(posedge vif.rst_n);
    @(vif.drv_cb);

    forever begin
      alu_item req;
      seq_item_port.get(req);
      `uvm_do_callbacks(alu_driver, alu_driver_cb, pre_drive(this, req))
      drive_and_respond(req);
    end
  endtask

  virtual task drive_and_respond(alu_item req);
    alu_item rsp;
    vif.drv_cb.in_valid <= 1'b1;
    vif.drv_cb.op       <= req.op;
    vif.drv_cb.a        <= req.a;
    vif.drv_cb.b        <= req.b;
    vif.drv_cb.tag      <= req.tag;

    do @(vif.drv_cb); while (!vif.drv_cb.in_ready);
    vif.drv_cb.in_valid <= 1'b0;

    do @(vif.drv_cb); while (!vif.drv_cb.out_valid);
    rsp = alu_item::type_id::create("rsp");
    rsp.set_id_info(req);
    rsp.op       = req.op;
    rsp.a        = req.a;
    rsp.b        = req.b;
    rsp.tag      = vif.drv_cb.out_tag;
    rsp.result   = vif.drv_cb.result;
    rsp.err_flag = vif.drv_cb.err_flag;
    seq_item_port.put(rsp);
  endtask
endclass

`endif
