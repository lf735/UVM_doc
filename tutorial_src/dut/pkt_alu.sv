// -----------------------------------------------------------------------------
// pkt_alu.sv - Full Dual-Interface Packet-ALU + APB3 Register Slave (Ch.7 - Ch.13)
// Registers:
//   0x00 CTRL       : [0] EN, [1] SAT_EN, [2] ERR_MASK
//   0x04 STATUS     : [0] BUSY (RO), [1] LAST_ERR (W1C)
//   0x08 SAT_LIMIT  : [15:0] Saturation clamp upper threshold when SAT_EN=1
//   0x0C PKT_COUNT  : [31:0] Processed packets counter (RO)
//   0x10 ERR_INJECT : [0] FORCE_ERR (diagnostic register)
// -----------------------------------------------------------------------------
module pkt_alu (
  input  logic        clk,
  input  logic        rst_n,

  // Data Input Stream (Valid / Ready)
  input  logic        in_valid,
  output logic        in_ready,
  input  logic [2:0]  op,
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [3:0]  tag,

  // Data Output Stream (Valid / Ready)
  output logic        out_valid,
  input  logic        out_ready,
  output logic [31:0] result,
  output logic [3:0]  out_tag,
  output logic        err_flag,

  // APB3 Configuration / Status Register Interface
  input  logic        psel,
  input  logic        penable,
  input  logic        pwrite,
  input  logic [7:0]  paddr,
  input  logic [31:0] pwdata,
  output logic [31:0] prdata,
  output logic        pready
);

  localparam logic [2:0] OP_ADD    = 3'd0;
  localparam logic [2:0] OP_SUB    = 3'd1;
  localparam logic [2:0] OP_MUL    = 3'd2;
  localparam logic [2:0] OP_XOR    = 3'd3;
  localparam logic [2:0] OP_PASS_A = 3'd4;

  // Register storage (accessible via RAL backdoor HDL paths)
  logic [31:0] reg_ctrl;
  logic [31:0] reg_status;
  logic [31:0] reg_sat_limit;
  logic [31:0] reg_pkt_count;
  logic [31:0] reg_err_inject;

  wire cfg_en       = reg_ctrl[0];
  wire cfg_sat_en   = reg_ctrl[1];
  wire cfg_err_mask = reg_ctrl[2];
  wire force_err    = reg_err_inject[0];

  assign in_ready = cfg_en && (!out_valid || out_ready);
  assign pready   = 1'b1; // Zero-wait-state APB slave

  // APB3 Register Read/Write Logic
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      reg_ctrl       <= 32'h0000_0001; // EN=1 by default
      reg_status     <= 32'h0000_0000;
      reg_sat_limit  <= 32'h0000_FFFF;
      reg_pkt_count  <= 32'h0000_0000;
      reg_err_inject <= 32'h0000_0000;
    end else begin
      // Update BUSY bit
      reg_status[0] <= out_valid;

      if (psel && penable && pwrite) begin
        case (paddr)
          8'h00: reg_ctrl       <= pwdata & 32'h0000_0007;
          8'h04: reg_status[1]  <= reg_status[1] & ~pwdata[1]; // W1C LAST_ERR
          8'h08: reg_sat_limit  <= pwdata & 32'h0000_FFFF;
          8'h10: reg_err_inject <= pwdata & 32'h0000_0001;
          default: ;
        endcase
      end

      if (in_valid && in_ready) begin
        reg_pkt_count <= reg_pkt_count + 32'd1;
        if (force_err || (op > OP_PASS_A)) begin
          reg_status[1] <= 1'b1;
        end
      end
    end
  end

  // Combinational APB read mux
  always_comb begin
    prdata = 32'h0000_0000;
    if (psel && !pwrite) begin
      case (paddr)
        8'h00: prdata = reg_ctrl;
        8'h04: prdata = reg_status;
        8'h08: prdata = reg_sat_limit;
        8'h0C: prdata = reg_pkt_count;
        8'h10: prdata = reg_err_inject;
        default: prdata = 32'h0000_0000;
      endcase
    end
  end

  // Packet-ALU Datapath with Saturation
  logic [31:0] raw_res;
  logic        raw_err;

  always_comb begin
    raw_err = force_err;
    case (op)
      OP_ADD:    raw_res = {16'd0, a} + {16'd0, b};
      OP_SUB:    raw_res = {16'd0, a} - {16'd0, b};
      OP_MUL:    raw_res = a * b;
      OP_XOR:    raw_res = {16'd0, (a ^ b)};
      OP_PASS_A: raw_res = {16'd0, a};
      default: begin
        raw_res = 32'hDEAD_BEEF;
        raw_err = 1'b1;
      end
    endcase

    if (!raw_err && cfg_sat_en && (raw_res > {16'd0, reg_sat_limit[15:0]})) begin
      raw_res = {16'd0, reg_sat_limit[15:0]};
    end
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_valid <= 1'b0;
      result    <= 32'd0;
      out_tag   <= 4'd0;
      err_flag  <= 1'b0;
    end else begin
      if (in_valid && in_ready) begin
        out_valid <= 1'b1;
        out_tag   <= tag;
        result    <= raw_res;
        err_flag  <= raw_err & ~cfg_err_mask;
      end else if (out_valid && out_ready) begin
        out_valid <= 1'b0;
      end
    end
  end

endmodule
