import re

with open('docs_view/comps/uvm_algorithmic_comparator-svh.html', 'r', encoding='utf-8') as f:
    c = f.read()

print("Anchors in uvm_algorithmic_comparator-svh.html:")
for m in re.finditer(r'<[^>]+(?:name|id|data-anchor)=["\'][^"\']*before_export[^"\']*["\'][^>]*>', c):
    print(" ", m.group(0))

with open('docs_view/base/uvm_cmdline_processor-svh.html', 'r', encoding='utf-8') as f:
    c2 = f.read()
print("Anchors in uvm_cmdline_processor-svh.html:")
for m in re.finditer(r'<[^>]+(?:name|id|data-anchor)=["\'][^"\']*UVM_DUMP_CMDLINE_ARGS[^"\']*["\'][^>]*>', c2):
    print(" ", m.group(0))

