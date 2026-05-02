import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
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
