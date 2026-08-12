import os, re
d = r'C:\Users\MSI\Desktop\Archivos\projects\deskmon\mechanics'
has_it = []
no_it = []
for f in os.listdir(d):
    if not f.endswith('.py') or f in ['__init__.py', 'shared_vfx.py', 'dark_arts.py', 'telekinesis.py']: continue
    path = os.path.join(d, f)
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
        if re.search(r'(self\.current_state\s*=\s*[\''\"].*?(channel|charg|gather|absorb|windup|prep|aim)[\''\"])|(def\s+.*?(channel|charg|gather|absorb|windup|prep|aim))', content, re.IGNORECASE):
            has_it.append(f)
        else:
            no_it.append(f)
print('NO:', no_it)
