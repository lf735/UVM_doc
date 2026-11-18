// -----------------------------------------------------------------------------
// pkt_alu_dpi_pkg.sv - SystemVerilog <-> C DPI-C Bindings (Chapter 12)
// -----------------------------------------------------------------------------
`ifndef PKT_ALU_DPI_PKG_SV
`define PKT_ALU_DPI_PKG_SV

import "DPI-C" function void pkt_alu_dpi_calc(
  input  int unsigned op,
  input  int unsigned a,
  input  int unsigned b,
  input  int unsigned sat_en,
  input  int unsigned sat_limit,
  input  int unsigned err_mask,
  input  int unsigned force_err,
  output int unsigned out_result,
  output int unsigned out_err
);

`endif
