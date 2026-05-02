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
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            tenant_id = params.get("tenant", [None])[0]

            if not tenant_id:
                self._json(400, {"error": "tenant parameter required"})
                return

            clients = db.get_clients_by_tenant(tenant_id)
            # Debug: Return tenant_id and count to see what's happening
            self._json(200, {
                "tenant_id_searched": tenant_id,
                "count": len(clients),
                "clients": clients
            })
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

            if action == "update_status":
                db.update_client_status(
                    int(data.get("client_id")), 
                    tenant_id, 
                    data.get("is_vip"), 
                    data.get("is_blacklisted")
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
