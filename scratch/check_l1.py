import json, re

with open('js/search_data.js', 'r', encoding='utf-8') as f:
    text = f.read()

# UVM_DATA = {...};
m = re.search(r'const\s+UVM_DATA\s*=\s*(\{[\s\S]*\});?\s*$', text)
if m:
    data = json.loads(m.group(1))
    items = data.get('searchIndex', [])
    l1_items = [it for it in items if it.get('src', '').endswith('#L1')]
    print(f"Total searchIndex: {len(items)}")
    print(f"Items with #L1: {len(l1_items)}")
    types_l1 = {}
    for it in l1_items:
        t = it.get('type')
        types_l1[t] = types_l1.get(t, 0) + 1
    print("Types with #L1:", types_l1)
    for it in l1_items[:15]:
        print("  Sample #L1:", it['type'], it['name'], "->", it.get('src'))
else:
    print("Could not match UVM_DATA")

