#!/usr/bin/env python3
"""
Unit test suite for scripts/syntax_highlighter.py
Tests tokenization and HTML rendering across SystemVerilog, C/DPI, Makefiles, and doc snippets.
"""

import sys
from pathlib import Path

# Add scripts directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

import syntax_highlighter as sh

def test_system_tasks():
    code = '$display("Time: %0t, data=%0h", $time, data); $cast(dest, src); $finish();'
    rows, count = sh.highlight_source_code_table_rows(code, "test.sv")
    html_out = "".join(rows)
    assert '<span class="sv-system-tf">$display</span>' in html_out, "$display should be .sv-system-tf"
    assert '<span class="sv-system-tf">$time</span>' in html_out, "$time should be .sv-system-tf"
    assert '<span class="sv-system-tf">$cast</span>' in html_out, "$cast should be .sv-system-tf"
    assert '<span class="sv-system-tf">$finish</span>' in html_out, "$finish should be .sv-system-tf"
    assert '<span class="sv-string-escape">%0t</span>' in html_out, "%0t should be .sv-string-escape"
    assert '<span class="sv-string-escape">%0h</span>' in html_out, "%0h should be .sv-string-escape"
    print("✔ test_system_tasks passed")

def test_types_vs_keywords():
    code = 'virtual class my_env extends uvm_env;\n  rand logic [31:0] addr;\n  int timeout;\n  if (addr > 0) return;\nendclass'
    rows, count = sh.highlight_source_code_table_rows(code, "test.sv")
    html_out = "".join(rows)
    assert '<span class="sv-qualifier">virtual</span>' in html_out, "virtual should be .sv-qualifier"
    assert '<span class="sv-keyword-decl">class</span>' in html_out, "class should be .sv-keyword-decl"
    assert '<span class="sv-keyword-decl">extends</span>' in html_out, "extends should be .sv-keyword-decl"
    assert '<span class="sv-uvm-type">uvm_env</span>' in html_out, "uvm_env should be .sv-uvm-type"
    assert '<span class="sv-qualifier">rand</span>' in html_out, "rand should be .sv-qualifier"
    assert '<span class="sv-type">logic</span>' in html_out, "logic should be .sv-type"
    assert '<span class="sv-type">int</span>' in html_out, "int should be .sv-type"
    assert '<span class="sv-keyword">if</span>' in html_out, "if should be .sv-keyword"
    assert '<span class="sv-keyword">return</span>' in html_out, "return should be .sv-keyword"
    print("✔ test_types_vs_keywords passed")

def test_methods_and_phases():
    code = 'function void build_phase(uvm_phase phase);\n  super.build_phase(phase);\n  drv.seq_item_port.connect(sqr.seq_item_export);\nendfunction'
    rows, count = sh.highlight_source_code_table_rows(code, "test.sv")
    html_out = "".join(rows)
    assert '<span class="sv-method">build_phase</span>' in html_out, "build_phase should be .sv-method"
    assert '<span class="sv-constant">super</span>' in html_out, "super should be .sv-constant"
    assert '<span class="sv-method">connect</span>' in html_out, "connect should be .sv-method"
    print("✔ test_methods_and_phases passed")

def test_preproc_vs_macros():
    code = '`include "uvm_macros.svh"\n`ifdef DEBUG\n  `uvm_info("TEST", "Running...", UVM_LOW)\n`endif'
    rows, count = sh.highlight_source_code_table_rows(code, "test.sv")
    html_out = "".join(rows)
    assert '<span class="sv-preproc">`include</span>' in html_out, "`include should be .sv-preproc"
    assert '<span class="sv-preproc">`ifdef</span>' in html_out, "`ifdef should be .sv-preproc"
    assert '<span class="sv-macro">`uvm_info</span>' in html_out, "`uvm_info should be .sv-macro"
    assert '<span class="sv-constant">UVM_LOW</span>' in html_out, "UVM_LOW should be .sv-constant"
    print("✔ test_preproc_vs_macros passed")

def test_operators_and_numbers():
    code = 'logic [7:0] data = 8\'hA5;\n#10ns;\nif (a <= b && c != d) obj::func();'
    rows, count = sh.highlight_source_code_table_rows(code, "test.sv")
    html_out = "".join(rows)
    assert '<span class="sv-number">8&#x27;hA5</span>' in html_out or '<span class="sv-number">8\'hA5</span>' in html_out, "8'hA5 should be .sv-number"
    assert '<span class="sv-number">10ns</span>' in html_out, "10ns should be .sv-number"
    assert '<span class="sv-op">&lt;=</span>' in html_out or '<span class="sv-op"><=</span>' in html_out, "<= should be atomic .sv-op"
    assert '<span class="sv-op">::</span>' in html_out, ":: should be atomic .sv-op"
    assert '<span class="sv-op">&amp;&amp;</span>' in html_out, "&& should be atomic .sv-op"
    print("✔ test_operators_and_numbers passed")

def test_comments_and_tags():
    code = '// TODO: verify handshake\n/* NOTE: critical path */'
    rows, count = sh.highlight_source_code_table_rows(code, "test.sv")
    html_out = "".join(rows)
    assert '<span class="sv-comment-tag">TODO:</span>' in html_out, "TODO: should be .sv-comment-tag"
    assert '<span class="sv-comment-tag">NOTE:</span>' in html_out, "NOTE: should be .sv-comment-tag"
    print("✔ test_comments_and_tags passed")

def test_c_dpi_and_makefile():
    c_code = '#include "uvm_dpi.h"\nvoid uvm_hdl_read(svLogicVecVal* val) {\n  printf("Reading\\n");\n}'
    c_rows, _ = sh.highlight_source_code_table_rows(c_code, "dpi.c")
    c_html = "".join(c_rows)
    assert '<span class="sv-preproc">#include</span>' in c_html, "#include in C should be .sv-preproc"
    assert '<span class="sv-type">svLogicVecVal</span>' in c_html, "svLogicVecVal in C should be .sv-type"
    assert '<span class="sv-method">printf</span>' in c_html, "printf in C should be .sv-method"

    make_code = 'VCS = vcs\nall: sim\n\t$(VCS) -sverilog\nifeq ($(OPT), 1)\n\t@echo "Optimized"\nendif'
    make_rows, _ = sh.highlight_source_code_table_rows(make_code, "Makefile.vcs")
    make_html = "".join(make_rows)
    assert '<span class="sv-proto-name">VCS</span>' in make_html, "VCS should be .sv-proto-name"
    assert '<span class="sv-proto-name" style="font-weight:700">all</span>' in make_html, "all should be target"
    assert '<span class="sv-keyword">ifeq</span>' in make_html, "ifeq should be .sv-keyword"
    print("✔ test_c_dpi_and_makefile passed")

if __name__ == "__main__":
    test_system_tasks()
    test_types_vs_keywords()
    test_methods_and_phases()
    test_preproc_vs_macros()
    test_operators_and_numbers()
    test_comments_and_tags()
    test_c_dpi_and_makefile()
    print("\n🎉 ALL SYNTAX HIGHLIGHTER TESTS PASSED!")
