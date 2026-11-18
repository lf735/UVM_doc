// -----------------------------------------------------------------------------
// alu_virtual_sequencer.sv - Virtual Sequencer Coordinating Sub-Agents (Ch.7)
// -----------------------------------------------------------------------------
`ifndef ALU_VIRTUAL_SEQUENCER_SV
`define ALU_VIRTUAL_SEQUENCER_SV

class alu_virtual_sequencer extends uvm_sequencer;
  `uvm_component_utils(alu_virtual_sequencer)

  uvm_sequencer #(alu_item) alu_sqr;
  uvm_sequencer #(apb_item) apb_sqr;

  function new(string name = "alu_virtual_sequencer", uvm_component parent = null);
    super.new(name, parent);
  endfunction
endclass

`endif
