import json
import os

# Read search_data.js (it's a JS file, so we need to clean it to parse as JSON)
with open('c:/Users/uf755lfr/Perso/UVM_doc/js/search_data.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Clean up JS content to get JSON
json_content = content.replace('const UVM_DATA = ', '').strip().rstrip(';')
data = json.loads(json_content)

# Extract indexed hrefs
indexed_hrefs = set()
def extract_hrefs(node):
    if isinstance(node, dict):
        if 'href' in node:
            indexed_hrefs.add(node['href'])
        for key in node:
            extract_hrefs(node[key])
    elif isinstance(node, list):
        for item in node:
            extract_hrefs(item)

extract_hrefs(data)

# Extract actual .svh files
actual_files = set()
for root, dirs, files in os.walk('c:/Users/uf755lfr/Perso/UVM_doc/uvm-1.2/src'):
    for file in files:
        if file.endswith('.svh'):
            rel_path = os.path.relpath(os.path.join(root, file), 'c:/Users/uf755lfr/Perso/UVM_doc/uvm-1.2/src')
            actual_files.add(rel_path)

# Compare
# The index uses 'docs_view/' path, while actual files are in 'src/'
# Let's map them
print("Checking for missing files in the index...")

# Simplified comparison: looking for files that should be indexed
# This is a bit complex as the index seems to point to html files in docs_view/
# Let's just output the files on disk for the user to review
print("Files on disk (actual src):")
for f in sorted(list(actual_files)):
    print(f)

