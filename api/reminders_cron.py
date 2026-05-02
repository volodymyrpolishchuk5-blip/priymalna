import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import asyncio
from datetime import datetime, timedelta
from lib import db
from aiogram import Bot
from http.server import BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        asyncio.run(self.process_reminders())
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    async def process_reminders(self):
        bot = Bot(token=BOT_TOKEN)
        try:
            # Fetch all active appointments
            # In production, you'd filter by date in SQL
            db_conn = db.get_db()
            res = db_conn.table("appointments").select("*, tenants(business_name)").eq("status", "active").execute()
            appts = res.data or []
            
            now = datetime.now()
            
            for a in appts:
                # Basic logic: parse date/time string from DB
                # Date format is "D Month", time "HH:MM"
                # This is simplified. Proper date parsing would be needed for real prod.
                # For now, we'll just implement the structure.
                
                # Check 24h reminder
                if not a.get("reminder_24h_sent"):
                    # Logic to check if appt is tomorrow
                    # ...
                    pass
                
                # Check 1h reminder
                if not a.get("reminder_1h_sent"):
                    # Logic to check if appt is in 1 hour
                    # ...
                    pass
                    
            # Placeholder for now, as real date parsing of "3 травня" is tricky without locale
            # We would typically store dates in ISO format in DB.
            
        finally:
            await bot.session.close()
