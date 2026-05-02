import sqlite3
import uuid
from datetime import datetime

DB_PATH = 'booking_system.db'

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Таблиця бізнесів (tenants)
    c.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            owner_telegram_id INTEGER UNIQUE,
            business_name TEXT,
            created_at TEXT
        )
    ''')

    # Таблиця майстрів
    c.execute('''
        CREATE TABLE IF NOT EXISTS masters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            name TEXT,
            specialty TEXT,
            telegram_id INTEGER,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id)
        )
    ''')

    # Таблиця послуг
    c.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            name TEXT,
            price INTEGER,
            duration INTEGER,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id)
        )
    ''')

    # Таблиця записів
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            master_id INTEGER,
            client_name TEXT,
            client_phone TEXT,
            service TEXT,
            date TEXT,
            time TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id),
            FOREIGN KEY (master_id) REFERENCES masters(id)
        )
    ''')

    conn.commit()
    conn.close()

# ===================== TENANTS =====================

def create_tenant(owner_telegram_id, business_name):
    conn = get_conn()
    c = conn.cursor()
    tenant_id = str(uuid.uuid4())[:8]  # короткий унікальний ID
    c.execute(
        'INSERT INTO tenants (id, owner_telegram_id, business_name, created_at) VALUES (?, ?, ?, ?)',
        (tenant_id, owner_telegram_id, business_name, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return tenant_id

def get_tenant_by_owner(owner_telegram_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM tenants WHERE owner_telegram_id = ?', (owner_telegram_id,))
    row = c.fetchone()
    conn.close()
    return row  # (id, owner_telegram_id, business_name, created_at)

def get_tenant_by_id(tenant_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM tenants WHERE id = ?', (tenant_id,))
    row = c.fetchone()
    conn.close()
    return row

# ===================== MASTERS =====================

def add_master(tenant_id, name, specialty, telegram_id=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO masters (tenant_id, name, specialty, telegram_id) VALUES (?, ?, ?, ?)',
        (tenant_id, name, specialty, telegram_id)
    )
    conn.commit()
    conn.close()

def get_masters_by_tenant(tenant_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM masters WHERE tenant_id = ?', (tenant_id,))
    rows = c.fetchall()
    conn.close()
    return rows  # (id, tenant_id, name, specialty, telegram_id)

def get_master_by_id(master_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM masters WHERE id = ?', (master_id,))
    row = c.fetchone()
    conn.close()
    return row

def delete_master(master_id, tenant_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM masters WHERE id = ? AND tenant_id = ?', (master_id, tenant_id))
    conn.commit()
    conn.close()

# ===================== SERVICES =====================

def add_service(tenant_id, name, price, duration=60):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO services (tenant_id, name, price, duration) VALUES (?, ?, ?, ?)',
        (tenant_id, name, price, duration)
    )
    conn.commit()
    conn.close()

def get_services_by_tenant(tenant_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM services WHERE tenant_id = ?', (tenant_id,))
    rows = c.fetchall()
    conn.close()
    return rows  # (id, tenant_id, name, price, duration)

def update_service(service_id, tenant_id, name, price, duration):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'UPDATE services SET name = ?, price = ?, duration = ? WHERE id = ? AND tenant_id = ?',
        (name, price, duration, service_id, tenant_id)
    )
    conn.commit()
    conn.close()

def delete_service(service_id, tenant_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM services WHERE id = ? AND tenant_id = ?', (service_id, tenant_id))
    conn.commit()
    conn.close()

# ===================== APPOINTMENTS =====================

def add_appointment(tenant_id, master_id, client_name, client_phone, service, date, time):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        '''INSERT INTO appointments
           (tenant_id, master_id, client_name, client_phone, service, date, time, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (tenant_id, master_id, client_name, client_phone, service, date, time,
         datetime.now().isoformat())
    )
    appt_id = c.lastrowid
    conn.commit()
    conn.close()
    return appt_id

def get_appointments_by_tenant(tenant_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        '''SELECT a.id, a.client_name, a.client_phone, a.service, a.date, a.time,
                  a.status, m.name as master_name
           FROM appointments a
           LEFT JOIN masters m ON a.master_id = m.id
           WHERE a.tenant_id = ?
           ORDER BY a.date, a.time''',
        (tenant_id,)
    )
    rows = c.fetchall()
    conn.close()
    return rows

def update_appointment_status(appt_id, tenant_id, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'UPDATE appointments SET status = ? WHERE id = ? AND tenant_id = ?',
        (status, appt_id, tenant_id)
    )
    conn.commit()
    conn.close()