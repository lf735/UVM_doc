import json, re
from pathlib import Path

text = open('js/search_data.js', encoding='utf-8').read()
m = re.search(r'const\s+UVM_DATA\s*=\s*(\{[\s\S]*\});?\s*$', text)
data = json.loads(m.group(1))
items = data['searchIndex']

print(f"Total items in searchIndex: {len(items)}")

no_doc = [it for it in items if not it.get('doc')]
print(f"Items with no doc: {len(no_doc)}")
types_no_doc = {}
for it in no_doc:
    t = it.get('type')
    types_no_doc[t] = types_no_doc.get(t, 0) + 1
print("Types with no doc:", types_no_doc)

# Check if doc files actually exist on disk!
missing_doc_files = []
broken_anchors = []
for it in items:
    doc = it.get('doc')
    if not doc:
        continue
    file_part, _, anchor = doc.partition('#')
    fpath = Path(file_part)
    if not fpath.exists():
        missing_doc_files.append((it['name'], it['type'], doc))
    elif anchor:
        # Check if anchor exists in fpath
        content = fpath.read_text(encoding='utf-8', errors='ignore')
        # Look for anchor in name= or id= or data-anchor=
        has_anchor = (f'name="{anchor}"' in content or f'name=\'{anchor}\'' in content or
                      f'id="{anchor}"' in content or f'id=\'{anchor}\'' in content or
                      f'data-anchor="{anchor}"' in content or f'data-anchor=\'{anchor}\'' in content)
        if not has_anchor:
            broken_anchors.append((it['name'], it['type'], doc, anchor))

print(f"Items with missing doc files on disk: {len(missing_doc_files)}")
for it in missing_doc_files[:10]:
    print("  Missing file:", it)

print(f"Items with broken anchors: {len(broken_anchors)}")
for it in broken_anchors[:20]:
    print("  Broken anchor:", it)

