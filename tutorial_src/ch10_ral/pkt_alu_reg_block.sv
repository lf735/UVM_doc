// -----------------------------------------------------------------------------
// pkt_alu_reg_block.sv - UVM Register Abstraction Layer (RAL) Model (Ch.10)
// -----------------------------------------------------------------------------
`ifndef PKT_ALU_REG_BLOCK_SV
`define PKT_ALU_REG_BLOCK_SV

class ctrl_reg extends uvm_reg;
  `uvm_object_utils(ctrl_reg)
  rand uvm_reg_field en;
  rand uvm_reg_field sat_en;
  rand uvm_reg_field err_mask;

  function new(string name = "ctrl_reg");
    super.new(name, 32, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    en       = uvm_reg_field::type_id::create("en");
    sat_en   = uvm_reg_field::type_id::create("sat_en");
    err_mask = uvm_reg_field::type_id::create("err_mask");
    en.configure      (this, 1, 0, "RW", 0, 1'b1, 1, 1, 0);
    sat_en.configure  (this, 1, 1, "RW", 0, 1'b0, 1, 1, 0);
    err_mask.configure(this, 1, 2, "RW", 0, 1'b0, 1, 1, 0);
  endfunction
endclass

class status_reg extends uvm_reg;
  `uvm_object_utils(status_reg)
  uvm_reg_field busy;
  uvm_reg_field last_err;

  function new(string name = "status_reg");
    super.new(name, 32, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    busy     = uvm_reg_field::type_id::create("busy");
    last_err = uvm_reg_field::type_id::create("last_err");
    busy.configure    (this, 1, 0, "RO",  1, 1'b0, 1, 0, 0);
    last_err.configure(this, 1, 1, "W1C", 1, 1'b0, 1, 1, 0);
  endfunction
endclass

class sat_limit_reg extends uvm_reg;
  `uvm_object_utils(sat_limit_reg)
  rand uvm_reg_field limit;

  function new(string name = "sat_limit_reg");
    super.new(name, 32, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    limit = uvm_reg_field::type_id::create("limit");
    limit.configure(this, 16, 0, "RW", 0, 16'hFFFF, 1, 1, 0);
  endfunction
endclass

class pkt_count_reg extends uvm_reg;
  `uvm_object_utils(pkt_count_reg)
  uvm_reg_field count;

  function new(string name = "pkt_count_reg");
    super.new(name, 32, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    count = uvm_reg_field::type_id::create("count");
    count.configure(this, 32, 0, "RO", 1, 32'h0, 1, 0, 0);
  endfunction
endclass

class pkt_alu_reg_block extends uvm_reg_block;
  `uvm_object_utils(pkt_alu_reg_block)

  rand ctrl_reg      CTRL;
       status_reg    STATUS;
  rand sat_limit_reg SAT_LIMIT;
       pkt_count_reg PKT_COUNT;
       uvm_reg_map   apb_map;

  function new(string name = "pkt_alu_reg_block");
    super.new(name, UVM_NO_COVERAGE);
  endfunction

  virtual function void build();
    CTRL      = ctrl_reg::type_id::create("CTRL");
    STATUS    = status_reg::type_id::create("STATUS");
    SAT_LIMIT = sat_limit_reg::type_id::create("SAT_LIMIT");
    PKT_COUNT = pkt_count_reg::type_id::create("PKT_COUNT");

    CTRL.configure(this, null, "reg_ctrl");          CTRL.build();
    STATUS.configure(this, null, "reg_status");      STATUS.build();
    SAT_LIMIT.configure(this, null, "reg_sat_limit"); SAT_LIMIT.build();
    PKT_COUNT.configure(this, null, "reg_pkt_count"); PKT_COUNT.build();

    apb_map = create_map("apb_map", 'h0, 4, UVM_LITTLE_ENDIAN);
    apb_map.add_reg(CTRL,      'h00, "RW");
    apb_map.add_reg(STATUS,    'h04, "RW");
    apb_map.add_reg(SAT_LIMIT, 'h08, "RW");
    apb_map.add_reg(PKT_COUNT, 'h0C, "RO");

    add_hdl_path("tb_top.u_dut");
    lock_model();
  endfunction
endclass

`endif
