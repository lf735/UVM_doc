import json, re

text = open('js/search_data.js', encoding='utf-8').read()
m = re.search(r'const\s+UVM_DATA\s*=\s*(\{[\s\S]*\});?\s*$', text)
data = json.loads(m.group(1))
items = data['searchIndex']
constants = [it for it in items if it.get('type') == 'constant']

print(f"Total constants: {len(constants)}")
for c in constants[:15]:
    print(c['name'], "-> doc:", c.get('doc'))

