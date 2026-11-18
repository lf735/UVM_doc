// -----------------------------------------------------------------------------
// alu_ref_model.sv - Reference Model Delegating to C via DPI-C (Chapter 12)
// -----------------------------------------------------------------------------
`ifndef ALU_REF_MODEL_SV
`define ALU_REF_MODEL_SV

class alu_ref_model extends uvm_component;
  `uvm_component_utils(alu_ref_model)

  uvm_tlm_nb_target_socket #(alu_ref_model) nb_target_socket;
  uvm_analysis_port #(alu_item)             tlm2_exp_ap;

  function new(string name = "alu_ref_model", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    nb_target_socket = new("nb_target_socket", this);
    tlm2_exp_ap      = new("tlm2_exp_ap", this);
  endfunction

  virtual function alu_item predict_with_cfg(
      alu_item req,
      bit sat_en = 1'b0,
      logic [15:0] sat_limit = 16'hFFFF,
      bit err_mask = 1'b0);
    alu_item exp = alu_item::type_id::create("exp_item");
    int unsigned c_res, c_err;
    exp.copy(req);

    // Call C reference model directly across SystemVerilog DPI-C boundary
    pkt_alu_dpi_calc(
      int'(req.op),
      int'(req.a),
      int'(req.b),
      int'(sat_en),
      int'(sat_limit),
      int'(err_mask),
      0,
      c_res,
      c_err
    );
    exp.result   = c_res;
    exp.err_flag = c_err[0];
    return exp;
  endfunction

  virtual function alu_item predict(alu_item req);
    return predict_with_cfg(req, 1'b0, 16'hFFFF, 1'b0);
  endfunction

  virtual function uvm_tlm_sync_e nb_transport_fw(
      uvm_tlm_generic_payload gp,
      ref uvm_tlm_phase_e phase,
      input uvm_tlm_time delay);
    if (phase == BEGIN_REQ) begin
      byte unsigned payload[];
      alu_item tr = alu_item::type_id::create("tlm2_req");
      alu_item exp;
      uvm_tlm_phase_e bw_ph = BEGIN_RESP;

      gp.get_data(payload);
      tr.op  = alu_op_e'(payload[0][2:0]);
      tr.tag = payload[1][3:0];
      tr.a   = {payload[3], payload[2]};
      tr.b   = {payload[5], payload[4]};

      exp = predict(tr);
      tlm2_exp_ap.write(exp);
      gp.set_response_status(UVM_TLM_OK_RESPONSE);
      void'(nb_target_socket.nb_transport_bw(gp, bw_ph, delay));
      return UVM_TLM_UPDATED;
    end
    return UVM_TLM_COMPLETED;
  endfunction
endclass

`endif
