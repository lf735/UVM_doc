import json, re
from pathlib import Path

# 1. Test database
db = json.load(open('data/uvm_source_database.json', encoding='utf-8'))
constants = [s for s in db['symbols_index'] if s.get('type') == 'constant']
assert len(constants) == 136, f"Expected 136 constants, got {len(constants)}"
bad_db_lines = [c for c in constants if not c.get('line') or c['line'] <= 1]
assert len(bad_db_lines) == 0, f"Found constants with line <= 1 in database: {bad_db_lines}"
print("PASS: All 136 constants in uvm_source_database.json have line > 1")

# Check specific constant lines
uvm_active = next(c for c in constants if c['name'] == 'UVM_ACTIVE')
assert uvm_active['line'] == 147, f"Expected UVM_ACTIVE at line 147, got {uvm_active['line']}"
begin_req = next(c for c in constants if c['name'] == 'BEGIN_REQ')
assert begin_req['line'] == 37, f"Expected BEGIN_REQ at line 37, got {begin_req['line']}"
print(f"PASS: Verified UVM_ACTIVE -> line {uvm_active['line']} and BEGIN_REQ -> line {begin_req['line']}")

# 2. Test search_data.js
search_js = open('js/search_data.js', encoding='utf-8').read()
m = re.search(r'const\s+UVM_DATA\s*=\s*(\{[\s\S]*\});?\s*$', search_js)
assert m, "Could not extract UVM_DATA from js/search_data.js"
data = json.loads(m.group(1))
s_items = data['searchIndex']
s_constants = [it for it in s_items if it.get('type') == 'constant']
assert len(s_constants) == 136, f"Expected 136 constants in searchIndex, got {len(s_constants)}"

s_l1_constants = [it for it in s_constants if it.get('src', '').endswith('#L1')]
assert len(s_l1_constants) == 0, f"Constants with #L1 in searchIndex: {len(s_l1_constants)}"
print("PASS: Zero constants in searchIndex point to #L1")

# Check exact src link in searchIndex
s_active = next(it for it in s_constants if it['name'] == 'UVM_ACTIVE')
assert s_active['src'] == 'src_view/base/uvm_object_globals.svh.html#L147', f"Bad src for UVM_ACTIVE: {s_active['src']}"
s_req = next(it for it in s_constants if it['name'] == 'BEGIN_REQ')
assert s_req['src'] == 'src_view/tlm2/uvm_tlm2_ifs.svh.html#L37', f"Bad src for BEGIN_REQ: {s_req['src']}"
print("PASS: Constant source links in searchIndex point to exact code lines")

# 3. Test index.html pills
index_html = open('index.html', encoding='utf-8').read()
assert 'data-type="class"' in index_html and 'data-type="overview"' in index_html
print("PASS: index.html has updated sidebar-filter-pills")

# 4. Test js/app.js
app_js = open('js/app.js', encoding='utf-8').read()
assert 'currentActiveIndexKey' in app_js, "currentActiveIndexKey not in app_js"
assert 'data-index-key' in app_js, "data-index-key not in app_js"
assert 'updateSidebarPillsForTab()' in app_js, "updateSidebarPillsForTab call not in app_js"
assert 'activeSidebarTab === \'docs\'' in app_js, "docs tab check not in app_js"
assert 'activeSidebarTab === \'source\'' in app_js, "source tab check not in app_js"
print("PASS: js/app.js contains active item tracking and tab-specific pills")

# 5. Test css/style.css
css = open('css/style.css', encoding='utf-8').read()
assert '.az-index-link.active' in css, ".az-index-link.active not in css"
assert '[data-theme="dark"] .az-index-link.active' in css, "dark theme active index styling not in css"
print("PASS: css/style.css contains high-visibility active index element styling")

print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

