// -----------------------------------------------------------------------------
// apb_reg_adapter.sv - Translating RAL Operations to/from apb_item (Ch.10)
// -----------------------------------------------------------------------------
`ifndef APB_REG_ADAPTER_SV
`define APB_REG_ADAPTER_SV

class apb_reg_adapter extends uvm_reg_adapter;
  `uvm_object_utils(apb_reg_adapter)

  function new(string name = "apb_reg_adapter");
    super.new(name);
    supports_byte_enable = 0;
    provides_responses   = 0;
  endfunction

  virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);
    apb_item tr = apb_item::type_id::create("apb_tr");
    tr.pwrite = (rw.kind == UVM_WRITE);
    tr.paddr  = rw.addr[7:0];
    tr.pwdata = rw.data[31:0];
    return tr;
  endfunction

  virtual function void bus2reg(uvm_sequence_item bus_item, ref uvm_reg_bus_op rw);
    apb_item tr;
    if (!$cast(tr, bus_item)) begin
      `uvm_fatal("ADAPT", "bus_item is not an apb_item")
    end
    rw.kind   = tr.pwrite ? UVM_WRITE : UVM_READ;
    rw.addr   = tr.paddr;
    rw.data   = tr.pwrite ? tr.pwdata : tr.prdata;
    rw.status = UVM_IS_OK;
  endfunction
endclass

`endif
