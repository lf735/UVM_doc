import json, re
from pathlib import Path

SRC_DIR = Path('uvm-1.2/src')
with open('data/uvm_source_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

for stype in ['variable', 'type', 'port']:
    syms = [s for s in db['symbols_index'] if s.get('type') == stype]
    comment_count = 0
    l1_count = 0
    for s in syms:
        frel = s.get('file')
        line = s.get('line')
        if not frel or not line:
            l1_count += 1
            continue
        lines = (SRC_DIR / frel).read_text(encoding='latin-1').splitlines() if (SRC_DIR / frel).exists() else []
        if line < 1 or line > len(lines):
            l1_count += 1
            continue
        l_str = lines[line - 1].strip()
        if l_str.startswith('//') or l_str.startswith('/*') or l_str.startswith('*'):
            comment_count += 1
    print(f"Type '{stype}': total={len(syms)}, comment_lines={comment_count}, l1_or_invalid={l1_count}")

