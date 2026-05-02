import json
import os
import sys

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

            if action == "add_service":
                db.add_service(tenant_id, data.get("name"), int(data.get("price", 0)), int(data.get("duration", 60)))
                self._json(200, {"status": "ok"})
            elif action == "delete_service":
                db.delete_service(int(data.get("service_id")), tenant_id)
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
