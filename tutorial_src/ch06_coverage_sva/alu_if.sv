// -----------------------------------------------------------------------------
// alu_if.sv - Virtual Interface with SVA Protocol Assertions (Chapter 6)
// -----------------------------------------------------------------------------
interface alu_if (input logic clk, input logic rst_n);
  logic        in_valid;
  logic        in_ready;
  logic [2:0]  op;
  logic [15:0] a;
  logic [15:0] b;
  logic [3:0]  tag;

  logic        out_valid;
  logic        out_ready;
  logic [31:0] result;
  logic [3:0]  out_tag;
  logic        err_flag;

  clocking drv_cb @(posedge clk);
    default input #1step output #1;
    output in_valid, op, a, b, tag, out_ready;
    input  in_ready, out_valid, result, out_tag, err_flag;
  endclocking

  clocking mon_cb @(posedge clk);
    default input #1step;
    input in_valid, in_ready, op, a, b, tag;
    input out_valid, out_ready, result, out_tag, err_flag;
  endclocking

  task automatic reset_signals();
    in_valid  <= 1'b0;
    op        <= 3'd0;
    a         <= 16'd0;
    b         <= 16'd0;
    tag       <= 4'd0;
    out_ready <= 1'b1;
  endtask

  // SVA 1: Valid request payload must remain stable while stalled (!in_ready)
  property p_in_valid_stable;
    @(posedge clk) disable iff (!rst_n)
    (in_valid && !in_ready) |=> (in_valid && $stable({op, a, b, tag}));
  endproperty
  a_in_valid_stable: assert property (p_in_valid_stable)
    else $error("[SVA] Input payload changed during Valid/Ready stall!");

  // SVA 2: Output valid must never assert during async/sync reset release
  property p_out_valid_reset;
    @(posedge clk) (!rst_n) |-> (!out_valid);
  endproperty
  a_out_valid_reset: assert property (p_out_valid_reset)
    else $error("[SVA] out_valid asserted while rst_n=0!");

  // Functional cover property on backpressure
  c_backpressure: cover property (@(posedge clk) disable iff (!rst_n) in_valid && !in_ready);
endinterface
