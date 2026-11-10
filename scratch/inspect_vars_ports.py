import json, re
from pathlib import Path

SRC_DIR = Path('uvm-1.2/src')
with open('data/uvm_source_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

for stype in ['variable', 'port']:
    syms = [s for s in db['symbols_index'] if s.get('type') == stype]
    print(f"\n--- Sample {stype}s ---")
    for s in syms[:5]:
        frel = s.get('file')
        name = s.get('name')
        lines = (SRC_DIR / frel).read_text(encoding='latin-1').splitlines()
        print(f"{name} in {frel}:")
        # search for name anywhere in lines
        pat = re.compile(r'\b' + re.escape(name) + r'\b')
        matches = [(idx, l) for idx, l in enumerate(lines, 1) if pat.search(l)]
        for idx, l in matches[:4]:
            print(f"  Line {idx}: {l}")

