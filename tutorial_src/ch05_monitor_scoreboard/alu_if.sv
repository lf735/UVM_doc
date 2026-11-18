// -----------------------------------------------------------------------------
// alu_if.sv - Interface Adding Passive Monitor Clocking Block (Chapter 5)
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

  // Purely passive input clocking block used by uvm_monitor
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
endinterface
