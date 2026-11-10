with open('docs_view/tlm2/uvm_tlm2_ifs-svh.html', 'r', encoding='utf-8') as f:
    c = f.read()

idx = c.find('BEGIN_REQ')
print(c[idx-200:idx+300])

