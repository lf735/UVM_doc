with open('docs_view/base/uvm_component-svh.html', 'r', encoding='utf-8') as f:
    c = f.read()

idx = c.find('id="uvm_component.accept_tr"')
print("Snippet around accept_tr:")
print(c[idx-250:idx+350])

