// -----------------------------------------------------------------------------
// alu_ref_model.sv - Reference Model Exposing TLM-2.0 Target Socket (Ch.11)
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

  virtual function alu_item predict(alu_item req);
    alu_item exp = alu_item::type_id::create("exp_item");
    exp.copy(req);
    exp.err_flag = 1'b0;

    case (req.op)
      ALU_ADD:    exp.result = {16'd0, req.a} + {16'd0, req.b};
      ALU_SUB:    exp.result = {16'd0, req.a} - {16'd0, req.b};
      ALU_MUL:    exp.result = req.a * req.b;
      ALU_XOR:    exp.result = {16'd0, (req.a ^ req.b)};
      ALU_PASS_A: exp.result = {16'd0, req.a};
      default: begin
        exp.result   = 32'hDEAD_BEEF;
        exp.err_flag = 1'b1;
      end
    endcase
    return exp;
  endfunction

  // TLM-2.0 Non-Blocking Forward Transport Target Implementation
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
