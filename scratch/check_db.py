import os
import sys
# Add project root to sys.path
sys.path.append(os.getcwd())
from lib import db

# The tenant_id should be what the user is using.
# Based on the bot name @priymalna_bot and the user requests, 
# I'll try to find the tenant_id from the appointments table first.

try:
    db_conn = db.get_db()
    # Get all tenants who have appointments
    appts = db_conn.table("appointments").select("tenant_id").limit(1).execute()
    if appts.data:
        tenant_id = appts.data[0]['tenant_id']
        print(f"Detected tenant_id: {tenant_id}")
        
        clients = db.get_clients_by_tenant(tenant_id)
        print(f"Total clients found: {len(clients)}")
        for c in clients:
            print(f"- {c['name']} (ID: {c['id']}, VIP: {c['is_vip']})")
    else:
        print("No appointments found in the database.")
except Exception as e:
    print(f"Error: {e}")
