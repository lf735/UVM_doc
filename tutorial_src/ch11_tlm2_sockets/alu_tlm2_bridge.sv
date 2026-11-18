// -----------------------------------------------------------------------------
// alu_tlm2_bridge.sv - TLM-1 to TLM-2.0 Initiator Socket Bridge (Chapter 11)
// Converts alu_item transactions into uvm_tlm_generic_payload with temporal
// decoupling (uvm_tlm_time) and 4-phase non-blocking transport.
// -----------------------------------------------------------------------------
`ifndef ALU_TLM2_BRIDGE_SV
`define ALU_TLM2_BRIDGE_SV

class alu_tlm2_bridge extends uvm_component;
  `uvm_component_utils(alu_tlm2_bridge)

  uvm_analysis_imp #(alu_item, alu_tlm2_bridge) req_imp;
  uvm_tlm_nb_initiator_socket #(alu_tlm2_bridge) nb_init_socket;

  uvm_tlm_time local_quantum;
  uvm_event    resp_done_ev;

  function new(string name = "alu_tlm2_bridge", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    req_imp        = new("req_imp", this);
    nb_init_socket = new("nb_init_socket", this);
    local_quantum  = new("local_quantum", 1.0e-9);
    resp_done_ev   = new("resp_done_ev");
  endfunction

  // Receive alu_item from monitor and marshal into TLM-2.0 Generic Payload
  virtual function void write(alu_item t);
    uvm_tlm_generic_payload gp = new("alu_gp");
    byte unsigned           data_bytes[] = new[8];
    uvm_tlm_phase_e         ph = BEGIN_REQ;
    uvm_tlm_sync_e          sync;

    data_bytes[0] = byte'(t.op);
    data_bytes[1] = byte'(t.tag);
    data_bytes[2] = t.a[7:0];
    data_bytes[3] = t.a[15:8];
    data_bytes[4] = t.b[7:0];
    data_bytes[5] = t.b[15:8];

    gp.set_write();
    gp.set_address(64'h0000_0000_0000_1000 + t.tag);
    gp.set_data(data_bytes);
    gp.set_data_length(8);

    // Temporal decoupling quantum check
    local_quantum.incr(5.0, 1ns);
    if (local_quantum.get_realtime(1ns) >= 20.0) begin
      `uvm_info("TLM2", $sformatf("Quantum limit reached (%0t), syncing local time",
                local_quantum.get_realtime(1ns)), UVM_HIGH)
      local_quantum.reset();
    end

    sync = nb_init_socket.nb_transport_fw(gp, ph, local_quantum);
    `uvm_info("TLM2", $sformatf("FW BEGIN_REQ addr=0x%04h sync=%s",
              gp.get_address(), sync.name()), UVM_HIGH)
  endfunction

  // Backward path called by target socket upon BEGIN_RESP
  virtual function uvm_tlm_sync_e nb_transport_bw(
      uvm_tlm_generic_payload gp,
      ref uvm_tlm_phase_e phase,
      input uvm_tlm_time delay);
    if (phase == BEGIN_RESP) begin
      phase = END_RESP;
      `uvm_info("TLM2", $sformatf("BW BEGIN_RESP -> END_RESP status=%s",
                gp.get_response_string()), UVM_HIGH)
      resp_done_ev.trigger();
      return UVM_TLM_COMPLETED;
    end
    return UVM_TLM_ACCEPTED;
  endfunction
endclass

`endif
