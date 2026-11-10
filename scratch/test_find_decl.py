import json, re
from pathlib import Path

SRC_DIR = Path('uvm-1.2/src')

def find_actual_decl(lines, sym_name, sym_type=None, parent_class=None):
    clean = sym_name.split('::')[-1].split('#')[0].lstrip('+`').strip()
    if not clean:
        return 1
    
    pat = re.compile(r'\b' + re.escape(clean) + r'\b')
    
    candidates = []
    for idx, l in enumerate(lines, 1):
        s = l.strip()
        is_comment = s.startswith('//') or s.startswith('/*') or s.startswith('*')
        if not is_comment and pat.search(l):
            candidates.append((idx, l))
            
    if candidates:
        if sym_type in ('constant', 'parameter'):
            for idx, l in candidates:
                if re.search(r'\b(parameter|localparam|const)\b', l):
                    return idx
            for idx, l in candidates:
                if re.search(r'\b(enum|typedef)\b', l) or '=' in l or ',' in l:
                    return idx
        elif sym_type in ('type', 'enum'):
            for idx, l in candidates:
                if re.search(r'\btypedef\b', l):
                    return idx
        elif sym_type == 'port':
            for idx, l in candidates:
                if re.search(r'\b(port|export|imp)\b', l):
                    return idx
        return candidates[0][0]
    
    # Check comment line and first non-comment line after it
    comment_line = None
    for idx, l in enumerate(lines, 1):
        if pat.search(l):
            comment_line = idx
            break
            
    if comment_line:
        in_block_comment = False
        for idx in range(comment_line, min(comment_line + 60, len(lines) + 1)):
            s = lines[idx - 1].strip()
            if '/*' in s:
                in_block_comment = True
            if '*/' in s:
                in_block_comment = False
                continue
            if in_block_comment or s.startswith('//') or s.startswith('*') or not s:
                continue
            return idx
        return comment_line

    return 1

with open('data/uvm_source_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

for stype in ['constant', 'variable', 'type', 'port']:
    syms = [s for s in db['symbols_index'] if s.get('type') == stype]
    found_code = 0
    total = len(syms)
    for s in syms:
        frel = s.get('file')
        if not frel or not (SRC_DIR / frel).exists():
            continue
        lines = (SRC_DIR / frel).read_text(encoding='latin-1').splitlines()
        decl_line = find_actual_decl(lines, s['name'], stype)
        l_str = lines[decl_line - 1].strip()
        is_comment = l_str.startswith('//') or l_str.startswith('/*') or l_str.startswith('*')
        if not is_comment:
            found_code += 1
    print(f"Results for {stype}: {found_code}/{total} on actual code lines ({found_code/total*100:.1f}%)")
