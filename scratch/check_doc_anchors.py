import re

with open('docs_view/base/uvm_component-svh.html', 'r', encoding='utf-8') as f:
    c = f.read()

print("Matching accept_tr in doc html:")
for m in re.finditer(r'<[^>]+(?:name|id|data-anchor)=["\'][^"\']*accept_tr[^"\']*["\'][^>]*>', c):
    print(" ", m.group(0))

with open('docs_view/tlm2/uvm_tlm2_ifs-svh.html', 'r', encoding='utf-8') as f:
    c2 = f.read()
print("Matching BEGIN_REQ in tlm2 doc html:")
for m in re.finditer(r'<[^>]+(?:name|id|data-anchor)=["\'][^"\']*BEGIN_REQ[^"\']*["\'][^>]*>', c2):
    print(" ", m.group(0))

with open('docs_view/base/uvm_object_globals-svh.html', 'r', encoding='utf-8') as f:
    c3 = f.read()
print("Matching UVM_ACTIVE in object_globals doc html:")
for m in re.finditer(r'<[^>]+(?:name|id|data-anchor)=["\'][^"\']*UVM_ACTIVE[^"\']*["\'][^>]*>', c3):
    print(" ", m.group(0))

