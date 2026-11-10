from pathlib import Path

# 1. uvm_comparer
txt = Path('docs_view/base/uvm_comparer-svh.html').read_text(encoding='utf-8')
for sym in ['policy', 'show_max', 'verbosity', 'sev', 'miscompares', 'physical', 'abstract', 'check_type', 'result']:
    key = f'name="uvm_comparer.{sym}"'
    idx = txt.find(key)
    if idx != -1:
        print(f'uvm_comparer.{sym}: {txt[idx:idx+150]}')
    else:
        print(f'uvm_comparer.{sym}: NOT FOUND')

# 2. uvm_object_globals
txt2 = Path('docs_view/base/uvm_object_globals-svh.html').read_text(encoding='utf-8')
for sym in ['uvm_bitstream_t', 'uvm_radix_enum']:
    key = f'name="{sym}"'
    idx = txt2.find(key)
    if idx != -1:
        print(f'{sym}: {txt2[idx:idx+150]}')
    else:
        print(f'{sym}: NOT FOUND')

# 3. uvm_driver
txt3 = Path('docs_view/comps/uvm_driver-svh.html').read_text(encoding='utf-8')
for sym in ['seq_item_port', 'rsp_port', 'req', 'rsp']:
    idx = txt3.find(sym)
    # find src-code-link around it
    key = f'>{sym}</a></h3>'
    idx = txt3.find(key)
    if idx != -1:
        print(f'uvm_driver.{sym}: {txt3[idx-120:idx+len(key)]}')
    else:
        print(f'uvm_driver.{sym}: NOT FOUND')

