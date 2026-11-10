import json, re

with open('js/search_data.js', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'const\s+UVM_DATA\s*=\s*(\{[\s\S]*\});?\s*$', text)
if m:
    data = json.loads(m.group(1))
    cats = data.get('categories', [])
    print("Categories count:", len(cats))
    for c in cats:
        print(f"  {c.get('type')}: {c.get('title')} ({len(c.get('children', []))} children)")
    
    dh = data.get('docHeadings', {})
    print("docHeadings pages:", len(dh))
    h_types = set()
    for p, heads in dh.items():
        for h in heads:
            h_types.add(h.get('type'))
    print("docHeadings types:", h_types)

