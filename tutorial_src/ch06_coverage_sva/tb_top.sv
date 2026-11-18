// -----------------------------------------------------------------------------
// tb_top.sv - Top Testbench with Functional Coverage & SVA (Chapter 6)
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

package alu_tb_pkg;
  import uvm_pkg::*;
  `include "uvm_macros.svh"
  `include "alu_cfg.sv"
  `include "alu_item.sv"
  `include "alu_seq.sv"
  `include "alu_driver.sv"
  `include "alu_monitor.sv"
  `include "alu_agent.sv"
  `include "alu_ref_model.sv"
  `include "alu_scoreboard.sv"
  `include "alu_cov_subscriber.sv"
  `include "alu_env.sv"
  `include "alu_test.sv"
endpackage

module tb_top;
  import uvm_pkg::*;
  import alu_tb_pkg::*;

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
    uvm_config_db#(virtual alu_if)::set(null, "uvm_test_top", "alu_vif", u_alu_if);
    run_test("alu_base_test");
  end
endmodule
