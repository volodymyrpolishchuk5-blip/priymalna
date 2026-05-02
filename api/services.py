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

            if not tenant_id:
                self._json(400, {"error": "tenant parameter required"})
                return

            services = db.get_services_by_tenant(tenant_id)
            self._json(200, services)
        except Exception as e:
            import traceback
            self._json(500, {"error": str(e), "trace": traceback.format_exc()})

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            action = data.get("action")
            tenant_id = data.get("tenant_id")
            user_id = data.get("user_id")

            # Access Control: Only owner can manage services
            tenant = db.get_tenant_by_id(tenant_id)
            if not tenant:
                self._json(404, {"error": "Tenant not found"})
                return

            # Robust user_id check
            is_owner = str(tenant["owner_telegram_id"]) == str(user_id)
            if not is_owner:
                self._json(403, {"error": f"Access denied for user {user_id}"})
                return

            if action == "add_service":
                db.add_service(tenant_id, data.get("name"), int(data.get("price", 0)), int(data.get("duration", 60)))
                self._json(200, {"status": "ok"})
            elif action == "delete_service":
                db.delete_service(int(data.get("service_id")), tenant_id)
                self._json(200, {"status": "ok"})
            elif action == "update_service":
                db.update_service(
                    int(data.get("service_id")), 
                    tenant_id, 
                    data.get("name"), 
                    int(data.get("price", 0)), 
                    int(data.get("duration", 60))
                )
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
