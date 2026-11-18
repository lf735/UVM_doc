// -----------------------------------------------------------------------------
// alu_driver.sv - Minimal Pin-Level Bus Driver (Chapter 3)
// -----------------------------------------------------------------------------
`ifndef ALU_DRIVER_SV
`define ALU_DRIVER_SV

class alu_driver extends uvm_driver #(alu_item);
  `uvm_component_utils(alu_driver)

  virtual alu_if vif;

  function new(string name = "alu_driver", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual alu_if)::get(this, "", "vif", vif)) begin
      `uvm_fatal("DRV", "Virtual interface 'vif' not found in uvm_config_db")
    end
  endfunction

  virtual task run_phase(uvm_phase phase);
    alu_item req;
    vif.reset_signals();
    @(posedge vif.rst_n);
    @(vif.drv_cb);

    forever begin
      seq_item_port.get_next_item(req);
      drive_item(req);
      seq_item_port.item_done();
    end
  endtask

  virtual task drive_item(alu_item req);
    `uvm_info("DRV", $sformatf("Driving %s", req.convert2string()), UVM_MEDIUM)
    vif.drv_cb.in_valid <= 1'b1;
    vif.drv_cb.op       <= req.op;
    vif.drv_cb.a        <= req.a;
    vif.drv_cb.b        <= req.b;
    vif.drv_cb.tag      <= req.tag;

    do begin
      @(vif.drv_cb);
    end while (!vif.drv_cb.in_ready);

    vif.drv_cb.in_valid <= 1'b0;
  endtask
endclass

`endif
