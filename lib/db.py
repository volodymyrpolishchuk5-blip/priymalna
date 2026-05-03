import os
from supabase import create_client, Client

_client: Client = None

def get_db() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL")
        # Try both common names for the key
        key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError(f"Supabase credentials missing! URL: {'set' if url else 'MISSING'}, KEY: {'set' if key else 'MISSING'}")
            
        _client = create_client(url, key)
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
    return res.data if res and getattr(res, "data", None) else None

def get_tenant_by_id(tenant_id: str):
    db = get_db()
    res = db.table("tenants").select("*").eq("id", tenant_id).maybe_single().execute()
    return res.data if res and getattr(res, "data", None) else None

# ===================== MASTERS =====================

def add_master(tenant_id: str, name: str, specialty: str, telegram_id=None, commission_rate=50):
    db = get_db()
    db.table("masters").insert({
        "tenant_id": tenant_id,
        "name": name,
        "specialty": specialty,
        "telegram_id": telegram_id,
        "commission_rate": commission_rate
    }).execute()

def get_master_by_tg_id(tenant_id: str, tg_id: str):
    db = get_db()
    res = db.table("masters").select("*").eq("tenant_id", tenant_id).eq("telegram_id", tg_id).maybe_single().execute()
    return res.data if res and getattr(res, "data", None) else None

def get_masters_by_tenant(tenant_id: str):
    db = get_db()
    res = db.table("masters").select("*").eq("tenant_id", tenant_id).execute()
    return res.data or []

def get_master_by_id(master_id: int):
    db = get_db()
    res = db.table("masters").select("*").eq("id", master_id).maybe_single().execute()
    return res.data if res and getattr(res, "data", None) else None

def delete_master(master_id: int, tenant_id: str):
    db = get_db()
    db.table("masters").delete().eq("id", master_id).eq("tenant_id", tenant_id).execute()

def update_master(master_id: int, tenant_id: str, name: str, specialty: str, telegram_id: str, commission_rate: int):
    db = get_db()
    db.table("masters").update({
        "name": name,
        "specialty": specialty,
        "telegram_id": telegram_id,
        "commission_rate": commission_rate
    }).eq("id", master_id).eq("tenant_id", tenant_id).execute()

# ===================== CLIENTS =====================

def get_client_by_phone(tenant_id: str, phone: str):
    db = get_db()
    res = db.table("clients").select("*").eq("tenant_id", tenant_id).eq("phone", phone).maybe_single().execute()
    return res.data if res and getattr(res, "data", None) else None

def get_client_by_id(client_id: int):
    db = get_db()
    res = db.table("clients").select("*").eq("id", client_id).maybe_single().execute()
    return res.data if res and getattr(res, "data", None) else None

def create_db_client(tenant_id: str, name: str, phone: str):
    db = get_db()
    res = db.table("clients").insert({
        "tenant_id": tenant_id,
        "name": name,
        "phone": phone
    }).execute()
    return res.data[0]["id"] if res.data else None

def get_clients_by_tenant(tenant_id: str):
    db = get_db()
    # 1. Try to get from clients table
    res = db.table("clients").select("*").eq("tenant_id", tenant_id).execute()
    if res.data and len(res.data) > 0:
        return res.data
    
    # 2. Fallback: If clients table is empty for this tenant, 
    # try to reconstruct from appointments (since we know they exist there)
    res_appts = db.table("appointments").select("client_name, client_phone, created_at").eq("tenant_id", tenant_id).execute()
    if res_appts.data:
        # Deduplicate by phone
        seen = set()
        fallback_clients = []
        for a in res_appts.data:
            if a["client_phone"] not in seen:
                seen.add(a["client_phone"])
                fallback_clients.append({
                    "id": f"fb_{len(seen)}",
                    "name": a["client_name"],
                    "phone": a["client_phone"],
                    "created_at": a["created_at"],
                    "is_vip": False,
                    "is_blacklisted": False
                })
        return fallback_clients
        
    return []

def update_client_status(client_id: int, tenant_id: str, is_vip: bool = None, is_blacklisted: bool = None):
    db = get_db()
    data = {}
    if is_vip is not None: data["is_vip"] = is_vip
    if is_blacklisted is not None: data["is_blacklisted"] = is_blacklisted
    db.table("clients").update(data).eq("id", client_id).eq("tenant_id", tenant_id).execute()

