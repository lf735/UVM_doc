import json, re
from pathlib import Path

SRC_DIR = Path('uvm-1.2/src')
with open('data/uvm_source_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

vars = [s for s in db['symbols_index'] if s.get('type') == 'variable']
for v in vars[10:20]:
    print(v['name'], "file:", v.get('file'), "class:", v.get('class'))

