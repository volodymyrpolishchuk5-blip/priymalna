import re
import sys

file_path = 'lib/db.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'res = db\.table\("appointments"\)\.select\(\s*"id, client_id, client_name, client_phone, service, price, date, time, status, masters\(name\)"\s*\)\.eq\("tenant_id", tenant_id\)\.order\("date"\)\.order\("time"\)\.execute\(\)'

replacement = """query = db.table("appointments").select(
        "id, client_id, client_name, client_phone, service, price, date, time, status, masters(name)"
    ).eq("tenant_id", tenant_id)
    
    if master_id:
        query = query.eq("master_id", master_id)
        
    res = query.order("date").order("time").execute()"""

new_content = re.sub(pattern, replacement, content)

if new_content != content:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Success")
else:
    print("Pattern not found")
