// -----------------------------------------------------------------------------
// pkt_alu_basic.sv - Minimal Valid/Ready Packet-ALU DUT (Chapters 3 to 6)
// Simple streaming handshake on input and output with 1-cycle registered latency.
// -----------------------------------------------------------------------------
module pkt_alu_basic (
  input  logic        clk,
  input  logic        rst_n,

  // Input stream (Valid / Ready handshake)
  input  logic        in_valid,
  output logic        in_ready,
  input  logic [2:0]  op,        // 0:ADD, 1:SUB, 2:MUL, 3:XOR, 4:PASS_A, >=5:INVALID
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [3:0]  tag,

  // Output stream (Valid / Ready handshake)
  output logic        out_valid,
  input  logic        out_ready,
  output logic [31:0] result,
  output logic [3:0]  out_tag,
  output logic        err_flag
);

  localparam logic [2:0] OP_ADD    = 3'd0;
  localparam logic [2:0] OP_SUB    = 3'd1;
  localparam logic [2:0] OP_MUL    = 3'd2;
  localparam logic [2:0] OP_XOR    = 3'd3;
  localparam logic [2:0] OP_PASS_A = 3'd4;

  // Accept input whenever output stage is empty or currently being consumed
  assign in_ready = !out_valid || out_ready;

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
        err_flag  <= 1'b0;
        case (op)
          OP_ADD:    result <= {16'd0, a} + {16'd0, b};
          OP_SUB:    result <= {16'd0, a} - {16'd0, b};
          OP_MUL:    result <= a * b;
          OP_XOR:    result <= {16'd0, (a ^ b)};
          OP_PASS_A: result <= {16'd0, a};
          default: begin
            result   <= 32'hDEAD_BEEF;
            err_flag <= 1'b1;
          end
        endcase
      end else if (out_valid && out_ready) begin
        out_valid <= 1'b0;
      end
    end
  end

endmodule
