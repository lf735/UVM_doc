import json, re
from pathlib import Path

SRC_DIR = Path('uvm-1.2/src')
with open('data/uvm_source_database.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

constants = [s for s in db['symbols_index'] if s.get('type') == 'constant']
print(f"Total constants: {len(constants)}")

# Patterns for actual declarations
decl_patterns = [
    re.compile(r'^\s*parameter\b'),
    re.compile(r'^\s*localparam\b'),
    re.compile(r'^\s*const\b'),
    re.compile(r'typedef\s+enum\b'),
    re.compile(r'\benum\b')
]

issues = []
for c in constants:
    cname = c['name']
    frel = c.get('file')
    line = c.get('line')
    if not frel:
        issues.append((cname, "No file", None, None))
        continue
    fpath = SRC_DIR / frel
    if not fpath.exists():
        issues.append((cname, f"File not found: {frel}", None, None))
        continue
    lines = fpath.read_text(encoding='latin-1').splitlines()
    if line < 1 or line > len(lines):
        issues.append((cname, f"Line out of range: {line} of {len(lines)}", frel, line))
        continue
    matched_line = lines[line - 1]
    # Check if this line is a comment
    is_comment = matched_line.strip().startswith('//') or matched_line.strip().startswith('/*') or matched_line.strip().startswith('*')
    if is_comment:
        # Check if there is an actual code declaration nearby
        clean_name = cname.lstrip('+`')
        actual_decl = None
        for idx, l in enumerate(lines, 1):
            l_strip = l.strip()
            if l_strip.startswith('//') or l_strip.startswith('/*') or l_strip.startswith('*'):
                continue
            if re.search(r'\b' + re.escape(clean_name) + r'\b', l):
                actual_decl = idx
                break
        issues.append((cname, f"Comment line: '{matched_line.strip()}'", frel, line, actual_decl))

print(f"Constants on comment lines: {len(issues)}")
for iss in issues[:25]:
    cname = iss[0]
    msg = iss[1]
    frel = iss[2]
    line = iss[3]
    actual = iss[4] if len(iss) > 4 else None
    print(f"  {cname} in {frel}:{line} (actual code decl at line {actual}): {msg}")

