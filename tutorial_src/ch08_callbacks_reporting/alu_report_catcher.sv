// -----------------------------------------------------------------------------
// alu_report_catcher.sv - Report Catcher Demoting Expected Fault Errors (Ch.8)
// -----------------------------------------------------------------------------
`ifndef ALU_REPORT_CATCHER_SV
`define ALU_REPORT_CATCHER_SV

class alu_report_catcher extends uvm_report_catcher;
  `uvm_object_utils(alu_report_catcher)

  int unsigned demoted_count = 0;

  function new(string name = "alu_report_catcher");
    super.new(name);
  endfunction

  virtual function action_e catch();
    // Demote controlled fault-injection error logs so negative tests pass cleanly
    if (get_severity() == UVM_ERROR && get_id() == "ALU_ERR_INJ") begin
      demoted_count++;
      set_severity(UVM_INFO);
      set_verbosity(UVM_LOW);
      set_message({"[CAUGHT & DEMOTED] ", get_message()});
    end
    return THROW;
  endfunction
endclass

`endif