def delete_client(client_id: int, tenant_id: str):
    db = get_db()
    db.table("clients").delete().eq("id", client_id).eq("tenant_id", tenant_id).execute()

def update_client_data(client_id, tenant_id: str, name: str, phone: str):
    db = get_db()
    # If client_id is a string (like fb_...), it means we need to create it
    if isinstance(client_id, str) and client_id.startswith("fb_"):
        db.table("clients").insert({
            "tenant_id": tenant_id,
            "name": name,
            "phone": phone
        }).execute()
    else:
        db.table("clients").update({
            "name": name,
            "phone": phone
        }).eq("id", int(client_id)).eq("tenant_id", tenant_id).execute()

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

def update_service(service_id: int, tenant_id: str, name: str, price: int, duration: int):
    db = get_db()
    db.table("services").update({
        "name": name,
        "price": price,
        "duration": duration
    }).eq("id", service_id).eq("tenant_id", tenant_id).execute()

# ===================== APPOINTMENTS =====================

def add_appointment(tenant_id, master_id, client_id, client_name, client_phone, service, price, date, time, status="active"):
    db = get_db()
    res = db.table("appointments").insert({
        "tenant_id": tenant_id,
        "master_id": master_id if master_id else None,
        "client_id": client_id,
        "client_name": client_name,
        "client_phone": client_phone,
        "service": service,
        "price": price,
        "date": date,
        "time": time,
        "status": status,
    }).execute()
    return res.data[0]["id"] if res.data else None

def get_appointments_by_tenant(tenant_id: str, master_id: int = None):
    db = get_db()
    query = db.table("appointments").select(
        "id, client_id, client_name, client_phone, service, price, date, time, status, masters(name)"
    ).eq("tenant_id", tenant_id)
    
    if master_id:
        query = query.eq("master_id", master_id)
        
    res = query.order("date").order("time").execute()
    rows = []
    for r in (res.data or []):
        rows.append({
            "id": r["id"],
            "client_id": r["client_id"],
            "name": r["client_name"],
            "phone": r["client_phone"],
            "service": r["service"],
            "price": r.get("price") or 0,
            "date": r["date"],
            "time": r["time"],
            "status": r["status"],
            "master": r["masters"]["name"] if r.get("masters") else None,
        })
    return rows

def update_appointment_datetime(appt_id: int, tenant_id: str, new_date: str, new_time: str):
    db = get_db()
    db.table("appointments").update({"date": new_date, "time": new_time}).eq("id", appt_id).eq("tenant_id", tenant_id).execute()

def update_appointment_status(appt_id: int, tenant_id: str, status: str):
    db = get_db()
    db.table("appointments").update({"status": status}).eq("id", appt_id).eq("tenant_id", tenant_id).execute()

def get_appointment_by_id(appt_id: int):
    db = get_db()
    res = db.table("appointments").select("*").eq("id", appt_id).maybe_single().execute()
    return res.data if res and getattr(res, "data", None) else None

# ===================== STATS =====================

def get_stats(tenant_id: str):
    db = get_db()
    # Fetch all appointments to calculate stats
    # In a larger app, we would use SQL aggregations, but for now, we'll do it in Python
    res = db.table("appointments").select("price, status, created_at").eq("tenant_id", tenant_id).execute()
    appts = res.data or []
    
    stats = {
        "today_income": 0,
        "week_income": 0,
        "month_income": 0,
        "total_bookings": len(appts),
        "completed_bookings": 0
    }
    
    from datetime import datetime, timedelta
    now = datetime.now()
    
    for a in appts:
        price = a.get("price") or 0
        status = a.get("status")
        created_at = datetime.fromisoformat(a["created_at"].replace("Z", "+00:00"))
        
        if status == "виконано":
            stats["completed_bookings"] += 1
            # Check date ranges
            if created_at.date() == now.date():
                stats["today_income"] += price
            if created_at > now - timedelta(days=7):
                stats["week_income"] += price
            if created_at > now - timedelta(days=30):
                stats["month_income"] += price
                
    return stats
