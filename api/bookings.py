# Fix path robustly
import os
import sys
import json
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from lib import db
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            tenant_id = params.get("tenant", [None])[0]
            user_id = params.get("user_id", [None])[0]

            if not tenant_id:
                self._json(400, {"error": "tenant parameter required"})
                return

            # Check if user is owner
            tenant = db.get_tenant_by_id(tenant_id)
            is_owner = tenant and str(tenant["owner_telegram_id"]) == str(user_id)
            
            master_id = None
            if not is_owner and user_id:
                # Check if user is a master
                master = db.get_master_by_tg_id(tenant_id, str(user_id))
                if master:
                    master_id = master["id"]
                else:
                    self._json(403, {"error": "Access denied"})
                    return

            bookings = db.get_appointments_by_tenant(tenant_id, master_id)
            self._json(200, bookings)
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            action = data.get("action")
            tenant_id = data.get("tenant_id")

            if action in ("complete_booking", "cancel_booking"):
                status = "виконано" if action == "complete_booking" else "скасовано"
                db.update_appointment_status(int(data.get("appt_id")), tenant_id, status)
                self._json(200, {"status": "ok"})
            elif action == "reschedule":
                db.update_appointment_datetime(int(data.get("appt_id")), tenant_id, data.get("date"), data.get("time"))
                self._json(200, {"status": "ok"})
            elif action == "repeat_booking":
                old_appt = db.get_appointment_by_id(int(data.get("appt_id")))
                if old_appt:
                    from datetime import datetime
                    today = datetime.now().strftime("%Y-%m-%d")
                    now_time = datetime.now().strftime("%H:%M")
                    db.add_appointment(
                        tenant_id,
                        old_appt["master_id"],
                        old_appt["client_id"],
                        old_appt["client_name"],
                        old_appt["client_phone"],
                        old_appt["service"],
                        old_appt["price"],
                        today,
                        now_time
                    )
                    self._json(200, {"status": "ok"})
                else:
                    self._json(404, {"error": "Appointment not found"})
            elif action == "repeat_booking_with_time":
                old_appt = db.get_appointment_by_id(int(data.get("appt_id")))
                if old_appt:
                    db.add_appointment(
                        tenant_id,
                        old_appt["master_id"],
                        old_appt["client_id"],
                        old_appt["client_name"],
                        old_appt["client_phone"],
                        old_appt["service"],
                        old_appt["price"],
                        data.get("date"),
                        data.get("time")
                    )
                    self._json(200, {"status": "ok"})
                else:
                    self._json(404, {"error": "Appointment not found"})
            else:
                self._json(400, {"error": "invalid action"})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
