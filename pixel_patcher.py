import os
import glob
import re

files = glob.glob(r'C:\Users\MSI\Desktop\Archivos\projects\deskmon\mechanics\*.py')
files.extend(glob.glob(r'C:\Users\MSI\Desktop\Archivos\projects\deskmon\entities\*.py'))
files.extend(glob.glob(r'C:\Users\MSI\Desktop\Archivos\projects\deskmon\core\*.py'))

changes = 0
ovals_replaced = 0
smooths_removed = 0

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    
    # Count occurrences
    ovals = len(re.findall(r'\.create_oval\(', new_content))
    smooths = len(re.findall(r'smooth\s*=\s*(?:True|1)', new_content))
    
    # Replace
    new_content = re.sub(r'\.create_oval\(', '.create_rectangle(', new_content)
    new_content = re.sub(r',\s*smooth\s*=\s*(?:True|1)', '', new_content)
    new_content = re.sub(r'smooth\s*=\s*(?:True|1)\s*,?', '', new_content)
    
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        changes += 1
        ovals_replaced += ovals
        smooths_removed += smooths

print(f"Patched {changes} files successfully!")
print(f"Ovals replaced with rectangles: {ovals_replaced}")
print(f"Smooth/anti-aliasing removed: {smooths_removed}")
