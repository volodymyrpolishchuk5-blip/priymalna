import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

_client: Client = None

def get_db() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client

import uuid
from datetime import datetime

# ===================== TENANTS =====================

def create_tenant(owner_telegram_id: int, business_name: str) -> str:
    db = get_db()
    tenant_id = str(uuid.uuid4())[:8]
    db.table("tenants").insert({
        "id": tenant_id,
        "owner_telegram_id": owner_telegram_id,
        "business_name": business_name,
    }).execute()
    return tenant_id

def get_tenant_by_owner(owner_telegram_id: int):
    db = get_db()
    res = db.table("tenants").select("*").eq("owner_telegram_id", owner_telegram_id).maybe_single().execute()
    return res.data if res.data else None

def get_tenant_by_id(tenant_id: str):
    db = get_db()
    res = db.table("tenants").select("*").eq("id", tenant_id).maybe_single().execute()
    return res.data if res.data else None

# ===================== MASTERS =====================

def add_master(tenant_id: str, name: str, specialty: str, telegram_id=None):
    db = get_db()
    db.table("masters").insert({
        "tenant_id": tenant_id,
        "name": name,
        "specialty": specialty,
        "telegram_id": telegram_id,
    }).execute()

def get_masters_by_tenant(tenant_id: str):
    db = get_db()
    res = db.table("masters").select("*").eq("tenant_id", tenant_id).execute()
    return res.data or []

def get_master_by_id(master_id: int):
    db = get_db()
    res = db.table("masters").select("*").eq("id", master_id).maybe_single().execute()
    return res.data if res.data else None

def delete_master(master_id: int, tenant_id: str):
    db = get_db()
    db.table("masters").delete().eq("id", master_id).eq("tenant_id", tenant_id).execute()

# ===================== SERVICES =====================

def add_service(tenant_id: str, name: str, price: int, duration: int = 60):
    db = get_db()
    db.table("services").insert({
        "tenant_id": tenant_id,
        "name": name,
        "price": price,
        "duration": duration,
    }).execute()

def get_services_by_tenant(tenant_id: str):
    db = get_db()
    res = db.table("services").select("*").eq("tenant_id", tenant_id).execute()
    return res.data or []

def delete_service(service_id: int, tenant_id: str):
    db = get_db()
    db.table("services").delete().eq("id", service_id).eq("tenant_id", tenant_id).execute()

# ===================== APPOINTMENTS =====================

def add_appointment(tenant_id, master_id, client_name, client_phone, service, date, time):
    db = get_db()
    res = db.table("appointments").insert({
        "tenant_id": tenant_id,
        "master_id": master_id if master_id else None,
        "client_name": client_name,
        "client_phone": client_phone,
        "service": service,
        "date": date,
        "time": time,
        "status": "active",
    }).execute()
    return res.data[0]["id"] if res.data else None

def get_appointments_by_tenant(tenant_id: str):
    db = get_db()
    res = db.table("appointments").select(
        "id, client_name, client_phone, service, date, time, status, masters(name)"
    ).eq("tenant_id", tenant_id).order("date").order("time").execute()
    rows = []
    for r in (res.data or []):
        rows.append({
            "id": r["id"],
            "name": r["client_name"],
            "phone": r["client_phone"],
            "service": r["service"],
            "date": r["date"],
            "time": r["time"],
            "status": r["status"],
            "master": r["masters"]["name"] if r.get("masters") else None,
        })
    return rows

def update_appointment_status(appt_id: int, tenant_id: str, status: str):
    db = get_db()
    db.table("appointments").update({"status": status}).eq("id", appt_id).eq("tenant_id", tenant_id).execute()
