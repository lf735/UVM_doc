// -----------------------------------------------------------------------------
// apb_if.sv - APB3 Configuration Register Interface (Chapter 7)
// -----------------------------------------------------------------------------
interface apb_if (input logic clk, input logic rst_n);
  logic        psel;
  logic        penable;
  logic        pwrite;
  logic [7:0]  paddr;
  logic [31:0] pwdata;
  logic [31:0] prdata;
  logic        pready;

  clocking drv_cb @(posedge clk);
    default input #1step output #1;
    output psel, penable, pwrite, paddr, pwdata;
    input  prdata, pready;
  endclocking

  clocking mon_cb @(posedge clk);
    default input #1step;
    input psel, penable, pwrite, paddr, pwdata, prdata, pready;
  endclocking

  task automatic reset_signals();
    psel    <= 1'b0;
    penable <= 1'b0;
    pwrite  <= 1'b0;
    paddr   <= 8'h00;
    pwdata  <= 32'd0;
  endtask
endinterface
