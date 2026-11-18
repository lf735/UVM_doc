// -----------------------------------------------------------------------------
// alu_agent.sv - Reusable Active/Passive Protocol Agent (Chapter 4)
// -----------------------------------------------------------------------------
`ifndef ALU_AGENT_SV
`define ALU_AGENT_SV

class alu_agent extends uvm_agent;
  `uvm_component_utils(alu_agent)

  alu_agent_cfg             cfg;
  uvm_sequencer #(alu_item) seqr;
  alu_driver                drv;

  function new(string name = "alu_agent", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(alu_agent_cfg)::get(this, "", "cfg", cfg)) begin
      `uvm_fatal("AGT", "alu_agent_cfg not found in uvm_config_db")
    end

    if (cfg.is_active == UVM_ACTIVE) begin
      uvm_config_db#(alu_agent_cfg)::set(this, "drv", "cfg", cfg);
      seqr = uvm_sequencer#(alu_item)::type_id::create("seqr", this);
      drv  = alu_driver::type_id::create("drv", this);
    end
  endfunction

  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    if (cfg.is_active == UVM_ACTIVE) begin
      drv.seq_item_port.connect(seqr.seq_item_export);
    end
  endfunction
endclass

`endif
