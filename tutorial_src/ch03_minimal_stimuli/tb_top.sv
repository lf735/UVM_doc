// -----------------------------------------------------------------------------
// tb_top.sv - Top Module Connecting RTL DUT & Minimal UVM Testbench (Ch.3)
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_top;
  import uvm_pkg::*;
  `include "uvm_macros.svh"
  `include "alu_item.sv"
  `include "alu_seq.sv"
  `include "alu_driver.sv"
  `include "alu_minimal_test.sv"

  logic clk = 1'b0;
  logic rst_n = 1'b0;

  always #5ns clk = ~clk;

  initial begin
    rst_n = 1'b0;
    #25ns;
    rst_n = 1'b1;
  end

  alu_if u_alu_if (.clk(clk), .rst_n(rst_n));

  pkt_alu_basic u_dut (
    .clk       (clk),
    .rst_n     (rst_n),
    .in_valid  (u_alu_if.in_valid),
    .in_ready  (u_alu_if.in_ready),
    .op        (u_alu_if.op),
    .a         (u_alu_if.a),
    .b         (u_alu_if.b),
    .tag       (u_alu_if.tag),
    .out_valid (u_alu_if.out_valid),
    .out_ready (u_alu_if.out_ready),
    .result    (u_alu_if.result),
    .out_tag   (u_alu_if.out_tag),
    .err_flag  (u_alu_if.err_flag)
  );

  initial begin
    uvm_config_db#(virtual alu_if)::set(null, "uvm_test_top.drv", "vif", u_alu_if);
    run_test("alu_minimal_test");
  end
endmodule
