import json, re

text = open('js/search_data.js', encoding='utf-8').read()
m = re.search(r'const\s+UVM_DATA\s*=\s*(\{[\s\S]*\});?\s*$', text)
data = json.loads(m.group(1))
items = data['searchIndex']

for name in ['uvm_component', 'uvm_object', 'uvm_sequence', 'uvm_driver', 'build_phase', 'run_phase']:
    matches = [it for it in items if it.get('name') == name]
    for m in matches:
        print(m['name'], m['type'], "-> doc:", m.get('doc'), "src:", m.get('src'))

