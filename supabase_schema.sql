-- =============================================
-- Supabase Schema for Booking Bot
-- Run this in: Supabase → SQL Editor → New Query
-- =============================================

-- 1. Tenants (businesses)
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    owner_telegram_id BIGINT UNIQUE NOT NULL,
    business_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Masters
CREATE TABLE IF NOT EXISTS masters (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    specialty TEXT,
    telegram_id TEXT -- Може бути ID (число) або @username
);

-- 3. Services
CREATE TABLE IF NOT EXISTS services (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    duration INTEGER DEFAULT 60
);

-- 4. Clients
CREATE TABLE IF NOT EXISTS clients (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    birthday TEXT,
    is_vip BOOLEAN DEFAULT FALSE,
    is_blacklisted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, phone)
);

-- 5. Appointments
CREATE TABLE IF NOT EXISTS appointments (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    master_id BIGINT REFERENCES masters(id) ON DELETE SET NULL,
    client_id BIGINT REFERENCES clients(id) ON DELETE CASCADE,
    client_name TEXT NOT NULL,
    client_phone TEXT NOT NULL,
    service TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    status TEXT DEFAULT 'active', -- active, виконано, скасовано, waitlist
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Enable Row Level Security (recommended)
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE masters ENABLE ROW LEVEL SECURITY;
ALTER TABLE services ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;

-- 7. Allow full access via service_role key (used by backend)
CREATE POLICY "Allow all for service role" ON tenants FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON masters FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON services FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON clients FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON appointments FOR ALL USING (true);
