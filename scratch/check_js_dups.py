import re

code = open('js/app.js', encoding='utf-8').read()

# Check for duplicate declarations in same function
# Simple regex to extract functions
funcs = re.split(r'\n  function ', code)
print(f"Checking {len(funcs)} top-level functions...")
duplicates_found = 0
for idx, fn in enumerate(funcs[1:], 1):
    fname = fn.split('(')[0].strip()
    # Find all const/let declarations at the root of the function
    decls = re.findall(r'^\s+(?:const|let)\s+([a-zA-Z0-9_]+)\s*=', fn, re.MULTILINE)
    seen = set()
    for d in decls:
        if d in seen:
            print(f"Warning in function '{fname}': duplicate variable '{d}'")
            duplicates_found += 1
        seen.add(d)

if duplicates_found == 0:
    print("PASS: No duplicate const/let declarations found in functions!")

